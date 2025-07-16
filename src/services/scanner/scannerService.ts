/**
 * 🎯 Scanner Service - Universal Camera Viewer
 * Servicio para comunicación con el backend de escaneo
 * 
 * ARQUITECTURA:
 * - Este servicio es el punto de integración entre el frontend y el backend
 * - Maneja todas las llamadas HTTP y WebSocket relacionadas con el scanner
 * - Los componentes UI NO deben llamar directamente a la API
 * 
 * FLUJO DE DATOS:
 * 1. Componente UI → llama método del servicio
 * 2. Servicio → realiza petición HTTP/WS al backend
 * 3. Backend → procesa y retorna respuesta
 * 4. Servicio → transforma respuesta si es necesario
 * 5. Servicio → actualiza store/retorna a componente
 * 
 * @module Services/Scanner
 */

import { apiClient } from "../api/apiClient";
import {
  NetworkDiscovery,
  ScanConfig,
  ScanStatus,
  DeviceScanResult,
  PortScanConfig,
  PortScanResult,
  AccessTestConfig,
  AccessTestResult,
  ScanSpeed,
} from "../../types/scanner.types";

/**
 * Configuración del servicio
 */
const SCANNER_API_BASE = "/api/v2/scanner";
const WEBSOCKET_BASE = "ws://localhost:8000/ws/scanner";

/**
 * Scanner Service
 * 
 * IMPORTANTE: Este servicio maneja la comunicación con el backend.
 * Para integrar con el backend real:
 * 
 * 1. Asegurarse de que el backend implemente los endpoints esperados
 * 2. Configurar CORS apropiadamente en el backend
 * 3. Implementar autenticación si es necesaria
 * 4. Manejar errores de red y timeout
 */
export class ScannerService {
  private static instance: ScannerService;
  private websocket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  /**
   * Singleton pattern para asegurar una sola instancia
   */
  public static getInstance(): ScannerService {
    if (!ScannerService.instance) {
      ScannerService.instance = new ScannerService();
    }
    return ScannerService.instance;
  }

