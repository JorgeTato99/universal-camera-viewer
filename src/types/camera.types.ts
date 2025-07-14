/**
 * Camera Types & Interfaces
 * Based on Python CameraModel and related types
 */

export enum ConnectionStatus {
  DISCONNECTED = "disconnected",
  CONNECTING = "connecting",
  CONNECTED = "connected",
  ERROR = "error",
  STREAMING = "streaming",
  UNAVAILABLE = "unavailable",
}

export enum ProtocolType {
  RTSP = "rtsp",
  ONVIF = "onvif",
  HTTP = "http",
  AMCREST = "amcrest",
  GENERIC = "generic",
}

export interface ConnectionConfig {
  ip: string;
  username: string;
  password: string;
  rtsp_port: number;
  onvif_port: number;
  http_port: number;
  timeout: number;
  max_retries: number;
  retry_delay: number;
}

export interface StreamConfig {
  channel: number;
  subtype: number;
  resolution: string;
  codec: string;
  fps: number;
  bitrate: number;
  quality: string;
}

export interface CameraCapabilities {
  supported_protocols: ProtocolType[];
  max_resolution: string;
  supported_codecs: string[];
  has_ptz: boolean;
  has_audio: boolean;
  has_ir: boolean;
  onvif_version?: string;
}

export interface ConnectionStats {
  connection_attempts: number;
  successful_connections: number;
  failed_connections: number;
  last_connection_time?: string;
  last_error?: string;
  total_uptime: number;
  average_response_time: number;
}

export interface Camera {
  camera_id: string;
  brand: string;
  model: string;
  display_name: string;
  connection_config: ConnectionConfig;
  stream_config: StreamConfig;
  capabilities: CameraCapabilities;
  status: ConnectionStatus;
  is_connected: boolean;
  is_streaming: boolean;
  current_protocol?: ProtocolType;
  stats: ConnectionStats;
  created_at: string;
  last_updated: string;
  metadata: Record<string, any>;
}

export interface CameraGridItem {
  camera: Camera;
  thumbnail?: string;
  last_frame?: string;
  error_message?: string;
}

export type CameraFormData = Omit<
  Camera,
  | "camera_id"
  | "stats"
  | "created_at"
  | "last_updated"
  | "status"
  | "is_connected"
  | "is_streaming"
>;
