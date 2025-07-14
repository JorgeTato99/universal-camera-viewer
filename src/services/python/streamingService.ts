/**
 * Servicio para streaming de video por WebSocket
 */

import { Camera } from '../../types/camera.types';
import { StreamMetrics, StreamQuality } from '../../types/streaming.types';

export interface StreamConfig {
  quality: StreamQuality;
  fps: number;
  format: 'jpeg' | 'png' | 'webp';
}

export interface FrameData {
  type: 'frame';
  camera_id: string;
  data: string; // base64
  timestamp: string;
  frame_number: number;
  metrics?: StreamMetrics;
}

export interface StreamMessage {
  type: 'frame' | 'status' | 'error' | 'connection';
  camera_id?: string;
  status?: string;
  error?: string;
  timestamp: string;
  [key: string]: any;
}

export type StreamEventCallback = (data: FrameData) => void;
export type StatusEventCallback = (status: string, data?: any) => void;
export type ErrorEventCallback = (error: string) => void;

export class StreamingService {
  private ws: WebSocket | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  
  private cameraId: string = '';
  private wsUrl: string = 'ws://localhost:8000/ws';
  private isConnecting: boolean = false;
  private shouldReconnect: boolean = true;
  private reconnectDelay: number = 3000;
  
  // Callbacks
  private onFrameCallbacks: Set<StreamEventCallback> = new Set();
  private onStatusCallbacks: Set<StatusEventCallback> = new Set();
  private onErrorCallbacks: Set<ErrorEventCallback> = new Set();
  
  // Métricas
  private frameCount: number = 0;
  private lastFrameTime: number = 0;
  private connectionStartTime: number = 0;

  constructor(wsUrl?: string) {
    if (wsUrl) {
      this.wsUrl = wsUrl;
    }
  }

