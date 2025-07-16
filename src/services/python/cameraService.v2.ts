/**
 * Camera Service V2
 * Updated for 3FN database structure
 */

import { apiClient, ApiClient } from '../api/apiClient';
import { ApiResponse } from '../../types/api.types';
import {
  CameraResponse,
  CameraListResponse,
  CreateCameraRequest,
  UpdateCameraRequest,
  TestConnectionRequest,
  TestConnectionResponse,
  EndpointRequest,
  CameraFormData,
  AuthType,
  ProtocolType,
} from '../../types/camera.types.v2';

export class CameraServiceV2 {
  private api: ApiClient;
  private baseUrl = '/v2/cameras';

  constructor(api: ApiClient = apiClient) {
    this.api = api;
  }

  /**
   * List all cameras with full configuration
   */
  async listCameras(activeOnly = true, protocol?: ProtocolType): Promise<CameraResponse[]> {
    const params = new URLSearchParams();
    params.append('active_only', activeOnly.toString());
    if (protocol) {
      params.append('protocol', protocol);
    }

    console.log('Fetching cameras from:', `${this.baseUrl}?${params.toString()}`);
    
    try {
      const response = await this.api.get<CameraListResponse>(
        `${this.baseUrl}?${params.toString()}`
      );

      console.log('Raw response:', response);

      // La respuesta siempre viene envuelta en ApiResponse
      if (response.success && response.data) {
        console.log('ApiResponse data:', response.data);
        // response.data es el CameraListResponse serializado
        return response.data.cameras || [];
      }

      // Si hay error
      if (!response.success) {
        console.error('API returned error:', response.error);
        throw new Error(response.error || 'Error fetching cameras');
      }

      // Caso por defecto - array vacío
      console.warn('Unexpected response format:', response);
      return [];
      
    } catch (error) {
      console.error('Error fetching cameras:', error);
      throw new Error('Error fetching cameras');
    }
  }

  /**
   * Get detailed camera information
   */
  async getCamera(cameraId: string): Promise<CameraResponse> {
    const response = await this.api.get<CameraResponse>(
      `${this.baseUrl}/${cameraId}`
    );

    if (response.success && response.data) {
      return response.data;
    }

    throw new Error(response.error || 'Camera not found');
  }

  /**
   * Create a new camera
   */
  async createCamera(data: CameraFormData): Promise<CameraResponse> {
    // Build request from form data
    const request: CreateCameraRequest = {
      brand: data.brand,
      model: data.model,
      display_name: data.display_name,
      ip: data.ip,
      location: data.location,
      description: data.description,
      credentials: {
        username: data.username,
        password: data.password,
        auth_type: data.auth_type || AuthType.BASIC,
      },
      protocols: [],
    };

    // Add protocol configurations if ports are provided
    if (data.onvif_port) {
      request.protocols?.push({
        protocol_type: ProtocolType.ONVIF,
        port: data.onvif_port,
        is_enabled: true,
        is_primary: true,
      });
    }

    if (data.rtsp_port) {
      request.protocols?.push({
        protocol_type: ProtocolType.RTSP,
        port: data.rtsp_port,
        is_enabled: true,
        is_primary: !data.onvif_port,
      });
    }

    if (data.http_port) {
      request.protocols?.push({
        protocol_type: ProtocolType.HTTP,
        port: data.http_port,
        is_enabled: true,
        is_primary: !data.onvif_port && !data.rtsp_port,
      });
    }

    const response = await this.api.post<CameraResponse>(this.baseUrl, request);

    if (response.success && response.data) {
      return response.data;
    }

    throw new Error(response.error || 'Error creating camera');
  }

  /**
   * Update camera configuration
   */
  async updateCamera(
    cameraId: string,
    updates: UpdateCameraRequest
  ): Promise<CameraResponse> {
    const response = await this.api.put<CameraResponse>(
      `${this.baseUrl}/${cameraId}`,
      updates
    );

    if (response.success && response.data) {
      return response.data;
    }

    throw new Error(response.error || 'Error updating camera');
  }

  /**
   * Delete a camera
   */
  async deleteCamera(cameraId: string): Promise<void> {
    const response = await this.api.delete(`${this.baseUrl}/${cameraId}`);

    if (!response.success) {
      throw new Error(response.error || 'Error deleting camera');
    }
  }

  /**
   * Connect to a camera
   */
  async connectCamera(cameraId: string): Promise<ApiResponse> {
    const response = await this.api.post(`${this.baseUrl}/${cameraId}/connect`);

    if (!response.success) {
      throw new Error(response.error || 'Error connecting to camera');
    }

    return response;
  }

  /**
   * Disconnect from a camera
   */
  async disconnectCamera(cameraId: string): Promise<ApiResponse> {
    const response = await this.api.post(`${this.baseUrl}/${cameraId}/disconnect`);

    if (!response.success) {
      throw new Error(response.error || 'Error disconnecting camera');
    }

    return response;
  }

