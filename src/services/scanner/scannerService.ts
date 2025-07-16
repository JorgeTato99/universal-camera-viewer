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
   * Inicia un escaneo de red
   * 
   * @integration
   * Endpoint: POST /api/v2/scanner/start
   * Body: ScanConfig
   * Response: { scan_id: string, status: string }
   * 
   * @param config Configuración del escaneo
   * @returns ID del escaneo iniciado
   */
  async startNetworkScan(config: Partial<ScanConfig>): Promise<string> {
    try {
      // Configuración por defecto basada en la velocidad
      const defaultConfig = this.getDefaultScanConfig(config.network_ranges?.[0] || "192.168.1.0/24");
      const finalConfig = { ...defaultConfig, ...config };

      const response = await apiClient.post(`${SCANNER_API_BASE}/start`, finalConfig);
      
      // Conectar WebSocket para recibir actualizaciones
      const scanId = response.data.scan_id;
      this.connectWebSocket(scanId);
      
      return scanId;
    } catch (error) {
      console.error("Error starting network scan:", error);
      throw new Error("Failed to start network scan");
    }
  }

  /**
   * Detiene el escaneo actual
   * 
   * @integration
   * Endpoint: POST /api/v2/scanner/stop/{scan_id}
   * Response: { status: "cancelled" }
   */
  async stopScan(scanId: string): Promise<void> {
    try {
      await apiClient.post(`${SCANNER_API_BASE}/stop/${scanId}`);
      this.disconnectWebSocket();
    } catch (error) {
      console.error("Error stopping scan:", error);
      throw new Error("Failed to stop scan");
    }
  }

  /**
   * Obtiene el estado actual del escaneo
   * 
   * @integration
   * Endpoint: GET /api/v2/scanner/status/{scan_id}
   * Response: NetworkDiscovery
   */
  async getScanStatus(scanId: string): Promise<NetworkDiscovery> {
    try {
      const response = await apiClient.get(`${SCANNER_API_BASE}/status/${scanId}`);
      return response.data;
    } catch (error) {
      console.error("Error getting scan status:", error);
      throw new Error("Failed to get scan status");
    }
  }

  /**
   * Obtiene los resultados del escaneo
   * 
   * @integration
   * Endpoint: GET /api/v2/scanner/results/{scan_id}
   * Response: DeviceScanResult[]
   * 
   * NOTA: El backend debe transformar ScanResult a DeviceScanResult
   * agregando los campos probability, deviceType, etc.
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
   * Inicia escaneo de puertos para una IP específica
   * 
   * @integration
   * Endpoint: POST /api/v2/scanner/ports/{ip}
   * Body: PortScanConfig
   * Response: { scan_id: string }
   */
  async startPortScan(config: PortScanConfig): Promise<string> {
    try {
      const ports = this.getPortsFromConfig(config);
      const response = await apiClient.post(
        `${SCANNER_API_BASE}/ports/${config.ip}`,
        {
          ports,
          timeout: config.timeout || 5,
        }
      );
      return response.data.scan_id;
    } catch (error) {
      console.error("Error starting port scan:", error);
      throw new Error("Failed to start port scan");
    }
  }

  /**
   * Obtiene resultados del escaneo de puertos
   * 
   * @integration
   * Endpoint: GET /api/v2/scanner/ports/{ip}/results
   * Response: PortScanResult[]
   */
  async getPortScanResults(ip: string): Promise<PortScanResult[]> {
    try {
      const response = await apiClient.get(`${SCANNER_API_BASE}/ports/${ip}/results`);
      return response.data;
    } catch (error) {
      console.error("Error getting port scan results:", error);
      throw new Error("Failed to get port scan results");
    }
  }

  // ============================================
  // PRUEBA DE ACCESO
  // ============================================

  /**
   * Prueba acceso a una cámara con credenciales
   * 
   * @integration
   * Endpoint: POST /api/v2/scanner/test-access
   * Body: AccessTestConfig
   * Response: AccessTestResult[]
   * 
   * NOTA: Si tryAllProtocols es true, el backend debe probar
   * ONVIF, RTSP y HTTP en paralelo y retornar todos los resultados
   */
  async testCameraAccess(config: AccessTestConfig): Promise<AccessTestResult[]> {
    try {
      const response = await apiClient.post(`${SCANNER_API_BASE}/test-access`, config);
      return Array.isArray(response.data) ? response.data : [response.data];
    } catch (error) {
      console.error("Error testing camera access:", error);
      throw new Error("Failed to test camera access");
    }
  }

  /**
   * Obtiene credenciales comunes para pruebas
   * 
   * @integration
   * Endpoint: GET /api/v2/scanner/default-credentials
   * Response: Array<{ username: string, password: string, brand: string }>
   */
  async getDefaultCredentials(): Promise<Array<{ username: string; password: string; brand: string }>> {
    try {
      const response = await apiClient.get(`${SCANNER_API_BASE}/default-credentials`);
      return response.data;
    } catch (error) {
      console.error("Error getting default credentials:", error);
      // Retornar credenciales por defecto si falla
      return [
        { username: "admin", password: "admin", brand: "Genérico" },
        { username: "admin", password: "12345", brand: "Genérico" },
        { username: "admin", password: "123456", brand: "Genérico" },
        { username: "admin", password: "", brand: "Dahua/Hikvision" },
      ];
    }
  }

  // ============================================
  // WEBSOCKET
  // ============================================

  /**
   * Conecta WebSocket para recibir actualizaciones en tiempo real
   * 
   * @integration
   * WebSocket: ws://localhost:8000/ws/scanner/{scan_id}
   * 
   * Mensajes esperados:
   * - { type: "progress", data: ScanProgress }
   * - { type: "device_found", data: DeviceScanResult }
   * - { type: "scan_complete", data: NetworkDiscovery }
   * - { type: "error", data: { message: string } }
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