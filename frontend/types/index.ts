export type RunStatus = "BASELINE" | "SAFE" | "PERMITTED" | "ALERT" | "ERROR";

export interface ExcavationResult {
  id: number;
  current_excavation_geojson: string | null;
  previous_excavation_geojson: string | null;
  new_excavation_geojson: string | null;
  unauthorized_expansion_geojson: string | null;
}

export interface MonitoringRun {
  id: number;
  quarry_id: number;
  image_date: string;
  previous_image_date: string | null;
  cloud_percentage: number | null;
  current_excavation_area_ha: number;
  previous_excavation_area_ha: number;
  new_excavation_area_ha: number;
  inside_area_ha: number;
  outside_area_ha: number;
  status: RunStatus;
  source: string;
  created_at: string;
  excavation_result?: ExcavationResult | null;
}

export interface MonitoringRunSummary {
  id: number;
  image_date: string;
  previous_image_date: string | null;
  current_excavation_area_ha: number;
  new_excavation_area_ha: number;
  outside_area_ha: number;
  status: RunStatus;
  source: string;
}

export interface Alert {
  id: number;
  monitoring_run_id: number;
  alert_type: string;
  severity: string;
  message: string;
  expansion_area_ha: number;
  geometry: string | null;
  is_read: boolean;
  created_at: string;
}

export interface Quarry {
  id: number;
  name: string;
  area_ha: number;
  geometry_geojson: string;
}

export interface RunGeoJsonLayers {
  current_excavation: GeoJSON.FeatureCollection | GeoJSON.Feature | null;
  previous_excavation: GeoJSON.FeatureCollection | GeoJSON.Feature | null;
  new_excavation: GeoJSON.FeatureCollection | GeoJSON.Feature | null;
  unauthorized_expansion: GeoJSON.FeatureCollection | GeoJSON.Feature | null;
}
