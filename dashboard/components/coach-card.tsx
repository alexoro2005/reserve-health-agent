"use client";
import { Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { band, Today } from "@/lib/api";

export function CoachCard({ data, briefing, error }: { data: Today | null; briefing: string | null; error: string | null }) {
  const b = band(data?.today.readiness);
  const plan = !data ? "…" : b === "good" ? "Good day to push" : b === "low" ? "Go easy today" : "Train, but keep it moderate";
  return (
    <Card className="h-full">
      <CardHeader>
        <CardDescription>Today&apos;s plan</CardDescription>
        <CardTitle className="text-2xl tracking-tight">{plan}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        <div className="rounded-lg bg-accent p-4 text-sm">
          <div className="mb-2 flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            <span className="font-medium text-accent-foreground">Daily briefing</span>
            <Badge variant="outline" className="ml-auto font-mono text-[10px]">Claude</Badge>
          </div>
          {error ? (
            <p className="text-destructive">{error}</p>
          ) : briefing ? (
            <div className="prose-answer leading-relaxed"><ReactMarkdown>{briefing}</ReactMarkdown></div>
          ) : (
            <div className="space-y-2">
              <Skeleton className="h-3.5 w-[95%] bg-background/70" />
              <Skeleton className="h-3.5 w-[85%] bg-background/70" />
              <Skeleton className="h-3.5 w-[60%] bg-background/70" />
              <p className="pt-1 text-xs text-muted-foreground">Claude is reading the latest data…</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
