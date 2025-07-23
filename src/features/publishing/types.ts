/**
 * 🎯 Publishing Types - Universal Camera Viewer
 * Tipos TypeScript para el módulo de publicación MediaMTX
 */

// === INTERFACES BASE ===

/**
 * Configuración de servidor MediaMTX
 */
export interface PublishConfiguration {
  id: number;
  name: string;
  mediamtx_url: string;
  api_url?: string;
  api_enabled: boolean;
  username?: string;
  password?: string;
  auth_enabled: boolean;
  use_tcp: boolean;
  is_active: boolean;
  max_reconnects: number;
  reconnect_delay: number;
  publish_path_template: string;
  created_at: string;
  updated_at: string;
}

/**
 * Estado de publicación de una cámara
 */
export interface PublishStatus {
  camera_id: string;
  status: PublishingStatus;
  publish_path: string;
  uptime_seconds: number;
  error_count: number;
  last_error?: string;
  metrics: PublishMetrics;
}

/**
 * Estados posibles de publicación
 * 
 * IMPORTANTE: Estados híbridos backend/frontend
 * - Backend maneja: IDLE, STARTING, PUBLISHING, ERROR, STOPPED
 * - Frontend agrega: STOPPING, RECONNECTING (estados transitorios locales)
 * 
 * Los estados STOPPING y RECONNECTING son manejados localmente en el frontend
 * para proporcionar mejor feedback al usuario durante operaciones asíncronas.
 */
export enum PublishingStatus {
  IDLE = 'IDLE',
  STARTING = 'STARTING', 
  PUBLISHING = 'PUBLISHING',  // Antes era RUNNING
  STOPPING = 'STOPPING',      // Solo frontend - transitorio
  STOPPED = 'STOPPED',        // Nuevo - del backend
  ERROR = 'ERROR',
  RECONNECTING = 'RECONNECTING' // Solo frontend - transitorio
}

/**
 * Métricas de publicación en tiempo real
 */
export interface PublishMetrics {
  fps: number;
  bitrate_kbps: number;
  viewers: number;
  frames_sent: number;
  bytes_sent: number;
  timestamp: string;
}

/**
 * Estado de salud del sistema de publicación
 */
export interface PublishingHealth {
  overall_status: 'healthy' | 'warning' | 'error';
  total_servers: number;
  healthy_servers: number;
  active_publications: number;
  total_viewers: number;
  active_alerts: PublishingAlert[];
}

/**
 * Alerta del sistema
 */
export interface PublishingAlert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  alert_type: string;
  message: string;
  timestamp: string;
  camera_id?: string;
  dismissible: boolean;
}

/**
 * Sesión histórica de publicación
 */
export interface PublishingHistorySession {
  session_id: string;
  camera_id: string;
  server_id: number;
  start_time: string;
  end_time?: string;
  duration_seconds: number;
  status: string;
  error_message?: string;
  total_frames: number;
  total_bytes: number;
  average_fps: number;
  average_bitrate_kbps: number;
}

/**
 * Path de MediaMTX
 */
export interface MediaMTXPath {
  id: number;
  server_id: number;
  path_name: string;
  source_type: 'rtsp' | 'rtmp' | 'hls' | 'webrtc';
  source_url: string;
  record_enabled: boolean;
  authentication_required: boolean;
  allowed_ips?: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// === REQUESTS ===

/**
 * Request para iniciar publicación
 */
export interface StartPublishingRequest {
  camera_id: string;
  force_restart?: boolean;
}

/**
 * Request para detener publicación
 */
export interface StopPublishingRequest {
  camera_id: string;
}

/**
 * Request para crear configuración
 */
export interface CreateConfigurationRequest {
  name: string;
  mediamtx_url: string;
  api_url?: string;
  api_enabled?: boolean;
  username?: string;
  password?: string;
  auth_enabled?: boolean;
  use_tcp?: boolean;
  max_reconnects?: number;
  reconnect_delay?: number;
  publish_path_template?: string;
}

/**
 * Request para crear path
 */
export interface CreatePathRequest {
  server_id: number;
  path_name: string;
  source_type: 'rtsp' | 'rtmp' | 'hls' | 'webrtc';
  source_url: string;
  record_enabled?: boolean;
  authentication_required?: boolean;
  allowed_ips?: string[];
}

// === RESPONSES ===

/**
 * Respuesta paginada genérica
 */
export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

/**
 * Respuesta de API genérica
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  error_code?: string;
}

/**
 * Estadísticas agregadas
 */
export interface PublishingStatistics {
  time_range: string;
  total_sessions: number;
  total_duration_hours: number;
  total_data_gb: number;
  average_viewers: number;
  peak_viewers: number;
  most_active_cameras: CameraActivity[];
  error_rate: number;
  uptime_percentage: number;
}

/**
 * Actividad de cámara
 */
export interface CameraActivity {
  camera_id: string;
  camera_name: string;
  total_sessions: number;
  total_duration_hours: number;
  average_viewers: number;
}

// === FILTROS ===

/**
 * Filtros para historial
 */
export interface HistoryFilters {
  camera_id?: string;
  start_date?: string;
  end_date?: string;
  status?: string;
  min_duration?: number;
  page?: number;
  page_size?: number;
  order_by?: string;
  order_desc?: boolean;
}

/**
 * Filtros para métricas
 */
export interface MetricsFilters {
  time_range?: 'last_hour' | 'last_6_hours' | 'last_24_hours' | 'last_7_days' | 'last_30_days' | 'custom';
  start_date?: string;
  end_date?: string;
  include_events?: boolean;
}

// === UTILIDADES ===

/**
 * Colores de estado para UI
 */
export const STATUS_COLORS = {
  [PublishingStatus.IDLE]: '#9e9e9e',         // Gris
  [PublishingStatus.STARTING]: '#ff9800',     // Naranja
  [PublishingStatus.PUBLISHING]: '#4caf50',   // Verde (antes RUNNING)
  [PublishingStatus.STOPPING]: '#ff9800',     // Naranja
  [PublishingStatus.STOPPED]: '#757575',      // Gris oscuro
  [PublishingStatus.ERROR]: '#f44336',        // Rojo
  [PublishingStatus.RECONNECTING]: '#2196f3'  // Azul
} as const;

/**
 * Labels de estado para UI
 */
export const STATUS_LABELS = {
  [PublishingStatus.IDLE]: 'Inactivo',
  [PublishingStatus.STARTING]: 'Iniciando',
  [PublishingStatus.PUBLISHING]: 'Publicando',  // Antes RUNNING
  [PublishingStatus.STOPPING]: 'Deteniendo',
  [PublishingStatus.STOPPED]: 'Detenido',
  [PublishingStatus.ERROR]: 'Error',
  [PublishingStatus.RECONNECTING]: 'Reconectando'
} as const;

/**
 * Iconos de severidad para alertas
 */
export const ALERT_ICONS = {
  info: 'ℹ️',
  warning: '⚠️',
  error: '❌',
  critical: '🚨'
} as const;