import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const STEPS = [
  ["Data", "~1,000 days of Apple Watch data: HRV, resting heart rate, sleep stages, respiratory rate and 168 workouts, parsed from a 1.4 GB Health export."],
  ["Personal baselines", "Each signal is compared to its own previous 30 days (z-scores), so the score reflects you, not population averages."],
  ["Weighting", "HRV 50% (3-day smoothed, log scale), resting HR 25%, sleep 25%. Elevated breathing rate only subtracts. Alternative weightings correlate at 0.97."],
  ["Score", "The weighted composite becomes a 1–100 percentile-style score: 72 ≈ better than ~72% of recent days."],
  ["AI layer", "Claude never sees raw data. It calls Python tools (pandas + SQLite) and explains the results, so math stays in code and every number is traceable."],
];

export function MethodCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>How Reserve works</CardTitle>
        <CardDescription>Python pipeline → readiness model → SQLite → FastAPI → Claude agent → this dashboard (Next.js + shadcn/ui)</CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {STEPS.map(([title, body], i) => (
            <li key={title} className="rounded-lg border bg-muted/40 p-4">
              <div className="font-mono text-xs text-primary">0{i + 1}</div>
              <div className="mt-1 text-sm font-semibold">{title}</div>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{body}</p>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
