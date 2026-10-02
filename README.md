# Reserve — a personal readiness dashboard and AI agent built on Apple Watch data

Reserve turns ~1,000 days of my own Apple Watch data into a daily **Readiness score (1–100)**,
explains *why* the score moved, and lets me ask an AI agent (Claude) questions about my own
recovery — and run small experiments on my habits.

> Status: in progress. Pipeline, scoring model, AI agent, database and API complete; dashboard next.

## Why this project
Wearables tell you a score, not the reasoning behind it. Reserve is built to be transparent:
every score is decomposed into what helped and what hurt, the method is documented, and
the agent only states numbers it pulled from the data.

## Pipeline
| Step | Script | Output |
|---|---|---|
| 1. Parse | `parse_health.py` — streams the 1.4 GB Apple Health `export.xml` straight out of the zip | tidy CSVs (heart rate, HRV, sleep, workouts, …) |
| 2. Daily table | `build_daily.py` — one row per day; sleep assigned to wake date; training load via Banister TRIMP | `data/daily.csv` |
| 3. Scores | `scores.py` — Readiness, per-signal impact points, training-load context | `data/daily_scores.csv` |
| 4. Database | `build_db.py` — loads daily scores and workouts into SQLite | `data/reserve.db` |
| 5. Agent | `agent.py` — Claude + 6 tools (incl. read-only SQL) in a tool-use loop | answers in plain English |
| 6. API | `api.py` — FastAPI endpoints for the dashboard (`/api/today`, `/api/trend`, `/api/ask`, …) | JSON |

## The agent
Claude never sees the raw data. It answers by calling tools that run in Python — `get_days`, `get_summary`,
`explain_day`, `compare_groups` (difference, effect size, p-value), `get_workouts`, and `run_sql`
(single read-only SELECT, enforced by opening SQLite in read-only mode). All math happens in code;
Claude decides what to look up and explains the results.

Example findings from my own data:
- Late workouts (ending after 7 PM) showed **no meaningful effect** on next-day readiness (d = −0.06).
- Readiness after Friday/Saturday nights averages **5.7 points lower** (n = 264, d = −0.21), driven mainly by shorter sleep rather than HRV or resting HR.

## Readiness model
Each signal is compared to **my own previous 30 days** (z-scores; today never sees itself):

| Signal | Direction | Weight | Rationale |
|---|---|---|---|
| HRV (log, 3-day smoothed) | higher = better | 50% | Most-studied daily recovery marker; basis of HRV-guided training research |
| Resting heart rate | lower = better | 25% | Useful but slower to respond than HRV |
| Sleep duration | more = better (capped) | 25% | A driver of recovery rather than a direct measure of it |
| Respiratory rate | penalty only when elevated | — | Normally very stable; a rise can be an early illness signal |

The weighted composite is converted to a **1–100 percentile-style score**: 72 ≈ "better than ~72% of my recent days."

**Robustness check:** alternative weightings (equal; 70/15/15) correlate **0.97** with the chosen
weights, so conclusions don't hinge on the exact split.

## Roadmap
- [x] Data pipeline and daily table
- [x] Readiness model with explanations
- [x] AI agent (Claude + tool use) that answers questions from the data
- [x] SQLite storage + FastAPI backend
- [ ] Next.js dashboard
- [ ] Habit experiments (before/after with effect size)

## Running it
```bash
pip install -r requirements.txt
python parse_health.py "path/to/export.zip"   # default: raw/AO Apple Watch Health.zip
python build_daily.py
python scores.py
python build_db.py
uvicorn api:app --reload      # then open http://127.0.0.1:8000/docs
```
Personal health data (`data/`) and the API key (`.env`) are excluded from this repo.
