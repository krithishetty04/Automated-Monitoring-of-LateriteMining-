"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import AppShell from "@/components/AppShell";
import { useDashboardData } from "@/components/useDashboardData";
import { formatAcresValue, PERMITTED_AREA_ACRES } from "@/area";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function MapPage() {
  const data = useDashboardData();

  useEffect(() => {
    const runId = Number(new URLSearchParams(window.location.search).get("run"));
    if (runId) data.loadRunOnMap(runId).catch(() => undefined);
  }, [data.loadRunOnMap]);

  return <AppShell title="Quarry Map" eyebrow="Geospatial monitoring" actions={<span className="rounded-full border border-white/10 px-3 py-1.5 text-[11px] text-[#939185]">{data.quarry?.name || "Loading site"}</span>}>
    <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <div className="rounded-xl border border-white/[0.08] bg-[#3B4251] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#939185]">Permitted area</p><p className="mt-2 text-2xl font-semibold text-[#E6B9A6]">{formatAcresValue(PERMITTED_AREA_ACRES)}</p></div>
      <div className="rounded-xl border border-white/[0.08] bg-[#3B4251] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#939185]">Latest result</p><p className="mt-2 text-2xl font-semibold text-white">{data.latestRun?.status || "NO DATA"}</p></div>
      <div className="rounded-xl border border-white/[0.08] bg-[#3B4251] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#939185]">Overlay run</p><p className="mt-2 text-2xl font-semibold text-white">{data.mapRunId ? `#${data.mapRunId}` : "-"}</p></div>
      <div className="rounded-xl border border-white/[0.08] bg-[#3B4251] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#939185]">Permitted period</p><p className="mt-2 text-lg font-semibold text-white">23 Jan 2026 - 22 Jan 2027</p></div>
    </div>
    <div className="mb-5"><h2 className="text-lg font-semibold text-white">Activity map</h2><p className="mt-1 text-sm text-[#939185]">The legal boundary stays visible. Toggle excavation activity on or off to review the latest detected areas.</p></div>
    <MapView officialGeoJson={data.officialGeoJson} layers={data.layers} mapRunId={data.mapRunId} height={680} />
    <div className="mt-5 grid gap-4 md:grid-cols-2"><div className="rounded-xl border border-white/[0.08] bg-[#3B4251] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#939185]">Map note</p><p className="mt-2 text-sm leading-6 text-[#D7D5D0]">The permitted boundary marks the approved quarry area. The analysis area used by monitoring is not a legal buffer.</p></div><div className="rounded-xl border border-white/[0.08] bg-[#3B4251] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#939185]">Satellite source</p><p className="mt-2 text-sm leading-6 text-[#D7D5D0]">{data.latestRun?.source || "No monitoring source recorded yet"}</p></div></div>
  </AppShell>;
}
