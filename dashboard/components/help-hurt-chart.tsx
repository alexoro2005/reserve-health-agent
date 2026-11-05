"use client";
import { Bar, CartesianGrid, ComposedChart, Line, ReferenceLine, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartConfig, ChartContainer, ChartLegendContent, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";
import { Day, fmtDate } from "@/lib/api";

const config = {
  helped: { label: "Helped (pts)", color: "var(--good)" },
  hurt: { label: "Hurt (pts)", color: "var(--warn)" },
  readiness: { label: "Readiness", color: "var(--chart-1)" },
} satisfies ChartConfig;

const KEYS = ["impact_hrv", "impact_rhr", "impact_sleep", "impact_resp"] as const;

export function HelpHurtChart({ trend }: { trend: Day[] }) {
  const data = trend.slice(-14).map((d) => {
    const v = KEYS.map((k) => d[k] ?? 0);
    return {
      date: d.date,
      helped: +v.filter((x) => x > 0).reduce((a, b) => a + b, 0).toFixed(1),
      hurt: +v.filter((x) => x < 0).reduce((a, b) => a + b, 0).toFixed(1),
      readiness: d.readiness,
    };
  });
  return (
    <Card>
      <CardHeader>
        <CardTitle>What helped vs. what hurt</CardTitle>
        <CardDescription>Last 14 days · bars are readiness points, line is the score</CardDescription>
      </CardHeader>
      <CardContent className="px-2 sm:px-6">
        {data.length === 0 ? (
          <Skeleton className="h-[230px] w-full" />
        ) : (
          <>
            <ChartContainer config={config} className="aspect-auto h-[230px] w-full">
              <ComposedChart data={data} stackOffset="sign" margin={{ left: 0, right: 0, top: 8 }}>
                <CartesianGrid vertical={false} strokeDasharray="3 4" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} tickMargin={8} tickFormatter={(d) => fmtDate(d, { weekday: "narrow" })} />
                <YAxis yAxisId="pts" tickLine={false} axisLine={false} width={34} />
                <YAxis yAxisId="r" orientation="right" domain={[0, 100]} hide />
                <ReferenceLine yAxisId="pts" y={0} stroke="var(--foreground)" strokeOpacity={0.5} />
                <ChartTooltip content={<ChartTooltipContent labelFormatter={(d) => fmtDate(String(d), { weekday: "short", month: "short", day: "numeric" })} />} />
                <Bar yAxisId="pts" dataKey="helped" stackId="s" fill="var(--color-helped)" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="pts" dataKey="hurt" stackId="s" fill="var(--color-hurt)" radius={[0, 0, 4, 4]} />
                <Line yAxisId="r" dataKey="readiness" type="monotone" stroke="var(--color-readiness)" strokeWidth={2} dot={{ r: 3, fill: "var(--card)", strokeWidth: 2 }} connectNulls />
              </ComposedChart>
            </ChartContainer>
            <ChartLegendContent config={config} className="pt-3" />
          </>
        )}
      </CardContent>
    </Card>
  );
}
