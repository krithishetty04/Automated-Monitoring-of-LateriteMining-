"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { useDashboardData } from "@/components/useDashboardData";
import { formatAcres } from "@/area";

function formatDate(value: string) {
  return new Date(value).toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default function AlertsPage() {
  const data = useDashboardData();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const filteredAlerts = useMemo(() => data.alerts.filter((alert) => {
    const matchesFilter = filter === "all" || (filter === "unread" ? !alert.is_read : alert.severity.toLowerCase() === filter);
    const text = `${alert.message} ${alert.alert_type} ${alert.severity}`.toLowerCase();
    return matchesFilter && text.includes(query.toLowerCase());
  }), [data.alerts, filter, query]);

  return <AppShell title="Alerts & Notifications" eyebrow="Review centre" actions={<span className="rounded-full border border-[#E6B9A6]/25 bg-[#E6B9A6]/[0.08] px-3 py-1.5 text-[11px] text-[#EED0C4]">{data.alerts.filter((alert) => !alert.is_read).length} unread</span>}>
    <section className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-sm text-[#B9B7B0]">Review generated notifications and potential unauthorized quarry expansion detections.</p><p className="mt-2 text-xs text-[#939185]">Severity and read status reflect the existing monitoring system.</p></div><Link href="/map" className="w-fit rounded-lg border border-white/10 px-3 py-2 text-xs text-[#E6B9A6] hover:border-[#E6B9A6]/40">Open activity map ></Link></section>
    <div className="mb-5 flex flex-col gap-3 rounded-xl border border-white/[0.08] bg-[#3B4251] p-4 sm:flex-row"><label className="flex-1"><span className="sr-only">Search alerts</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search alert details" className="w-full rounded-lg border border-white/10 bg-[#2F3645] px-3 py-2.5 text-sm text-white outline-none placeholder:text-[#939185] focus:border-[#E6B9A6]/50" /></label><div className="flex gap-2"><button onClick={() => setFilter("all")} className={`rounded-lg px-3 py-2 text-xs ${filter === "all" ? "bg-[#E6B9A6]/15 text-[#F4E1D9]" : "text-[#939185] hover:bg-white/5"}`}>All</button><button onClick={() => setFilter("unread")} className={`rounded-lg px-3 py-2 text-xs ${filter === "unread" ? "bg-[#E6B9A6]/15 text-[#F4E1D9]" : "text-[#939185] hover:bg-white/5"}`}>Unread</button><button onClick={() => setFilter("high")} className={`rounded-lg px-3 py-2 text-xs ${filter === "high" ? "bg-[#D28A83]/15 text-[#D28A83]" : "text-[#939185] hover:bg-white/5"}`}>High severity</button></div></div>
    <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-[#3B4251]">
      <div className="flex items-center justify-between border-b border-white/[0.08] px-5 py-4"><div><h2 className="text-sm font-semibold text-white">All generated alerts</h2><p className="mt-1 text-xs text-[#939185]">{filteredAlerts.length} of {data.alerts.length} notifications</p></div><span className="text-[10px] uppercase tracking-[0.15em] text-[#939185]">Quarry: {data.quarry?.name || "Loading"}</span></div>
      <div className="divide-y divide-white/[0.06]">
        {filteredAlerts.map((alert) => { const isExpansion = alert.alert_type === "UNAUTHORIZED_EXPANSION"; return <article key={alert.id} className={`p-5 ${alert.is_read ? "opacity-65" : ""}`}>
          <div className="flex flex-col justify-between gap-3 lg:flex-row lg:items-start"><div className="flex gap-3"><span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${isExpansion ? "bg-[#D28A83]/15 text-[#D28A83]" : "bg-[#E6B9A6]/15 text-[#E6B9A6]"}`}>{isExpansion ? "!" : "OK"}</span><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-semibold text-white">{isExpansion ? "Potential unauthorized quarry expansion" : "Permitted excavation activity"}</h3><span className={`rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] ${isExpansion ? "border-[#D28A83]/30 text-[#D28A83]" : "border-[#E6B9A6]/30 text-[#E6B9A6]"}`}>{alert.severity}</span></div><p className="mt-2 text-sm leading-6 text-[#D7D5D0]">{alert.message}</p></div></div><div className="text-left lg:text-right"><p className="text-xs text-[#939185]">{formatDate(alert.created_at)}</p><p className="mt-1 text-[10px] uppercase tracking-[0.12em] text-[#939185]">{alert.is_read ? "Reviewed" : "New"}</p></div></div>
          <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-white/[0.06] pt-3 text-xs text-[#939185]"><span>Site: <strong className="font-medium text-[#EEEDEB]">{data.quarry?.name || "Official Quarry"}</strong></span><span>Detected area: <strong className="font-medium text-[#E6B9A6]">{formatAcres(alert.expansion_area_ha, 3)}</strong></span><span>Run #{alert.monitoring_run_id}</span><div className="ml-auto flex gap-2"><Link href={`/map?run=${alert.monitoring_run_id}`} className="rounded-md border border-white/10 px-2.5 py-1.5 text-xs text-[#E6B9A6] hover:border-[#E6B9A6]/40">View map</Link>{!alert.is_read && <button onClick={() => data.handleMarkRead(alert.id)} className="rounded-md bg-[#E6B9A6] px-2.5 py-1.5 text-xs font-medium text-[#2F3645]">Mark reviewed</button>}</div></div>
        </article>; })}
        {filteredAlerts.length === 0 && <div className="px-5 py-14 text-center text-sm text-[#939185]">No alerts match the current filter.</div>}
      </div>
    </div>
  </AppShell>;
}
