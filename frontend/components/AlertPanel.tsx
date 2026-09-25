"use client";

import { Alert } from "@/types";

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

export default function AlertPanel({
  alerts,
  onMarkRead,
  onViewOnMap,
}: {
  alerts: Alert[];
  onMarkRead: (id: number) => void;
  onViewOnMap: (runId: number) => void;
}) {
  return (
    <div className="flex max-h-[560px] flex-col gap-3 overflow-y-auto p-4">
      {alerts.length === 0 && (
        <p className="text-sm text-slate-400">No alerts yet.</p>
      )}
      {alerts.map((alert) => {
        const isUnauthorized = alert.alert_type === "UNAUTHORIZED_EXPANSION";
        const severityTone = isUnauthorized ? "border-red-500/30 bg-red-500/5 text-red-300" : alert.severity === "WARNING" ? "border-amber-500/30 bg-amber-500/5 text-amber-300" : "border-emerald-500/30 bg-emerald-500/5 text-emerald-300";

        return (
          <div
            key={alert.id}
            className={`rounded-xl border p-3 ${severityTone} ${alert.is_read ? "opacity-60" : ""}`}
          >
            <div className="flex items-start justify-between gap-3">
              <span className="text-sm font-semibold text-slate-50">
                {isUnauthorized ? "Unauthorized Quarry Expansion" : "Permitted Excavation Activity"}
              </span>
              <span className="text-[10px] uppercase tracking-[0.16em] text-slate-400">{formatDate(alert.created_at)}</span>
            </div>
            <div className="mt-2 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.18em]">
              <span className={isUnauthorized ? "text-red-300" : alert.severity === "WARNING" ? "text-amber-300" : "text-emerald-300"}>{alert.severity}</span>
              <span className="text-slate-500">{alert.is_read ? "Read" : "Unread"}</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-300">{alert.message}</p>
            {alert.expansion_area_ha > 0 && (
              <p className="mt-2 text-xs text-slate-300">
                Expansion: <span className="font-medium text-amber-300">{alert.expansion_area_ha.toFixed(3)} ha</span> — Outside permitted boundary
              </p>
            )}
            <div className="mt-3 flex gap-2">
              <button
                onClick={() => onViewOnMap(alert.monitoring_run_id)}
                className="rounded-lg border border-white/10 bg-slate-800 px-2.5 py-1.5 text-xs text-slate-200 transition hover:border-slate-500 hover:text-white"
              >
                View on Map
              </button>
              {!alert.is_read && (
                <button
                  onClick={() => onMarkRead(alert.id)}
                  className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1.5 text-xs font-medium text-emerald-300 transition hover:bg-emerald-500/20"
                >
                  Mark as Read
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
