/**
 * Scanner Types & Interfaces
 * Based on Python ScanModel and related types
 */

export enum ScanStatus {
  IDLE = "idle",
  PREPARING = "preparing",
  SCANNING = "scanning",
  PROCESSING = "processing",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
  ERROR = "error",
}

export enum ScanMethod {
  PING_SWEEP = "ping_sweep",
  PORT_SCAN = "port_scan",
  PROTOCOL_DETECTION = "protocol_detection",
  ONVIF_DISCOVERY = "onvif_discovery",
  UPNP_DISCOVERY = "upnp_discovery",
}

export interface ScanRange {
  start_ip: string;
  end_ip: string;
  ports: number[];
  protocols: string[];
  timeout: number;
}

export interface ScanConfig {
  network_ranges: string[];
  ports: number[];
  timeout: number;
  max_threads: number;
  include_onvif: boolean;
  include_rtsp: boolean;
  include_http: boolean;
  include_amcrest: boolean;
  test_authentication: boolean;
  auto_detect_protocols: boolean;
}

export interface ScanProgress {
  total_ips: number;
  scanned_ips: number;
  total_ports: number;
  scanned_ports: number;
  cameras_found: number;
  current_ip?: string;
  elapsed_time: number;
  estimated_remaining: number;
}

export interface ProtocolDetectionResult {
  ip: string;
  port: number;
  protocol: string;
  detected: boolean;
  response_time_ms: number;
  details: Record<string, any>;
  error_message?: string;
}

export interface ScanResult {
  ip: string;
  hostname?: string;
  is_alive: boolean;
  open_ports: number[];
  detected_protocols: ProtocolDetectionResult[];
  scan_duration_ms: number;
  scan_timestamp: string;
}

export interface NetworkDiscovery {
  scan_id: string;
  status: ScanStatus;
  progress: ScanProgress;
  results: ScanResult[];
  cameras_found: ScanResult[];
  scan_range: ScanRange;
  methods: ScanMethod[];
  start_time?: string;
  end_time?: string;
  duration_seconds: number;
}

export interface ScanFormData {
  network_range: string;
  ports: string;
  timeout: number;
  methods: ScanMethod[];
}
