"""
Reserve agent: Claude + tools over your Apple Watch data.

How it works (the "agent loop"):
  1. Your question goes to Claude along with a description of the TOOLS below.
  2. Claude either answers, or asks to call one or more tools.
  3. This script runs those tools (plain pandas on data/daily_scores.csv) and sends
     the results back.
  4. Repeat until Claude has what it needs and writes a final answer.

Claude never sees the raw CSV. It only sees what the tools return, so every number
in its answer comes from your data, and all math happens here in Python.

Use:  python agent.py "Why was my readiness so low last week?"
  or, in a notebook:  from agent import ask;  ask("...")
"""
import json
import math
import re
import sqlite3
from pathlib import Path

import anthropic
import numpy as np
import pandas as pd
from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE / ".env", override=True)

import os
DB = Path(os.environ.get("RESERVE_DB", HERE / "data" / "reserve.db"))   # built by build_db.py
def _db_ready():
    try:
        with sqlite3.connect(DB) as con:
            return con.execute("SELECT count(*) FROM sqlite_master WHERE name IN ('daily','workouts')").fetchone()[0] == 2
    except sqlite3.Error:
        return False

if not _db_ready():                        # missing or empty database -> build it from the CSVs
    print("Building data/reserve.db from the CSVs (one time)...")
    import runpy
    runpy.run_path(str(HERE / "build_db.py"))

with sqlite3.connect(DB) as _con:
    DAILY = pd.read_sql("SELECT * FROM daily ORDER BY date", _con, index_col="date")
    WORKOUTS = pd.read_sql("SELECT * FROM workouts ORDER BY start", _con)
FIRST, LAST = DAILY.index.min(), DAILY.index.max()

# Columns Claude may ask for, with plain-English meanings (also shown to Claude)
COLUMNS = {
    "readiness": "Readiness score 1-100 (percentile-style vs. the previous 30 days)",
    "readiness_change": "Change in readiness vs. the previous day",
    "hrv_ms": "Raw nightly HRV (SDNN, ms) - noisy day to day",
    "hrv_smoothed": "3-day smoothed HRV (ms) - this is what the readiness score uses",
    "hrv_baseline": "30-day HRV baseline (ms)",
    "resting_hr": "Resting heart rate (bpm)",
    "rhr_baseline": "30-day resting HR baseline (bpm)",
    "sleep_hrs": "Hours asleep the night before (Apple Watch stages)",
    "sleep_baseline": "30-day sleep baseline (hours)",
    "deep_hrs": "Deep sleep hours", "rem_hrs": "REM sleep hours",
    "bedtime": "Time fell asleep", "wake_time": "Time woke up",
    "respiratory_rate": "Breaths per minute",
    "impact_hrv": "Readiness points added/removed by HRV",
    "impact_rhr": "Readiness points added/removed by resting HR",
    "impact_sleep": "Readiness points added/removed by sleep",
    "impact_resp": "Readiness points removed by elevated respiratory rate",
    "workouts": "Number of workouts that day", "workout_types": "Workout types",
    "workout_min": "Workout minutes", "training_load": "Training load (TRIMP) that day",
    "late_workout": "1 if a workout ended at/after 7 PM", "load_7d": "7-day training load",
    "acwr": "Acute:chronic workload ratio (7-day vs 28-day)",
    "steps": "Steps", "vo2max": "VO2 max estimate",
}

NUMERIC = [c for c in COLUMNS if c in DAILY and pd.api.types.is_numeric_dtype(DAILY[c])]

