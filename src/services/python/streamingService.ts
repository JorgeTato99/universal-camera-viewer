/**
 * Servicio para streaming de video por WebSocket
 */

import { StreamMetrics } from '../../types/streaming.types';
import { StreamQuality, Camera } from '../../types/service.types';

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
  capture_timestamp: string; // ISO timestamp de cuando se capturó el frame
  frame_number: number;
  metrics?: StreamMetrics;
}

export interface StreamMessage {
  type: 'frame' | 'status' | 'error' | 'connection' | 'pong';
  camera_id?: string;
  status?: string;
  error?: string;
  timestamp: string;
  ping_id?: string;
  [key: string]: any;
}

export type StreamEventCallback = (data: FrameData) => void;
export type StatusEventCallback = (status: string, data?: any) => void;
export type ErrorEventCallback = (error: string) => void;
export type RTTUpdateCallback = (rtt: number) => void;

export class StreamingService {
  // Múltiples conexiones WebSocket - una por cámara
  private connections: Map<string, {
    ws: WebSocket;
    heartbeatInterval: NodeJS.Timeout | null;  // Ya no se usa, pero mantenido por compatibilidad
    reconnectTimeout: NodeJS.Timeout | null;
    isConnecting: boolean;
    shouldReconnect: boolean;
    frameCount: number;
    lastFrameTime: number;
    connectionStartTime: number;
    recentFrameTimes: number[];
    // Latency tracking (antes era RTT)
    recentRTTs: number[];  // Ahora almacena latencias
    averageRTT: number;    // Promedio de latencias
    lastRTT: number;       // Última latencia
  }> = new Map();
  
  private wsUrl: string = 'ws://localhost:8000/ws';
  private reconnectDelay: number = 3000;
  
  // Callbacks por cámara
  private onFrameCallbacks: Map<string, Set<StreamEventCallback>> = new Map();
  private onStatusCallbacks: Map<string, Set<StatusEventCallback>> = new Map();
  private onErrorCallbacks: Map<string, Set<ErrorEventCallback>> = new Map();
  private onRTTCallbacks: Map<string, Set<RTTUpdateCallback>> = new Map();
  
  // Para cálculo de FPS más preciso (ventana deslizante)
  private fpsWindowSize: number = 30; // Calcular FPS sobre los últimos 30 frames
  
  // Para cálculo de latencia (ventana deslizante) - antes era RTT
  private rttWindowSize: number = 10; // Mantener últimas 10 mediciones de latencia
  private pingInterval: number = 5000; // @deprecated - Ya no se usa

  constructor(wsUrl?: string) {
    if (wsUrl) {
      this.wsUrl = wsUrl;
    }
  }

