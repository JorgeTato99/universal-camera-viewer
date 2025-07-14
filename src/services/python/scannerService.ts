/**
 * Servicio para operaciones de escaneo de red
 */

import { apiClient, ApiClient } from '../api/apiClient';
import { Camera } from '../../types/service.types';
import { ApiResponse } from '../../types/api.types';

export interface ScanRange {
  start_ip: string;
  end_ip: string;
  port?: number;
}

export interface ScanRequest {
  ranges: ScanRange[];
  protocols?: string[];
  timeout?: number;
  max_threads?: number;
}

export interface ScanProgress {
  scan_id: string;
  status: 'idle' | 'scanning' | 'completed' | 'cancelled' | 'error';
  progress: number;
  total_ips: number;
  scanned_ips: number;
  found_cameras: number;
  elapsed_time: number;
  estimated_time_remaining?: number;
  current_ip?: string;
}

export interface ScanResult {
  scan_id: string;
  cameras: Camera[];
  total_scanned: number;
  duration_seconds: number;
  completed_at: string;
}

export class ScannerService {
  private api: ApiClient;
  private currentScanId: string | null = null;

  constructor(api: ApiClient = apiClient) {
    this.api = api;
  }

  /**
   * Iniciar escaneo de red
   */
  async startScan(request: ScanRequest): Promise<{ scan_id: string }> {
    const response = await this.api.post<{ data: { scan_id: string } }>(
      '/scanner/scan',
      request
    );
    
    if (response.success && response.data?.data) {
      this.currentScanId = response.data.data.scan_id;
      return response.data.data;
    }
    
    throw new Error(response.error || 'Error al iniciar escaneo');
  }

  /**
   * Obtener progreso del escaneo actual
   */
  async getScanProgress(scanId?: string): Promise<ScanProgress> {
    const id = scanId || this.currentScanId;
    if (!id) {
      throw new Error('No hay escaneo activo');
    }

    const response = await this.api.get<{ data: ScanProgress }>(
      `/scanner/scan/${id}/progress`
    );
    
    if (response.success && response.data?.data) {
      return response.data.data;
    }
    
    throw new Error(response.error || 'Error al obtener progreso');
  }

  /**
   * Detener escaneo en progreso
   */
  async stopScan(scanId?: string): Promise<void> {
    const id = scanId || this.currentScanId;
    if (!id) {
      throw new Error('No hay escaneo activo');
    }

    const response = await this.api.post(`/scanner/scan/${id}/stop`);
    
    if (!response.success) {
      throw new Error(response.error || 'Error al detener escaneo');
    }

    if (id === this.currentScanId) {
      this.currentScanId = null;
    }
  }

  /**
   * Obtener resultados del escaneo
   */
  async getScanResults(scanId?: string): Promise<ScanResult> {
    const id = scanId || this.currentScanId;
    if (!id) {
      throw new Error('No hay escaneo para obtener resultados');
    }

    const response = await this.api.get<{ data: ScanResult }>(
      `/scanner/scan/${id}/results`
    );
    
    if (response.success && response.data?.data) {
      return response.data.data;
    }
    
    throw new Error(response.error || 'Error al obtener resultados');
  }

  /**
   * Escaneo rápido de una IP específica
   */
  async quickScan(ip: string, ports?: number[]): Promise<Camera[]> {
    const response = await this.api.post<{ data: { cameras: Camera[] } }>(
      '/scanner/quick-scan',
      {
        ip,
        ports: ports || [80, 554, 8000, 8080, 2020, 5543]
      }
    );
    
    if (response.success && response.data?.data) {
      return response.data.data.cameras;
    }
    
    throw new Error(response.error || 'Error en escaneo rápido');
  }

  /**
   * Detectar protocolos soportados por una cámara
   */
  async detectProtocols(ip: string, port?: number): Promise<string[]> {
    const response = await this.api.post<{ data: { protocols: string[] } }>(
      '/scanner/detect-protocols',
      { ip, port }
    );
    
    if (response.success && response.data?.data) {
      return response.data.data.protocols;
    }
    
    throw new Error(response.error || 'Error al detectar protocolos');
  }

  /**
   * Monitorear progreso del escaneo con callback
   */
  async monitorScanProgress(
    scanId: string,
    onProgress: (progress: ScanProgress) => void,
    interval: number = 1000
  ): Promise<() => void> {
    let isMonitoring = true;
    
    const monitor = async () => {
      while (isMonitoring) {
        try {
          const progress = await this.getScanProgress(scanId);
          onProgress(progress);
          
          // Detener monitoreo si el escaneo terminó
          if (['completed', 'cancelled', 'error'].includes(progress.status)) {
            isMonitoring = false;
            break;
          }
          
          await new Promise(resolve => setTimeout(resolve, interval));
        } catch (error) {
          console.error('Error monitoreando progreso:', error);
          isMonitoring = false;
        }
      }
    };
    
    // Iniciar monitoreo en background
    monitor();
    
    // Retornar función para detener monitoreo
    return () => {
      isMonitoring = false;
    };
  }

  /**
   * Obtener configuración recomendada de escaneo
   */
  async getRecommendedConfig(): Promise<ScanRequest> {
    const response = await this.api.get<{ data: ScanRequest }>(
      '/scanner/recommended-config'
    );
    
    if (response.success && response.data?.data) {
      return response.data.data;
    }
    
    // Configuración por defecto si falla
    return {
      ranges: [{ start_ip: '192.168.1.1', end_ip: '192.168.1.254' }],
      protocols: ['ONVIF', 'RTSP'],
      timeout: 3,
      max_threads: 10
    };
  }

  /**
   * Validar rango de IP
   */
  validateIPRange(startIP: string, endIP: string): boolean {
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    
    if (!ipRegex.test(startIP) || !ipRegex.test(endIP)) {
      return false;
    }
    
    const start = startIP.split('.').map(Number);
    const end = endIP.split('.').map(Number);
    
    // Verificar que cada octeto esté en rango válido
    for (let i = 0; i < 4; i++) {
      if (start[i] < 0 || start[i] > 255 || end[i] < 0 || end[i] > 255) {
        return false;
      }
    }
    
    // Verificar que end >= start
    for (let i = 0; i < 4; i++) {
      if (end[i] > start[i]) return true;
      if (end[i] < start[i]) return false;
    }
    
    return true; // IPs son iguales
  }

  /**
   * Obtener ID del escaneo actual
   */
  getCurrentScanId(): string | null {
    return this.currentScanId;
  }

  /**
   * Limpiar ID del escaneo actual
   */
  clearCurrentScan(): void {
    this.currentScanId = null;
  }
}

// Instancia singleton del servicio
export const scannerService = new ScannerService();

// Exportar instancia por defecto
export default scannerService;