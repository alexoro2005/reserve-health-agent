"use client";
import { Area, AreaChart, CartesianGrid, ReferenceLine, XAxis, YAxis } from "recharts";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Day, fmtDate } from "@/lib/api";

const config = { readiness: { label: "Readiness", color: "var(--chart-1)" } } satisfies ChartConfig;

export function ChartReadiness({ data, range, setRange }: { data: Day[]; range: number; setRange: (n: number) => void }) {
  const vals = data.map((d) => d.readiness).filter((v): v is number => v != null);
  const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  return (
    <Card className="@container/card">
      <CardHeader>
        <CardTitle>Readiness over time</CardTitle>
        <CardDescription>
          {avg != null ? `Averaging ${avg.toFixed(0)} over this period · dashed line = average` : "Loading…"}
        </CardDescription>
        <CardAction>
          <ToggleGroup type="single" value={String(range)} onValueChange={(v) => v && setRange(Number(v))} aria-label="Time range">
            <ToggleGroupItem value="30">30d</ToggleGroupItem>
            <ToggleGroupItem value="90">90d</ToggleGroupItem>
            <ToggleGroupItem value="365">1y</ToggleGroupItem>
          </ToggleGroup>
        </CardAction>
      </CardHeader>
      <CardContent className="px-2 pt-2 sm:px-6">
        {data.length === 0 ? (
          <Skeleton className="h-[260px] w-full" />
        ) : (
          <ChartContainer config={config} className="aspect-auto h-[260px] w-full">
            <AreaChart data={data} margin={{ left: 0, right: 8, top: 8 }}>
              <defs>
                <linearGradient id="fillReadiness" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--color-readiness)" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="var(--color-readiness)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} strokeDasharray="3 4" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} tickMargin={8} minTickGap={36} tickFormatter={(d) => fmtDate(d)} />
              <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tickLine={false} axisLine={false} width={34} />
              {avg != null && <ReferenceLine y={avg} stroke="var(--muted-foreground)" strokeDasharray="4 4" />}
              <ChartTooltip
                cursor={false}
                content={<ChartTooltipContent labelFormatter={(d) => fmtDate(String(d), { weekday: "short", month: "short", day: "numeric" })} />}
              />
              <Area dataKey="readiness" type="monotone" fill="url(#fillReadiness)" stroke="var(--color-readiness)" strokeWidth={2} connectNulls />
            </AreaChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