  // ============================================
  // ESCANEO DE RED
  // ============================================

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Iniciar Escaneo de Red
   * 
   * TODO: Conectar con endpoint real del backend
   * 
   * ENDPOINT ESPERADO:
   * POST /api/v2/scanner/network/start
   * 
   * REQUEST BODY:
   * {
   *   "mode": "auto" | "manual",
   *   "network_ranges": ["192.168.1.0/24"],
   *   "scan_speed": "fast" | "normal" | "thorough",
   *   "port_list": [80, 554, 8080, 2020, 8000],
   *   "timeout_seconds": 5,
   *   "parallel_scans": 50
   * }
   * 
   * RESPONSE:
   * {
   *   "scan_id": "uuid-v4",
   *   "status": "started",
   *   "estimated_time": 120,
   *   "websocket_channel": "scanner:network:uuid-v4"
   * }
   * 
   * IMPLEMENTACIÓN REAL:
   * ```typescript
   * const response = await apiClient.post(`${SCANNER_API_BASE}/network/start`, {
   *   mode: config.mode || 'auto',
   *   network_ranges: config.network_ranges || ['192.168.1.0/24'],
   *   scan_speed: config.scan_speed || 'normal',
   *   port_list: this.getPortsForSpeed(config.scan_speed),
   *   timeout_seconds: this.getTimeoutForSpeed(config.scan_speed),
   *   parallel_scans: this.getParallelScansForSpeed(config.scan_speed)
   * });
   * 
   * // Suscribirse a eventos WebSocket
   * this.subscribeToScanEvents(response.data.scan_id);
   * 
   * return response.data.scan_id;
   * ```
   * 
   * @param config Configuración del escaneo
   * @returns ID del escaneo iniciado
   */
  async startNetworkScan(config: Partial<ScanConfig>): Promise<string> {
    try {
      // 🔧 MOCK: Simulación de inicio de escaneo
      console.log("🔧 MOCK: Iniciando escaneo de red con config:", config);
      
      // TODO: Reemplazar con llamada real al API
      const mockScanId = `scan_${Date.now()}`;
      
      // Simular conexión WebSocket
      console.log(`🔧 MOCK: Conectando WebSocket para scan ${mockScanId}`);
      
      return mockScanId;
    } catch (error) {
      console.error("Error starting network scan:", error);
      throw new Error("Failed to start network scan");
    }
  }

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Detener Escaneo
   * 
   * TODO: Conectar con endpoint real
   * 
   * ENDPOINT: POST /api/v2/scanner/network/stop
   * BODY: { "scan_id": "uuid-v4" }
   * RESPONSE: { "status": "stopped", "devices_found": 12 }
   * 
   * IMPLEMENTACIÓN:
   * ```typescript
   * await apiClient.post(`${SCANNER_API_BASE}/network/stop`, { scan_id: scanId });
   * this.unsubscribeFromScanEvents(scanId);
   * ```
   */
  async stopScan(scanId: string): Promise<void> {
    try {
      // 🔧 MOCK: Simular detención de escaneo
      console.log(`🔧 MOCK: Deteniendo escaneo ${scanId}`);
      
      // TODO: Reemplazar con llamada real
      // await apiClient.post(`${SCANNER_API_BASE}/network/stop`, { scan_id: scanId });
    } catch (error) {
      console.error("Error stopping scan:", error);
      throw new Error("Failed to stop scan");
    }
  }

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Estado del Escaneo
   * 
   * TODO: Endpoint para obtener estado actual
   * 
   * ENDPOINT: GET /api/v2/scanner/network/status/{scan_id}
   * RESPONSE: NetworkDiscovery object con campos actualizados
   */
  async getScanStatus(scanId: string): Promise<NetworkDiscovery> {
    try {
      // 🔧 MOCK: Retornar estado simulado
      console.log(`🔧 MOCK: Obteniendo estado del escaneo ${scanId}`);
      
      return {
        network_info: {
          local_ip: "192.168.1.100",
          network_cidr: "192.168.1.0/24",
          gateway: "192.168.1.1",
          interface_name: "eth0"
        },
        scan_results: [],
        scan_stats: {
          total_scanned: 100,
          devices_found: 5,
          scan_duration: 45.2,
          start_time: new Date().toISOString(),
          end_time: null
        },
        status: "scanning" as ScanStatus
      };
    } catch (error) {
      console.error("Error getting scan status:", error);
      throw new Error("Failed to get scan status");
    }
  }

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Resultados del Escaneo
   * 
   * TODO: Obtener dispositivos encontrados
   * 
   * ENDPOINT: GET /api/v2/scanner/network/results/{scan_id}
   * 
   * TRANSFORMACIÓN NECESARIA:
   * Backend debe agregar campos UI:
   * - probability: Calcular basado en puertos abiertos
   * - deviceType: Inferir tipo (camera, router, computer, etc)
   * - cameraLikelihood: Porcentaje de probabilidad de ser cámara
   */
  async getScanResults(scanId: string): Promise<DeviceScanResult[]> {
    try {
      const response = await apiClient.get(`${SCANNER_API_BASE}/results/${scanId}`);
      return response.data;
    } catch (error) {
      console.error("Error getting scan results:", error);
      throw new Error("Failed to get scan results");
    }
  }

  // ============================================
  // ESCANEO DE PUERTOS
  // ============================================

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Escaneo de Puertos
   * 
   * TODO: Escanear puertos de dispositivos específicos
   * 
   * ENDPOINT: POST /api/v2/scanner/ports/start
   * BODY:
   * {
   *   "devices": [{ "ip": "192.168.1.10", "mac": "XX:XX:XX" }],
   *   "port_range": "1-65535" | "common" | "camera",
   *   "scan_speed": "fast" | "normal" | "thorough",
   *   "timeout_per_port": 2
   * }
   * 
   * RESPONSE:
   * {
   *   "scan_id": "uuid-v4",
   *   "total_operations": 120,
   *   "websocket_channel": "scanner:ports:uuid-v4"
   * }
   */
  async startPortScan(config: PortScanConfig): Promise<string> {
    try {
      // 🔧 MOCK: Simular inicio de escaneo de puertos
      console.log("🔧 MOCK: Iniciando escaneo de puertos:", config);
      
      // TODO: Implementar llamada real
      const mockScanId = `port_scan_${Date.now()}`;
      return mockScanId;
    } catch (error) {
      console.error("Error starting port scan:", error);
      throw new Error("Failed to start port scan");
    }
  }

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Resultados de Puertos
   * 
   * TODO: Obtener puertos abiertos por dispositivo
   * 
   * ENDPOINT: GET /api/v2/scanner/ports/results/{scan_id}
   * 
   * RESPONSE:
   * [
   *   {
   *     "ip": "192.168.1.10",
   *     "ports": [
   *       { "port": 80, "service": "http", "state": "open" },
   *       { "port": 554, "service": "rtsp", "state": "open" }
   *     ],
   *     "scan_time": 2.5
   *   }
   * ]
   */
  async getPortScanResults(ip: string): Promise<PortScanResult[]> {
    try {
      // 🔧 MOCK: Retornar puertos simulados
      console.log(`🔧 MOCK: Obteniendo resultados de puertos para ${ip}`);
      
      return [
        {
          ip,
          port: 80,
          protocol: "tcp",
          service: "http",
          state: "open",
          banner: "Server: Mini Web Server"
        },
        {
          ip,
          port: 554,
          protocol: "tcp",
          service: "rtsp",
          state: "open",
          banner: "RTSP/1.0 200 OK"
        }
      ];
    } catch (error) {
      console.error("Error getting port scan results:", error);
      throw new Error("Failed to get port scan results");
    }
  }

