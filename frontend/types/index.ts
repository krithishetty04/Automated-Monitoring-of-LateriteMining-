export type RunStatus = "BASELINE" | "SAFE" | "PERMITTED" | "ALERT" | "ERROR";

export interface ExcavationResult {
  id: number;
  current_excavation_geojson: string | null;
  previous_excavation_geojson: string | null;
  new_excavation_geojson: string | null;
  unauthorized_expansion_geojson: string | null;
  depth_status: "AVAILABLE" | "UNAVAILABLE" | "INSUFFICIENT_DATA" | "ESTIMATE" | null;
  depth_message: string | null;
  mean_depth_m: number | null;
  median_depth_m: number | null;
  max_depth_m: number | null;
  min_depth_m: number | null;
  estimated_volume_m3: number | null;
  valid_elevation_samples: number | null;
  elevation_source: string | null;
  depth_method: string | null;
  before_elevation_date: string | null;
  after_elevation_date: string | null;
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

export interface LateritePredictionSummary {
  available: boolean;
  model_path: string;
  reason: string;
  grade: string | null;
  confidence: number | null;
  sample_image: string | null;
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

export type CoverStatus = "NEEDS_COVERING" | "COVERING" | "COVERED" | "AGRICULTURE";

export interface SiteUpdate {
  id: number;
  area_name: string | null;
  tonnes_removed: number | null;
  depth_m: number | null;
  cover_status: CoverStatus | null;
  notes: string | null;
  created_at: string;
}

export interface SiteProgress {
  total_tonnes_removed: number;
  has_tonnage_records: boolean;
  latest_depth_m: number | null;
  latest_depth_area: string | null;
  latest_depth_at: string | null;
  updates: SiteUpdate[];
}

export interface SiteUpdateInput {
  area_name?: string;
  tonnes_removed?: number;
  depth_m?: number;
  cover_status?: CoverStatus;
  notes?: string;
}
