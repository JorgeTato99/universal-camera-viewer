"""
Sistema de eventos WebSocket para notificaciones en tiempo real.

Este módulo proporciona un mecanismo simple para que los presenters
emitan eventos que pueden ser enviados a clientes WebSocket conectados.
"""

import asyncio
from typing import Dict, Any, Set, Callable, Optional
from datetime import datetime
import json

from services.logging_service import get_secure_logger
from api.schemas.websocket.ws_messages import EventType


logger = get_secure_logger("api.websocket_events")


class WebSocketEventEmitter:
    """
    Emisor de eventos WebSocket.
    
    Los presenters pueden usar esta clase para emitir eventos
    que serán enviados a todos los clientes WebSocket conectados.
    """
    
    def __init__(self):
        """Inicializa el emisor de eventos."""
        self._subscribers: Set[Callable] = set()
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self.logger = logger
        
    def subscribe(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Suscribe un callback para recibir eventos.
        
        Args:
            callback: Función que será llamada con (event_type, data)
        """
        self._subscribers.add(callback)
        self.logger.debug(f"Suscriptor agregado, total: {len(self._subscribers)}")
        
    def unsubscribe(self, callback: Callable) -> None:
        """
        Desuscribe un callback.
        
        Args:
            callback: Función a desuscribir
        """
        self._subscribers.discard(callback)
        self.logger.debug(f"Suscriptor removido, total: {len(self._subscribers)}")
        
    async def emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Emite un evento a todos los suscriptores.
        
        Args:
            event_type: Tipo de evento
            data: Datos del evento
        """
        event = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Agregar a la cola para procesamiento asíncrono
        await self._event_queue.put(event)
        
        # Iniciar procesador si no está corriendo
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_events())
            
    async def _process_events(self) -> None:
        """Procesa eventos de la cola y los envía a suscriptores."""
        while not self._event_queue.empty():
            try:
                event = await self._event_queue.get()
                
                # Notificar a todos los suscriptores
                for subscriber in self._subscribers.copy():
                    try:
                        if asyncio.iscoroutinefunction(subscriber):
                            await subscriber(event['event_type'], event)
                        else:
                            subscriber(event['event_type'], event)
                    except Exception as e:
                        self.logger.error(
                            f"Error notificando suscriptor: {e}",
                            exc_info=True
                        )
                        
                self.logger.debug(
                    f"Evento {event['event_type']} enviado a "
                    f"{len(self._subscribers)} suscriptores"
                )
                
            except Exception as e:
                self.logger.error(f"Error procesando evento: {e}", exc_info=True)
                
    async def emit_remote_publication_event(
        self,
        event_type: EventType,
        camera_id: str,
        server_id: int,
        **kwargs
    ) -> None:
        """
        Emite un evento específico de publicación remota.
        
        Args:
            event_type: Tipo de evento (debe ser REMOTE_PUBLICATION_*)
            camera_id: ID de la cámara
            server_id: ID del servidor
            **kwargs: Datos adicionales del evento
        """
        data = {
            "camera_id": camera_id,
            "server_id": server_id,
            **kwargs
        }
        
        await self.emit(event_type.value, data)
        
    async def emit_server_event(
        self,
        event_type: EventType,
        server_id: int,
        server_name: str,
        **kwargs
    ) -> None:
        """
        Emite un evento específico de servidor.
        
        Args:
            event_type: Tipo de evento (debe ser REMOTE_SERVER_*)
            server_id: ID del servidor
            server_name: Nombre del servidor
            **kwargs: Datos adicionales del evento
        """
        data = {
            "server_id": server_id,
            "server_name": server_name,
            **kwargs
        }
        
        await self.emit(event_type.value, data)


# Instancia global del emisor
_event_emitter = WebSocketEventEmitter()


def get_websocket_event_emitter() -> WebSocketEventEmitter:
    """
    Obtiene la instancia singleton del emisor de eventos.
    
    Returns:
        WebSocketEventEmitter singleton
    """
    return _event_emitter


# Funciones de conveniencia para emisión directa
async def emit_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Emite un evento genérico.
    
    Args:
        event_type: Tipo de evento
        data: Datos del evento
    """
    await _event_emitter.emit(event_type, data)


async def emit_remote_publication_started(
    camera_id: str,
    server_id: int,
    publish_url: str,
    webrtc_url: Optional[str] = None
) -> None:
    """Emite evento de publicación remota iniciada."""
    await _event_emitter.emit_remote_publication_event(
        EventType.REMOTE_PUBLICATION_STARTED,
        camera_id=camera_id,
        server_id=server_id,
        publish_url=publish_url,
        webrtc_url=webrtc_url
    )


async def emit_remote_publication_stopped(
    camera_id: str,
    server_id: int,
    reason: Optional[str] = None
) -> None:
    """Emite evento de publicación remota detenida."""
    await _event_emitter.emit_remote_publication_event(
        EventType.REMOTE_PUBLICATION_STOPPED,
        camera_id=camera_id,
        server_id=server_id,
        reason=reason
    )


async def emit_remote_publication_error(
    camera_id: str,
    server_id: int,
    error: str,
    recoverable: bool = True
) -> None:
    """Emite evento de error en publicación remota."""
    await _event_emitter.emit_remote_publication_event(
        EventType.REMOTE_PUBLICATION_ERROR,
        camera_id=camera_id,
        server_id=server_id,
        error=error,
        recoverable=recoverable
    )


async def emit_remote_server_connected(
    server_id: int,
    server_name: str,
    api_url: str
) -> None:
    """Emite evento de servidor conectado."""
    await _event_emitter.emit_server_event(
        EventType.REMOTE_SERVER_CONNECTED,
        server_id=server_id,
        server_name=server_name,
        api_url=api_url
    )


async def emit_remote_server_disconnected(
    server_id: int,
    server_name: str,
    reason: Optional[str] = None
) -> None:
    """Emite evento de servidor desconectado."""
    await _event_emitter.emit_server_event(
        EventType.REMOTE_SERVER_DISCONNECTED,
        server_id=server_id,
        server_name=server_name,
        reason=reason
    )