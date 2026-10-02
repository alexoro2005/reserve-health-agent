"""
Reserve API (FastAPI) - the layer the dashboard talks to.

Run:   uvicorn api:app --reload
Docs:  http://127.0.0.1:8000/docs   (interactive page to try every endpoint)

Data endpoints reuse the agent's tools, so the dashboard and the agent always agree.
"""
from datetime import date as _date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import agent
from agent import DAILY, LAST, _clean

app = FastAPI(title="Reserve API", description="Readiness, explanations and an AI agent over Apple Watch data")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
                   allow_methods=["*"], allow_headers=["*"])


def _check(result):
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/health")
def health():
    return {"status": "ok", "data_from": agent.FIRST, "data_to": LAST, "days": len(DAILY)}


@app.get("/api/today")
def today():
    """Hero card: latest readiness with its full explanation."""
    latest = DAILY.dropna(subset=["readiness"]).index[-1]
    return _check(agent.explain_day(latest))


@app.get("/api/explain/{day}")
def explain(day: str):
    return _check(agent.explain_day(day))


@app.get("/api/trend")
def trend(days: int = Query(30, ge=7, le=365)):
    """Readiness and key signals for the last N days (trend chart)."""
    d = DAILY.iloc[-days:][["readiness", "hrv_smoothed", "hrv_baseline", "resting_hr", "sleep_hrs",
                            "impact_hrv", "impact_rhr", "impact_sleep", "impact_resp", "training_load"]]
    return {"days": _clean(d.reset_index().to_dict(orient="records"))}


@app.get("/api/days")
def days(start: str, end: str, columns: list[str] = Query(None)):
    return _check(agent.get_days(start, end, columns))


@app.get("/api/summary")
def summary(start: str, end: str, metrics: list[str] = Query(["readiness", "sleep_hrs", "hrv_smoothed"])):
    return _check(agent.get_summary(start, end, metrics))


@app.get("/api/compare")
def compare(condition: str, metric: str = "readiness"):
    """Experiments / 'what helps or hurts' cards."""
    return _check(agent.compare_groups(condition, metric))


@app.get("/api/workouts")
def workouts(start: str, end: str):
    return _check(agent.get_workouts(start, end))


class Question(BaseModel):
    question: str


@app.post("/api/ask")
def ask(q: Question):
    """The 'Ask about your data' bar: runs the agent and returns its answer plus the tools it used."""
    trace = []
    answer = agent.ask(q.question, verbose=False, trace=trace)
    return {"answer": answer, "tools_used": trace}


_briefing_cache = {}

@app.get("/api/briefing")
def briefing():
    """Daily coach note, generated once per data-day and cached (saves API cost)."""
    key = LAST
    if key not in _briefing_cache:
        trace = []
        text = agent.ask(f"Write today's ({LAST}) briefing: 2-3 sentences on readiness and what drove it, "
                         "then one specific recommendation for today. No headers or tables.",
                         verbose=False, trace=trace)
        _briefing_cache[key] = {"date": key, "briefing": text, "tools_used": trace}
    return _briefing_cache[key]
