"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { ChangeEvent, useState } from "react";
import AppShell from "@/components/AppShell";
import AlertPanel from "@/components/AlertPanel";
import RunControls from "@/components/RunControls";
import SummaryCards from "@/components/SummaryCards";
import { useDashboardData } from "@/components/useDashboardData";
import { predictLateriteImage } from "@/services/api";
import { LateritePredictionSummary } from "@/types";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

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
  const [selectedImageName, setSelectedImageName] = useState<string>("");
  const [isPredicting, setIsPredicting] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedLateritePrediction, setUploadedLateritePrediction] = useState<LateritePredictionSummary | null>(null);
  const lateritePrediction = uploadedLateritePrediction ?? data.lateritePrediction;
  const unreadAlerts = data.alerts.filter((alert) => !alert.is_read).length;
  const potentialDetections = data.alerts.filter((alert) => alert.alert_type === "UNAUTHORIZED_EXPANSION").length;
  const isSafe = data.latestRun && ["SAFE", "PERMITTED", "BASELINE"].includes(data.latestRun.status);
  const lastScanDate = data.latestRun?.image_date
    ? new Date(data.latestRun.image_date).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })
    : "Awaiting run";

  const handleImageUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedImageName(file.name);
    setUploadError(null);
    setIsPredicting(true);

    try {
      const result = await predictLateriteImage(file);
      setUploadedLateritePrediction(result);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Image prediction failed.";
      setUploadError(message);
    } finally {
      setIsPredicting(false);
    }
  };

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

      <section className="mb-8 rounded-2xl border border-amber-500/20 bg-gradient-to-br from-amber-500/10 via-slate-900/80 to-slate-900/70 p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-300">Laterite stone prediction</p>
            <h3 className="mt-2 text-xl font-semibold text-white">Quality grade assessment</h3>
          </div>
          <span className={`rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.16em] ${lateritePrediction?.available ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300" : "border-slate-600 bg-slate-800/80 text-slate-300"}`}>
            {lateritePrediction?.available ? "Model active" : "Model idle"}
          </span>
        </div>

        <div className="mt-5 rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-xs font-medium uppercase tracking-[0.14em] text-emerald-300">
              <input type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
              {isPredicting ? "Analyzing..." : "Upload laterite image"}
            </label>
            {selectedImageName && <span className="text-xs text-slate-300">{selectedImageName}</span>}
          </div>

          {uploadError && <p className="mt-3 text-sm text-red-300">{uploadError}</p>}

          {lateritePrediction?.available ? (
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
                <p className="text-[10px] uppercase tracking-[0.16em] text-slate-400">Predicted grade</p>
                <p className="mt-3 text-3xl font-semibold text-amber-300">{lateritePrediction.grade || "—"}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
                <p className="text-[10px] uppercase tracking-[0.16em] text-slate-400">Confidence</p>
                <p className="mt-3 text-3xl font-semibold text-emerald-300">{lateritePrediction.confidence != null ? `${lateritePrediction.confidence.toFixed(1)}%` : "—"}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
                <p className="text-[10px] uppercase tracking-[0.16em] text-slate-400">Model source</p>
                <p className="mt-3 text-sm leading-6 text-slate-200">{lateritePrediction.model_path ? lateritePrediction.model_path.split("\\").slice(-2).join("\\") : "Unavailable"}</p>
              </div>
            </div>
          ) : (
            <div className="mt-5 rounded-xl border border-dashed border-slate-600 bg-slate-950/30 p-4 text-sm text-slate-300">
              {lateritePrediction?.reason || "Laterite model is not available right now."}
            </div>
          )}
        </div>
      </section>

      <section className="mb-8 grid gap-6 xl:grid-cols-[minmax(0,1.8fr)_minmax(300px,0.9fr)]">
        <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
          <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Site activity map</h3>
              <p className="mt-1 text-xs text-slate-400">Official boundary and latest detected areas</p>
            </div>
            <Link href="/map" className="text-xs font-medium text-emerald-300 hover:text-white">Open full map →</Link>
          </div>

          <MapView officialGeoJson={data.officialGeoJson} layers={data.layers} mapRunId={data.mapRunId} height={430} />

          <div className="border-t border-white/10 bg-slate-950/40 px-5 py-4">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">Latest satellite analysis</h3>
                <p className="mt-1 text-xs text-slate-400">Current monitoring result and change summary</p>
              </div>
              <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-slate-300">{data.latestRun?.source || "Awaiting run"}</span>
            </div>
            <SummaryCards quarry={data.quarry} run={data.latestRun} compact />
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-slate-900/70 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
          <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Recent alerts</h3>
              <p className="mt-1 text-xs text-slate-400">Items needing attention</p>
            </div>
            <Link href="/alerts" className="text-xs font-medium text-emerald-300 hover:text-white">View all →</Link>
          </div>
          <AlertPanel alerts={data.alerts.slice(0, 3)} onMarkRead={data.handleMarkRead} onViewOnMap={async (runId) => { await data.loadRunOnMap(runId); }} />
        </div>
      </section>
    </AppShell>
  );
}
