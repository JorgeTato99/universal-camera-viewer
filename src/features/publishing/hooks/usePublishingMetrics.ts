/**
 * 🪝 usePublishingMetrics Hook - Universal Camera Viewer
 * Hook para gestión de métricas de publicación
 */

import { useCallback, useEffect, useRef } from 'react';
import { usePublishingStore } from '../../../stores/publishingStore';
import { PublishMetrics } from '../types';
import { calculateMetricStats } from '../utils';

interface UsePublishingMetricsOptions {
  cameraId: string;
  autoRefresh?: boolean;
  refreshInterval?: number; // en segundos
  maxSamples?: number;
}

/**
 * Hook para métricas de publicación en tiempo real
 */
export function usePublishingMetrics({
  cameraId,
  autoRefresh = true,
  refreshInterval = 5,
  maxSamples = 50
}: UsePublishingMetricsOptions) {
  const {
    currentMetrics,
    isLoadingMetrics,
    fetchMetrics,
    getLatestMetrics,
    isPublishingActive
  } = usePublishingStore();

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isActive = isPublishingActive(cameraId);
  const isLoading = isLoadingMetrics.get(cameraId) || false;
  const metrics = getLatestMetrics(cameraId, maxSamples);

  // Función para actualizar métricas
  const refresh = useCallback(async () => {
    if (isActive) {
      await fetchMetrics(cameraId);
    }
  }, [cameraId, isActive, fetchMetrics]);

  // Auto-refresh de métricas
  useEffect(() => {
    if (autoRefresh && isActive && refreshInterval > 0) {
      // Fetch inicial
      refresh();

      // Configurar intervalo
      intervalRef.current = setInterval(refresh, refreshInterval * 1000);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [autoRefresh, isActive, refreshInterval, refresh]);

  // Calcular estadísticas
  const stats = calculateMetricStats(metrics);

  // Obtener última métrica
  const latestMetric: PublishMetrics | undefined = metrics[metrics.length - 1];

  return {
    // Datos
    metrics,
    latestMetric,
    stats,
    
    // Estados
    isLoading,
    isActive,
    
    // Acciones
    refresh
  };
}