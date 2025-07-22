/**
 * 🏷️ Sistema Centralizado de Etiquetas de Estado - Universal Camera Viewer
 * 
 * Este archivo centraliza todas las traducciones de estados del sistema al español.
 * En el futuro, este sistema facilitará la internacionalización (i18n) de la aplicación.
 * 
 * IMPORTANTE: Los estados en el código SIEMPRE deben ser en inglés (enums).
 * Este archivo es el único lugar donde se definen las traducciones.
 */

// ============================================
// ESTADOS DE PUBLICACIÓN (MediaMTX)
// ============================================

/**
 * Estados de publicación MediaMTX
 * 
 * NOTA IMPORTANTE: 
 * - Backend maneja: IDLE, STARTING, PUBLISHING, ERROR, STOPPED
 * - Frontend agrega: STOPPING, RECONNECTING (estados locales para mejor UX)
 * 
 * Los estados STOPPING y RECONNECTING son transitorios y se manejan
 * únicamente en el frontend para dar mejor feedback al usuario.
 */
export const PublishingStatusLabels = {
  IDLE: 'Inactivo',
  STARTING: 'Iniciando',
  PUBLISHING: 'Publicando',
  STOPPING: 'Deteniendo',      // Solo frontend - estado transitorio
  STOPPED: 'Detenido',
  ERROR: 'Error',
  RECONNECTING: 'Reconectando' // Solo frontend - estado transitorio
} as const;

/**
 * Descripciones detalladas de estados de publicación
 */
export const PublishingStatusDescriptions = {
  IDLE: 'No hay publicación activa',
  STARTING: 'Iniciando conexión con MediaMTX',
  PUBLISHING: 'Transmitiendo activamente a MediaMTX',
  STOPPING: 'Deteniendo la publicación...',
  STOPPED: 'Publicación detenida manualmente',
  ERROR: 'Error en la publicación',
  RECONNECTING: 'Intentando reconectar con el servidor...'
} as const;

// ============================================
// ESTADOS DE CONEXIÓN DE CÁMARAS
// ============================================

/**
 * Estados de conexión de cámaras IP
 */
export const CameraConnectionLabels = {
  CONNECTED: 'Conectado',
  CONNECTING: 'Conectando',
  DISCONNECTED: 'Desconectado',
  ERROR: 'Error',
  STREAMING: 'Transmitiendo',
  UNAVAILABLE: 'No disponible'
} as const;

/**
 * Descripciones de estados de conexión
 */
export const CameraConnectionDescriptions = {
  CONNECTED: 'Cámara conectada y lista',
  CONNECTING: 'Estableciendo conexión con la cámara...',
  DISCONNECTED: 'Sin conexión con la cámara',
  ERROR: 'Error al conectar con la cámara',
  STREAMING: 'Transmitiendo video en vivo',
  UNAVAILABLE: 'Cámara no disponible en la red'
} as const;

// ============================================
// ESTADOS DE ESCANEO DE RED
// ============================================

/**
 * Estados de escaneo de red
 */
export const ScanStatusLabels = {
  IDLE: 'Esperando',
  SCANNING: 'Escaneando',
  COMPLETED: 'Completado',
  ERROR: 'Error',
  CANCELLED: 'Cancelado'
} as const;

/**
 * Descripciones de estados de escaneo
 */
export const ScanStatusDescriptions = {
  IDLE: 'Esperando inicio de escaneo',
  SCANNING: 'Buscando dispositivos en la red...',
  COMPLETED: 'Escaneo completado exitosamente',
  ERROR: 'Error durante el escaneo',
  CANCELLED: 'Escaneo cancelado por el usuario'
} as const;

// ============================================
// ESTADOS DE SERVICIO
// ============================================

/**
 * Estados generales de servicios del sistema
 */
export const ServiceStatusLabels = {
  RUNNING: 'Ejecutando',
  STOPPED: 'Detenido',
  STARTING: 'Iniciando',
  STOPPING: 'Deteniendo',
  ERROR: 'Error'
} as const;

// ============================================
// SEVERIDAD DE ALERTAS
// ============================================

/**
 * Niveles de severidad para alertas
 */
export const AlertSeverityLabels = {
  info: 'Información',
  warning: 'Advertencia',
  error: 'Error',
  critical: 'Crítico'
} as const;

// ============================================
// TIPOS DE ERROR
// ============================================

/**
 * Tipos de error comunes en el sistema
 */
