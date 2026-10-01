"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  LateritePredictionSummary,
  MonitoringRun,
  MonitoringRunSummary,
  Quarry,
  RunGeoJsonLayers,
} from "@/types";
import {
  getAlerts,
  getHistory,
  getLatestRun,
  getLateritePrediction,
  getQuarry,
  getQuarryGeoJson,
  getRunGeoJson,
  markAlertRead,
  triggerMonitoringRun,
} from "@/services/api";

export function useDashboardData() {
  const [quarry, setQuarry] = useState<Quarry | null>(null);
  const [officialGeoJson, setOfficialGeoJson] = useState<GeoJSON.Feature | null>(null);
  const [latestRun, setLatestRun] = useState<MonitoringRun | null>(null);
  const [history, setHistory] = useState<MonitoringRunSummary[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [lateritePrediction, setLateritePrediction] = useState<LateritePredictionSummary | null>(null);
  const [layers, setLayers] = useState<RunGeoJsonLayers | null>(null);
  const [mapRunId, setMapRunId] = useState<number | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  const refreshAll = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [quarryResult, geoResult, latestResult, historyResult, alertsResult, lateriteResult] = await Promise.allSettled([
        getQuarry(),
        getQuarryGeoJson(),
        getLatestRun(),
        getHistory(),
        getAlerts(),
        getLateritePrediction(),
      ]);

      if (quarryResult.status === "fulfilled") setQuarry(quarryResult.value);
      if (geoResult.status === "fulfilled") setOfficialGeoJson(geoResult.value);
      if (latestResult.status === "fulfilled") setLatestRun(latestResult.value);
      if (historyResult.status === "fulfilled") setHistory(historyResult.value);
      if (alertsResult.status === "fulfilled") setAlerts(alertsResult.value);
      if (lateriteResult.status === "fulfilled") setLateritePrediction(lateriteResult.value);

      const run = latestResult.status === "fulfilled" ? latestResult.value : null;
      if (run) {
        try {
          const nextLayers = await getRunGeoJson(run.id);
          setLayers(nextLayers);
          setMapRunId(run.id);
        } catch {
          // Keep the previous map state if only the overlay request fails.
        }
      }

      const failures = [quarryResult, geoResult, latestResult, historyResult, alertsResult, lateriteResult]
        .filter((result) => result.status === "rejected").length;
      setDashboardError(failures ? "Some monitoring data could not be refreshed." : null);
      setLastUpdated(new Date());
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 45000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  const loadRunOnMap = useCallback(async (runId: number) => {
    const nextLayers = await getRunGeoJson(runId);
    setLayers(nextLayers);
    setMapRunId(runId);
  }, []);

  const handleRun = useCallback(async () => {
    await triggerMonitoringRun();
    await refreshAll();
  }, [refreshAll]);

  const handleMarkRead = useCallback(async (alertId: number) => {
    await markAlertRead(alertId);
    setAlerts((current) => current.map((alert) =>
      alert.id === alertId ? { ...alert, is_read: true } : alert
    ));
  }, []);

  return {
    quarry,
    officialGeoJson,
    latestRun,
    history,
    alerts,
    lateritePrediction,
    layers,
    mapRunId,
    isRefreshing,
    lastUpdated,
    dashboardError,
    refreshAll,
    loadRunOnMap,
    handleRun,
    handleMarkRead,
  };
}