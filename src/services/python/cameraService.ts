/**
 * Servicio para operaciones de cámaras
 */

import { apiClient, ApiClient } from '../api/apiClient';
import { ConnectionStatus } from '../../types/camera.types';
import { 
  ConnectionConfig, 
  CameraInfo,
  Camera 
} from '../../types/service.types';
import { ApiResponse } from '../../types/api.types';

export interface ConnectCameraRequest {
  camera_id: string;
  connection_config: ConnectionConfig;
}

export interface CameraSnapshot {
  camera_id: string;
  timestamp: string;
  image_data: string;
  format: string;
  size_bytes: number;
}

export interface StreamStatus {
  camera_id: string;
  is_streaming: boolean;
  status: string;
  metrics?: {
    fps: number;
    resolution: string | null;
    bitrate_kbps: number;
    latency_ms: number;
  };
}

export class CameraService {
  private api: ApiClient;

  constructor(api: ApiClient = apiClient) {
    this.api = api;
  }

  /**
   * Listar todas las cámaras
   */
  async listCameras(): Promise<Camera[]> {
    const response = await this.api.get<Camera[]>('/cameras');
    
    if (response.success && response.data) {
      // Convertir a objetos Camera con tipos correctos
      return response.data.map(cam => ({
        ...cam,
        is_connected: Boolean(cam.is_connected),
        is_streaming: Boolean(cam.is_streaming),
        capabilities: cam.capabilities || [],
        last_updated: cam.last_updated || new Date().toISOString()
      }));
    }
    
    throw new Error(response.error || 'Error al obtener cámaras');
  }

  /**
   * Obtener información de una cámara específica
   */
  async getCameraInfo(cameraId: string): Promise<Camera> {
    const response = await this.api.get<Camera>(`/cameras/${cameraId}`);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Cámara no encontrada');
  }

  /**
   * Conectar a una cámara
   */
  async connectCamera(
    cameraId: string, 
    config: ConnectionConfig
  ): Promise<ApiResponse> {
    const request: ConnectCameraRequest = {
      camera_id: cameraId,
      connection_config: config
    };
    
    const response = await this.api.post('/cameras/connect', request);
    
    if (!response.success) {
      throw new Error(response.error || 'Error al conectar cámara');
    }
    
    return response;
  }

  /**
   * Desconectar una cámara
   */
  async disconnectCamera(cameraId: string): Promise<ApiResponse> {
    const response = await this.api.delete(`/cameras/${cameraId}/disconnect`);
    
    if (!response.success) {
      throw new Error(response.error || 'Error al desconectar cámara');
    }
    
    return response;
  }

  /**
   * Capturar snapshot de una cámara
   */
  async captureSnapshot(cameraId: string): Promise<CameraSnapshot> {
    const response = await this.api.post<{ data: CameraSnapshot }>(
      `/cameras/${cameraId}/snapshot`
    );
    
    if (response.success && response.data?.data) {
      return response.data.data;
    }
    
    throw new Error(response.error || 'Error al capturar snapshot');
  }

  /**
   * Obtener estado del stream
   */
  async getStreamStatus(cameraId: string): Promise<StreamStatus> {
    const response = await this.api.get<{ data: StreamStatus }>(
      `/cameras/${cameraId}/stream/status`
    );
    
    if (response.success && response.data?.data) {
      return response.data.data;
    }
    
    throw new Error(response.error || 'Error al obtener estado del stream');
  }

  /**
   * Conectar múltiples cámaras
   */
  async connectMultipleCameras(
    cameras: Array<{ cameraId: string; config: ConnectionConfig }>
  ): Promise<Array<{ cameraId: string; success: boolean; error?: string }>> {
    const results = await Promise.allSettled(
      cameras.map(({ cameraId, config }) => 
        this.connectCamera(cameraId, config)
          .then(() => ({ cameraId, success: true }))
          .catch(error => ({ cameraId, success: false, error: error.message }))
      )
    );
    
    return results.map(result => 
      result.status === 'fulfilled' ? result.value : { 
        cameraId: 'unknown', 
        success: false, 
        error: 'Promise rejected' 
      }
    );
  }

  /**
   * Desconectar todas las cámaras
   */
  async disconnectAllCameras(): Promise<void> {
    const cameras = await this.listCameras();
    const connectedCameras = cameras.filter(cam => cam.is_connected);
    
    await Promise.allSettled(
      connectedCameras.map(cam => this.disconnectCamera(cam.camera_id))
    );
  }

  /**
   * Buscar cámaras por criterios
   */
  async searchCameras(criteria: {
    brand?: string;
    status?: ConnectionStatus;
    isConnected?: boolean;
    isStreaming?: boolean;
  }): Promise<Camera[]> {
    const cameras = await this.listCameras();
    
    return cameras.filter(camera => {
      if (criteria.brand && camera.brand !== criteria.brand) return false;
      if (criteria.status && camera.status !== criteria.status) return false;
      if (criteria.isConnected !== undefined && camera.is_connected !== criteria.isConnected) return false;
      if (criteria.isStreaming !== undefined && camera.is_streaming !== criteria.isStreaming) return false;
      return true;
    });
  }
}

// Instancia singleton del servicio
export const cameraService = new CameraService();

// Exportar instancia por defecto
export default cameraService;