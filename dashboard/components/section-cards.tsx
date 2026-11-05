import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardAction, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { band, Today } from "@/lib/api";

type Tone = "good" | "warn" | "outline";

function Kpi({ label, value, unit, delta, tone, line1, line2 }: {
  label: string; value: React.ReactNode; unit?: string; delta?: string; tone: Tone; line1: string; line2: string;
}) {
  const Icon = tone === "good" ? TrendingUp : tone === "warn" ? TrendingDown : Minus;
  return (
    <Card className="@container/card bg-gradient-to-t from-primary/5 to-card shadow-xs dark:bg-card">
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl font-semibold tabular-nums font-mono @[250px]/card:text-4xl">
          {value}{unit && <span className="ml-1 text-base font-normal text-muted-foreground">{unit}</span>}
        </CardTitle>
        {delta && (
          <CardAction>
            <Badge variant={tone}><Icon />{delta}</Badge>
          </CardAction>
        )}
      </CardHeader>
      <CardFooter className="flex-col items-start gap-1 text-sm">
        <div className="font-medium">{line1}</div>
        <div className="text-muted-foreground">{line2}</div>
      </CardFooter>
    </Card>
  );
}

export function SectionCards({ data }: { data: Today | null }) {
  if (!data) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-40 rounded-xl" />)}
      </div>
    );
  }
  const t = data.today;
  const b = band(t.readiness);
  const hrvPct = t.hrv_smoothed && t.hrv_baseline ? Math.round((t.hrv_smoothed / t.hrv_baseline - 1) * 100) : null;
  const rhrDiff = t.resting_hr != null && t.rhr_baseline ? Math.round(t.resting_hr - t.rhr_baseline) : null;
  const sleepMin = t.sleep_hrs != null && t.sleep_baseline ? Math.round((t.sleep_hrs - t.sleep_baseline) * 60) : null;
  const sign = (n: number) => (n > 0 ? `+${n}` : `${n}`);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Kpi
        label="Readiness" value={t.readiness ?? "–"} unit="/ 100"
        delta={t.readiness_change != null ? `${sign(t.readiness_change)} vs yesterday` : undefined}
        tone={t.readiness_change == null ? "outline" : t.readiness_change >= 0 ? "good" : "warn"}
        line1={b === "good" ? "Recovered: ready to push" : b === "low" ? "Under-recovered: go easy" : "Moderate: train, don't max out"}
        line2="Percentile vs. your previous 30 days"
      />
      <Kpi
        label="HRV (3-day smoothed)" value={t.hrv_smoothed ?? "–"} unit="ms"
        delta={hrvPct != null ? `${sign(hrvPct)}%` : undefined}
        tone={hrvPct == null ? "outline" : hrvPct >= 0 ? "good" : "warn"}
        line1={hrvPct == null ? "No reading" : hrvPct >= 0 ? "At or above your normal" : "Below your normal"}
        line2={`Your 30-day baseline: ${t.hrv_baseline != null ? Math.round(t.hrv_baseline) : "–"} ms`}
      />
      <Kpi
        label="Resting heart rate" value={t.resting_hr ?? "–"} unit="bpm"
        delta={rhrDiff != null ? `${sign(rhrDiff)} bpm` : undefined}
        tone={rhrDiff == null ? "outline" : rhrDiff <= 0 ? "good" : "warn"}
        line1={rhrDiff == null ? "No reading" : rhrDiff <= 0 ? "Lower is better: on track" : "Elevated vs. your normal"}
        line2={`Your 30-day baseline: ${t.rhr_baseline != null ? Math.round(t.rhr_baseline) : "–"} bpm`}
      />
      <Kpi
        label="Sleep" value={t.sleep_hrs != null ? `${Math.floor(t.sleep_hrs)}h ${Math.round((t.sleep_hrs % 1) * 60)}m` : "–"}
        delta={sleepMin != null ? `${sign(sleepMin)} min` : undefined}
        tone={sleepMin == null ? "outline" : sleepMin >= 0 ? "good" : "warn"}
        line1={t.bedtime ? `Fell asleep ${t.bedtime}` : "Not recorded last night"}
        line2={`Your 30-day baseline: ${t.sleep_baseline != null ? t.sleep_baseline.toFixed(1) : "–"} h`}
      />
    </div>
  );
}