# ---------------------------------------------------------------- helpers
def _clean(obj):
    """Make pandas/numpy values JSON-safe (NaN -> None, numpy -> python)."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if math.isnan(obj) else round(float(obj), 2)
    if isinstance(obj, np.integer):
        return int(obj)
    return obj

def _window(start, end):
    d = DAILY.loc[max(start, FIRST): min(end, LAST)]
    if d.empty:
        raise ValueError(f"No data between {start} and {end}. Data covers {FIRST} to {LAST}.")
    return d

# ---------------------------------------------------------------- tools
def get_days(start: str, end: str, columns: list = None):
    """Daily rows for a date range (max 45 days)."""
    d = _window(start, end)
    if len(d) > 45:
        return {"error": "Range too long - use get_summary for periods over 45 days."}
    cols = [c for c in (columns or ["readiness", "hrv_smoothed", "resting_hr", "sleep_hrs",
                                    "impact_hrv", "impact_rhr", "impact_sleep", "impact_resp",
                                    "workouts", "training_load"]) if c in DAILY]
    return {"days": _clean(d[cols].reset_index().to_dict(orient="records"))}

def get_summary(start: str, end: str, metrics: list):
    """Average / median / min / max / trend of metrics over any period."""
    d = _window(start, end)
    out = {"period": f"{d.index[0]} to {d.index[-1]}", "days": len(d)}
    for m in metrics:
        if m not in DAILY or not pd.api.types.is_numeric_dtype(DAILY[m]):
            out[m] = "unknown or non-numeric metric"; continue
        s = d[m].dropna()
        if s.empty:
            out[m] = "no data"; continue
        half = len(s) // 2
        out[m] = {"mean": s.mean(), "median": s.median(), "min": s.min(), "min_date": s.idxmin(),
                  "max": s.max(), "max_date": s.idxmax(), "days_with_data": len(s),
                  "first_half_mean": s.iloc[:half].mean() if half else None,
                  "second_half_mean": s.iloc[half:].mean()}
    return _clean(out)

def explain_day(date: str):
    """Everything needed to explain one day's readiness score."""
    if date not in DAILY.index:
        return {"error": f"No row for {date}. Data covers {FIRST} to {LAST}."}
    i = DAILY.index.get_loc(date)
    row = DAILY.iloc[i]
    prev = DAILY.iloc[max(0, i - 3): i]
    resp_base = DAILY.respiratory_rate.iloc[max(0, i - 30): i].mean()
    keys = ["readiness", "readiness_change", "hrv_ms", "hrv_smoothed", "hrv_baseline", "resting_hr",
            "rhr_baseline", "sleep_hrs", "sleep_baseline", "bedtime", "respiratory_rate",
            "impact_hrv", "impact_rhr", "impact_sleep", "impact_resp", "signals_used"]
    return _clean({
        "date": date,
        "today": {**{k: row.get(k) for k in keys}, "respiratory_baseline_30d": resp_base},
        "previous_3_days": prev[["readiness", "hrv_ms", "resting_hr", "sleep_hrs", "workouts",
                                  "training_load", "late_workout"]].reset_index().to_dict(orient="records"),
        "workouts_day_before": WORKOUTS[WORKOUTS.date == (DAILY.index[i - 1] if i else "")]
            [["type", "start", "duration_min", "avg_hr"]].to_dict(orient="records"),
    })

CONDITIONS = {
    "late_workout": ("a workout ended at/after 7 PM", lambda d: d.late_workout == 1, lambda d: (d.workouts > 0) & (d.late_workout == 0)),
    "any_workout": ("any workout", lambda d: d.workouts > 0, lambda d: d.workouts == 0),
    "hard_day": ("training load in your top 25% of workout days",
                 lambda d: d.training_load >= d.training_load[d.training_load > 0].quantile(.75),
                 lambda d: (d.training_load > 0) & (d.training_load < d.training_load[d.training_load > 0].quantile(.75))),
    "short_sleep": ("under 6 hours of sleep", lambda d: d.sleep_hrs < 6, lambda d: d.sleep_hrs >= 7),
    "weekend": ("Friday or Saturday", lambda d: d.weekday.isin(["Friday", "Saturday"]),
                lambda d: ~d.weekday.isin(["Friday", "Saturday"])),
}

