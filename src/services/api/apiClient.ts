/**
 * Cliente API base para comunicación con el backend FastAPI
 */

import { ApiResponse } from '../../types/api.types';

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: any
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

export interface RequestConfig extends RequestInit {
  params?: Record<string, any>;
  timeout?: number;
}

export class ApiClient {
  private baseURL: string;
  private defaultHeaders: HeadersInit;
  private timeout: number;

  constructor(
    baseURL: string = 'http://localhost:8000/api',
    timeout: number = 30000
  ) {
    this.baseURL = baseURL;
    this.timeout = timeout;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  /**
   * Construir URL completa con parámetros de consulta
   */
  private buildURL(endpoint: string, params?: Record<string, any>): string {
    // Asegurar que los endpoints terminen con / para evitar redirecciones
    const normalizedEndpoint = endpoint.endsWith('/') ? endpoint : `${endpoint}/`;
    const url = new URL(`${this.baseURL}${normalizedEndpoint}`);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    
    return url.toString();
  }

  /**
   * Ejecutar request con timeout
   */
  private async fetchWithTimeout(
    url: string,
    config: RequestInit,
    timeout: number
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });
      return response;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Método genérico para realizar requests
   */
  private async request<T>(
    method: string,
    endpoint: string,
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    const { params, timeout = this.timeout, ...fetchConfig } = config || {};
    
    const url = this.buildURL(endpoint, params);
    
    const requestConfig: RequestInit = {
      method,
      headers: {
        ...this.defaultHeaders,
        ...(fetchConfig.headers || {}),
      },
      ...fetchConfig,
    };

    try {
      const response = await this.fetchWithTimeout(url, requestConfig, timeout);
      
      // Manejar respuestas no OK
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new ApiError(response.status, response.statusText, errorData);
      }
      
      // Parsear respuesta JSON
      const data = await response.json();
      
      // Las respuestas de nuestra API siempre tienen el formato ApiResponse
      return data as ApiResponse<T>;
      
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new ApiError(408, 'Request Timeout', { message: 'La solicitud tardó demasiado tiempo' });
        }
        throw new ApiError(0, 'Network Error', { message: error.message });
      }
      
      throw new ApiError(0, 'Unknown Error', { message: 'Error desconocido' });
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    return this.request<T>('GET', endpoint, { params });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>('POST', endpoint, {
      ...config,
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', endpoint, {
      ...config,
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', endpoint, { params });
  }

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>('PATCH', endpoint, {
      ...config,
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * Configurar headers personalizados
   */
  setHeader(key: string, value: string): void {
    this.defaultHeaders = {
      ...this.defaultHeaders,
      [key]: value,
    };
  }

  /**
   * Eliminar header
   */
  removeHeader(key: string): void {
    const headers = { ...this.defaultHeaders };
    delete headers[key];
    this.defaultHeaders = headers;
  }

  /**
   * Obtener URL base actual
   */
  getBaseURL(): string {
    return this.baseURL;
  }

  /**
   * Cambiar URL base
   */
  setBaseURL(url: string): void {
    this.baseURL = url;
  }
}

// Instancia singleton del cliente API
export const apiClient = new ApiClient();

// Exportar instancia por defecto
export default apiClient;