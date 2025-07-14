/**
 * Tipos adicionales para los servicios
 */

export type StreamQuality = 'low' | 'medium' | 'high' | 'ultra';

// Tipo simplificado de Camera que coincide con la respuesta de la API
export interface CameraInfo {
  camera_id: string;
  display_name: string;
  brand: string;
  model?: string;
  ip: string;
  is_connected: boolean;
  is_streaming: boolean;
  status: string;
  last_updated: string;
  capabilities?: string[];
}

export interface ConnectionConfig {
  ip: string;
  username: string;
  password: string;
  protocol: string;
  port?: number;
}

// Para compatibilidad temporal mientras se migra completamente
export type Camera = CameraInfo;