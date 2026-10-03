 import { MonitoringRunSummary } from "@/types";
import { formatAcres } from "@/area";

function statusBadge(status: string) {
  const map: Record<string, string> = {
    ALERT: "bg-excavate/20 text-excavate border-excavate/50",
    PERMITTED: "bg-permit/20 text-permit border-permit/50",
    SAFE: "bg-permit/10 text-permit/80 border-permit/30",
    BASELINE: "bg-clay-600/20 text-clay-400 border-clay-600/50",
    ERROR: "bg-base-700 text-base-600 border-base-600",
  };
  return map[status] || "bg-base-700 text-[#EEEDEB]";
}

export default function HistoryTable({ runs }: { runs: MonitoringRunSummary[] }) {
  return (
    <div className="bg-base-900 border border-base-700 rounded-lg p-4 overflow-x-auto">
      <h2 className="font-mono text-sm uppercase tracking-widest text-base-600 mb-3">
        Weekly Monitoring History
      </h2>
      <table className="w-full text-sm font-mono">
        <thead>
          <tr className="text-left text-base-600 border-b border-base-700">
            <th className="py-2 pr-4">Date</th>
            <th className="py-2 pr-4">Previous</th>
            <th className="py-2 pr-4">Excavation</th>
            <th className="py-2 pr-4">New Area</th>
            <th className="py-2 pr-4">Outside</th>
            <th className="py-2 pr-4">Status</th>
            <th className="py-2 pr-4">Source</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id} className="border-b border-base-800 hover:bg-base-800/50">
              <td className="py-2 pr-4">{run.image_date}</td>
              <td className="py-2 pr-4">{run.previous_image_date || "-"}</td>
              <td className="py-2 pr-4">{formatAcres(run.current_excavation_area_ha)}</td>
              <td className="py-2 pr-4">
                {run.status === "BASELINE" ? "-" : formatAcres(run.new_excavation_area_ha)}
              </td>
              <td className="py-2 pr-4">
                {run.status === "BASELINE" ? "-" : formatAcres(run.outside_area_ha)}
              </td>
              <td className="py-2 pr-4">
                <span className={`px-2 py-0.5 rounded border text-xs ${statusBadge(run.status)}`}>
                  {run.status}
                </span>
              </td>
              <td className="py-2 pr-4 text-xs text-base-600">{run.source}</td>
            </tr>
          ))}
          {runs.length === 0 && (
            <tr>
              <td colSpan={7} className="py-4 text-center text-base-600">
                No monitoring runs yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