  /**
   * Conectar al WebSocket de streaming
   */
  async connect(cameraId: string): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      console.warn('Ya existe una conexión activa o en proceso');
      return;
    }

    this.cameraId = cameraId;
    this.isConnecting = true;
    this.shouldReconnect = true;
    this.frameCount = 0;

    return new Promise((resolve, reject) => {
      try {
        const url = `${this.wsUrl}/stream/${cameraId}`;
        console.log(`Conectando a WebSocket: ${url}`);
        
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
          console.log('WebSocket conectado');
          this.isConnecting = false;
          this.connectionStartTime = Date.now();
          this.startHeartbeat();
          this.emitStatus('connected');
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };
        
        this.ws.onerror = (error) => {
          console.error('Error en WebSocket:', error);
          this.isConnecting = false;
          this.emitError('Error de conexión WebSocket');
          reject(new Error('Error de conexión WebSocket'));
        };
        
        this.ws.onclose = (event) => {
          console.log('WebSocket cerrado:', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          this.emitStatus('disconnected');
          
          if (this.shouldReconnect && event.code !== 1000) {
            this.scheduleReconnect();
          }
        };
        
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Desconectar del WebSocket
   */
  disconnect(): void {
    this.shouldReconnect = false;
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.stopHeartbeat();
    
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close(1000, 'Desconexión solicitada');
      }
      this.ws = null;
    }
    
    this.emitStatus('disconnected');
  }

  /**
   * Iniciar streaming
   */
  async startStream(config?: Partial<StreamConfig>): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket no conectado');
    }

    const defaultConfig: StreamConfig = {
      quality: 'medium',
      fps: 30,
      format: 'jpeg'
    };

    const finalConfig = { ...defaultConfig, ...config };

    this.send({
      action: 'start_stream',
      params: finalConfig
    });
  }

  /**
   * Detener streaming
   */
  async stopStream(): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket no conectado');
    }

    this.send({
      action: 'stop_stream'
    });
  }

  /**
   * Actualizar calidad del stream
   */
  async updateQuality(quality: StreamQuality): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket no conectado');
    }

    this.send({
      action: 'update_quality',
      params: { quality }
    });
  }

  /**
   * Actualizar FPS del stream
   */
  async updateFPS(fps: number): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket no conectado');
    }

    if (fps < 1 || fps > 60) {
      throw new Error('FPS debe estar entre 1 y 60');
    }

    this.send({
      action: 'update_fps',
      params: { fps }
    });
  }

  /**
   * Enviar mensaje al WebSocket
   */
  private send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  /**
   * Manejar mensajes recibidos
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: StreamMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'frame':
          this.handleFrame(message as FrameData);
          break;
          
        case 'status':
          this.emitStatus(message.status || 'unknown', message);
          break;
          
        case 'error':
          this.emitError(message.error || 'Error desconocido');
          break;
          
        case 'connection':
          console.log('Mensaje de conexión:', message);
          break;
          
        default:
          console.warn('Tipo de mensaje desconocido:', message.type);
      }
    } catch (error) {
      console.error('Error procesando mensaje:', error);
    }
  }

  /**
   * Manejar frame recibido
   */
  private handleFrame(frameData: FrameData): void {
    this.frameCount++;
    this.lastFrameTime = Date.now();
    
    // Emitir a todos los callbacks registrados
    this.onFrameCallbacks.forEach(callback => {
      try {
        callback(frameData);
      } catch (error) {
        console.error('Error en callback de frame:', error);
      }
    });
  }

  /**
   * Programar reconexión
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    
    console.log(`Reconectando en ${this.reconnectDelay}ms...`);
    this.emitStatus('reconnecting');
    
    this.reconnectTimeout = setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect(this.cameraId).catch(error => {
          console.error('Error al reconectar:', error);
        });
      }
    }, this.reconnectDelay);
  }

  /**
   * Iniciar heartbeat
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000); // 30 segundos
  }

  /**
   * Detener heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Emitir estado
   */
  private emitStatus(status: string, data?: any): void {
    this.onStatusCallbacks.forEach(callback => {
      try {
        callback(status, data);
      } catch (error) {
        console.error('Error en callback de estado:', error);
      }
    });
  }

  /**
   * Emitir error
   */
  private emitError(error: string): void {
    this.onErrorCallbacks.forEach(callback => {
      try {
        callback(error);
      } catch (error) {
        console.error('Error en callback de error:', error);
      }
    });
  }

  /**
   * Registrar callback para frames
   */
  onFrame(callback: StreamEventCallback): () => void {
    this.onFrameCallbacks.add(callback);
    
    // Retornar función para desregistrar
    return () => {
      this.onFrameCallbacks.delete(callback);
    };
  }

  /**
   * Registrar callback para estados
   */
  onStatus(callback: StatusEventCallback): () => void {
    this.onStatusCallbacks.add(callback);
    
    return () => {
      this.onStatusCallbacks.delete(callback);
    };
  }

  /**
   * Registrar callback para errores
   */
  onError(callback: ErrorEventCallback): () => void {
    this.onErrorCallbacks.add(callback);
    
    return () => {
      this.onErrorCallbacks.delete(callback);
    };
  }

  /**
   * Obtener estado de conexión
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Obtener métricas actuales
   */
  getMetrics(): {
    frameCount: number;
    connectionTime: number;
    fps: number;
  } {
    const now = Date.now();
    const connectionTime = this.connectionStartTime ? 
      (now - this.connectionStartTime) / 1000 : 0;
    
    const fps = connectionTime > 0 ? 
      this.frameCount / connectionTime : 0;
    
    return {
      frameCount: this.frameCount,
      connectionTime: Math.round(connectionTime),
      fps: Math.round(fps * 10) / 10
    };
  }

  /**
   * Configurar URL del WebSocket
   */
  setWebSocketUrl(url: string): void {
    this.wsUrl = url;
  }

  /**
   * Configurar delay de reconexión
   */
  setReconnectDelay(delay: number): void {
    this.reconnectDelay = Math.max(1000, delay);
  }
}

// Instancia singleton del servicio
export const streamingService = new StreamingService();

// Exportar instancia por defecto
export default streamingService;