/**
 * 🎯 Publishing Service - Universal Camera Viewer
 * Servicio para comunicación con APIs de publicación MediaMTX
 */

import { apiClient } from '../api/apiClient';
import {
  PublishConfiguration,
  PublishStatus,
  PublishingHealth,
  PublishingHistorySession,
  PublishMetrics,
  MediaMTXPath,
  PublishingStatistics,
  StartPublishingRequest,
  StopPublishingRequest,
  CreateConfigurationRequest,
  CreatePathRequest,
  HistoryFilters,
  MetricsFilters,
  PaginatedResponse,
  ApiResponse
} from '../../features/publishing/types';

/**
 * Servicio principal para gestión de publicaciones MediaMTX
 */
class PublishingService {
  private baseEndpoint = '/publishing';

  // === CONTROL DE PUBLICACIONES ===

  /**
   * Iniciar publicación de una cámara
   */
  async startPublishing(request: StartPublishingRequest): Promise<ApiResponse<PublishStatus>> {
    return apiClient.post<PublishStatus>(`${this.baseEndpoint}/start`, request);
  }

  /**
   * Detener publicación de una cámara
   */
  async stopPublishing(request: StopPublishingRequest): Promise<ApiResponse<{ message: string }>> {
    return apiClient.post<{ message: string }>(`${this.baseEndpoint}/stop`, request);
  }

  /**
   * Obtener estado de todas las publicaciones
   */
  async getAllPublishingStatus(): Promise<ApiResponse<PublishStatus[]>> {
    return apiClient.get<PublishStatus[]>(`${this.baseEndpoint}/status`);
  }

  /**
   * Obtener estado de publicación de una cámara específica
   */
  async getPublishingStatus(cameraId: string): Promise<ApiResponse<PublishStatus>> {
    return apiClient.get<PublishStatus>(`${this.baseEndpoint}/status/${cameraId}`);
  }

  // === SALUD DEL SISTEMA ===

  /**
   * Obtener estado de salud general del sistema
   */
  async getSystemHealth(): Promise<ApiResponse<PublishingHealth>> {
    return apiClient.get<PublishingHealth>(`${this.baseEndpoint}/health`);
  }

  /**
   * Verificar salud de un servidor específico
   */
  async checkServerHealth(serverId: number): Promise<ApiResponse<{ 
    status: string; 
    rtsp_available: boolean; 
    api_available: boolean 
  }>> {
    return apiClient.post(`${this.baseEndpoint}/servers/${serverId}/health-check`, {
      check_rtsp: true,
      check_api: true,
      timeout_seconds: 10
    });
  }

  // === CONFIGURACIONES ===

  /**
   * Obtener todas las configuraciones de servidores MediaMTX
   */
  async getConfigurations(): Promise<ApiResponse<PublishConfiguration[]>> {
    return apiClient.get<PublishConfiguration[]>(`${this.baseEndpoint}/config`);
  }

  /**
   * Obtener configuración activa
   */
  async getActiveConfiguration(): Promise<ApiResponse<PublishConfiguration>> {
    return apiClient.get<PublishConfiguration>(`${this.baseEndpoint}/config/active`);
  }

  /**
   * Crear nueva configuración
   */
  async createConfiguration(config: CreateConfigurationRequest): Promise<ApiResponse<PublishConfiguration>> {
    return apiClient.post<PublishConfiguration>(`${this.baseEndpoint}/config`, config);
  }

  /**
   * Actualizar configuración existente
   */
  async updateConfiguration(
    configName: string, 
    config: Partial<CreateConfigurationRequest>
  ): Promise<ApiResponse<PublishConfiguration>> {
    return apiClient.put<PublishConfiguration>(`${this.baseEndpoint}/config/${configName}`, config);
  }

  /**
   * Eliminar configuración
   */
  async deleteConfiguration(configName: string): Promise<ApiResponse<{ message: string }>> {
    return apiClient.delete<{ message: string }>(`${this.baseEndpoint}/config/${configName}`);
  }