  // ============================================
  // PRUEBA DE ACCESO
  // ============================================

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Prueba de Acceso
   * 
   * TODO: Validar credenciales en dispositivos
   * 
   * ENDPOINT: POST /api/v2/scanner/access/test
   * BODY:
   * {
   *   "devices": [{ "ip": "192.168.1.10", "ports": [80, 554] }],
   *   "credentials": { "username": "admin", "password": "admin123" },
   *   "protocols": ["onvif", "rtsp", "http"],
   *   "timeout": 10
   * }
   * 
   * RESPONSE:
   * [
   *   {
   *     "ip": "192.168.1.10",
   *     "protocol": "onvif",
   *     "success": true,
   *     "message": "Acceso exitoso",
   *     "device_info": {
   *       "manufacturer": "Dahua",
   *       "model": "IPC-HFW1230S",
   *       "firmware": "2.800.0000000.20.R"
   *     }
   *   }
   * ]
   * 
   * NOTA: El backend debe probar todos los protocolos solicitados
   * y retornar resultados para cada uno
   */
  async testCameraAccess(config: AccessTestConfig): Promise<AccessTestResult[]> {
    try {
      // 🔧 MOCK: Simular prueba de acceso
      console.log("🔧 MOCK: Probando acceso con:", config);
      
      // TODO: Implementar llamada real
      return [
        {
          ip: config.ip,
          protocol: "onvif" as any,
          success: true,
          message: "Acceso exitoso (MOCK)",
          responseTime: 1.2
        }
      ];
    } catch (error) {
      console.error("Error testing camera access:", error);
      throw new Error("Failed to test camera access");
    }
  }

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - Credenciales Por Defecto
   * 
   * TODO: Obtener lista de credenciales comunes
   * 
   * ENDPOINT: GET /api/v2/scanner/credentials/defaults
   * 
   * RESPONSE:
   * [
   *   { "username": "admin", "password": "admin", "brand": "generic" },
   *   { "username": "admin", "password": "admin123", "brand": "dahua" },
   *   { "username": "admin", "password": "12345", "brand": "hikvision" }
   * ]
   * 
   * NOTA: Lista debe estar ordenada por frecuencia de uso
   */
  async getDefaultCredentials(): Promise<Array<{ username: string; password: string; brand: string }>> {
    try {
      // 🔧 MOCK: Retornar credenciales comunes
      console.log("🔧 MOCK: Obteniendo credenciales por defecto");
      
      // TODO: Reemplazar con llamada real
      // const response = await apiClient.get(`${SCANNER_API_BASE}/credentials/defaults`);
      // return response.data;
      
      return [
        { username: "admin", password: "admin", brand: "Genérico" },
        { username: "admin", password: "12345", brand: "Genérico" },
        { username: "admin", password: "123456", brand: "Genérico" },
        { username: "admin", password: "", brand: "Dahua/Hikvision" },
        { username: "admin", password: "admin123", brand: "Dahua" },
        { username: "888888", password: "888888", brand: "XMEye" },
      ];
    } catch (error) {
      console.error("Error getting default credentials:", error);
      throw new Error("Failed to get default credentials");
    }
  }

