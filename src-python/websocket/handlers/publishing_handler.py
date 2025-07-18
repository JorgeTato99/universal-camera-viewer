"""
WebSocket handler para eventos de publicación en tiempo real.

Gestiona la comunicación bidireccional para:
- Notificaciones de cambio de estado
- Actualizaciones de métricas
- Control remoto de publicación
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Set
from datetime import datetime
import json

from websocket.connection_manager import manager
from presenters.publishing_presenter import get_publishing_presenter
from models.publishing import PublishStatus, PublishErrorType


logger = logging.getLogger(__name__)


class PublishingWebSocketHandler:
    """
    Handler para eventos de publicación vía WebSocket.
    
    Responsabilidades:
    - Procesar comandos de control desde clientes
    - Emitir eventos de cambio de estado
    - Distribuir métricas en tiempo real
    - Gestionar suscripciones a cámaras específicas
    """
    
    def __init__(self):
        """Inicializa el handler."""
        self.logger = logger
        # Clientes suscritos a eventos de publicación por cámara
        self.camera_subscribers: Dict[str, Set[str]] = {}
        # Task para actualización periódica de métricas
        self._metrics_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """
        Inicia el handler y tareas de background.
        
        Debe llamarse al iniciar la aplicación para comenzar
        el monitoreo de métricas.
        """
        if self._running:
            self.logger.warning("PublishingWebSocketHandler ya está en ejecución")
            return
            
        self._running = True
        self.logger.info("Iniciando PublishingWebSocketHandler")
        
        # Iniciar task de actualización de métricas
        self._metrics_task = asyncio.create_task(
            self._metrics_update_loop(),
            name="publishing_metrics_updater"
        )
        
    async def stop(self):
        """
        Detiene el handler y limpia recursos.
        
        Debe llamarse durante el shutdown de la aplicación.
        """
        self._running = False
        
        if self._metrics_task and not self._metrics_task.done():
            self._metrics_task.cancel()
            try:
                await self._metrics_task
            except asyncio.CancelledError:
                pass
                
        self.camera_subscribers.clear()
        self.logger.info("PublishingWebSocketHandler detenido")
        
    async def handle_client_disconnect(self, client_id: str) -> None:
        """
        Limpia las suscripciones cuando un cliente se desconecta.
        
        Args:
            client_id: ID del cliente desconectado
        """
        self.logger.info(f"Limpiando suscripciones del cliente {client_id}")
        
        # Eliminar cliente de todas las suscripciones
        for camera_id in list(self.camera_subscribers.keys()):
            self.camera_subscribers[camera_id].discard(client_id)
            # Limpiar set vacío
            if not self.camera_subscribers[camera_id]:
                del self.camera_subscribers[camera_id]
    
    async def handle_message(self, client_id: str, message: dict) -> Optional[dict]:
        """
        Procesa mensaje recibido de un cliente WebSocket.
        
        Args:
            client_id: ID del cliente que envió el mensaje
            message: Mensaje JSON recibido
            
        Returns:
            Respuesta opcional para el cliente
            
        Comandos soportados:
            - subscribe_camera: Suscribirse a eventos de una cámara
            - unsubscribe_camera: Desuscribirse de una cámara
            - start_publishing: Iniciar publicación
            - stop_publishing: Detener publicación
            - get_status: Obtener estado actual
        """
        msg_type = message.get("type")
        
        if not msg_type:
            return {"error": "Tipo de mensaje no especificado"}
            
        self.logger.debug(f"Procesando mensaje '{msg_type}' de cliente {client_id}")
        
        try:
            # Router de comandos
            if msg_type == "subscribe_camera":
                return await self._handle_subscribe(client_id, message)
            elif msg_type == "unsubscribe_camera":
                return await self._handle_unsubscribe(client_id, message)
            elif msg_type == "start_publishing":
                return await self._handle_start_publishing(client_id, message)
            elif msg_type == "stop_publishing":
                return await self._handle_stop_publishing(client_id, message)
            elif msg_type == "get_status":
                return await self._handle_get_status(client_id, message)
            elif msg_type == "get_all_status":
                return await self._handle_get_all_status(client_id)
            else:
                return {"error": f"Tipo de mensaje no soportado: {msg_type}"}
                
        except ValueError as e:
            self.logger.warning(f"Error de validación procesando {msg_type}: {e}")
            return {
                "error": "Error de validación",
                "details": str(e)
            }
        except KeyError as e:
            self.logger.error(f"Clave faltante procesando {msg_type}: {e}")
            return {
                "error": "Datos faltantes en la solicitud",
                "details": str(e)
            }
        except Exception as e:
            self.logger.exception(f"Error inesperado procesando mensaje {msg_type}")
            return {
                "error": "Error interno procesando mensaje",
                "details": "Error inesperado, revise los logs del servidor"
            }
            
    async def _handle_subscribe(self, client_id: str, message: dict) -> dict:
        """
        Maneja suscripción a eventos de una cámara.
        
        Args:
            client_id: ID del cliente
            message: Debe contener 'camera_id'
            
        Returns:
            Confirmación de suscripción
        """
        camera_id = message.get("camera_id")
        if not camera_id:
            return {"error": "camera_id es requerido"}
            
        # Validar que la cámara existe
        if not await self._validate_camera_exists(camera_id):
            return {"error": f"Cámara {camera_id} no encontrada"}
            
        # Agregar cliente a suscriptores de esta cámara
        if camera_id not in self.camera_subscribers:
            self.camera_subscribers[camera_id] = set()
            
        self.camera_subscribers[camera_id].add(client_id)
        
        # Unir cliente a sala de la cámara para broadcasts dirigidos
        await manager.join_room(client_id, f"camera_{camera_id}")
        
        self.logger.info(f"Cliente {client_id} suscrito a cámara {camera_id}")
        
        # Enviar estado actual de la cámara
        presenter = await get_publishing_presenter()
        status = await presenter.get_camera_status(camera_id)
        
        return {
            "type": "subscribed",
            "camera_id": camera_id,
            "current_status": self._serialize_status(status) if status else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    async def _handle_unsubscribe(self, client_id: str, message: dict) -> dict:
        """
        Maneja desuscripción de eventos de una cámara.
        
        Args:
            client_id: ID del cliente
            message: Debe contener 'camera_id'
            
        Returns:
            Confirmación de desuscripción
        """
        camera_id = message.get("camera_id")
        if not camera_id:
            return {"error": "camera_id es requerido"}
            
        # Remover cliente de suscriptores
        if camera_id in self.camera_subscribers:
            self.camera_subscribers[camera_id].discard(client_id)
            if not self.camera_subscribers[camera_id]:
                del self.camera_subscribers[camera_id]
                
        # Salir de sala de la cámara
        await manager.leave_room(client_id, f"camera_{camera_id}")
        
        self.logger.info(f"Cliente {client_id} desuscrito de cámara {camera_id}")
        
        return {
            "type": "unsubscribed",
            "camera_id": camera_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    async def _handle_start_publishing(self, client_id: str, message: dict) -> dict:
        """
        Maneja solicitud de inicio de publicación.
        
        Args:
            client_id: ID del cliente
            message: Debe contener 'camera_id' y opcionalmente 'force_restart'
            
        Returns:
            Resultado de la operación
        """
        camera_id = message.get("camera_id")
        if not camera_id:
            return {"error": "camera_id es requerido"}
            
        force_restart = message.get("force_restart", False)
        
        self.logger.info(f"Cliente {client_id} solicitando publicación de {camera_id}")
        
        # Delegar al presenter
        presenter = await get_publishing_presenter()
        result = await presenter.start_publishing(camera_id, force_restart)
        
        # Preparar respuesta
        response = {
            "type": "publishing_started" if result.success else "publishing_failed",
            "camera_id": camera_id,
            "success": result.success,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if result.success:
            response["publish_path"] = result.publish_path
            response["process_id"] = result.process_id
        else:
            response["error"] = result.error
            response["error_type"] = result.error_type.value if result.error_type else None
            
        # Notificar a todos los suscriptores de esta cámara
        await self._broadcast_to_camera_subscribers(camera_id, response)
        
        return response
        
    async def _handle_stop_publishing(self, client_id: str, message: dict) -> dict:
        """
        Maneja solicitud de detención de publicación.
        
        Args:
            client_id: ID del cliente
            message: Debe contener 'camera_id'
            
        Returns:
            Resultado de la operación
        """
        camera_id = message.get("camera_id")
        if not camera_id:
            return {"error": "camera_id es requerido"}
            
        self.logger.info(f"Cliente {client_id} solicitando detener publicación de {camera_id}")
        
        # Delegar al presenter
        presenter = await get_publishing_presenter()
        success = await presenter.stop_publishing(camera_id)
        
        # Preparar respuesta
        response = {
            "type": "publishing_stopped" if success else "stop_failed",
            "camera_id": camera_id,
            "success": success,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if not success:
            response["error"] = "Cámara no está publicando"
            
        # Notificar a todos los suscriptores
        await self._broadcast_to_camera_subscribers(camera_id, response)
        
        return response
        
    async def _handle_get_status(self, client_id: str, message: dict) -> dict:
        """
        Maneja solicitud de estado de una cámara.
        
        Args:
            client_id: ID del cliente
            message: Debe contener 'camera_id'
            
        Returns:
            Estado actual de la cámara
        """
        camera_id = message.get("camera_id")
        if not camera_id:
            return {"error": "camera_id es requerido"}
            
        presenter = await get_publishing_presenter()
        status = await presenter.get_camera_status(camera_id)
        
        if not status:
            return {
                "type": "status_response",
                "camera_id": camera_id,
                "status": None,
                "error": "Cámara no encontrada o sin proceso",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        return {
            "type": "status_response",
            "camera_id": camera_id,
            "status": self._serialize_status(status),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    async def _handle_get_all_status(self, client_id: str) -> dict:
        """
        Maneja solicitud de estado de todas las cámaras.
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Estado de todas las publicaciones
        """
        presenter = await get_publishing_presenter()
        all_status = await presenter.get_all_status()
        
        items = []
        for camera_id, status in all_status.items():
            items.append({
                "camera_id": camera_id,
                **self._serialize_status(status)
            })
            
        return {
            "type": "all_status_response",
            "total": len(items),
            "active": sum(1 for s in all_status.values() if s.is_active),
            "items": items,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    async def _metrics_update_loop(self):
        """
        Loop de actualización periódica de métricas.
        
        Envía métricas actualizadas a los suscriptores cada 2 segundos
        para las cámaras que están publicando activamente.
        """
        self.logger.info("Iniciando loop de actualización de métricas")
        
        while self._running:
            try:
                # Obtener presenter
                presenter = await get_publishing_presenter()
                all_status = await presenter.get_all_status()
                
                # Actualizar métricas para cámaras activas con suscriptores
                for camera_id, status in all_status.items():
                    if status.is_active and camera_id in self.camera_subscribers:
                        # Preparar actualización de métricas
                        update = {
                            "type": "metrics_update",
                            "camera_id": camera_id,
                            "metrics": status.metrics,
                            "uptime_seconds": status.uptime_seconds,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                        
                        # Enviar a suscriptores
                        await self._broadcast_to_camera_subscribers(camera_id, update)
                        
                # Esperar antes de próxima actualización
                await asyncio.sleep(2.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en loop de métricas: {e}")
                await asyncio.sleep(5.0)  # Espera más larga en caso de error
                
        self.logger.info("Loop de actualización de métricas detenido")
        
    async def _broadcast_to_camera_subscribers(self, camera_id: str, message: dict):
        """
        Envía mensaje a todos los suscriptores de una cámara.
        
        Args:
            camera_id: ID de la cámara
            message: Mensaje a enviar
        """
        room = f"camera_{camera_id}"
        await manager.broadcast(message, room=room)
        
    def _serialize_status(self, status) -> dict:
        """
        Serializa PublisherProcess para envío por WebSocket.
        
        Args:
            status: PublisherProcess a serializar
            
        Returns:
            Dict serializable a JSON
        """
        if not status:
            return None
            
        return {
            "status": status.status.value,
            "is_active": status.is_active,
            "uptime_seconds": status.uptime_seconds,
            "error_count": status.error_count,
            "last_error": status.last_error,
            "error_type": status.error_type.value if status.error_type else None,
            "metrics": status.metrics,
            "start_time": status.start_time.isoformat() + "Z" if status.start_time else None
        }
        
    async def emit_publishing_event(self, event_type: str, data: dict):
        """
        Emite evento de publicación a los suscriptores apropiados.
        
        Método público para que otros componentes puedan emitir eventos.
        
        Args:
            event_type: Tipo de evento
            data: Datos del evento (debe incluir camera_id)
        """
        camera_id = data.get("camera_id")
        if not camera_id:
            self.logger.warning(f"Evento {event_type} sin camera_id")
            return
            
        # Agregar metadatos
        event_data = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **data
        }
        
        # Enviar a suscriptores
        await self._broadcast_to_camera_subscribers(camera_id, event_data)
        
        self.logger.debug(f"Evento {event_type} emitido para cámara {camera_id}")
    
    async def _validate_camera_exists(self, camera_id: str) -> bool:
        """
        Valida que una cámara existe en el sistema.
        
        Args:
            camera_id: ID de la cámara a validar
            
        Returns:
            True si la cámara existe, False si no
        """
        try:
            # Por ahora asumimos que todas las cámaras con formato válido existen
            # TODO: Implementar validación real contra CameraManagerService
            if not camera_id or not isinstance(camera_id, str):
                return False
            # Validar formato básico de ID
            if camera_id.startswith('cam-') and len(camera_id) > 4:
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error validando cámara {camera_id}: {e}")
            return False


# Instancia singleton del handler
_handler: Optional[PublishingWebSocketHandler] = None


def get_publishing_ws_handler() -> PublishingWebSocketHandler:
    """
    Obtiene la instancia singleton del handler.
    
    Returns:
        PublishingWebSocketHandler singleton
    """
    global _handler
    if _handler is None:
        _handler = PublishingWebSocketHandler()
    return _handler