"""
Step 4 of the Reserve pipeline: CSVs -> data/reserve.db (SQLite)

Tables
  daily     one row per day: all signals, baselines, readiness, impact points, training load
  workouts  one row per workout
Run after scores.py:  python build_db.py
"""
import sqlite3
from pathlib import Path
import pandas as pd

D = Path(__file__).resolve().parent / "data"
daily = pd.read_csv(D / "daily_scores.csv")
workouts = pd.read_csv(D / "workouts.csv")
workouts.insert(0, "date", workouts.start.str[:10])

import os
OUT = Path(os.environ.get("RESERVE_DB", D / "reserve.db"))
with sqlite3.connect(OUT) as con:
    daily.to_sql("daily", con, if_exists="replace", index=False)
    workouts.to_sql("workouts", con, if_exists="replace", index=False)
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_daily_date ON daily(date)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_workouts_date ON workouts(date)")
print(f"Wrote data/reserve.db: daily={len(daily)} rows, workouts={len(workouts)} rows")
