"use client";

import { useState } from "react";
import { MapContainer, TileLayer, GeoJSON as LeafletGeoJSON } from "react-leaflet";
import { RunGeoJsonLayers } from "@/types";

interface LayerToggleState {
  activity: boolean;
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
    activity: true,
  });

  const toggleActivity = () =>
    setToggles((prev) => ({ ...prev, activity: !prev.activity }));

  return (
    <div className="relative overflow-hidden rounded-t-2xl bg-slate-950">
      <div className="absolute right-3 top-3 z-[1000] w-[220px] rounded-lg border border-slate-700/50 bg-slate-900/90 p-2.5 shadow-xl backdrop-blur-md">
        <p className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-300">Map layers</p>
        <div className="space-y-2">
          <div className="flex items-center gap-2 rounded-md border border-slate-700/60 bg-slate-800/70 px-2 py-2 text-[11px] font-medium text-slate-100">
            <span className="inline-block h-0.5 w-4 rounded bg-emerald-950 ring-1 ring-emerald-200" />
            <span>Permitted boundary</span>
          </div>
          <Toggle label="Excavation activity" color="#733A32" checked={toggles.activity} onChange={toggleActivity} />
        </div>
      </div>

      <div style={{ height: `${height}px`, width: "100%" }}>
        <MapContainer center={QUARRY_CENTER} zoom={17} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
          {officialGeoJson && (
            <LeafletGeoJSON
              key="official-halo"
              data={officialGeoJson as any}
              style={{ color: "#EEEDEB", weight: 7, opacity: 0.9, fillOpacity: 0 }}
            />
          )}
          {officialGeoJson && (
            <LeafletGeoJSON
              key="official-boundary"
              data={officialGeoJson as any}
              style={{ color: "#14532D", weight: 4, opacity: 1, fillColor: "#166534", fillOpacity: 0.16 }}
            />
          )}
          {toggles.activity && layers?.current_excavation && (
            <LeafletGeoJSON
              key={`current-${mapRunId}`}
              data={layers.current_excavation as any}
              style={{ color: "#65302B", weight: 1.5, fillColor: "#65302B", fillOpacity: 0.82 }}
            />
          )}
          {toggles.activity && layers?.new_excavation && (
            <LeafletGeoJSON
              key={`newExc-${mapRunId}`}
              data={layers.new_excavation as any}
              style={{ color: "#733A32", weight: 1.8, fillColor: "#733A32", fillOpacity: 0.82 }}
            />
          )}
          {toggles.activity && layers?.unauthorized_expansion && (
            <LeafletGeoJSON
              key={`unauthorized-${mapRunId}`}
              data={layers.unauthorized_expansion as any}
              style={{ color: "#939185", weight: 2.2, fillOpacity: 0.58 }}
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}
