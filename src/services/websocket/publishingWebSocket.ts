/**
 * WebSocket service para eventos de publicación en tiempo real
 * Maneja eventos tanto locales como remotos
 * 
 * @module services/websocket/publishingWebSocket
 */

import { usePublishingStore } from '../../stores/publishingStore';
import { notificationStore } from '../../stores/notificationStore';

// ====================================================================
// Types & Interfaces
// ====================================================================

/**
 * Tipos de mensajes WebSocket soportados
 */
export type WebSocketMessageType = 
  | 'connection'
  | 'subscribed'
  | 'unsubscribed'
  | 'publishing_started'
  | 'publishing_failed'
  | 'publishing_stopped'
  | 'stop_failed'
  | 'status_response'
  | 'all_status_response'
  | 'metrics_update'
  | 'error'
  | 'publication_status'
  | 'remote_publication_started'
  | 'remote_publication_stopped'
  | 'remote_publication_error'
  | 'remote_metrics_update'
  | 'server_status_update'
  | 'auth_status_update'
  | 'system_health'
  | 'alert';

/**
 * Mensaje WebSocket genérico
 */
export interface WebSocketMessage {
  type: WebSocketMessageType;
  camera_id?: string;
  server_id?: number;
  data?: any;
  error?: string;
  timestamp?: string;
}

/**
 * Estado de publicación desde WebSocket
 */
export interface WebSocketPublicationStatus {
  camera_id: string;
  is_active: boolean;
  status: string;
  last_error?: string;
  start_time?: string;
  process_id?: number;
  metrics?: any;
}

/**
 * Configuración del WebSocket
 */
export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

// ====================================================================
// WebSocket Manager Class
// ====================================================================

/**
 * Gestor de conexión WebSocket para publicaciones
 * Implementa reconexión automática y heartbeat
 */
class PublishingWebSocketManager {
  private static instance: PublishingWebSocketManager;
  
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private subscribedCameras = new Set<string>();
  private isIntentionallyClosed = false;
  
  private constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...config
    };
  }
  
  /**
   * Obtiene la instancia singleton
   */
  static getInstance(config?: WebSocketConfig): PublishingWebSocketManager {
    if (!PublishingWebSocketManager.instance) {
      if (!config) {
        throw new Error('Se requiere configuración en la primera inicialización');
      }
      PublishingWebSocketManager.instance = new PublishingWebSocketManager(config);
    }
    return PublishingWebSocketManager.instance;
  }
  
  /**
   * Conecta al WebSocket
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket ya está conectado');
      return;
    }
    
    this.isIntentionallyClosed = false;
    this.attemptConnection();
  }
  
  /**
   * Desconecta el WebSocket
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;
    this.cleanup();
  }
  
  /**
   * Intenta establecer conexión
   */
  private attemptConnection(): void {
    try {
      console.log(`Conectando a WebSocket: ${this.config.url}`);
      this.ws = new WebSocket(this.config.url);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      
    } catch (error) {
      console.error('Error creando WebSocket:', error);
      this.scheduleReconnect();
    }
  }
  
  /**
   * Maneja apertura de conexión
   */
  private handleOpen(): void {
    console.log('WebSocket conectado');
    this.reconnectAttempts = 0;
    
    // Iniciar heartbeat
    this.startHeartbeat();
    
    // Re-suscribir a cámaras si había alguna
    this.subscribedCameras.forEach(cameraId => {
      this.subscribeToCamera(cameraId);
    });
    
    // Solicitar estado inicial
    this.send({ type: 'get_all_status' });
  }
  
  /**
   * Maneja mensajes entrantes
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.processMessage(message);
    } catch (error) {
      console.error('Error procesando mensaje WebSocket:', error);
    }
  }
  
  /**
   * Procesa mensaje según su tipo
   */
  private processMessage(message: WebSocketMessage): void {
    const store = usePublishingStore.getState();
    
    switch (message.type) {
      case 'connection':
        console.log('WebSocket conectado:', message.data?.message);
        break;
        
      case 'publishing_started':
        if (message.camera_id) {
          notificationStore.addNotification({
            type: 'success',
            title: 'Publicación iniciada',
            message: `Cámara ${message.camera_id} está publicando`,
          });
          // Actualizar estado local si es necesario
          store.fetchPublishingStatus();
        }
        break;
        
      case 'publishing_stopped':
        if (message.camera_id) {
          notificationStore.addNotification({
            type: 'info',
            title: 'Publicación detenida',
            message: `Cámara ${message.camera_id} dejó de publicar`,
          });
          store.fetchPublishingStatus();
        }
        break;
        
      case 'remote_publication_started':
        if (message.camera_id && message.server_id) {
          notificationStore.addNotification({
            type: 'success',
            title: 'Publicación remota iniciada',
            message: `Cámara ${message.camera_id} publicando al servidor ${message.server_id}`,
          });
          store.fetchRemotePublications();
        }
        break;
        
      case 'remote_publication_stopped':
        if (message.camera_id) {
          store.fetchRemotePublications();
        }
        break;
        
      case 'remote_publication_error':
        if (message.camera_id && message.error) {
          notificationStore.addNotification({
            type: 'error',
            title: 'Error en publicación remota',
            message: message.error,
          });
        }
        break;
        
      case 'metrics_update':
      case 'remote_metrics_update':
        if (message.camera_id && message.data) {
          store.addMetricSample(message.camera_id, message.data);
        }
        break;
        
      case 'server_status_update':
        if (message.server_id) {
          // Recargar información del servidor
          store.fetchRemoteServers();
        }
        break;
        
      case 'auth_status_update':
        if (message.server_id && message.data) {
          const authStatuses = new Map(store.remote.authStatuses);
          authStatuses.set(message.server_id, message.data);
          store.remote.authStatuses = authStatuses;
        }
        break;
        
      case 'status_response':
      case 'all_status_response':
        // El store ya maneja estos casos
        if (message.data) {
          // TODO: Actualizar cuando el backend envíe el formato correcto
        }
        break;
        
      case 'system_health':
        if (message.data) {
          store.systemHealth = message.data;
        }
        break;
        
      case 'alert':
        if (message.data) {
          store.alerts.push(message.data);
          
          // Mostrar notificación según severidad
          const severity = message.data.severity || 'info';
          const type = severity === 'critical' || severity === 'error' ? 'error' : 
                      severity === 'warning' ? 'warning' : 'info';
          
          notificationStore.addNotification({
            type,
            title: 'Alerta del sistema',
            message: message.data.message,
          });
        }
        break;
        
      case 'error':
        console.error('Error del servidor:', message.error);
        break;
        
      default:
        console.log('Mensaje no manejado:', message.type);
    }
  }
  
  /**
   * Maneja errores de conexión
   */
  private handleError(event: Event): void {
    console.error('Error en WebSocket:', event);
  }
  
  /**
   * Maneja cierre de conexión
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket cerrado:', event.code, event.reason);
    this.cleanup();
    
    if (!this.isIntentionallyClosed) {
      this.scheduleReconnect();
    }
  }
  
  /**
   * Programa reconexión
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts!) {
      console.error('Máximo de intentos de reconexión alcanzado');
      notificationStore.addNotification({
        type: 'error',
        title: 'Conexión perdida',
        message: 'No se pudo restablecer la conexión con el servidor',
      });
      return;
    }
    
    this.reconnectAttempts++;
    const delay = Math.min(
      this.config.reconnectInterval! * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Máximo 30 segundos
    );
    
    console.log(`Reconectando en ${delay}ms (intento ${this.reconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.attemptConnection();
    }, delay);
  }
  
  /**
   * Limpia recursos
   */
  private cleanup(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  /**
   * Inicia heartbeat
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' as any });
      }
    }, this.config.heartbeatInterval!);
  }
  
  /**
   * Envía mensaje
   */
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket no está conectado');
    }
  }
  
  /**
   * Suscribe a eventos de una cámara
   */
  subscribeToCamera(cameraId: string): void {
    this.subscribedCameras.add(cameraId);
    this.send({
      type: 'subscribe_camera',
      camera_id: cameraId
    });
  }
  
  /**
   * Desuscribe de eventos de una cámara
   */
  unsubscribeFromCamera(cameraId: string): void {
    this.subscribedCameras.delete(cameraId);
    this.send({
      type: 'unsubscribe_camera',
      camera_id: cameraId
    });
  }
  
  /**
   * Verifica si está conectado
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
  
  /**
   * Obtiene el estado de la conexión
   */
  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

