"use client";
import { useEffect, useState } from "react";
import { AskPanel } from "@/components/ask-panel";
import { ChartReadiness } from "@/components/chart-readiness";
import { CoachCard } from "@/components/coach-card";
import { HelpHurtChart } from "@/components/help-hurt-chart";
import { MethodCard } from "@/components/method-card";
import { PatternsCard } from "@/components/patterns-card";
import { ScoreDrivers } from "@/components/score-drivers";
import { SectionCards } from "@/components/section-cards";
import { SiteHeader } from "@/components/site-header";
import { API, Day, getJSON, Today } from "@/lib/api";

const CONDITIONS = ["late_workout", "weekend", "hard_day", "any_workout"];

export default function Dashboard() {
  const [today, setToday] = useState<Today | null>(null);
  const [trend, setTrend] = useState<Day[]>([]);
  const [range, setRange] = useState(90);
  const [briefing, setBriefing] = useState<string | null>(null);
  const [briefErr, setBriefErr] = useState<string | null>(null);
  const [patterns, setPatterns] = useState<any[] | null>(null);
  const [apiDown, setApiDown] = useState(false);

  useEffect(() => {
    getJSON<Today>("/api/today").then(setToday).catch(() => setApiDown(true));
    Promise.all(CONDITIONS.map((c) => getJSON(`/api/compare?condition=${c}`).catch((e) => ({ error: e.message })))).then(setPatterns);
    getJSON<{ briefing: string }>("/api/briefing").then((b) => setBriefing(b.briefing)).catch((e) => setBriefErr(e.message));
  }, []);

  useEffect(() => {
    getJSON<{ days: Day[] }>(`/api/trend?days=${range}`).then((r) => setTrend(r.days)).catch(() => setApiDown(true));
  }, [range]);

  return (
    <>
      <SiteHeader latest={today?.date} />
      <main className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 lg:px-6">
        {apiDown && (
          <div role="alert" className="rounded-lg border border-warn/40 bg-warn-soft px-4 py-3 text-sm">
            Can&apos;t reach the API at <code className="font-mono">{API}</code>. From the project folder run{" "}
            <code className="rounded bg-background px-1.5 py-0.5 font-mono">uvicorn api:app --reload</code>, then refresh.
          </div>
        )}

        <section id="overview" className="scroll-mt-20 space-y-6">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Recovery overview</h1>
            <p className="text-sm text-muted-foreground">A personal readiness score built from Apple Watch data, explained by an AI agent.</p>
          </div>
          <SectionCards data={today} />
          <div className="grid gap-6 lg:grid-cols-3 [&>*]:min-w-0">
            <div className="lg:col-span-2"><ChartReadiness data={trend} range={range} setRange={setRange} /></div>
            <CoachCard data={today} briefing={briefing} error={briefErr} />
          </div>
        </section>

        <section id="drivers" className="scroll-mt-20 grid gap-6 lg:grid-cols-2 [&>*]:min-w-0">
          <ScoreDrivers data={today} />
          <HelpHurtChart trend={trend} />
        </section>

        <section className="grid gap-6 lg:grid-cols-2 [&>*]:min-w-0">
          <div id="patterns" className="scroll-mt-20"><PatternsCard results={patterns} /></div>
          <div id="ask" className="scroll-mt-20"><AskPanel /></div>
        </section>

        <section id="method" className="scroll-mt-20"><MethodCard /></section>

        <footer className="pb-4 text-center text-xs text-muted-foreground">
          Built by Alex Orozco · Python, pandas, SQLite, FastAPI, Claude API, Next.js, shadcn/ui · Not medical advice.
        </footer>
      </main>
    </>
  );
}
