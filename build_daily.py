"""
Step 2 of the Reserve pipeline: tidy CSVs -> data/daily.csv (one row per day).

Conventions
- Dates are LOCAL dates taken from Apple's timestamps (e.g. "2026-09-22 19:05:41 -0600").
- Sleep is assigned to the morning you WOKE UP (a night ending Sep 24 counts for Sep 24).
- Steps / active calories: the iPhone and Watch both log these, so we take the larger
  of the two per-device daily totals instead of adding them (avoids double counting).
- Workout training load uses Banister's TRIMP:
      minutes * HRr * 0.64 * e^(1.92 * HRr),  HRr = (avg HR - resting HR) / (max HR - resting HR)
"""
import numpy as np
import pandas as pd
from pathlib import Path

D = Path(__file__).parent / "data"
WATCH_START = "2023-12-24"


def local_date(s):
    return s.str[:10]


def local_hour(s):
    return s.str[11:13].astype(int) + s.str[14:16].astype(int) / 60


# ---------- quantity records ----------
r = pd.read_csv(D / "records.csv")
r["date"] = local_date(r.start)

def daily_mean(metric, scale=1):
    x = r[r.metric == metric]
    return x.groupby("date").value.mean() * scale

def max_device_total(metric):
    x = r[r.metric == metric]
    return x.groupby(["date", "source"]).value.sum().groupby("date").max()

hrv = r[r.metric == "hrv_sdnn"].groupby("date").value
daily = pd.DataFrame({
    "hrv_ms": hrv.mean(),
    "hrv_readings": hrv.size(),
    "resting_hr": daily_mean("resting_hr"),
    "respiratory_rate": daily_mean("respiratory_rate"),
    "spo2_pct": daily_mean("spo2", 100),
    "steps": max_device_total("steps"),
    "active_kcal": max_device_total("active_kcal"),
    "exercise_min": r[r.metric == "exercise_min"].groupby("date").value.sum(),
    "vo2max": daily_mean("vo2max"),
})

# ---------- sleep (Apple Watch stages only) ----------
s = pd.read_csv(D / "sleep_segments.csv")
s = s[s.source.str.contains("Watch")].copy()
s["start_ts"] = pd.to_datetime(s.start.str[:19])
s["end_ts"] = pd.to_datetime(s.end.str[:19])
s["hrs"] = (s.end_ts - s.start_ts).dt.total_seconds() / 3600
s["date"] = local_date(s.end)
s = s[s.end_ts.dt.hour < 14]          # overnight sleep only (wake before 2 PM); naps ignored for now
stage = s.pivot_table(index="date", columns="stage", values="hrs", aggfunc="sum").fillna(0)
asleep_cols = [c for c in ("AsleepCore", "AsleepDeep", "AsleepREM", "AsleepUnspecified") if c in stage]
sleep = pd.DataFrame({
    "sleep_hrs": stage[asleep_cols].sum(axis=1),
    "deep_hrs": stage.get("AsleepDeep", 0),
    "rem_hrs": stage.get("AsleepREM", 0),
    "core_hrs": stage.get("AsleepCore", 0),
    "awake_hrs": stage.get("Awake", 0),
})
asleep = s[s.stage.str.startswith("Asleep")]
sleep["bedtime"] = asleep.groupby("date").start_ts.min().dt.strftime("%H:%M")
sleep["wake_time"] = asleep.groupby("date").end_ts.max().dt.strftime("%H:%M")
sleep.loc[sleep.sleep_hrs < 2, :] = np.nan      # < 2h usually means the watch wasn't worn
daily = daily.join(sleep, how="outer")

# ---------- workouts ----------
w = pd.read_csv(D / "workouts.csv")
w["date"] = local_date(w.start)
w["end_hour"] = local_hour(w.end)
rest = daily.resting_hr.rolling(30, min_periods=5).median()   # recent resting HR baseline
w["rest_hr"] = w.date.map(rest).fillna(daily.resting_hr.median())
hr_max = w.max_hr.quantile(0.98)                                # observed max HR
hrr = ((w.avg_hr - w.rest_hr) / (hr_max - w.rest_hr)).clip(0, 1)
w["trimp"] = (w.duration_min * hrr * 0.64 * np.exp(1.92 * hrr)).fillna(0)
wd = w.groupby("date").agg(
    workouts=("type", "size"),
    workout_min=("duration_min", "sum"),
    workout_kcal=("kcal", "sum"),
    training_load=("trimp", "sum"),
    last_workout_end=("end_hour", "max"),
    workout_types=("type", lambda x: ", ".join(sorted(set(x)))),
)
wd["late_workout"] = (wd.last_workout_end >= 19).astype(int)
daily = daily.join(wd, how="outer")

# ---------- tidy up ----------
daily.index.name = "date"
daily = daily[daily.index >= WATCH_START].sort_index()
full = pd.date_range(daily.index.min(), daily.index.max()).strftime("%Y-%m-%d")
daily = daily.reindex(full)
daily.index.name = "date"
for c in ("workouts", "workout_min", "workout_kcal", "training_load", "late_workout"):
    daily[c] = daily[c].fillna(0)
daily["weekday"] = pd.to_datetime(daily.index).day_name()
daily = daily.round(2)
daily.to_csv(D / "daily.csv")
print(f"Wrote data/daily.csv: {len(daily)} days, {daily.shape[1]} columns  (max HR used: {hr_max:.0f})")
