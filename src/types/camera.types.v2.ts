/**
 * Camera Types & Interfaces V2
 * Updated for 3FN database structure
 */

// === Enums ===

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

export enum AuthType {
  BASIC = "basic",
  DIGEST = "digest",
  BEARER = "bearer",
  CUSTOM = "custom",
}

// === Request Interfaces ===

export interface CredentialsRequest {
  username: string;
  password: string;
  auth_type?: AuthType;
}

export interface ProtocolConfigRequest {
  protocol_type: ProtocolType;
  port: number;
  is_enabled?: boolean;
  is_primary?: boolean;
  version?: string;
}

export interface EndpointRequest {
  type: string; // rtsp_main, snapshot, etc
  url: string;
  protocol?: ProtocolType;
  verified?: boolean;
  priority?: number;
}

export interface StreamProfileRequest {
  profile_name: string;
  stream_type?: string; // main, sub
  resolution?: string;
  fps?: number;
  bitrate?: number;
  codec?: string;
  quality?: string;
  channel?: number;
  subtype?: number;
  is_default?: boolean;
}

export interface CreateCameraRequest {
  brand: string;
  model?: string;
  display_name: string;
  ip: string;
  location?: string;
  description?: string;
  credentials: CredentialsRequest;
  protocols?: ProtocolConfigRequest[];
  endpoints?: EndpointRequest[];
  stream_profiles?: StreamProfileRequest[];
}

export interface UpdateCameraRequest {
  display_name?: string;
  location?: string;
  description?: string;
  is_active?: boolean;
  credentials?: CredentialsRequest;
  endpoints?: EndpointRequest[];
  stream_profiles?: StreamProfileRequest[];
}

export interface TestConnectionRequest {
  ip: string;
  username: string;
  password: string;
  protocol?: ProtocolType;
  port?: number;
  brand?: string;
}

// === Response Interfaces ===

export interface CredentialsResponse {
  username: string;
  auth_type: AuthType;
  is_configured: boolean;
}

export interface ProtocolResponse {
  protocol_id?: number;
  protocol_type: ProtocolType;
  port: number;
  is_enabled: boolean;
  is_primary: boolean;
  version?: string;
}

export interface EndpointResponse {
  endpoint_id?: number;
  type: string;
  url: string;
  protocol?: ProtocolType;
  is_verified: boolean;
  last_verified?: string;
  response_time_ms?: number;
  priority: number;
}

export interface StreamProfileResponse {
  profile_id?: number;
  profile_name: string;
  stream_type: string;
  resolution?: string;
  fps?: number;
  bitrate?: number;
  codec?: string;
  quality?: string;
  channel: number;
  subtype: number;
  is_default: boolean;
}

export interface CameraStatisticsResponse {
  total_connections: number;
  successful_connections: number;
  failed_connections: number;
  success_rate: number;
  total_uptime_minutes: number;
  average_fps?: number;
  average_latency_ms?: number;
  last_connection_at?: string;
  last_error_at?: string;
  last_error_message?: string;
}

export interface CameraCapabilitiesResponse {
  supported_protocols: ProtocolType[];
  has_ptz: boolean;
  has_audio: boolean;
  has_ir: boolean;
  has_motion_detection: boolean;
  max_resolution?: string;
  supported_codecs: string[];
}

export interface CameraResponse {
  // Identification
  camera_id: string;
  brand: string;
  model: string;
  display_name: string;
  
  // Connection
  ip_address: string;
  mac_address?: string;
  
  // Status
  status: ConnectionStatus;
  is_active: boolean;
  is_connected: boolean;
  is_streaming: boolean;
  
  // Hardware info
  firmware_version?: string;
  hardware_version?: string;
  serial_number?: string;
  
  // Location
  location?: string;
  description?: string;
  
  // Configuration
  credentials?: CredentialsResponse;
  protocols: ProtocolResponse[];
  endpoints: EndpointResponse[];
  stream_profiles: StreamProfileResponse[];
  
  // Capabilities
  capabilities: CameraCapabilitiesResponse;
  
  // Statistics
  statistics?: CameraStatisticsResponse;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface CameraListResponse {
  total: number;
  cameras: CameraResponse[];
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  discovered_endpoints?: EndpointResponse[];
  detected_capabilities?: CameraCapabilitiesResponse;
}

// === Utility Types ===

// For forms - simplified camera data
export interface CameraFormData {
  brand: string;
  model?: string;
  display_name: string;
  ip: string;
  location?: string;
  description?: string;
  username: string;
  password: string;
  auth_type?: AuthType;
  onvif_port?: number;
  rtsp_port?: number;
  http_port?: number;
}

// For camera grid display
export interface CameraGridItem {
  camera: CameraResponse;
  thumbnail?: string;
  streaming_url?: string;
  last_frame?: string;
  error_message?: string;
}

// For quick actions
export interface CameraQuickAction {
  camera_id: string;
  action: 'connect' | 'disconnect' | 'stream' | 'snapshot' | 'settings';
  params?: Record<string, any>;
}

// For bulk operations
export interface BulkCameraOperation {
  camera_ids: string[];
  operation: 'connect' | 'disconnect' | 'delete' | 'update';
  params?: Record<string, any>;
}

// === Helper Functions ===

export const isConnected = (camera: CameraResponse): boolean => {
  return camera.status === ConnectionStatus.CONNECTED || 
         camera.status === ConnectionStatus.STREAMING;
};

export const hasCredentials = (camera: CameraResponse): boolean => {
  return camera.credentials?.is_configured ?? false;
};

export const getPrimaryProtocol = (camera: CameraResponse): ProtocolResponse | undefined => {
  return camera.protocols.find(p => p.is_primary);
};

export const getVerifiedEndpoint = (camera: CameraResponse, type: string): EndpointResponse | undefined => {
  return camera.endpoints.find(e => e.type === type && e.is_verified);
};

export const getDefaultStreamProfile = (camera: CameraResponse): StreamProfileResponse | undefined => {
  return camera.stream_profiles.find(p => p.is_default);
};

// Default values for forms
export const DEFAULT_CAMERA_FORM: Partial<CameraFormData> = {
  brand: 'generic',
  auth_type: AuthType.BASIC,
  onvif_port: 80,
  rtsp_port: 554,
  http_port: 80,
};