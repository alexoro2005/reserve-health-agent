"""
Step 3 of the Reserve pipeline: data/daily.csv -> data/daily_scores.csv

READINESS (0-100) — "how does today's body compare to MY normal?"
  1. Personal baseline: for each signal, the mean and spread of the previous 30 days
     (today is excluded, so the score never "peeks" at itself; needs >= 10 days of data).
  2. z-score per signal = how many standard deviations today sits from baseline.
       HRV          higher is better   (log scale, 3-day smoothed)        weight 0.50
       Resting HR   lower is better                                      weight 0.25
       Sleep hours  more is better (capped at +1 SD so oversleeping isn't "extra" good) weight 0.25
       Resp. rate   only penalized when ELEVATED (> +1 SD, an early illness signal)    penalty
  3. Composite = weighted average of the z-scores that exist today (missing signals are
     skipped and their weight redistributed; `signals_used` records how many we had).
  4. Readiness = 1 + 99 x normal CDF of the composite, standardized by its own 90-day spread
     -> reads like a percentile: 72 = better than ~72% of your recent days.

IMPACT columns (readiness points, can be negative): for each signal, how many readiness points it added or removed
versus a day where that signal sat exactly at baseline. Powers "What changed?" and the
"helped vs. hurt" chart, and gives the agent something concrete to explain.

TRAINING LOAD context (not part of readiness, which measures recovery, not effort):
  load_7d (acute), load_28d (chronic, weekly avg), and their ratio (ACWR).
"""
import numpy as np
import pandas as pd
from math import erf, sqrt
from pathlib import Path

D = Path(__file__).parent / "data"
WINDOW, MIN_DAYS = 30, 10
HRV_SPAN = 3               # smooth HRV over ~3 days: Apple takes few readings, so one day is noisy
WEIGHTS = {"hrv": 0.50, "rhr": 0.25, "sleep": 0.25}
RESP_PENALTY = 0.5          # z-units subtracted per SD that respiratory rate is above +1 SD

d = pd.read_csv(D / "daily.csv", index_col="date")


def baseline_z(series):
    """z-score of each day vs. the previous WINDOW days (excluding today)."""
    prior = series.shift(1).rolling(WINDOW, min_periods=MIN_DAYS)
    mean, sd = prior.mean(), prior.std()
    return (series - mean) / sd.where(sd > 0), mean


z = pd.DataFrame(index=d.index)
log_hrv = np.log(d.hrv_ms)
log_hrv_smooth = log_hrv.ewm(span=HRV_SPAN, ignore_na=True).mean().where(log_hrv.notna() | log_hrv.shift(1).notna())
d["hrv_smoothed"] = np.exp(log_hrv_smooth).round(1)
z["hrv"], d["hrv_baseline"] = baseline_z(log_hrv_smooth)
d["hrv_baseline"] = np.exp(d.hrv_baseline)
z["rhr"], d["rhr_baseline"] = baseline_z(d.resting_hr)
z["rhr"] = -z.rhr                                   # lower resting HR = better
z["sleep"], d["sleep_baseline"] = baseline_z(d.sleep_hrs)
z["sleep"] = z.sleep.clip(upper=1)
z_resp, _ = baseline_z(d.respiratory_rate)
z = z.clip(-3, 3)                                    # one weird reading can't dominate

w = pd.DataFrame({k: np.where(z[k].notna(), v, 0.0) for k, v in WEIGHTS.items()}, index=d.index)
wsum = w.sum(axis=1)
composite = (z[list(WEIGHTS)].fillna(0) * w).sum(axis=1) / wsum.where(wsum > 0)
resp_pen = (z_resp - 1).clip(lower=0).fillna(0) * RESP_PENALTY
composite = composite - resp_pen

spread = composite.rolling(90, min_periods=20).std().bfill()
phi = np.vectorize(lambda x: 0.5 * (1 + erf(x / sqrt(2))) if np.isfinite(x) else np.nan)
d["readiness"] = np.round(1 + 99 * phi(composite / spread))   # scale 1-100
d["signals_used"] = (w > 0).sum(axis=1)
d.loc[wsum < 0.5, "readiness"] = np.nan             # need HRV, or both RHR and sleep

# ---- contributions in readiness points (vs. that signal sitting at baseline) ----
for k in WEIGHTS:
    without = composite - (z[k].fillna(0) * w[k]) / wsum.where(wsum > 0)
    d[f"impact_{k}"] = np.round(d.readiness - (1 + 99 * phi(without / spread)), 1)
d["impact_resp"] = np.round(d.readiness - (1 + 99 * phi((composite + resp_pen) / spread)), 1)
for k in ("hrv", "rhr", "sleep"):
    d[f"zscore_{k}"] = z[k].round(2)

# ---- training load context ----
d["load_7d"] = d.training_load.rolling(7, min_periods=1).sum().round(1)
d["load_28d_weekly"] = (d.training_load.rolling(28, min_periods=7).sum() / 4).round(1)
d["acwr"] = (d.load_7d / d.load_28d_weekly.where(d.load_28d_weekly > 0)).round(2)

d["readiness_change"] = d.readiness.diff()
# readiness first, then the signals, then the explanation columns
front = ["readiness", "readiness_change", "hrv_ms", "hrv_baseline", "resting_hr", "rhr_baseline",
         "sleep_hrs", "sleep_baseline", "impact_hrv", "impact_rhr", "impact_sleep", "impact_resp"]
d = d[front + [c for c in d.columns if c not in front]]
d.round(2).to_csv(D / "daily_scores.csv")
print(f"Wrote data/daily_scores.csv — readiness on {d.readiness.notna().sum()} of {len(d)} days")
