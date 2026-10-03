"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { MonitoringRunSummary } from "@/types";
import { hectaresToAcres } from "@/area";

export default function Charts({ runs }: { runs: MonitoringRunSummary[] }) {
  const data = runs.map((r) => ({
    date: r.image_date,
    excavation: hectaresToAcres(r.current_excavation_area_ha),
    unauthorized: hectaresToAcres(r.outside_area_ha),
  }));

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
          Excavation Area Over Time
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <CartesianGrid stroke="#4B5261" strokeDasharray="3 3" />
            <XAxis dataKey="date" stroke="#939185" fontSize={11} />
            <YAxis stroke="#939185" fontSize={11} unit=" ac" />
            <Tooltip
              contentStyle={{ backgroundColor: "#252C3B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, fontSize: 12, color: "#EEEDEB" }}
            />
            <Line type="monotone" dataKey="excavation" stroke="#D28A83" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
          Unauthorized Expansion Over Time
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <CartesianGrid stroke="#4B5261" strokeDasharray="3 3" />
            <XAxis dataKey="date" stroke="#939185" fontSize={11} />
            <YAxis stroke="#939185" fontSize={11} unit=" ac" />
            <Tooltip
              contentStyle={{ backgroundColor: "#252C3B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, fontSize: 12, color: "#EEEDEB" }}
            />
            <Line type="monotone" dataKey="unauthorized" stroke="#E6B9A6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
