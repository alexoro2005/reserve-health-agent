"""
Step 1 of the Reserve pipeline: Apple Health export.zip -> tidy CSV tables.

export.xml is ~1.4 GB, so we stream it line by line straight out of the zip
(no unzipping, low memory) and keep only the data types the project needs.
Writes one CSV per table into ./data/.

Run:  python parse_health.py   (reads raw/AO Apple Watch Health.zip by default)
"""
import csv, io, re, sys, time, zipfile
from pathlib import Path

HERE = Path(__file__).parent
ZIP_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "raw" / "AO Apple Watch Health.zip"
OUT = HERE / "data"
OUT.mkdir(exist_ok=True)

ATTR = re.compile(r'(\w+)="([^"]*)"')

# Quantity records we keep: Apple identifier -> short name
QUANTITY = {
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": "hrv_sdnn",
    "HKQuantityTypeIdentifierRestingHeartRate": "resting_hr",
    "HKQuantityTypeIdentifierRespiratoryRate": "respiratory_rate",
    "HKQuantityTypeIdentifierOxygenSaturation": "spo2",
    "HKQuantityTypeIdentifierAppleSleepingWristTemperature": "wrist_temp",
    "HKQuantityTypeIdentifierVO2Max": "vo2max",
    "HKQuantityTypeIdentifierStepCount": "steps",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "active_kcal",
    "HKQuantityTypeIdentifierAppleExerciseTime": "exercise_min",
}
HR = "HKQuantityTypeIdentifierHeartRate"
SLEEP = "HKCategoryTypeIdentifierSleepAnalysis"


def record_type(line):
    i = line.find('type="')
    return line[i + 6: line.find('"', i + 6)] if i >= 0 else ""


def main():
    t0 = time.time()
    files = {n: open(OUT / f"{n}.csv", "w", newline="", encoding="utf-8")
             for n in ("heart_rate", "records", "sleep_segments", "workouts")}
    w = {n: csv.writer(f) for n, f in files.items()}
    w["heart_rate"].writerow(["start", "bpm", "source"])
    w["records"].writerow(["metric", "start", "end", "value", "unit", "source"])
    w["sleep_segments"].writerow(["start", "end", "stage", "source"])
    w["workouts"].writerow(["type", "start", "end", "duration_min", "kcal", "distance",
                            "distance_unit", "avg_hr", "max_hr", "source"])
    counts = {}
    workout = None  # attributes of the <Workout> we're inside, if any

    with zipfile.ZipFile(ZIP_PATH) as z:
        name = next(n for n in z.namelist() if n.endswith("/export.xml"))
        with io.TextIOWrapper(z.open(name), encoding="utf-8") as fh:
            for line in fh:
                s = line.lstrip()
                if s.startswith("<Record "):
                    rtype = record_type(s)
                    if rtype == HR:
                        a = dict(ATTR.findall(s))
                        w["heart_rate"].writerow([a["startDate"], a["value"], a.get("sourceName", "")])
                        counts["heart_rate"] = counts.get("heart_rate", 0) + 1
                    elif rtype in QUANTITY:
                        a = dict(ATTR.findall(s)); m = QUANTITY[rtype]
                        w["records"].writerow([m, a["startDate"], a["endDate"], a.get("value", ""),
                                               a.get("unit", ""), a.get("sourceName", "")])
                        counts[m] = counts.get(m, 0) + 1
                    elif rtype == SLEEP:
                        a = dict(ATTR.findall(s))
                        stage = a.get("value", "").replace("HKCategoryValueSleepAnalysis", "")
                        w["sleep_segments"].writerow([a["startDate"], a["endDate"], stage, a.get("sourceName", "")])
                        counts["sleep_segments"] = counts.get("sleep_segments", 0) + 1
                elif s.startswith("<Workout "):
                    workout = dict(ATTR.findall(s))
                    workout["_stats"] = []
                    if s.rstrip().endswith("/>"):
                        s = "</Workout>"
                if workout is not None:
                    if s.startswith("<WorkoutStatistics "):
                        workout["_stats"].append(dict(ATTR.findall(s)))
                    elif s.startswith("</Workout>"):
                        a = workout; kcal = dist = unit = avg = mx = ""
                        for st in a["_stats"]:
                            t = st.get("type", "")
                            if t.endswith("ActiveEnergyBurned"):
                                kcal = st.get("sum", "")
                            elif t.endswith("Identifier" + "HeartRate"):
                                avg, mx = st.get("average", ""), st.get("maximum", "")
                            elif "Distance" in t and not dist:
                                dist, unit = st.get("sum", ""), st.get("unit", "")
                        dur = float(a.get("duration") or 0)
                        if a.get("durationUnit") == "sec":
                            dur /= 60
                        w["workouts"].writerow([
                            a.get("workoutActivityType", "").replace("HKWorkoutActivityType", ""),
                            a.get("startDate"), a.get("endDate"), round(dur, 1),
                            kcal or a.get("totalEnergyBurned", ""), dist or a.get("totalDistance", ""),
                            unit or a.get("totalDistanceUnit", ""), avg, mx, a.get("sourceName", "")])
                        counts["workouts"] = counts.get("workouts", 0) + 1
                        workout = None

    for f in files.values():
        f.close()
    print(f"Done in {time.time() - t0:.0f}s")
    for k, v in sorted(counts.items()):
        print(f"  {k:18s} {v:>10,}")


if __name__ == "__main__":
    main()
