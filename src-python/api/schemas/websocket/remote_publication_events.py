"""
Eventos WebSocket específicos para publicaciones remotas MediaMTX.

Define eventos adicionales para notificar cambios en publicaciones
a servidores remotos, permitiendo actualizaciones en tiempo real
en el frontend.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from api.schemas.websocket.ws_messages import (
    WSServerMessage, 
    WSMessageType, 
    EventType,
    create_event_message
)
from services.logging_service import get_secure_logger


logger = get_secure_logger("api.schemas.websocket.remote_publication_events")


def create_remote_publication_event(
    event_type: EventType,
    camera_id: str,
    server_id: int,
    server_name: str,
    title: str,
    severity: str = "info",
    description: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crea un evento de publicación remota.
    
    Args:
        event_type: Tipo de evento (REMOTE_PUBLICATION_*)
        camera_id: ID de la cámara
        server_id: ID del servidor MediaMTX
        server_name: Nombre del servidor
        title: Título del evento
        severity: Severidad (info, warning, error)
        description: Descripción opcional
        additional_data: Datos adicionales del evento
        
    Returns:
        Dict con el mensaje formateado para WebSocket
    """
    data = {
        "camera_id": camera_id,
        "server_id": server_id,
        "server_name": server_name,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if additional_data:
        data.update(additional_data)
    
    return create_event_message(
        event_type=event_type,
        source=f"remote_publisher_{server_id}",
        title=title,
        severity=severity,
        description=description,
        data=data
    )


def remote_publication_started(
    camera_id: str,
    server_id: int,
    server_name: str,
    publish_url: str,
    webrtc_url: str
) -> Dict[str, Any]:
    """
    Evento cuando se inicia una publicación remota exitosamente.
    
    Args:
        camera_id: ID de la cámara
        server_id: ID del servidor
        server_name: Nombre del servidor
        publish_url: URL de publicación RTMP
        webrtc_url: URL para visualización WebRTC
        
    Returns:
        Mensaje de evento formateado
    """
    # También emitir a través del sistema WebSocket global
    try:
        from api.websocket_events import emit_remote_publication_started
        import asyncio
        asyncio.create_task(emit_remote_publication_started(
            camera_id=camera_id,
            server_id=server_id,
            publish_url=publish_url,
            webrtc_url=webrtc_url
        ))
    except Exception:
        pass
    
    return create_remote_publication_event(
        event_type=EventType.REMOTE_PUBLICATION_STARTED,
        camera_id=camera_id,
        server_id=server_id,
        server_name=server_name,
        title=f"Publicación iniciada en {server_name}",
        severity="info",
        description=f"La cámara {camera_id} comenzó a publicar en el servidor remoto",
        additional_data={
            "publish_url": publish_url,
            "webrtc_url": webrtc_url,
            "status": "active"
        }
    )


def remote_publication_stopped(
    camera_id: str,
    server_id: int,
    server_name: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evento cuando se detiene una publicación remota.
    
    Args:
        camera_id: ID de la cámara
        server_id: ID del servidor
        server_name: Nombre del servidor
        reason: Razón de la detención (opcional)
        
    Returns:
        Mensaje de evento formateado
    """
    description = f"La publicación de {camera_id} se detuvo"
    if reason:
        description += f": {reason}"
    
    return create_remote_publication_event(
        event_type=EventType.REMOTE_PUBLICATION_STOPPED,
        camera_id=camera_id,
        server_id=server_id,
        server_name=server_name,
        title=f"Publicación detenida en {server_name}",
        severity="warning",
        description=description,
        additional_data={
            "status": "stopped",
            "reason": reason
        }
    )


def remote_publication_error(
    camera_id: str,
    server_id: int,
    server_name: str,
    error_code: str,
    error_message: str,
    recoverable: bool = True
) -> Dict[str, Any]:
    """
    Evento de error en publicación remota.
    
    Args:
        camera_id: ID de la cámara
        server_id: ID del servidor
        server_name: Nombre del servidor
        error_code: Código de error
        error_message: Mensaje de error
        recoverable: Si el error es recuperable
        
    Returns:
        Mensaje de evento formateado
    """
    return create_remote_publication_event(
        event_type=EventType.REMOTE_PUBLICATION_ERROR,
        camera_id=camera_id,
        server_id=server_id,
        server_name=server_name,
        title=f"Error de publicación en {server_name}",
        severity="error",
        description=error_message,
        additional_data={
            "error_code": error_code,
            "recoverable": recoverable,
            "status": "error"
        }
    )


def remote_server_connected(
    server_id: int,
    server_name: str,
    api_url: str,
    authenticated: bool = False
) -> Dict[str, Any]:
    """
    Evento cuando se conecta exitosamente con un servidor remoto.
    
    Args:
        server_id: ID del servidor
        server_name: Nombre del servidor
        api_url: URL de la API
        authenticated: Si está autenticado
        
    Returns:
        Mensaje de evento formateado
    """
    return create_event_message(
        event_type=EventType.REMOTE_SERVER_CONNECTED,
        source=f"server_{server_id}",
        title=f"Conectado con servidor {server_name}",
        severity="info",
        description=f"Conexión establecida con {api_url}",
        data={
            "server_id": server_id,
            "server_name": server_name,
            "api_url": api_url,
            "authenticated": authenticated,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def remote_server_disconnected(
    server_id: int,
    server_name: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evento cuando se pierde conexión con un servidor remoto.
    
    Args:
        server_id: ID del servidor
        server_name: Nombre del servidor
        reason: Razón de la desconexión
        
    Returns:
        Mensaje de evento formateado
    """
    description = f"Se perdió la conexión con {server_name}"
    if reason:
        description += f": {reason}"
    
    return create_event_message(
        event_type=EventType.REMOTE_SERVER_DISCONNECTED,
        source=f"server_{server_id}",
        title=f"Desconectado de {server_name}",
        severity="warning",
        description=description,
        data={
            "server_id": server_id,
            "server_name": server_name,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    )