SAME_DAY_DEFAULT = {"short_sleep"}   # sleep_hrs on a date = the night BEFORE it, so its effect shows the same day

def compare_groups(condition: str, metric: str = "readiness", next_day: bool = None,
                   start: str = None, end: str = None):
    """Compare a metric between days where a condition was true vs. a comparison group."""
    if condition not in CONDITIONS:
        return {"error": f"condition must be one of {list(CONDITIONS)}"}
    if next_day is None:
        next_day = condition not in SAME_DAY_DEFAULT
    d = _window(start or FIRST, end or LAST).copy()
    label, is_true, is_compare = CONDITIONS[condition]
    if metric not in NUMERIC:
        return {"error": f"'{metric}' isn't numeric. Use one of {NUMERIC}"}
    target = d[metric].shift(-1) if next_day else d[metric]
    a, b = target[is_true(d)].dropna(), target[is_compare(d)].dropna()
    if len(a) < 5 or len(b) < 5:
        return {"error": f"Not enough days (n={len(a)} vs {len(b)}) for a fair comparison."}
    diff = a.mean() - b.mean()
    se = math.sqrt(a.var() / len(a) + b.var() / len(b))
    pooled = math.sqrt((a.var() + b.var()) / 2)
    t = diff / se if se else 0
    p = math.erfc(abs(t) / math.sqrt(2))      # normal approx of a two-sided Welch test
    return _clean({
        "condition": label, "metric": metric, "measured": "the NEXT day" if next_day else "the same day",
        "condition_true": {"mean": a.mean(), "n": len(a)},
        "comparison": {"mean": b.mean(), "n": len(b)},
        "difference": diff, "effect_size_d": diff / pooled if pooled else None, "p_value": p,
        "note": "Observational data: other factors can differ between these days. |d|<0.2 is a negligible effect.",
    })

def get_workouts(start: str, end: str):
    """List individual workouts in a date range."""
    w = WORKOUTS[(WORKOUTS.date >= start) & (WORKOUTS.date <= end)]
    return {"workouts": _clean(w[["date", "type", "start", "duration_min", "kcal", "avg_hr", "max_hr"]]
                               .to_dict(orient="records")), "count": len(w)}

def run_sql(query: str):
    """Read-only SQL for questions the other tools can't answer (max 200 rows)."""
    q = query.strip().rstrip(";")
    if not re.match(r"(?is)^\s*(select|with)\b", q) or ";" in q:
        return {"error": "Only a single SELECT (or WITH ... SELECT) statement is allowed."}
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)     # opened read-only: can't modify data
    try:
        df = pd.read_sql(q, con)
    finally:
        con.close()
    return {"rows": _clean(df.head(200).to_dict(orient="records")), "row_count": len(df),
            "truncated": len(df) > 200}

TOOLS = {f.__name__: f for f in (get_days, get_summary, explain_day, compare_groups, get_workouts, run_sql)}

