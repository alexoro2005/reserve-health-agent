"use client";
// shadcn/ui chart: wraps Recharts so series colors and labels come from one `config` object
import * as React from "react";
import * as RechartsPrimitive from "recharts";
import { cn } from "@/lib/utils";

export type ChartConfig = {
  [k: string]: { label?: React.ReactNode; icon?: React.ComponentType; color?: string };
};

const ChartContext = React.createContext<{ config: ChartConfig } | null>(null);

function useChart() {
  const ctx = React.useContext(ChartContext);
  if (!ctx) throw new Error("useChart must be used within a <ChartContainer />");
  return ctx;
}

function ChartContainer({
  id,
  className,
  children,
  config,
  ...props
}: React.ComponentProps<"div"> & {
  config: ChartConfig;
  children: React.ComponentProps<typeof RechartsPrimitive.ResponsiveContainer>["children"];
}) {
  const uniqueId = React.useId();
  const chartId = `chart-${id || uniqueId.replace(/:/g, "")}`;
  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-slot="chart"
        data-chart={chartId}
        className={cn(
          "[&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/60 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border flex aspect-video justify-center text-xs [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-hidden [&_.recharts-surface]:outline-hidden",
          className
        )}
        {...props}
      >
        <ChartStyle id={chartId} config={config} />
        <RechartsPrimitive.ResponsiveContainer>{children}</RechartsPrimitive.ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  );
}

const ChartStyle = ({ id, config }: { id: string; config: ChartConfig }) => {
  const entries = Object.entries(config).filter(([, c]) => c.color);
  if (!entries.length) return null;
  return (
    <style
      dangerouslySetInnerHTML={{
        __html: `[data-chart=${id}] {\n${entries.map(([key, c]) => `  --color-${key}: ${c.color};`).join("\n")}\n}`,
      }}
    />
  );
};

const ChartTooltip = RechartsPrimitive.Tooltip;

type TooltipItem = { name?: string | number; value?: number | string; dataKey?: string | number; color?: string; payload?: any };

function ChartTooltipContent({
  active,
  payload,
  label,
  className,
  labelFormatter,
  valueFormatter,
  hideLabel = false,
}: {
  active?: boolean;
  payload?: TooltipItem[];
  label?: any;
  className?: string;
  labelFormatter?: (label: any) => React.ReactNode;
  valueFormatter?: (value: any, key: string) => React.ReactNode;
  hideLabel?: boolean;
}) {
  const { config } = useChart();
  if (!active || !payload?.length) return null;
  return (
    <div className={cn("border-border/50 bg-background grid min-w-[8rem] items-start gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs shadow-xl", className)}>
      {!hideLabel && <div className="font-medium">{labelFormatter ? labelFormatter(label) : label}</div>}
      <div className="grid gap-1.5">
        {payload
          .filter((p) => p.value != null)
          .map((p) => {
            const key = String(p.dataKey ?? p.name ?? "value");
            const item = config[key];
            return (
              <div key={key} className="flex w-full items-center gap-2">
                <div className="h-2.5 w-2.5 shrink-0 rounded-[2px]" style={{ background: p.color ?? `var(--color-${key})` }} />
                <span className="text-muted-foreground">{item?.label ?? p.name}</span>
                <span className="text-foreground ml-auto font-mono font-medium tabular-nums">
                  {valueFormatter ? valueFormatter(p.value, key) : p.value}
                </span>
              </div>
            );
          })}
      </div>
    </div>
  );
}

// Legend that can sit anywhere (e.g. in a card header), so it takes the config directly
function ChartLegendContent({ className, config, keys }: { className?: string; config: ChartConfig; keys?: string[] }) {
  const list = keys ?? Object.keys(config);
  return (
    <div className={cn("flex items-center justify-center gap-4", className)}>
      {list.map((k) => (
        <div key={k} className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <div className="h-2 w-2 shrink-0 rounded-[2px]" style={{ background: `var(--color-${k})` }} />
          {config[k]?.label}
        </div>
      ))}
    </div>
  );
}

export { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegendContent, ChartStyle };