// ====================================================================
// Exported Functions
// ====================================================================

// Instancia singleton
let wsManager: PublishingWebSocketManager | null = null;

/**
 * Inicializa y conecta el WebSocket de publicaciones
 */
export function initializePublishingWebSocket(
  url: string = 'ws://localhost:8000/ws/publishing'
): void {
  if (!wsManager) {
    wsManager = PublishingWebSocketManager.getInstance({ url });
  }
  wsManager.connect();
}

/**
 * Desconecta el WebSocket
 */
export function disconnectPublishingWebSocket(): void {
  wsManager?.disconnect();
}

/**
 * Suscribe a eventos de una cámara
 */
export function subscribeToCamera(cameraId: string): void {
  wsManager?.subscribeToCamera(cameraId);
}

/**
 * Desuscribe de eventos de una cámara
 */
export function unsubscribeFromCamera(cameraId: string): void {
  wsManager?.unsubscribeFromCamera(cameraId);
}

/**
 * Envía comando de inicio de publicación
 */
export function startPublishingCommand(
  cameraId: string, 
  forceRestart: boolean = false
): void {
  wsManager?.send({
    type: 'start_publishing',
    camera_id: cameraId,
    force_restart: forceRestart
  });
}

/**
 * Envía comando de detención de publicación
 */
export function stopPublishingCommand(cameraId: string): void {
  wsManager?.send({
    type: 'stop_publishing',
    camera_id: cameraId
  });
}

/**
 * Solicita estado de una cámara
 */
export function requestCameraStatus(cameraId: string): void {
  wsManager?.send({
    type: 'get_status',
    camera_id: cameraId
  });
}

/**
 * Solicita estado de todas las publicaciones
 */
export function requestAllStatus(): void {
  wsManager?.send({
    type: 'get_all_status'
  });
}

/**
 * Verifica si el WebSocket está conectado
 */
export function isWebSocketConnected(): boolean {
  return wsManager?.isConnected() ?? false;
}

/**
 * Obtiene el estado de la conexión WebSocket
 */
export function getWebSocketState(): string {
  if (!wsManager) return 'No inicializado';
  
  const state = wsManager.getReadyState();
  switch (state) {
    case WebSocket.CONNECTING: return 'Conectando';
    case WebSocket.OPEN: return 'Conectado';
    case WebSocket.CLOSING: return 'Cerrando';
    case WebSocket.CLOSED: return 'Cerrado';
    default: return 'Desconocido';
  }
}