# ---------------------------------------------------------------- tool descriptions for Claude
date = {"type": "string", "description": "YYYY-MM-DD"}
TOOL_SPECS = [
    {"name": "get_days", "description": "Get daily rows (max 45 days) for a date range. Use for 'what happened last week' style questions.",
     "input_schema": {"type": "object", "properties": {"start": date, "end": date,
        "columns": {"type": "array", "items": {"type": "string", "enum": list(COLUMNS)}, "description": "Optional; sensible defaults if omitted."}},
        "required": ["start", "end"]}},
    {"name": "get_summary", "description": "Mean/median/min/max and first-half vs second-half trend of numeric metrics over any period (use for months/years).",
     "input_schema": {"type": "object", "properties": {"start": date, "end": date,
        "metrics": {"type": "array", "items": {"type": "string", "enum": NUMERIC}}},
        "required": ["start", "end", "metrics"]}},
    {"name": "explain_day", "description": "Full breakdown of one day's readiness: each signal vs. baseline, the points each added/removed, the previous 3 days, and the day-before workouts. Use whenever asked WHY a score was high or low.",
     "input_schema": {"type": "object", "properties": {"date": date}, "required": ["date"]}},
    {"name": "compare_groups", "description": "Statistically compare a metric between days where a condition held vs. a comparison group (with n, difference, effect size, p-value). Use for 'does X affect my recovery?' questions. By default measures the metric the NEXT day (same day for short_sleep, since sleep_hrs on a date is the night before it).",
     "input_schema": {"type": "object", "properties": {
        "condition": {"type": "string", "enum": list(CONDITIONS), "description": "; ".join(f"{k} = {v[0]}" for k, v in CONDITIONS.items())},
        "metric": {"type": "string", "enum": NUMERIC},
        "next_day": {"type": "boolean"}, "start": date, "end": date}, "required": ["condition"]}},
    {"name": "run_sql", "description": "Run a read-only SQLite SELECT against tables `daily` (one row per date; columns as listed in the system prompt plus weekday, deep_hrs, steps, etc.) and `workouts` (date, type, start, end, duration_min, kcal, distance, avg_hr, max_hr). Use ONLY when the other tools can't answer, e.g. rankings, custom filters, monthly groupings (strftime('%Y-%m', date)). Max 200 rows returned.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "get_workouts", "description": "List individual workouts (type, start time, duration, calories, heart rate) in a date range.",
     "input_schema": {"type": "object", "properties": {"start": date, "end": date}, "required": ["start", "end"]}},
]

SYSTEM = f"""You are Reserve, a recovery analyst for Alex's own Apple Watch data ({FIRST} to {LAST}).
"Today" means {LAST}, the latest day with data.

How the readiness score works: each day HRV (3-day smoothed, 50% weight), resting HR (25%) and sleep (25%)
are compared to the previous 30 days; respiratory rate only subtracts when elevated. The score is 1-100 and
reads like a percentile vs. recent days. impact_* columns are the points each signal added or removed.

Columns: {json.dumps(COLUMNS)}

Rules:
- Use tools for every number you state. Never estimate or invent data.
- Be concise: lead with the answer, then the 2-3 numbers that support it.
- For comparisons, report sample sizes and effect size, and say plainly when an effect is small or uncertain.
  This is observational data from one person: say "associated with", not "causes".
- You are not a doctor. If data looks like illness or something concerning, say it is worth paying attention
  to, without diagnosing."""

# ---------------------------------------------------------------- the agent loop
client = anthropic.Anthropic()
MODEL = None

def _model():
    global MODEL
    if MODEL is None:
        MODEL = next(iter(client.models.list(limit=1))).id     # newest model your key can use
    return MODEL

def ask(question: str, max_steps: int = 8, verbose: bool = True, trace: list = None) -> str:
    """Run the agent loop. Pass a list as `trace` to collect each tool call (used by the API)."""
    messages = [{"role": "user", "content": question}]
    for _ in range(max_steps):
        resp = client.messages.create(model=_model(), max_tokens=4000, system=SYSTEM,
                                      tools=TOOL_SPECS, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})   # keep ALL blocks (incl. thinking)

        if resp.stop_reason != "tool_use":
            answer = "".join(b.text for b in resp.content if b.type == "text")
            if verbose:
                print("\n" + answer)
            return answer

        results = []
        for block in resp.content:
            if block.type == "tool_use":
                if verbose:
                    print(f"  -> {block.name}({json.dumps(block.input)})")
                if trace is not None:
                    trace.append({"tool": block.name, "input": block.input})
                try:
                    output = TOOLS[block.name](**block.input)
                except Exception as e:                       # let Claude see and recover from errors
                    output = {"error": f"{type(e).__name__}: {e}"}
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(output, default=str)})
        messages.append({"role": "user", "content": results})
    return "Stopped: reached the step limit without a final answer."


if __name__ == "__main__":
    import sys
    ask(" ".join(sys.argv[1:]) or "How has my readiness been over the last two weeks, and why?")
