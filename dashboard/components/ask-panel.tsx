"use client";
import { useState } from "react";
import { ArrowUp, Database, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { postJSON } from "@/lib/api";

const SUGGESTIONS = [
  "Why was readiness so low last week?",
  "Which month this year had the best recovery?",
  "Do late workouts hurt next-day recovery?",
];

type Result = { answer: string; tools_used: { tool: string; input: Record<string, unknown> }[] };

export function AskPanel() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<Result | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run(question: string) {
    if (!question.trim() || loading) return;
    setQ(question); setLoading(true); setErr(null); setRes(null);
    try { setRes(await postJSON<Result>("/api/ask", { question })); }
    catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Sparkles className="size-4 text-primary" /> Ask the data</CardTitle>
        <CardDescription>
          An AI agent (Claude) answers by calling 6 tools over the dataset: lookups, summaries, day explanations, statistical comparisons, workouts and read-only SQL. Every number comes from the data.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); run(q); }}>
          <label htmlFor="ask" className="sr-only">Ask a question about the data</label>
          <Input id="ask" value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. Do weekends affect recovery?" className="h-10" />
          <Button type="submit" size="lg" disabled={loading} aria-label="Ask">
            {loading ? "Thinking…" : <><ArrowUp /> Ask</>}
          </Button>
        </form>
        {!res && !loading && (
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <Button key={s} variant="outline" size="sm" type="button" className="h-auto max-w-full shrink whitespace-normal rounded-full py-1.5 text-left font-normal text-muted-foreground" onClick={() => run(s)}>{s}</Button>
            ))}
          </div>
        )}
        {loading && (
          <div className="space-y-2 rounded-lg border p-4">
            <Skeleton className="h-3.5 w-[90%]" /><Skeleton className="h-3.5 w-[75%]" /><Skeleton className="h-3.5 w-[50%]" />
            <p className="pt-1 text-xs text-muted-foreground">Claude is choosing tools and querying the data (10–30s)…</p>
          </div>
        )}
        {err && <p className="text-sm text-destructive">{err}</p>}
        {res && (
          <div className="rounded-lg border p-4">
            <div className="prose-answer text-sm leading-relaxed"><ReactMarkdown remarkPlugins={[remarkGfm]}>{res.answer}</ReactMarkdown></div>
            {res.tools_used.length > 0 && (
              <>
                <Separator className="my-3" />
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="mr-1 flex items-center gap-1 text-xs text-muted-foreground"><Database className="size-3" /> Tools used</span>
                  {res.tools_used.map((t, i) => (
                    <Badge key={i} variant="secondary" className="font-mono" title={JSON.stringify(t.input)}>{t.tool}</Badge>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
