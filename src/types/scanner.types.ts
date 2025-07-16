/**
 * 🎯 Scanner Types & Interfaces - Universal Camera Viewer
 * Based on Python ScanModel and related types
 * 
 * ARQUITECTURA:
 * - Estos tipos definen el contrato entre el frontend y el backend
 * - Deben coincidir con los modelos Pydantic del backend FastAPI
 * - Se utilizan en toda la cadena: UI → Service → API → Backend
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

// ============================================
// TIPOS ADICIONALES PARA UI
// ============================================

/**
 * Tipos de dispositivos detectables en la red
 * @ui Usado para mostrar iconos apropiados en la UI
 */
export enum DeviceType {
  CAMERA = "camera",
  ROUTER = "router",
  COMPUTER = "computer",
  MOBILE = "mobile",
  UNKNOWN = "unknown",
}

/**
 * Velocidad de escaneo para la UI
 * @ui Mapea a diferentes conjuntos de puertos
 */
export enum ScanSpeed {
  FAST = "fast",       // Solo puertos comunes: 80, 554, 8080, 2020, 8000
  NORMAL = "normal",   // Puertos estándar: + 443, 8081, 5000, 5543
  THOROUGH = "thorough", // Escaneo completo: 1-10000
}

/**
 * Resultado extendido para la UI con información adicional
 * @ui Extiende ScanResult con campos calculados para mostrar
 */
export interface DeviceScanResult extends ScanResult {
  /** Tipo de dispositivo detectado basado en puertos y fingerprinting */
  deviceType: DeviceType;
  
  /** Probabilidad de que sea una cámara (0-1) calculada por el backend */
  probability: number;
  
  /** Fabricante detectado por MAC o fingerprinting */
  manufacturer?: string;
  
  /** Modelo si se pudo identificar */
  model?: string;
  
  /** Estado del escaneo para este dispositivo específico */
  status: "scanning" | "completed" | "error";
  
  /** MAC address si está disponible */
  mac?: string;
}

/**
 * Configuración para el escaneo de puertos específico
 * @integration POST /api/v2/scanner/ports/{ip}
 */
export interface PortScanConfig {
  ip: string;
  categories: {
    onvif: boolean;
    rtsp: boolean;
    http: boolean;
    proprietary: boolean;
  };
  customPorts?: number[];
  timeout?: number;
}

/**
 * Resultado del escaneo de un puerto específico
 * @integration Respuesta de escaneo de puertos
 */
export interface PortScanResult {
  port: number;
  status: "open" | "closed" | "filtered" | "scanning" | "pending";
  service?: string;
  protocol?: string;
  banner?: string;
  confidence?: number;
}

/**
 * Configuración para prueba de acceso a cámara
 * @integration POST /api/v2/scanner/test-access
 */
export interface AccessTestConfig {
  ip: string;
  port: number;
  protocol: string;
  credentials: {
    username: string;
    password: string;
  };
  tryAllProtocols?: boolean;
}

/**
 * Resultado de prueba de acceso
 * @integration Respuesta de test de acceso
 */
export interface AccessTestResult {
  protocol: string;
  port: number;
  status: "testing" | "success" | "failed" | "pending";
  message?: string;
  deviceInfo?: {
    manufacturer: string;
    model: string;
    serialNumber?: string;
    firmwareVersion?: string;
  };
  capabilities?: {
    ptz?: boolean;
    audio?: boolean;
    analytics?: boolean;
    events?: boolean;
  };
  streamUrls?: {
    main?: string;
    sub?: string;
    snapshot?: string;
  };
}
