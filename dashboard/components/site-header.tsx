import { Activity } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { fmtDate } from "@/lib/api";

export function SiteHeader({ latest }: { latest?: string }) {
  return (
    <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-4 lg:px-6">
        <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Activity className="size-4" />
        </div>
        <div className="leading-tight">
          <div className="font-semibold tracking-tight">Reserve</div>
          <div className="text-xs text-muted-foreground">Recovery dashboard · Apple Watch</div>
        </div>
        <nav className="ml-6 hidden gap-1 text-sm md:flex" aria-label="Sections">
          {[["#overview", "Overview"], ["#drivers", "Drivers"], ["#patterns", "Patterns"], ["#ask", "Ask"], ["#method", "Method"]].map(([h, l]) => (
            <a key={h} href={h} className="rounded-md px-3 py-1.5 text-muted-foreground hover:bg-muted hover:text-foreground">{l}</a>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          {latest && <Badge variant="outline" className="hidden sm:inline-flex font-mono">Data through {fmtDate(latest, { month: "short", day: "numeric", year: "numeric" })}</Badge>}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
