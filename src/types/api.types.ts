/**
 * API Types & Interfaces
 * Types for Tauri commands and Python backend communication
 */

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface TauriCommandResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

// Tauri Command Names
export enum TauriCommands {
  // Camera Commands
  SCAN_CAMERAS = "scan_cameras",
  CONNECT_CAMERA = "connect_camera",
  DISCONNECT_CAMERA = "disconnect_camera",
  GET_CAMERA_INFO = "get_camera_info",
  CAPTURE_SNAPSHOT = "capture_snapshot",

  // Streaming Commands
  START_STREAM = "start_stream",
  STOP_STREAM = "stop_stream",
  GET_STREAM_STATUS = "get_stream_status",
  GET_STREAM_METRICS = "get_stream_metrics",

  // Network Scanning Commands
  START_NETWORK_SCAN = "start_network_scan",
  STOP_NETWORK_SCAN = "stop_network_scan",
  GET_SCAN_PROGRESS = "get_scan_progress",
  GET_SCAN_RESULTS = "get_scan_results",

  // Configuration Commands
  GET_CONFIG = "get_config",
  SET_CONFIG = "set_config",
  SAVE_CONFIG = "save_config",
  LOAD_CONFIG = "load_config",

  // File System Commands
  SAVE_FILE = "save_file",
  LOAD_FILE = "load_file",
  CREATE_BACKUP = "create_backup",

  // System Commands
  GET_SYSTEM_INFO = "get_system_info",
  GET_PERFORMANCE_METRICS = "get_performance_metrics",
}

// Tauri Events
export enum TauriEvents {
  // Camera Events
  CAMERA_DISCOVERED = "camera_discovered",
  CAMERA_CONNECTED = "camera_connected",
  CAMERA_DISCONNECTED = "camera_disconnected",
  CAMERA_ERROR = "camera_error",

  // Streaming Events
  FRAME_RECEIVED = "frame_received",
  STREAM_STARTED = "stream_started",
  STREAM_STOPPED = "stream_stopped",
  STREAM_ERROR = "stream_error",
  STREAM_METRICS_UPDATE = "stream_metrics_update",

  // Scanning Events
  SCAN_STARTED = "scan_started",
  SCAN_PROGRESS = "scan_progress",
  SCAN_COMPLETED = "scan_completed",
  SCAN_ERROR = "scan_error",

  // System Events
  CONFIG_CHANGED = "config_changed",
  NOTIFICATION = "notification",
  ERROR = "error",
}

// Command Payloads
export interface ScanCamerasPayload {
  network_range?: string;
  timeout?: number;
  protocols?: string[];
}

export interface ConnectCameraPayload {
  camera_id: string;
  connection_config: {
    ip: string;
    username: string;
    password: string;
    protocol: string;
  };
}

export interface StartStreamPayload {
  camera_id: string;
  quality?: string;
  fps?: number;
}

export interface StartNetworkScanPayload {
  scan_range: {
    start_ip: string;
    end_ip: string;
    ports: number[];
  };
  methods: string[];
  timeout: number;
}

export interface SetConfigPayload {
  key: string;
  value: any;
  category?: string;
}

// Event Payloads
export interface CameraDiscoveredEvent {
  camera: {
    ip: string;
    brand: string;
    model: string;
    protocols: string[];
  };
}

export interface FrameReceivedEvent {
  camera_id: string;
  frame_data: string; // base64
  timestamp: string;
  frame_number: number;
}

export interface ScanProgressEvent {
  scan_id: string;
  current: number;
  total: number;
  message: string;
  cameras_found: number;
}

export interface StreamMetricsEvent {
  camera_id: string;
  metrics: {
    fps: number;
    latency_ms: number;
    bandwidth_kbps: number;
    frame_count: number;
    dropped_frames: number;
  };
}

export interface NotificationEvent {
  type: "success" | "error" | "warning" | "info";
  title: string;
  message: string;
  duration?: number;
}
