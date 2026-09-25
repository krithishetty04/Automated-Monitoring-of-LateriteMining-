"use client";

import { useState } from "react";

export default function RunControls({
  onRun,
}: {
  onRun: () => Promise<void>;
}) {
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      await onRun();
    } finally {
      setLoading(false);
    }
  };

  const btnClass =
    "inline-flex items-center justify-center rounded-lg border border-white/10 bg-slate-900/80 px-3 py-2 text-[11px] font-medium text-slate-200 transition hover:border-emerald-400/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-50";

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-white/10 bg-slate-900/70 p-2">
      <button className={`${btnClass} border-emerald-500/30 bg-emerald-500/10 text-emerald-300`} disabled={loading} onClick={run}>
        {loading ? "Running…" : "Run Analysis"}
      </button>
    </div>
  );
}
