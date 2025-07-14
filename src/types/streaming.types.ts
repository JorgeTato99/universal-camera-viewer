/**
 * Streaming Types & Interfaces
 * Based on Python StreamModel and related types
 */

export enum StreamStatus {
  IDLE = "idle",
  CONNECTING = "connecting",
  STREAMING = "streaming",
  PAUSED = "paused",
  ERROR = "error",
  DISCONNECTED = "disconnected",
}

export enum StreamProtocol {
  RTSP = "rtsp",
  ONVIF = "onvif",
  HTTP = "http",
  GENERIC = "generic",
}

export interface StreamMetrics {
  stream_id: string;
  current_fps: number;
  average_fps: number;
  current_latency_ms: number;
  average_latency_ms: number;
  bandwidth_kbps: number;
  average_bandwidth_kbps: number;
  total_frames: number;
  dropped_frames: number;
  drop_rate_percent: number;
  error_count: number;
  reconnect_count: number;
  total_bytes: number;
  uptime_seconds: number;
  health_score: number;
  last_update: string;
}

export interface StreamModel {
  stream_id: string;
  camera_id: string;
  protocol: StreamProtocol;
  target_fps: number;
  buffer_size: number;
  status: StreamStatus;
  fps: number;
  frame_count: number;
  dropped_frames: number;
  start_time?: string;
  last_frame_time?: string;
  error_message?: string;
  reconnect_attempts: number;
  metadata: Record<string, any>;
}

export interface FrameData {
  camera_id: string;
  stream_id: string;
  frame_base64: string;
  timestamp: string;
  frame_number: number;
  quality: number;
  size_bytes: number;
  resolution: string;
  encoding: string;
}

export interface StreamingConfig {
  resolution: string;
  fps: number;
  quality: string;
  codec: string;
  channel: number;
  subtype: number;
}

export interface VideoPlayerState {
  isPlaying: boolean;
  isFullscreen: boolean;
  volume: number;
  muted: boolean;
  currentTime: number;
  duration: number;
  buffered: number;
}

export interface StreamingSession {
  camera_id: string;
  stream: StreamModel;
  metrics: StreamMetrics;
  current_frame?: FrameData;
  player_state: VideoPlayerState;
  last_activity: string;
}
