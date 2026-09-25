"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { useDashboardData } from "@/components/useDashboardData";

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

  return <AppShell title="Alerts & Notifications" eyebrow="Review centre" actions={<span className="rounded-full border border-[#e6a45c]/25 bg-[#e6a45c]/[0.08] px-3 py-1.5 text-[11px] text-[#f2bf7b]">{data.alerts.filter((alert) => !alert.is_read).length} unread</span>}>
    <section className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-sm text-[#89a198]">Review generated notifications and potential unauthorized quarry expansion detections.</p><p className="mt-2 text-xs text-[#607a70]">Severity and read status reflect the existing monitoring system.</p></div><Link href="/map" className="w-fit rounded-lg border border-white/10 px-3 py-2 text-xs text-[#c5d86d] hover:border-[#c5d86d]/40">Open activity map →</Link></section>
    <div className="mb-5 flex flex-col gap-3 rounded-xl border border-white/[0.08] bg-[#10201b] p-4 sm:flex-row"><label className="flex-1"><span className="sr-only">Search alerts</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search alert details" className="w-full rounded-lg border border-white/10 bg-[#091612] px-3 py-2.5 text-sm text-white outline-none placeholder:text-[#587269] focus:border-[#c5d86d]/50" /></label><div className="flex gap-2"><button onClick={() => setFilter("all")} className={`rounded-lg px-3 py-2 text-xs ${filter === "all" ? "bg-[#c5d86d]/15 text-[#d5e987]" : "text-[#789187] hover:bg-white/5"}`}>All</button><button onClick={() => setFilter("unread")} className={`rounded-lg px-3 py-2 text-xs ${filter === "unread" ? "bg-[#c5d86d]/15 text-[#d5e987]" : "text-[#789187] hover:bg-white/5"}`}>Unread</button><button onClick={() => setFilter("high")} className={`rounded-lg px-3 py-2 text-xs ${filter === "high" ? "bg-[#e37862]/15 text-[#e37862]" : "text-[#789187] hover:bg-white/5"}`}>High severity</button></div></div>
    <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-[#10201b]">
      <div className="flex items-center justify-between border-b border-white/[0.08] px-5 py-4"><div><h2 className="text-sm font-semibold text-white">All generated alerts</h2><p className="mt-1 text-xs text-[#789187]">{filteredAlerts.length} of {data.alerts.length} notifications</p></div><span className="text-[10px] uppercase tracking-[0.15em] text-[#607a70]">Quarry: {data.quarry?.name || "Loading"}</span></div>
      <div className="divide-y divide-white/[0.06]">
        {filteredAlerts.map((alert) => { const isExpansion = alert.alert_type === "UNAUTHORIZED_EXPANSION"; return <article key={alert.id} className={`p-5 ${alert.is_read ? "opacity-65" : ""}`}>
          <div className="flex flex-col justify-between gap-3 lg:flex-row lg:items-start"><div className="flex gap-3"><span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${isExpansion ? "bg-[#e37862]/15 text-[#e37862]" : "bg-[#c5d86d]/15 text-[#c5d86d]"}`}>{isExpansion ? "!" : "✓"}</span><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-semibold text-white">{isExpansion ? "Potential unauthorized quarry expansion" : "Permitted excavation activity"}</h3><span className={`rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] ${isExpansion ? "border-[#e37862]/30 text-[#e37862]" : "border-[#c5d86d]/30 text-[#c5d86d]"}`}>{alert.severity}</span></div><p className="mt-2 text-sm leading-6 text-[#a7b9b0]">{alert.message}</p></div></div><div className="text-left lg:text-right"><p className="text-xs text-[#789187]">{formatDate(alert.created_at)}</p><p className="mt-1 text-[10px] uppercase tracking-[0.12em] text-[#607a70]">{alert.is_read ? "Reviewed" : "New"}</p></div></div>
          <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-white/[0.06] pt-3 text-xs text-[#789187]"><span>Site: <strong className="font-medium text-[#c4d0c9]">{data.quarry?.name || "Official Quarry"}</strong></span><span>Detected area: <strong className="font-medium text-[#e6a45c]">{alert.expansion_area_ha.toFixed(3)} ha</strong></span><span>Run #{alert.monitoring_run_id}</span><div className="ml-auto flex gap-2"><Link href={`/map?run=${alert.monitoring_run_id}`} className="rounded-md border border-white/10 px-2.5 py-1.5 text-xs text-[#c5d86d] hover:border-[#c5d86d]/40">View map</Link>{!alert.is_read && <button onClick={() => data.handleMarkRead(alert.id)} className="rounded-md bg-[#c5d86d] px-2.5 py-1.5 text-xs font-medium text-[#142219]">Mark reviewed</button>}</div></div>
        </article>; })}
        {filteredAlerts.length === 0 && <div className="px-5 py-14 text-center text-sm text-[#789187]">No alerts match the current filter.</div>}
      </div>
    </div>
  </AppShell>;
}