  // ============================================
  // WEBSOCKET
  // ============================================

  /**
   * 🚀 INTEGRACIÓN PENDIENTE - WebSocket para Eventos en Tiempo Real
   * 
   * TODO: Conectar con WebSocket del backend
   * 
   * ENDPOINT: ws://localhost:8000/ws/scanner/{scan_id}
   * 
   * EVENTOS ESPERADOS:
   * ```json
   * { "type": "scan:progress", "data": { "percentage": 45, "current_ip": "192.168.1.45" } }
   * { "type": "device:found", "data": { "ip": "192.168.1.10", "mac": "XX:XX", "open_ports": [80, 554] } }
   * { "type": "scan:complete", "data": { "total_devices": 12, "duration": 120.5 } }
   * { "type": "error", "data": { "code": "NETWORK_ERROR", "message": "Error de red" } }
   * ```
   * 
   * IMPLEMENTACIÓN:
   * - Usar reconexión automática con backoff exponencial
   * - Emitir eventos a componentes suscritos
   * - Manejar desconexiones gracefully
   */
  private connectWebSocket(scanId: string): void {
    if (this.websocket) {
      this.disconnectWebSocket();
    }

    try {
      this.websocket = new WebSocket(`${WEBSOCKET_BASE}/${scanId}`);
      
      this.websocket.onopen = () => {
        console.log("Scanner WebSocket connected");
        this.reconnectAttempts = 0;
      };

      this.websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      this.websocket.onerror = (error) => {
        console.error("Scanner WebSocket error:", error);
      };

      this.websocket.onclose = () => {
        console.log("Scanner WebSocket disconnected");
        this.handleWebSocketClose(scanId);
      };
    } catch (error) {
      console.error("Error connecting WebSocket:", error);
    }
  }

  /**
   * Maneja mensajes del WebSocket
   * 
   * TODO: Implementar actualización del store aquí
   */
  private handleWebSocketMessage(message: any): void {
    switch (message.type) {
      case "progress":
        // TODO: Actualizar progreso en el store
        console.log("Scan progress:", message.data);
        break;
      
      case "device_found":
        // TODO: Agregar dispositivo encontrado al store
        console.log("Device found:", message.data);
        break;
      
      case "scan_complete":
        // TODO: Marcar escaneo como completo en el store
        console.log("Scan complete:", message.data);
        this.disconnectWebSocket();
        break;
      
      case "error":
        // TODO: Manejar error en el store
        console.error("Scan error:", message.data);
        break;
    }
  }

  /**
   * Maneja desconexión del WebSocket con reintentos
   */
  private handleWebSocketClose(scanId: string): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => this.connectWebSocket(scanId), 2000 * this.reconnectAttempts);
    }
  }

  /**
   * Desconecta el WebSocket
   */
  private disconnectWebSocket(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  // ============================================
  // UTILIDADES
  // ============================================

  /**
   * Genera configuración por defecto basada en el rango de red
   */
  private getDefaultScanConfig(networkRange: string): ScanConfig {
    return {
      network_ranges: [networkRange],
      ports: [80, 554, 8080, 2020, 8000], // Puertos comunes de cámaras
      timeout: 5.0,
      max_threads: 50,
      include_onvif: true,
      include_rtsp: true,
      include_http: true,
      include_amcrest: true,
      test_authentication: false,
      auto_detect_protocols: true,
    };
  }

  /**
   * Obtiene lista de puertos basada en la configuración
   */
  private getPortsFromConfig(config: PortScanConfig): number[] {
    const ports: number[] = [];
    
    if (config.categories.onvif) {
      ports.push(80, 8080, 2020, 8000);
    }
    if (config.categories.rtsp) {
      ports.push(554, 8554, 5543, 5544);
    }
    if (config.categories.http) {
      ports.push(80, 443, 8080, 8081, 8443);
    }
    if (config.categories.proprietary) {
      ports.push(37777, 37778, 34567, 34568);
    }
    
    // Agregar puertos personalizados
    if (config.customPorts) {
      ports.push(...config.customPorts);
    }
    
    // Eliminar duplicados
    return [...new Set(ports)];
  }
}

// Exportar instancia singleton
export const scannerService = ScannerService.getInstance();