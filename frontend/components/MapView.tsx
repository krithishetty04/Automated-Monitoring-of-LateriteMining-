"use client";

import { useState } from "react";
import { MapContainer, TileLayer, GeoJSON as LeafletGeoJSON } from "react-leaflet";
import { RunGeoJsonLayers } from "@/types";

interface LayerToggleState {
  official: boolean;
  current: boolean;
  previous: boolean;
  newExcavation: boolean;
  unauthorized: boolean;
}

const QUARRY_CENTER: [number, number] = [12.99335, 74.94085];

function Toggle({
  label,
  color,
  checked,
  onChange,
}: {
  label: string;
  color: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onChange}
      className={`flex w-full items-center justify-between gap-2 rounded-md border px-2 py-1.5 text-left text-[11px] font-medium transition ${
        checked
          ? "border-slate-600 bg-slate-800/80 text-slate-100"
          : "border-slate-700/60 bg-slate-900/60 text-slate-300"
      }`}
    >
      <span className="flex items-center gap-2">
        <span className="inline-block h-2.5 w-2.5 rounded-full border border-slate-200/70" style={{ backgroundColor: color }} />
        <span>{label}</span>
      </span>
      <span
        className={`inline-flex h-5 w-8 items-center rounded-full border transition ${
          checked ? "border-emerald-400/60 bg-emerald-500/30" : "border-slate-600 bg-slate-700/70"
        }`}
      >
        <span
          className={`ml-0.5 h-3.5 w-3.5 rounded-full bg-white transition ${checked ? "translate-x-3" : "translate-x-0"}`}
        />
      </span>
    </button>
  );
}

export default function MapView({
  officialGeoJson,
  layers,
  mapRunId,
  height = 520,
}: {
  officialGeoJson: GeoJSON.Feature | null;
  layers: RunGeoJsonLayers | null;
  mapRunId: number | null;
  height?: number;
}) {
  const [toggles, setToggles] = useState<LayerToggleState>({
    official: true,
    current: true,
    previous: false,
    newExcavation: true,
    unauthorized: true,
  });

  const toggle = (key: keyof LayerToggleState) =>
    setToggles((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <div className="relative overflow-hidden rounded-t-2xl bg-slate-950">
      <div className="absolute right-3 top-3 z-[1000] w-[220px] rounded-lg border border-slate-700/50 bg-slate-900/85 p-2.5 shadow-xl backdrop-blur-md">
        <div className="space-y-2">
          <Toggle label="Official Boundary" color="#22C55E" checked={toggles.official} onChange={() => toggle("official")} />
          <Toggle label="Current Excavation" color="#F97316" checked={toggles.current} onChange={() => toggle("current")} />
          <Toggle label="Previous Excavation" color="#9CA3AF" checked={toggles.previous} onChange={() => toggle("previous")} />
          <Toggle label="New Excavation" color="#F59E0B" checked={toggles.newExcavation} onChange={() => toggle("newExcavation")} />
          <Toggle label="Unauthorized Expansion" color="#DC2626" checked={toggles.unauthorized} onChange={() => toggle("unauthorized")} />
        </div>
      </div>

      <div style={{ height: `${height}px`, width: "100%" }}>
        <MapContainer center={QUARRY_CENTER} zoom={17} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
          {toggles.official && officialGeoJson && (
            <LeafletGeoJSON
              key="official"
              data={officialGeoJson as any}
              style={{ color: "#22C55E", weight: 2, fillOpacity: 0.08 }}
            />
          )}
          {toggles.current && layers?.current_excavation && (
            <LeafletGeoJSON
              key={`current-${mapRunId}`}
              data={layers.current_excavation as any}
              style={{ color: "#EF4444", weight: 1, fillOpacity: 0.35 }}
            />
          )}
          {toggles.previous && layers?.previous_excavation && (
            <LeafletGeoJSON
              key={`previous-${mapRunId}`}
              data={layers.previous_excavation as any}
              style={{ color: "#8B5E3C", weight: 1, fillOpacity: 0.18, dashArray: "4" }}
            />
          )}
          {toggles.newExcavation && layers?.new_excavation && (
            <LeafletGeoJSON
              key={`newExc-${mapRunId}`}
              data={layers.new_excavation as any}
              style={{ color: "#FB923C", weight: 1.5, fillOpacity: 0.32 }}
            />
          )}
          {toggles.unauthorized && layers?.unauthorized_expansion && (
            <LeafletGeoJSON
              key={`unauthorized-${mapRunId}`}
              data={layers.unauthorized_expansion as any}
              style={{ color: "#F59E0B", weight: 2, fillOpacity: 0.55 }}
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}