  /**
   * Activar configuración específica
   */
  async activateConfiguration(configName: string): Promise<ApiResponse<PublishConfiguration>> {
    return apiClient.post<PublishConfiguration>(`${this.baseEndpoint}/config/${configName}/activate`);
  }

  // === MÉTRICAS ===

  /**
   * Obtener métricas actuales de una cámara
   */
  async getMetrics(cameraId: string): Promise<ApiResponse<PublishMetrics>> {
    return apiClient.get<PublishMetrics>(`${this.baseEndpoint}/metrics/${cameraId}`);
  }

  /**
   * Obtener historial de métricas con paginación
   */
  async getMetricsHistory(
    cameraId: string, 
    filters: MetricsFilters & { page?: number; page_size?: number }
  ): Promise<ApiResponse<PaginatedResponse<PublishMetrics>>> {
    return apiClient.get<PaginatedResponse<PublishMetrics>>(
      `${this.baseEndpoint}/metrics/${cameraId}/history`,
      filters
    );
  }

  /**
   * Exportar métricas a archivo
   */
  async exportMetrics(
    cameraId: string,
    format: 'csv' | 'excel' | 'json',
    filters: MetricsFilters
  ): Promise<Blob> {
    const response = await fetch(
      apiClient.getBaseURL() + `${this.baseEndpoint}/metrics/${cameraId}/export`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          format,
          ...filters
        })
      }
    );

    if (!response.ok) {
      throw new Error(`Error exportando métricas: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * Obtener estadísticas agregadas
   */
  async getStatistics(timeRange: string = 'last_7_days'): Promise<ApiResponse<PublishingStatistics>> {
    return apiClient.get<PublishingStatistics>(`${this.baseEndpoint}/statistics/summary`, {
      time_range: timeRange
    });
  }

  // === HISTORIAL ===

  /**
   * Obtener historial de sesiones con filtros
   */
  async getHistory(filters: HistoryFilters): Promise<ApiResponse<PaginatedResponse<PublishingHistorySession>>> {
    return apiClient.get<PaginatedResponse<PublishingHistorySession>>(
      `${this.baseEndpoint}/history`,
      filters
    );
  }

  /**
   * Obtener detalle de una sesión específica
   */
  async getSessionDetail(sessionId: string): Promise<ApiResponse<PublishingHistorySession>> {
    return apiClient.get<PublishingHistorySession>(`${this.baseEndpoint}/history/${sessionId}`);
  }

  /**
   * Obtener historial por cámara
   */
  async getCameraHistory(
    cameraId: string, 
    days: number = 7
  ): Promise<ApiResponse<PublishingHistorySession[]>> {
    return apiClient.get<PublishingHistorySession[]>(
      `${this.baseEndpoint}/history/camera/${cameraId}`,
      { days }
    );
  }

  /**
   * Limpiar historial antiguo
   */
  async cleanupHistory(
    olderThanDays: number, 
    keepErrors: boolean = true,
    dryRun: boolean = true
  ): Promise<ApiResponse<{ 
    deleted_count: number; 
    sessions_to_delete?: string[] 
  }>> {
    return apiClient.delete(`${this.baseEndpoint}/history`, {
      older_than_days: olderThanDays,
      keep_errors: keepErrors,
      dry_run: dryRun
    });
  }

  // === PATHS MEDIAMTX ===

  /**
   * Obtener paths configurados
   */
  async getPaths(serverId?: number, activeOnly?: boolean): Promise<ApiResponse<MediaMTXPath[]>> {
    return apiClient.get<MediaMTXPath[]>(`${this.baseEndpoint}/paths`, {
      server_id: serverId,
      active_only: activeOnly
    });
  }

  /**
   * Crear nuevo path
   */
  async createPath(path: CreatePathRequest): Promise<ApiResponse<MediaMTXPath>> {
    return apiClient.post<MediaMTXPath>(`${this.baseEndpoint}/paths`, path);
  }

  /**
   * Actualizar path existente
   */
  async updatePath(pathId: number, path: Partial<CreatePathRequest>): Promise<ApiResponse<MediaMTXPath>> {
    return apiClient.put<MediaMTXPath>(`${this.baseEndpoint}/paths/${pathId}`, path);
  }

  /**
   * Eliminar path
   */
  async deletePath(pathId: number): Promise<ApiResponse<{ message: string }>> {
    return apiClient.delete<{ message: string }>(`${this.baseEndpoint}/paths/${pathId}`);
  }

  /**
   * Probar conectividad de un path
   */
  async testPath(
    pathId: number, 
    timeoutSeconds: number = 10,
    testWrite: boolean = true
  ): Promise<ApiResponse<{ 
    success: boolean; 
    message: string; 
    latency_ms?: number 
  }>> {
    return apiClient.post(`${this.baseEndpoint}/paths/${pathId}/test`, {
      timeout_seconds: timeoutSeconds,
      test_write: testWrite
    });
  }

  /**
   * Obtener plantillas de paths disponibles
   */
  async getPathTemplates(): Promise<ApiResponse<Array<{
    name: string;
    description: string;
    template: Partial<CreatePathRequest>;
  }>>> {
    return apiClient.get(`${this.baseEndpoint}/paths/templates`);
  }

  // === VIEWERS Y AUDIENCIA ===

  /**
   * Obtener viewers activos
   */
  async getActiveViewers(activeOnly: boolean = true, page: number = 1, pageSize: number = 50): Promise<ApiResponse<PaginatedResponse<{
    viewer_id: string;
    camera_id: string;
    protocol: string;
    ip_address: string;
    connected_at: string;
    duration_seconds: number;
  }>>> {
    return apiClient.get(`${this.baseEndpoint}/viewers`, {
      active_only: activeOnly,
      page,
      page_size: pageSize
    });
  }

  /**
   * Obtener análisis de audiencia
   */
  async getViewerAnalytics(
    timeRange: string = 'last_7_days',
    groupBy: 'hour' | 'day' | 'week' = 'day',
    includeGeographic: boolean = true
  ): Promise<ApiResponse<{
    time_range: string;
    total_unique_viewers: number;
    average_concurrent_viewers: number;
    peak_concurrent_viewers: number;
    peak_time: string;
    viewer_distribution: Array<{
      timestamp: string;
      viewers: number;
    }>;
    geographic_distribution?: Array<{
      country: string;
      viewers: number;
    }>;
  }>> {
    return apiClient.get(`${this.baseEndpoint}/viewers/analytics`, {
      time_range: timeRange,
      group_by: groupBy,
      include_geographic: includeGeographic
    });
  }

  /**
   * Obtener estadísticas por protocolo
   */
  async getProtocolStats(): Promise<ApiResponse<Array<{
    protocol: string;
    active_connections: number;
    total_data_gb: number;
    average_bitrate_mbps: number;
  }>>> {
    return apiClient.get(`${this.baseEndpoint}/stats/protocols`);
  }

  // === ALERTAS ===

  /**
   * Obtener alertas activas
   */
  async getAlerts(severity?: 'info' | 'warning' | 'error' | 'critical'): Promise<ApiResponse<Array<{
    id: string;
    severity: string;
    message: string;
    camera_id?: string;
    timestamp: string;
    dismissible: boolean;
  }>>> {
    return apiClient.get(`${this.baseEndpoint}/alerts`, { severity });
  }

  /**
   * Descartar alerta
   */
  async dismissAlert(alertId: string): Promise<ApiResponse<{ message: string }>> {
    return apiClient.post(`${this.baseEndpoint}/alerts/${alertId}/dismiss`);
  }
}

// Exportar instancia singleton
export const publishingService = new PublishingService();

// Exportar clase para testing
export default PublishingService;