"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import AppShell from "@/components/AppShell";
import { useDashboardData } from "@/components/useDashboardData";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function MapPage() {
  const data = useDashboardData();

  useEffect(() => {
    const runId = Number(new URLSearchParams(window.location.search).get("run"));
    if (runId) data.loadRunOnMap(runId).catch(() => undefined);
  }, [data.loadRunOnMap]);

  return <AppShell title="Quarry Map" eyebrow="Geospatial monitoring" actions={<span className="rounded-full border border-white/10 px-3 py-1.5 text-[11px] text-[#91a88f]">{data.quarry?.name || "Loading site"}</span>}>
    <div className="mb-6 grid gap-4 sm:grid-cols-3">
      <div className="rounded-xl border border-white/[0.08] bg-[#10201b] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#759087]">Official area</p><p className="mt-2 text-2xl font-semibold text-[#c5d86d]">{data.quarry?.area_ha.toFixed(2) || "—"} <span className="text-sm font-normal text-[#789187]">ha</span></p></div>
      <div className="rounded-xl border border-white/[0.08] bg-[#10201b] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#759087]">Latest result</p><p className="mt-2 text-2xl font-semibold text-white">{data.latestRun?.status || "NO DATA"}</p></div>
      <div className="rounded-xl border border-white/[0.08] bg-[#10201b] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#759087]">Overlay run</p><p className="mt-2 text-2xl font-semibold text-white">{data.mapRunId ? `#${data.mapRunId}` : "—"}</p></div>
    </div>
    <div className="mb-5"><h2 className="text-lg font-semibold text-white">Activity layers</h2><p className="mt-1 text-sm text-[#789187]">Use the layer controls to compare the legal boundary with current, previous, new, and potentially unauthorized excavation.</p></div>
    <MapView officialGeoJson={data.officialGeoJson} layers={data.layers} mapRunId={data.mapRunId} height={680} />
    <div className="mt-5 grid gap-4 md:grid-cols-2"><div className="rounded-xl border border-white/[0.08] bg-[#10201b] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#759087]">Map note</p><p className="mt-2 text-sm leading-6 text-[#a7b9b0]">The official quarry polygon is the legal boundary. The analysis area used by monitoring is not a legal buffer.</p></div><div className="rounded-xl border border-white/[0.08] bg-[#10201b] p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-[#759087]">Satellite source</p><p className="mt-2 text-sm leading-6 text-[#a7b9b0]">{data.latestRun?.source || "No monitoring source recorded yet"}</p></div></div>
  </AppShell>;
}
