/**
 * 🪝 usePublishingHealth Hook - Universal Camera Viewer
 * Hook para monitoreo de salud del sistema MediaMTX
 */

import { useCallback, useEffect, useRef } from 'react';
import { usePublishingStore } from '../../../stores/publishingStore';

interface UsePublishingHealthOptions {
  autoRefresh?: boolean;
  refreshInterval?: number; // en segundos
  includeAlerts?: boolean;
}

/**
 * Hook para monitoreo de salud del sistema
 */
export function usePublishingHealth({
  autoRefresh = true,
  refreshInterval = 60, // Incrementado de 30s a 60s para reducir carga del servidor
  includeAlerts = true
}: UsePublishingHealthOptions = {}) {
  const {
    systemHealth,
    alerts,
    isLoading,
    fetchSystemHealth,
    fetchAlerts,
    dismissAlert,
    getPublicationCounts
  } = usePublishingStore();

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const counts = getPublicationCounts();

  // Función para actualizar salud
  const refresh = useCallback(async () => {
    const promises: Promise<void>[] = [fetchSystemHealth()];
    
    if (includeAlerts) {
      promises.push(fetchAlerts());
    }
    
    await Promise.all(promises);
  }, [fetchSystemHealth, fetchAlerts, includeAlerts]);

  // Auto-refresh de salud
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
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
  }, [autoRefresh, refreshInterval, refresh]);

  // Calcular indicadores de salud
  const healthIndicators = {
    isHealthy: systemHealth?.overall_status === 'healthy',
    hasWarnings: systemHealth?.overall_status === 'warning',
    hasErrors: systemHealth?.overall_status === 'error',
    serverHealth: systemHealth ? 
      (systemHealth.healthy_servers / systemHealth.total_servers) * 100 : 0,
    activeAlerts: alerts.filter(a => !a.dismissible || a.severity === 'critical'),
    dismissibleAlerts: alerts.filter(a => a.dismissible && a.severity !== 'critical')
  };

  // Función para manejar alertas
  const handleDismissAlert = useCallback(async (alertId: string) => {
    dismissAlert(alertId);
  }, [dismissAlert]);

  return {
    // Datos
    systemHealth,
    alerts,
    publicationCounts: counts,
    healthIndicators,
    
    // Estados
    isLoading,
    
    // Acciones
    refresh,
    dismissAlert: handleDismissAlert
  };
}