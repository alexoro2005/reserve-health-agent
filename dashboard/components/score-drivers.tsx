import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Today } from "@/lib/api";

const ROWS: [string, string, string][] = [
  ["impact_hrv", "HRV", "50% weight"],
  ["impact_rhr", "Resting HR", "25% weight"],
  ["impact_sleep", "Sleep", "25% weight"],
  ["impact_resp", "Breathing rate", "penalty only"],
];

export function ScoreDrivers({ data }: { data: Today | null }) {
  const t = data?.today ?? {};
  const max = Math.max(10, ...ROWS.map(([k]) => Math.abs(t[k] ?? 0)));
  return (
    <Card>
      <CardHeader>
        <CardTitle>What moved today&apos;s score</CardTitle>
        <CardDescription>Readiness points each signal added or removed vs. a typical day</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!data
          ? ROWS.map(([k]) => <Skeleton key={k} className="h-6 w-full" />)
          : ROWS.map(([k, label, note]) => {
              const v: number | null = t[k];
              const w = v == null ? 0 : (Math.abs(v) / max) * 50;
              return (
                <div key={k} className="grid grid-cols-[110px_1fr_52px] items-center gap-3 text-sm">
                  <div>
                    <div className="font-medium">{label}</div>
                    <div className="text-xs text-muted-foreground">{note}</div>
                  </div>
                  <div className="relative h-2.5 rounded-full bg-muted" role="img" aria-label={`${label}: ${v ?? "no data"} points`}>
                    <div className="absolute inset-y-[-4px] left-1/2 w-px bg-muted-foreground/50" />
                    {v != null && (
                      <div
                        className={v >= 0 ? "absolute inset-y-0 rounded-full bg-good" : "absolute inset-y-0 rounded-full bg-warn"}
                        style={{ width: `${w}%`, left: v >= 0 ? "50%" : `${50 - w}%` }}
                      />
                    )}
                  </div>
                  <div className={`text-right font-mono font-semibold tabular-nums ${v == null ? "text-muted-foreground" : v >= 0 ? "text-good" : "text-warn"}`}>
                    {v == null ? "—" : `${v > 0 ? "+" : ""}${v}`}
                  </div>
                </div>
              );
            })}
      </CardContent>
    </Card>
  );
}
