// Helpers for talking to the FastAPI backend (api.py)
export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function handle<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? `Request failed (${r.status})`);
  return r.json();
}
export const getJSON = <T = any>(path: string) => fetch(`${API}${path}`).then((r) => handle<T>(r));
export const postJSON = <T = any>(path: string, body: unknown) =>
  fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then((r) => handle<T>(r));

export type Day = {
  date: string;
  readiness: number | null;
  hrv_smoothed: number | null;
  hrv_baseline: number | null;
  resting_hr: number | null;
  sleep_hrs: number | null;
  impact_hrv: number | null;
  impact_rhr: number | null;
  impact_sleep: number | null;
  impact_resp: number | null;
  training_load: number | null;
};

export type Today = { date: string; today: Record<string, any> };

export const fmtDate = (d: string, opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" }) =>
  new Date(d + "T12:00:00").toLocaleDateString("en-US", opts);

export const band = (r: number | null | undefined) =>
  r == null ? "neutral" : r >= 67 ? "good" : r < 34 ? "low" : "neutral";
