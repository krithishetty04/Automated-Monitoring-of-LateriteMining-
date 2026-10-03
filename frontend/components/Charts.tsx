"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { MonitoringRunSummary } from "@/types";
import { hectaresToAcres } from "@/area";

export default function Charts({ runs }: { runs: MonitoringRunSummary[] }) {
  const data = [...runs]
    .sort((a, b) => a.image_date.localeCompare(b.image_date) || a.id - b.id)
    .map((run) => ({
      date: new Date(run.image_date).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "2-digit" }),
      fullDate: run.image_date,
      runId: run.id,
      excavation: hectaresToAcres(run.current_excavation_area_ha),
      outsideBoundary: hectaresToAcres(run.outside_area_ha),
  }));

  if (data.length === 0) {
    return (
      <div className="flex min-h-[260px] items-center justify-center rounded-xl border border-dashed border-white/10 bg-[#090F20] px-6 text-center">
        <div>
          <p className="text-sm font-medium text-slate-200">No monitoring trends yet</p>
          <p className="mt-1 text-xs text-slate-400">Run an analysis to see excavation area changes here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#090F20] p-4 sm:p-5">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-white">Excavation trends</h3>
          <p className="mt-1 text-xs text-slate-400">Detected area by monitoring run, in acres</p>
        </div>
        <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500">Latest {data.length} runs</span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 12, right: 12, bottom: 2, left: -16 }}>
          <defs>
            <linearGradient id="excavationTrendFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#27C99A" stopOpacity={0.32} />
              <stop offset="95%" stopColor="#27C99A" stopOpacity={0.015} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#263148" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="date" stroke="#71809A" tickLine={false} axisLine={false} tick={{ fill: "#91A0B8", fontSize: 11 }} minTickGap={20} />
          <YAxis stroke="#71809A" tickLine={false} axisLine={false} tick={{ fill: "#91A0B8", fontSize: 11 }} tickFormatter={(value: number) => `${value}`} width={42} />
          <Tooltip
            labelFormatter={(_label, entries) => entries?.[0]?.payload ? `${entries[0].payload.fullDate} - Run #${entries[0].payload.runId}` : _label}
            formatter={(value: number | string | Array<number | string>, name: number | string) => [typeof value === "number" ? `${value.toFixed(3)} ac` : `${value} ac`, name]}
            contentStyle={{ backgroundColor: "#111A2D", border: "1px solid #33415A", borderRadius: 12, fontSize: 12, color: "#EEEDEB" }}
            labelStyle={{ color: "#B8C5D9", marginBottom: 4 }}
          />
          <Area type="linear" dataKey="excavation" name="Total excavation" stroke="#27C99A" strokeWidth={2.5} fill="url(#excavationTrendFill)" dot={{ r: 3, fill: "#27C99A", stroke: "#10231F", strokeWidth: 1.5 }} activeDot={{ r: 4, fill: "#27C99A", stroke: "#D9FFF2", strokeWidth: 1.5 }} />
          <Line type="linear" dataKey="outsideBoundary" name="New outside permitted boundary" stroke="#E58C78" strokeWidth={2.5} dot={{ r: 3, fill: "#E58C78", stroke: "#1A2437", strokeWidth: 1.5 }} activeDot={{ r: 5, fill: "#E58C78", stroke: "#FFF0E9", strokeWidth: 1.5 }} />
        </AreaChart>
      </ResponsiveContainer>
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-[11px] text-slate-300">
        <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[#27C99A]" />Total excavation</span>
        <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[#E58C78]" />New outside permitted boundary</span>
      </div>
    </div>
  );
}