  /**
   * Conectar al WebSocket de streaming
   */
  async connect(cameraId: string): Promise<void> {
    // Si ya hay una conexión activa para esta cámara, desconectar primero
    const existing = this.connections.get(cameraId);
    if (existing) {
      if (existing.ws.readyState === WebSocket.OPEN) {
        console.log(`Conexión existente encontrada para cámara ${cameraId}, reconectando...`);
        // Desconectar la conexión existente
        this.disconnect(cameraId);
        // Esperar un poco antes de reconectar
        await new Promise(resolve => setTimeout(resolve, 100));
      } else if (existing.ws.readyState === WebSocket.CONNECTING) {
        // Si está conectando, cerrar y reintentar
        existing.ws.close();
        this.connections.delete(cameraId);
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }
    
    // Si hay una conexión en proceso, esperar
    if (existing && existing.isConnecting) {
      console.log(`Conexión en proceso para cámara ${cameraId}, esperando...`);
      return new Promise((resolve, reject) => {
        const checkInterval = setInterval(() => {
          const conn = this.connections.get(cameraId);
          if (!conn || !conn.isConnecting) {
            clearInterval(checkInterval);
            if (conn && conn.ws.readyState === WebSocket.OPEN) {
              resolve();
            } else {
              reject(new Error('Conexión falló'));
            }
          }
        }, 100);
        
        // Timeout después de 5 segundos
        setTimeout(() => {
          clearInterval(checkInterval);
          reject(new Error('Timeout esperando conexión'));
        }, 5000);
      });
    }
    
    // Crear nueva conexión para esta cámara
    const connection = {
      ws: null as any,
      heartbeatInterval: null,
      reconnectTimeout: null,
      isConnecting: true,
      shouldReconnect: true,
      frameCount: 0,
      lastFrameTime: 0,
      connectionStartTime: 0,
      recentFrameTimes: [] as number[],
      // Latency tracking (reutilizamos variables RTT para compatibilidad)
      recentRTTs: [] as number[],  // Ahora almacena latencias calculadas
      averageRTT: 0,  // Promedio de latencias
      lastRTT: 0  // Última latencia calculada
    };
    
    this.connections.set(cameraId, connection);

    return new Promise((resolve, reject) => {
      try {
        const url = `${this.wsUrl}/stream/${cameraId}`;
        console.log(`Conectando a WebSocket para cámara ${cameraId}: ${url}`);
        
        const ws = new WebSocket(url);
        connection.ws = ws;
        
        ws.onopen = () => {
          console.log(`WebSocket conectado para cámara ${cameraId}`);
          connection.isConnecting = false;
          connection.connectionStartTime = Date.now();
          this.startHeartbeat(cameraId);
          this.emitStatus(cameraId, 'connected');
          resolve();
        };
        
        ws.onmessage = (event) => {
          this.handleMessage(cameraId, event);
        };
        
        ws.onerror = (error) => {
          console.error(`Error en WebSocket para cámara ${cameraId}:`, error);
          connection.isConnecting = false;
          this.emitError(cameraId, 'Error de conexión WebSocket');
          reject(new Error('Error de conexión WebSocket'));
        };
        
        ws.onclose = (event) => {
          console.log(`WebSocket cerrado para cámara ${cameraId}:`, event.code, event.reason);
          connection.isConnecting = false;
          this.stopHeartbeat(cameraId);
          this.emitStatus(cameraId, 'disconnected');
          
          // Reconectar si no fue cierre intencional
          if (connection.shouldReconnect && event.code !== 1000) {
            console.log(`Conexión perdida para cámara ${cameraId}, intentando reconectar...`);
            this.scheduleReconnect(cameraId);
          } else if (event.code === 1000) {
            console.log(`Desconexión intencional para cámara ${cameraId}, no se reconectará`);
          } else {
            console.warn(`WebSocket cerrado inesperadamente para cámara ${cameraId}:`, event.code, event.reason);
          }
        };
        
      } catch (error) {
        connection.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Desconectar de una cámara específica
   */
  disconnect(cameraId: string): void {
    const connection = this.connections.get(cameraId);
    if (!connection) {
      return;
    }
    
    connection.shouldReconnect = false;
    
    if (connection.reconnectTimeout) {
      clearTimeout(connection.reconnectTimeout);
      connection.reconnectTimeout = null;
    }
    
    this.stopHeartbeat(cameraId);
    
    if (connection.ws) {
      if (connection.ws.readyState === WebSocket.OPEN) {
        connection.ws.close(1000, 'Desconexión solicitada');
      }
    }
    
    this.emitStatus(cameraId, 'disconnected');
    
    // Limpiar conexión y callbacks
    this.connections.delete(cameraId);
    this.onFrameCallbacks.delete(cameraId);
    this.onStatusCallbacks.delete(cameraId);
    this.onErrorCallbacks.delete(cameraId);
    this.onRTTCallbacks.delete(cameraId);
  }
  
  /**
   * Desconectar todas las cámaras
   */
  disconnectAll(): void {
    const cameraIds = Array.from(this.connections.keys());
    cameraIds.forEach(cameraId => this.disconnect(cameraId));
  }

  /**
   * Iniciar streaming para una cámara específica
   */
  async startStream(cameraId: string, config?: Partial<StreamConfig>): Promise<void> {
    const connection = this.connections.get(cameraId);
    if (!connection || connection.ws.readyState !== WebSocket.OPEN) {
      throw new Error(`WebSocket no conectado para cámara ${cameraId}`);
    }

    const defaultConfig: StreamConfig = {
      quality: 'medium',
      fps: 30,
      format: 'jpeg'
    };

    const finalConfig = { ...defaultConfig, ...config };

    this.send(cameraId, {
      action: 'start_stream',
      params: finalConfig
    });
  }

  /**
   * Detener streaming para una cámara específica
   */
  async stopStream(cameraId: string): Promise<void> {
    const connection = this.connections.get(cameraId);
    if (!connection || connection.ws.readyState !== WebSocket.OPEN) {
      throw new Error(`WebSocket no conectado para cámara ${cameraId}`);
    }

    this.send(cameraId, {
      action: 'stop_stream'
    });
  }

  /**
   * Actualizar calidad del stream para una cámara específica
   */
  async updateQuality(cameraId: string, quality: StreamQuality): Promise<void> {
    const connection = this.connections.get(cameraId);
    if (!connection || connection.ws.readyState !== WebSocket.OPEN) {
      throw new Error(`WebSocket no conectado para cámara ${cameraId}`);
    }

    this.send(cameraId, {
      action: 'update_quality',
      params: { quality }
    });
  }

  /**
   * Actualizar FPS del stream para una cámara específica
   */
  async updateFPS(cameraId: string, fps: number): Promise<void> {
    const connection = this.connections.get(cameraId);
    if (!connection || connection.ws.readyState !== WebSocket.OPEN) {
      throw new Error(`WebSocket no conectado para cámara ${cameraId}`);
    }

    if (fps < 1 || fps > 60) {
      throw new Error('FPS debe estar entre 1 y 60');
    }

    this.send(cameraId, {
      action: 'update_fps',
      params: { fps }
    });
  }

  /**
   * Enviar mensaje al WebSocket de una cámara específica
   */
  private send(cameraId: string, data: any): void {
    const connection = this.connections.get(cameraId);
    if (connection && connection.ws && connection.ws.readyState === WebSocket.OPEN) {
      const message = JSON.stringify(data);
      console.log(`Enviando mensaje WebSocket para cámara ${cameraId}:`, message);
      connection.ws.send(message);
    }
  }

  /**
   * Manejar mensajes recibidos de una cámara específica
   */
  private handleMessage(cameraId: string, event: MessageEvent): void {
    try {
      const message: StreamMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'frame':
          this.handleFrame(cameraId, message as FrameData);
          break;
          
        case 'status':
          this.emitStatus(cameraId, message.status || 'unknown', message);
          break;
          
        case 'error':
          this.emitError(cameraId, message.error || 'Error desconocido');
          break;
          
        case 'connection':
          console.log(`Mensaje de conexión para cámara ${cameraId}:`, message);
          break;
          
        case 'room_joined':
          console.log(`Cliente unido a sala de cámara ${cameraId}`);
          this.emitStatus(cameraId, 'room_joined', message);
          break;
          
        case 'pong':
          // Ya no manejamos pong, la latencia se calcula con capture_timestamp
          break;
          
        default:
          console.warn(`Tipo de mensaje desconocido para cámara ${cameraId}:`, message.type);
      }
    } catch (error) {
      console.error(`Error procesando mensaje para cámara ${cameraId}:`, error);
    }
  }

  /**
   * Manejar frame recibido de una cámara específica
   */
  private handleFrame(cameraId: string, frameData: FrameData): void {
    const connection = this.connections.get(cameraId);
    if (!connection) return;
    
    connection.frameCount++;
    const now = Date.now();
    connection.lastFrameTime = now;
    
    // Calcular latencia usando capture_timestamp
    let latency = -1;
    if (frameData.capture_timestamp) {
      try {
        // Parse timestamp ISO con timezone UTC
        const captureTime = new Date(frameData.capture_timestamp).getTime();
        latency = now - captureTime;
        
        // Validar que la latencia sea razonable (no negativa y menor a 10 segundos)
        if (latency < 0 || latency > 10000) {
          console.warn(`[${cameraId}] Latencia inválida calculada: ${latency}ms. Timestamp captura: ${frameData.capture_timestamp}`);
          latency = -1;
        } else {
          // Actualizar RTT con la latencia calculada (para mantener compatibilidad)
          connection.lastRTT = latency;
          connection.recentRTTs.push(latency);
          
          // Mantener solo los últimos N valores
          if (connection.recentRTTs.length > this.rttWindowSize) {
            connection.recentRTTs.shift();
          }
          
          // Calcular promedio
          if (connection.recentRTTs.length > 0) {
            const sum = connection.recentRTTs.reduce((a, b) => a + b, 0);
            connection.averageRTT = Math.round(sum / connection.recentRTTs.length);
          }
          
          console.debug(`[${cameraId}] Latencia calculada: ${latency}ms (promedio: ${connection.averageRTT}ms)`);
          
          // Emitir actualización de latencia (usando el mismo callback que RTT para compatibilidad)
          this.emitRTT(cameraId, latency);
        }
      } catch (error) {
        console.error(`[${cameraId}] Error calculando latencia:`, error);
        latency = -1;
      }
    } else {
      console.debug(`[${cameraId}] Frame sin capture_timestamp, latencia no disponible`);
    }
    
    // Agregar tiempo del frame actual a la ventana deslizante para FPS
    connection.recentFrameTimes.push(now);
    
    // Mantener solo los últimos N frames
    if (connection.recentFrameTimes.length > this.fpsWindowSize) {
      connection.recentFrameTimes.shift();
    }
    
    // Emitir a todos los callbacks registrados para esta cámara
    const callbacks = this.onFrameCallbacks.get(cameraId);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(frameData);
        } catch (error) {
          console.error(`Error en callback de frame para cámara ${cameraId}:`, error);
        }
      });
    }
  }


