"use client";

import { ChangeEvent, useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { getLateritePrediction, predictLateriteImage } from "@/services/api";
import { LateritePredictionSummary } from "@/types";

export default function PredictionPage() {
  const [modelStatus, setModelStatus] = useState<LateritePredictionSummary | null>(null);
  const [prediction, setPrediction] = useState<LateritePredictionSummary | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imageName, setImageName] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLateritePrediction().then(setModelStatus).catch(() => {
      setError("Could not check whether the stone model is available.");
    });
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleImageSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setImageName(file.name);
    setPreviewUrl(URL.createObjectURL(file));
    setPrediction(null);
    setError(null);
    event.target.value = "";
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      setPrediction(await predictLateriteImage(selectedFile));
    } catch (analyzeError: unknown) {
      setError(analyzeError instanceof Error ? analyzeError.message : "Image analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <AppShell title="Stone Quality" eyebrow="Laterite grade prediction">
      <section className="mx-auto max-w-4xl rounded-2xl border border-amber-500/20 bg-gradient-to-br from-amber-500/10 via-slate-900/80 to-slate-900/70 p-5 sm:p-7">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-amber-300">Laterite stone prediction</p>
            <h2 className="mt-2 text-xl font-semibold text-white">Quality grade assessment</h2>
            <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400">Choose a stone image, then analyze it to see the predicted grade and confidence.</p>
          </div>
          <span className={`rounded-full border px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.16em] ${modelStatus?.available ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300" : "border-slate-600 bg-slate-800/80 text-slate-300"}`}>
            {modelStatus ? modelStatus.available ? "Model active" : "Model idle" : "Checking model"}
          </span>
        </div>

        <div className="mt-6 rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-3">
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-xs font-medium uppercase tracking-[0.14em] text-emerald-300">
                <input type="file" accept="image/*" className="hidden" onChange={handleImageSelect} />
                Choose stone image
              </label>
              {imageName && <span className="max-w-full truncate text-xs text-slate-300">{imageName}</span>}
            </div>
            <button type="button" onClick={handleAnalyze} disabled={!selectedFile || isAnalyzing || modelStatus?.available === false} className="rounded-xl border border-amber-400/50 bg-amber-500/15 px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-amber-200 transition hover:bg-amber-500/25 disabled:cursor-not-allowed disabled:opacity-40">
              {isAnalyzing ? "Analyzing..." : "Analyze image"}
            </button>
          </div>

          {error && <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">{error}</p>}
          {previewUrl && (
            <div className="mt-5 max-w-xl overflow-hidden rounded-xl border border-white/10 bg-slate-950/50 p-3">
              <p className="mb-3 text-[10px] uppercase tracking-[0.16em] text-slate-400">Uploaded stone</p>
              <img src={previewUrl} alt={`Uploaded laterite stone: ${imageName}`} className="max-h-96 w-full rounded-lg object-contain" />
              <p className="mt-2 truncate text-xs text-slate-400">{imageName}</p>
            </div>
          )}

          {selectedFile && !prediction && (
            <p className="mt-4 rounded-lg border border-dashed border-slate-600 bg-slate-950/30 p-4 text-sm text-slate-300">
              {isAnalyzing ? "Analyzing the selected stone image..." : "Image ready. Select Analyze image to get its quality grade."}
            </p>
          )}

          {prediction?.available && (
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4">
                <p className="text-[10px] uppercase tracking-[0.16em] text-slate-400">Predicted grade</p>
                <p className="mt-3 text-3xl font-semibold text-amber-300">{prediction.grade || "-"}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4">
                <p className="text-[10px] uppercase tracking-[0.16em] text-slate-400">Confidence</p>
                <p className="mt-3 text-3xl font-semibold text-emerald-300">{prediction.confidence != null ? `${prediction.confidence.toFixed(1)}%` : "-"}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-slate-950/50 p-4">
                <p className="text-[10px] uppercase tracking-[0.16em] text-slate-400">Model source</p>
                <p className="mt-3 break-all text-sm leading-6 text-slate-200">{prediction.model_path ? prediction.model_path.split("\\").slice(-2).join("\\") : "Unavailable"}</p>
              </div>
            </div>
          )}

          {modelStatus?.available === false && !error && (
            <p className="mt-4 rounded-lg border border-dashed border-slate-600 bg-slate-950/30 p-4 text-sm text-slate-300">{modelStatus.reason || "The laterite model is not available right now."}</p>
          )}
        </div>
      </section>
    </AppShell>
  );
}
