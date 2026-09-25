import axios from "axios";
import {
  MonitoringRun,
  MonitoringRunSummary,
  Alert,
  Quarry,
  RunGeoJsonLayers,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

const client = axios.create({ baseURL: API_BASE_URL });

export async function getLatestRun(): Promise<MonitoringRun | null> {
  try {
    const res = await client.get<MonitoringRun>("/api/monitoring/latest");
    return res.data;
  } catch {
    return null;
  }
}

export async function getHistory(limit = 50): Promise<MonitoringRunSummary[]> {
  const res = await client.get<MonitoringRunSummary[]>("/api/monitoring/history", {
    params: { limit },
  });
  return res.data;
}

export async function getRunGeoJson(runId: number): Promise<RunGeoJsonLayers> {
  const res = await client.get<RunGeoJsonLayers>(`/api/monitoring/${runId}/geojson`);
  return res.data;
}

export async function getQuarry(): Promise<Quarry> {
  const res = await client.get<Quarry>("/api/quarry");
  return res.data;
}

export async function getQuarryGeoJson(): Promise<GeoJSON.Feature> {
  const res = await client.get<GeoJSON.Feature>("/api/quarry/geojson");
  return res.data;
}

export async function getAlerts(): Promise<Alert[]> {
  const res = await client.get<Alert[]>("/api/alerts");
  return res.data;
}

export async function markAlertRead(alertId: number): Promise<Alert> {
  const res = await client.post<Alert>(`/api/alerts/${alertId}/read`);
  return res.data;
}

export async function triggerMonitoringRun(): Promise<MonitoringRun> {
  const res = await client.post<MonitoringRun>("/api/monitoring/run", {
    mode: "real",
  });
  return res.data;
}