  /**
   * Programar reconexión para una cámara específica
   */
  private scheduleReconnect(cameraId: string): void {
    const connection = this.connections.get(cameraId);
    if (!connection) return;
    
    if (connection.reconnectTimeout) {
      clearTimeout(connection.reconnectTimeout);
    }
    
    console.log(`Reconectando cámara ${cameraId} en ${this.reconnectDelay}ms...`);
    this.emitStatus(cameraId, 'reconnecting');
    
    connection.reconnectTimeout = setTimeout(() => {
      if (connection.shouldReconnect) {
        this.connect(cameraId).catch(error => {
          console.error(`Error al reconectar cámara ${cameraId}:`, error);
        });
      }
    }, this.reconnectDelay);
  }

  /**
   * Iniciar heartbeat para una cámara específica
   */
  private startHeartbeat(cameraId: string): void {
    // Ya no necesitamos heartbeat para medir latencia
    // La latencia ahora se calcula usando capture_timestamp del frame
    return;
  }

  /**
   * Detener heartbeat para una cámara específica
   */
  private stopHeartbeat(cameraId: string): void {
    // Ya no necesitamos heartbeat
    return;
  }

  /**
   * Emitir estado para una cámara específica
   */
  private emitStatus(cameraId: string, status: string, data?: any): void {
    const callbacks = this.onStatusCallbacks.get(cameraId);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(status, data);
        } catch (error) {
          console.error(`Error en callback de estado para cámara ${cameraId}:`, error);
        }
      });
    }
  }

  /**
   * Emitir error para una cámara específica
   */
  private emitError(cameraId: string, error: string): void {
    const callbacks = this.onErrorCallbacks.get(cameraId);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(error);
        } catch (error) {
          console.error(`Error en callback de error para cámara ${cameraId}:`, error);
        }
      });
    }
  }

  /**
   * Emitir actualización de RTT para una cámara específica
   */
  private emitRTT(cameraId: string, rtt: number): void {
    const callbacks = this.onRTTCallbacks.get(cameraId);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(rtt);
        } catch (error) {
          console.error(`Error en callback de RTT para cámara ${cameraId}:`, error);
        }
      });
    }
  }

  /**
   * Registrar callback para frames de una cámara específica
   */
  onFrame(cameraId: string, callback: StreamEventCallback): () => void {
    if (!this.onFrameCallbacks.has(cameraId)) {
      this.onFrameCallbacks.set(cameraId, new Set());
    }
    
    const callbacks = this.onFrameCallbacks.get(cameraId)!;
    callbacks.add(callback);
    
    // Retornar función para desregistrar
    return () => {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.onFrameCallbacks.delete(cameraId);
      }
    };
  }

  /**
   * Registrar callback para estados de una cámara específica
   */
  onStatus(cameraId: string, callback: StatusEventCallback): () => void {
    if (!this.onStatusCallbacks.has(cameraId)) {
      this.onStatusCallbacks.set(cameraId, new Set());
    }
    
    const callbacks = this.onStatusCallbacks.get(cameraId)!;
    callbacks.add(callback);
    
    return () => {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.onStatusCallbacks.delete(cameraId);
      }
    };
  }

  /**
   * Registrar callback para errores de una cámara específica
   */
  onError(cameraId: string, callback: ErrorEventCallback): () => void {
    if (!this.onErrorCallbacks.has(cameraId)) {
      this.onErrorCallbacks.set(cameraId, new Set());
    }
    
    const callbacks = this.onErrorCallbacks.get(cameraId)!;
    callbacks.add(callback);
    
    return () => {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.onErrorCallbacks.delete(cameraId);
      }
    };
  }

  /**
   * Registrar callback para actualizaciones de RTT de una cámara específica
   */
  onRTT(cameraId: string, callback: RTTUpdateCallback): () => void {
    if (!this.onRTTCallbacks.has(cameraId)) {
      this.onRTTCallbacks.set(cameraId, new Set());
    }
    
    const callbacks = this.onRTTCallbacks.get(cameraId)!;
    callbacks.add(callback);
    
    return () => {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.onRTTCallbacks.delete(cameraId);
      }
    };
  }

  /**
   * Obtener estado de conexión para una cámara específica
   */
  isConnected(cameraId: string): boolean {
    const connection = this.connections.get(cameraId);
    return connection ? connection.ws !== null && connection.ws.readyState === WebSocket.OPEN : false;
  }
  
  /**
   * Obtener todas las cámaras conectadas
   */
  getConnectedCameras(): string[] {
    const connected: string[] = [];
    this.connections.forEach((connection, cameraId) => {
      if (connection.ws && connection.ws.readyState === WebSocket.OPEN) {
        connected.push(cameraId);
      }
    });
    return connected;
  }

  /**
   * Obtener métricas actuales de una cámara específica
   */
  getMetrics(cameraId: string): {
    frameCount: number;
    connectionTime: number;
    fps: number;
    rtt: number;
    averageRTT: number;
    minRTT: number;
    maxRTT: number;
  } | null {
    const connection = this.connections.get(cameraId);
    if (!connection) {
      return null;
    }
    
    const now = Date.now();
    const connectionTime = connection.connectionStartTime ? 
      (now - connection.connectionStartTime) / 1000 : 0;
    
    // Calcular FPS basado en frames recientes
    let fps = 0;
    if (connection.recentFrameTimes.length >= 2) {
      const oldestFrame = connection.recentFrameTimes[0];
      const newestFrame = connection.recentFrameTimes[connection.recentFrameTimes.length - 1];
      const timeDiff = (newestFrame - oldestFrame) / 1000; // En segundos
      
      if (timeDiff > 0) {
        fps = (connection.recentFrameTimes.length - 1) / timeDiff;
      }
    }
    
    // Calcular estadísticas de RTT
    let minRTT = 0;
    let maxRTT = 0;
    if (connection.recentRTTs.length > 0) {
      minRTT = Math.min(...connection.recentRTTs);
      maxRTT = Math.max(...connection.recentRTTs);
    }
    
    return {
      frameCount: connection.frameCount,
      connectionTime: Math.round(connectionTime),
      fps: Math.round(fps * 10) / 10, // Redondear a 1 decimal
      rtt: connection.lastRTT,
      averageRTT: connection.averageRTT,
      minRTT,
      maxRTT
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

  /**
   * Configurar intervalo de ping
   * @deprecated Ya no se usa ping/pong. La latencia se calcula con timestamp de captura
   */
  setPingInterval(interval: number): void {
    console.warn('setPingInterval está deprecado. La latencia ahora se calcula con timestamp de captura');
  }

  /**
   * Obtener intervalo de ping actual
   * @deprecated Ya no se usa ping/pong
   */
  getPingInterval(): number {
    console.warn('getPingInterval está deprecado. Ya no se usa ping/pong');
    return 0;
  }

  /**
   * Obtener información de latencia para una cámara específica
   * Nota: Aunque se llama RTT por compatibilidad, ahora retorna latencias calculadas
   */
  getRTTInfo(cameraId: string): {
    current: number;
    average: number;
    min: number;
    max: number;
    samples: number;
  } | null {
    const connection = this.connections.get(cameraId);
    if (!connection) {
      return null;
    }
    
    let min = 0;
    let max = 0;
    if (connection.recentRTTs.length > 0) {
      min = Math.min(...connection.recentRTTs);
      max = Math.max(...connection.recentRTTs);
    }
    
    return {
      current: connection.lastRTT,
      average: connection.averageRTT,
      min,
      max,
      samples: connection.recentRTTs.length
    };
  }
}

// Instancia singleton del servicio
export const streamingService = new StreamingService();

// Exportar instancia por defecto
export default streamingService;