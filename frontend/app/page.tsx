"use client";

import Link from "next/link";
import AppShell from "@/components/AppShell";
import AlertPanel from "@/components/AlertPanel";
import RunControls from "@/components/RunControls";
import Charts from "@/components/Charts";
import { useDashboardData } from "@/components/useDashboardData";

function StatCard({ label, value, detail, tone = "neutral" }: { label: string; value: string | number; detail: string; tone?: "neutral" | "green" | "amber" | "red" }) {
  const tones = { neutral: "text-slate-50", green: "text-emerald-400", amber: "text-amber-400", red: "text-red-400" };
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.17em] text-slate-400">{label}</p>
      <p className={`mt-3 text-3xl font-semibold tracking-tight ${tones[tone]}`}>{value}</p>
      <p className="mt-2 text-xs text-slate-400">{detail}</p>
    </div>
  );
}

export default function DashboardPage() {
  const data = useDashboardData();
  const unreadAlerts = data.alerts.filter((alert) => !alert.is_read).length;
  const potentialDetections = data.alerts.filter((alert) => alert.alert_type === "UNAUTHORIZED_EXPANSION").length;
  const isSafe = data.latestRun && ["SAFE", "PERMITTED", "BASELINE"].includes(data.latestRun.status);
  const lastScanDate = data.latestRun?.image_date
    ? new Date(data.latestRun.image_date).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })
    : "Awaiting run";

  return (
    <AppShell
      title="Dashboard"
      eyebrow="Monitoring overview"
      actions={
        <div className="flex flex-wrap items-center justify-end gap-2">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1.5 text-[10px] font-medium uppercase tracking-[0.16em] text-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Live
          </span>
          <span className="inline-flex items-center rounded-full border border-white/10 bg-slate-900/80 px-2.5 py-1.5 text-[10px] font-medium uppercase tracking-[0.16em] text-slate-300">
            {lastScanDate}
          </span>
          <RunControls onRun={data.handleRun} />
        </div>
      }
    >
      {data.dashboardError && <div className="mb-6 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">{data.dashboardError} Retrying automatically.</div>}

      <section className="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Monitored sites" value={data.quarry ? 1 : 0} detail={data.quarry?.name || "Loading site registry"} />
        <StatCard label="Monitoring status" value={data.latestRun ? "Active" : "Standby"} detail={data.latestRun ? `Last scan ${data.latestRun.image_date}` : "Awaiting first run"} tone="green" />
        <StatCard label="Recent alerts" value={unreadAlerts} detail={`${data.alerts.length} generated alerts`} tone={unreadAlerts ? "amber" : "green"} />
        <StatCard label="Permitted / safe" value={isSafe ? 1 : 0} detail={isSafe ? "Latest run within boundary" : "No safe result yet"} tone="green" />
        <StatCard label="Potential detections" value={potentialDetections} detail="Expansion alerts requiring review" tone={potentialDetections ? "red" : "neutral"} />
      </section>

      <section className="mb-8 rounded-2xl border border-white/10 bg-slate-900/70 p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
        <Charts runs={data.history.slice(-12)} />
      </section>
      <section className="mb-8 rounded-2xl border border-white/10 bg-slate-900/70 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Recent alerts</h3>
            <p className="mt-1 text-xs text-slate-400">Items needing attention</p>
          </div>
          <Link href="/alerts" className="text-xs font-medium text-emerald-300 hover:text-white">View all &gt;</Link>
        </div>
        <AlertPanel alerts={data.alerts.slice(0, 3)} onMarkRead={data.handleMarkRead} onViewOnMap={async (runId) => { await data.loadRunOnMap(runId); }} />
      </section>
    </AppShell>
  );
}
