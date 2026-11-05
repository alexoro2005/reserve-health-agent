import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const sizeLabel = (d: number | null) => {
  const a = Math.abs(d ?? 0);
  return a < 0.2 ? "negligible" : a < 0.5 ? "small" : a < 0.8 ? "medium" : "large";
};

export function PatternsCard({ results }: { results: any[] | null }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Patterns in the data</CardTitle>
        <CardDescription>Next-day readiness when something happened vs. when it didn&apos;t (Welch test, Cohen&apos;s d)</CardDescription>
      </CardHeader>
      <CardContent className="divide-y">
        {!results && [0, 1, 2, 3].map((i) => <Skeleton key={i} className="my-3 h-10 w-full" />)}
        {results?.filter((r) => !r.error).map((r) => {
          const size = sizeLabel(r.effect_size_d);
          const meaningful = size !== "negligible";
          return (
            <div key={r.condition} className="flex items-start justify-between gap-4 py-3 first:pt-0 last:pb-0">
              <div className="min-w-0">
                <div className="text-sm font-medium first-letter:uppercase">After {r.condition}</div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  {r.condition_true.mean.toFixed(1)} vs {r.comparison.mean.toFixed(1)} · n = {r.condition_true.n} vs {r.comparison.n}
                  {r.p_value != null && ` · p ${r.p_value < 0.001 ? "< 0.001" : "= " + r.p_value.toFixed(2)}`}
                </div>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <span className={`font-mono text-sm font-semibold tabular-nums ${!meaningful ? "text-muted-foreground" : r.difference >= 0 ? "text-good" : "text-warn"}`}>
                  {r.difference >= 0 ? "+" : ""}{r.difference.toFixed(1)} pts
                </span>
                <Badge variant={!meaningful ? "outline" : r.difference >= 0 ? "good" : "warn"}>{size} effect</Badge>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