export const ErrorTypeLabels = {
  CONNECTION_FAILED: 'Fallo de conexión',
  AUTHENTICATION_FAILED: 'Fallo de autenticación',
  STREAM_UNAVAILABLE: 'Stream no disponible',
  MEDIAMTX_UNREACHABLE: 'MediaMTX inaccesible',
  PROCESS_CRASHED: 'Proceso terminado inesperadamente',
  TIMEOUT: 'Tiempo de espera agotado',
  UNKNOWN: 'Error desconocido'
} as const;

// ============================================
// FUNCIONES HELPER
// ============================================

/**
 * Obtiene la etiqueta en español para un estado
 * @param labels - Objeto con las etiquetas
 * @param status - Estado a traducir
 * @param defaultLabel - Etiqueta por defecto si no se encuentra
 * @returns Etiqueta en español
 */
export function getStatusLabel<T extends Record<string, string>>(
  labels: T,
  status: keyof T | string,
  defaultLabel = 'Desconocido'
): string {
  return labels[status as keyof T] || defaultLabel;
}

/**
 * Obtiene la etiqueta para un estado de publicación
 */
export function getPublishingStatusLabel(
  status: string,
  defaultLabel = 'Desconocido'
): string {
  return getStatusLabel(PublishingStatusLabels, status, defaultLabel);
}

/**
 * Obtiene la descripción para un estado de publicación
 */
export function getPublishingStatusDescription(
  status: string,
  defaultDescription = 'Estado desconocido'
): string {
  return getStatusLabel(PublishingStatusDescriptions, status, defaultDescription);
}

/**
 * Obtiene la etiqueta para un estado de conexión de cámara
 */
export function getCameraConnectionLabel(
  status: string,
  defaultLabel = 'Desconocido'
): string {
  return getStatusLabel(CameraConnectionLabels, status, defaultLabel);
}

/**
 * Obtiene la etiqueta para un estado de escaneo
 */
export function getScanStatusLabel(
  status: string,
  defaultLabel = 'Desconocido'
): string {
  return getStatusLabel(ScanStatusLabels, status, defaultLabel);
}

/**
 * Obtiene la etiqueta para un nivel de severidad
 */
export function getAlertSeverityLabel(
  severity: string,
  defaultLabel = 'Información'
): string {
  return getStatusLabel(AlertSeverityLabels, severity, defaultLabel);
}

/**
 * Obtiene la etiqueta para un tipo de error
 */
export function getErrorTypeLabel(
  errorType: string,
  defaultLabel = 'Error'
): string {
  return getStatusLabel(ErrorTypeLabels, errorType, defaultLabel);
}

// ============================================
// MAPEO BACKEND → FRONTEND
// ============================================

/**
 * Mapea estados del backend a estados del frontend
 * 
 * IMPORTANTE: Esta función maneja la conversión de estados del backend
 * a los estados más detallados del frontend, incluyendo estados transitorios.
 * 
 * @param backendStatus - Estado recibido del backend
 * @param context - Contexto adicional para determinar estados transitorios
 * @returns Estado correspondiente en el frontend
 */
export function mapBackendToFrontendPublishingStatus(
  backendStatus: string,
  context?: {
    isReconnecting?: boolean;
    isStopping?: boolean;
  }
): string {
  // Si el backend dice ERROR pero sabemos que estamos reconectando
  if (backendStatus === 'error' && context?.isReconnecting) {
    return 'RECONNECTING';
  }
  
  // Si estamos en proceso de detener (frontend tracking)
  if (context?.isStopping) {
    return 'STOPPING';
  }
  
  // Mapeo directo para el resto
  const statusMap: Record<string, string> = {
    'idle': 'IDLE',
    'starting': 'STARTING',
    'publishing': 'PUBLISHING',
    'stopped': 'STOPPED',
    'error': 'ERROR'
  };
  
  return statusMap[backendStatus.toLowerCase()] || 'ERROR';
}

/**
 * Determina si un estado indica actividad
 */
export function isActivePublishingStatus(status: string): boolean {
  return ['STARTING', 'PUBLISHING', 'RECONNECTING'].includes(status.toUpperCase());
}

/**
 * Determina si un estado es de error
 */
export function isErrorPublishingStatus(status: string): boolean {
  return status.toUpperCase() === 'ERROR';
}

/**
 * Determina si un estado es transitorio (solo frontend)
 */
export function isTransientPublishingStatus(status: string): boolean {
  return ['STOPPING', 'RECONNECTING'].includes(status.toUpperCase());
}