import { MonitoringRun, Quarry } from "@/types";
import { formatAcres, formatAcresValue, PERMITTED_AREA_ACRES } from "@/area";

function statusLabel(status: string) {
  switch (status) {
    case "ALERT":
      return { text: "ALERT", color: "text-red-400" };
    case "PERMITTED":
      return { text: "PERMITTED", color: "text-emerald-400" };
    case "BASELINE":
      return { text: "BASELINE", color: "text-slate-300" };
    case "SAFE":
      return { text: "SAFE", color: "text-emerald-400" };
    default:
      return { text: status || "NO DATA", color: "text-slate-400" };
  }
}

function Card({
  label,
  value,
  accent,
  compact = false,
}: {
  label: string;
  value: React.ReactNode;
  accent?: string;
  compact?: boolean;
}) {
  return (
    <div className={`rounded-xl border border-white/10 bg-slate-900/70 p-3 ${compact ? "min-h-[88px]" : "p-4"}`}>
      <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
        {label}
      </span>
      <span className={`mt-2 block ${compact ? "text-lg font-semibold" : "text-2xl font-semibold"} ${accent || "text-slate-50"}`}>
        {value}
      </span>
    </div>
  );
}

export default function SummaryCards({
  quarry,
  run,
  compact = false,
}: {
  quarry: Quarry | null;
  run: MonitoringRun | null;
  compact?: boolean;
}) {
  const status = run ? statusLabel(run.status) : { text: "NO DATA", color: "text-slate-400" };

  if (compact) {
    return (
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-5">
        <Card label="Permitted Area" value={formatAcresValue(PERMITTED_AREA_ACRES)} accent="text-emerald-400" compact />
        <Card label="Current Excavation" value={formatAcres(run?.current_excavation_area_ha ?? 0)} accent="text-red-400" compact />
        <Card label="Previous Excavation" value={formatAcres(run?.previous_excavation_area_ha ?? 0)} compact />
        <Card label="Inside Permitted" value={formatAcres(run?.inside_area_ha ?? 0)} accent="text-emerald-400" compact />
        <Card label="Unauthorized" value={formatAcres(run?.outside_area_ha ?? 0)} accent="text-amber-400" compact />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
      <Card label="Permitted Area" value={formatAcresValue(PERMITTED_AREA_ACRES)} accent="text-emerald-400" />
      <Card label="Current Excavation" value={formatAcres(run?.current_excavation_area_ha ?? 0)} accent="text-red-400" />
      <Card label="Previous Excavation" value={formatAcres(run?.previous_excavation_area_ha ?? 0)} />
      <Card label="New Excavation" value={formatAcres(run?.new_excavation_area_ha ?? 0)} />
      <Card label="Inside Permitted" value={formatAcres(run?.inside_area_ha ?? 0)} accent="text-emerald-400" />
      <Card label="Unauthorized Expansion" value={formatAcres(run?.outside_area_ha ?? 0)} accent="text-amber-400" />
      <Card label="Current Status" value={status.text} accent={status.color} />
    </div>
  );
}
