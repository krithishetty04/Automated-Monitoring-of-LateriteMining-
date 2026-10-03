"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { useDashboardData } from "@/components/useDashboardData";
import { formatAcres } from "@/area";

const statusClasses: Record<string, string> = { ALERT: "border-[#D28A83]/30 bg-[#D28A83]/10 text-[#D28A83]", SAFE: "border-[#E6B9A6]/30 bg-[#E6B9A6]/10 text-[#E6B9A6]", PERMITTED: "border-[#E6B9A6]/30 bg-[#E6B9A6]/10 text-[#E6B9A6]", BASELINE: "border-[#E6B9A6]/30 bg-[#E6B9A6]/10 text-[#E6B9A6]", ERROR: "border-white/10 text-[#939185]" };

export default function HistoryPage() {
  const data = useDashboardData();
  const [status, setStatus] = useState("all");
  const [source, setSource] = useState("all");
  const runs = useMemo(() => data.history.filter((run) => (status === "all" || run.status === status) && (source === "all" || run.source === source)), [data.history, status, source]);
  const sources = Array.from(new Set(data.history.map((run) => run.source)));

  return <AppShell title="Monitoring History" eyebrow="Analysis archive" actions={<span className="rounded-full border border-white/10 px-3 py-1.5 text-[11px] text-[#939185]">{data.history.length} runs</span>}>
    <section className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-sm text-[#B9B7B0]">Chronological monitoring results with comparison areas, status, and satellite source.</p><p className="mt-2 text-xs text-[#939185]">Select a run to inspect its overlay on the quarry map.</p></div><Link href="/map" className="w-fit rounded-lg border border-white/10 px-3 py-2 text-xs text-[#E6B9A6] hover:border-[#E6B9A6]/40">Open map &gt;</Link></section>
    <div className="mb-5 flex flex-wrap gap-2 rounded-xl border border-white/[0.08] bg-[#3B4251] p-4"><select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-lg border border-white/10 bg-[#2F3645] px-3 py-2 text-xs text-[#D7D5D0] outline-none"><option value="all">All statuses</option>{["SAFE", "PERMITTED", "BASELINE", "ALERT", "ERROR"].map((item) => <option key={item} value={item}>{item}</option>)}</select><select value={source} onChange={(event) => setSource(event.target.value)} className="rounded-lg border border-white/10 bg-[#2F3645] px-3 py-2 text-xs text-[#D7D5D0] outline-none"><option value="all">All sources</option>{sources.map((item) => <option key={item} value={item}>{item}</option>)}</select><span className="ml-auto self-center text-xs text-[#939185]">Showing {runs.length} results</span></div>
    <div className="mb-6 overflow-x-auto rounded-xl border border-white/[0.08] bg-[#3B4251]"><table className="w-full min-w-[900px] text-left text-sm"><thead className="border-b border-white/[0.08] text-[10px] uppercase tracking-[0.14em] text-[#939185]"><tr><th className="px-5 py-4">Monitoring date</th><th className="px-5 py-4">Site</th><th className="px-5 py-4">Result</th><th className="px-5 py-4">Current / previous</th><th className="px-5 py-4">Detected area</th><th className="px-5 py-4">Source</th><th className="px-5 py-4">Map</th></tr></thead><tbody className="divide-y divide-white/[0.06]">{runs.map((run) => <tr key={run.id} className="text-[#D7D5D0] hover:bg-white/[0.025]"><td className="px-5 py-4"><span className="font-medium text-white">{run.image_date}</span><span className="mt-1 block text-xs text-[#939185]">Previous: {run.previous_image_date || "-"}</span></td><td className="px-5 py-4">{data.quarry?.name || "Official Quarry"}</td><td className="px-5 py-4"><span className={`rounded-full border px-2 py-1 text-[10px] font-medium ${statusClasses[run.status] || statusClasses.ERROR}`}>{run.status}</span></td><td className="px-5 py-4 font-mono text-xs">{formatAcres(run.current_excavation_area_ha, 3)} <span className="text-[#939185]">/ {run.previous_image_date ? run.previous_image_date : "baseline"}</span></td><td className="px-5 py-4 font-mono text-xs text-[#E6B9A6]">{run.status === "BASELINE" ? "-" : formatAcres(run.outside_area_ha, 3)}</td><td className="px-5 py-4 text-xs text-[#939185]">{run.source}</td><td className="px-5 py-4"><Link href={`/map?run=${run.id}`} className="text-xs text-[#E6B9A6] hover:text-white">View result &gt;</Link></td></tr>)}{runs.length === 0 && <tr><td colSpan={7} className="px-5 py-14 text-center text-sm text-[#939185]">No monitoring runs match the selected filters.</td></tr>}</tbody></table></div>
  </AppShell>;
}