  /**
   * Test connection without saving
   */
  async testConnection(
    data: TestConnectionRequest
  ): Promise<TestConnectionResponse> {
    const response = await this.api.post<TestConnectionResponse>(
      `${this.baseUrl}/test-connection`,
      data
    );

    if (response.success && response.data) {
      return response.data;
    }

    throw new Error(response.error || 'Error testing connection');
  }

  /**
   * Get camera statistics
   */
  async getCameraStatistics(cameraId: string): Promise<ApiResponse> {
    return this.api.get(`${this.baseUrl}/${cameraId}/statistics`);
  }

  /**
   * Add discovered endpoint to camera
   */
  async addCameraEndpoint(
    cameraId: string,
    endpoint: EndpointRequest
  ): Promise<ApiResponse> {
    const response = await this.api.post(
      `${this.baseUrl}/${cameraId}/endpoints`,
      endpoint
    );

    if (!response.success) {
      throw new Error(response.error || 'Error adding endpoint');
    }

    return response;
  }

  /**
   * Update camera credentials
   */
  async updateCredentials(
    cameraId: string,
    username: string,
    password: string,
    authType: AuthType = AuthType.BASIC
  ): Promise<CameraResponse> {
    const updates: UpdateCameraRequest = {
      credentials: {
        username,
        password,
        auth_type: authType,
      },
    };

    return this.updateCamera(cameraId, updates);
  }

  /**
   * Update camera location info
   */
  async updateLocationInfo(
    cameraId: string,
    location?: string,
    description?: string
  ): Promise<CameraResponse> {
    const updates: UpdateCameraRequest = {
      location,
      description,
    };

    return this.updateCamera(cameraId, updates);
  }

  /**
   * Toggle camera active status
   */
  async toggleCameraActive(
    cameraId: string,
    isActive: boolean
  ): Promise<CameraResponse> {
    const updates: UpdateCameraRequest = {
      is_active: isActive,
    };

    return this.updateCamera(cameraId, updates);
  }

  /**
   * Batch connect multiple cameras
   */
  async batchConnect(cameraIds: string[]): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};

    // Use Promise.allSettled to handle partial failures
    const promises = cameraIds.map(async (cameraId) => {
      try {
        await this.connectCamera(cameraId);
        results[cameraId] = true;
      } catch (error) {
        results[cameraId] = false;
      }
    });

    await Promise.allSettled(promises);
    return results;
  }

  /**
   * Batch disconnect multiple cameras
   */
  async batchDisconnect(cameraIds: string[]): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};

    const promises = cameraIds.map(async (cameraId) => {
      try {
        await this.disconnectCamera(cameraId);
        results[cameraId] = true;
      } catch (error) {
        results[cameraId] = false;
      }
    });

    await Promise.allSettled(promises);
    return results;
  }

  /**
   * Search cameras by criteria
   */
  async searchCameras(criteria: {
    brand?: string;
    location?: string;
    isConnected?: boolean;
    hasCredentials?: boolean;
  }): Promise<CameraResponse[]> {
    // Get all cameras first
    const cameras = await this.listCameras();

    // Filter based on criteria
    return cameras.filter((camera) => {
      if (criteria.brand && camera.brand !== criteria.brand) {
        return false;
      }

      if (criteria.location && !camera.location?.includes(criteria.location)) {
        return false;
      }

      if (
        criteria.isConnected !== undefined &&
        camera.is_connected !== criteria.isConnected
      ) {
        return false;
      }

      if (
        criteria.hasCredentials !== undefined &&
        camera.credentials?.is_configured !== criteria.hasCredentials
      ) {
        return false;
      }

      return true;
    });
  }

  /**
   * Export camera configuration
   */
  async exportCameraConfig(cameraId: string): Promise<object> {
    const camera = await this.getCamera(cameraId);

    // Remove sensitive data
    const exportData = {
      brand: camera.brand,
      model: camera.model,
      display_name: camera.display_name,
      ip_address: camera.ip_address,
      location: camera.location,
      description: camera.description,
      protocols: camera.protocols,
      endpoints: camera.endpoints.filter((e) => e.is_verified),
      stream_profiles: camera.stream_profiles,
      capabilities: camera.capabilities,
    };

    return exportData;
  }

  /**
   * Import camera configuration
   */
  async importCameraConfig(
    config: any,
    credentials: { username: string; password: string }
  ): Promise<CameraResponse> {
    const request: CreateCameraRequest = {
      brand: config.brand,
      model: config.model,
      display_name: config.display_name,
      ip: config.ip_address,
      location: config.location,
      description: config.description,
      credentials: {
        username: credentials.username,
        password: credentials.password,
      },
      protocols: config.protocols,
      endpoints: config.endpoints,
      stream_profiles: config.stream_profiles,
    };

    return this.createCamera({
      ...request,
      username: credentials.username,
      password: credentials.password,
    } as CameraFormData);
  }
}

// Export singleton instance
export const cameraServiceV2 = new CameraServiceV2();