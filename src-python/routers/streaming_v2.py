"""
Router para endpoints WebSocket de streaming V2.

Version actualizada con schemas de validación para mensajes WebSocket.
"""

import logging
import uuid
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Query
from datetime import datetime

from api.schemas.websocket.ws_messages import (
    WSMessageType,
    WSClientMessage,
    StartStreamRequest,
    PTZCommandRequest,
    validate_ws_message,
    create_frame_message,
    create_event_message,
    create_error_message,
    StreamFormat,
    EventType
)
from websocket.connection_manager import manager
from websocket.stream_handler import stream_manager
from api.dependencies import create_response

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    tags=["websocket", "streaming"],
    responses={404: {"description": "Stream no encontrado"}}
)


# === HTTP Endpoints para información de streams ===

@router.get("/streams")
async def get_active_streams(
    include_metrics: bool = True,
    camera_id: Optional[str] = None
):
    """
    Obtener información de todos los streams activos.
    
    Args:
        include_metrics: Incluir métricas detalladas
        camera_id: Filtrar por cámara específica
    
    Returns:
        Lista de streams activos con sus métricas
    """
    try:
        stats = stream_manager.get_stream_stats()
        
        # Filtrar por cámara si se especifica
        if camera_id:
            if camera_id in stats.get("cameras", {}):
                stats["cameras"] = {camera_id: stats["cameras"][camera_id]}
            else:
                stats["cameras"] = {}
        
        # Excluir métricas si no se solicitan
        if not include_metrics:
            for cam_id in stats.get("cameras", {}):
                if "metrics" in stats["cameras"][cam_id]:
                    del stats["cameras"][cam_id]["metrics"]
        
        return create_response(
            success=True,
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo streams activos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/streams/{camera_id}")
async def get_camera_stream_info(camera_id: str):
    """
    Obtener información de streams activos para una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Información detallada del stream de la cámara
    """
    try:
        stats = stream_manager.get_stream_stats()
        
        if camera_id not in stats.get("cameras", {}):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No hay streams activos para la cámara {camera_id}"
            )
        
        camera_info = stats["cameras"][camera_id]
        
        # Enriquecer información
        response_data = {
            "camera_id": camera_id,
            "is_streaming": camera_info.get("is_active", False),
            "clients_connected": camera_info.get("clients", 0),
            "start_time": camera_info.get("start_time"),
            "duration_seconds": camera_info.get("duration", 0),
            "current_quality": camera_info.get("quality", "unknown"),
            "metrics": camera_info.get("metrics", {})
        }
        
        return create_response(
            success=True,
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo info de stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/streams/{camera_id}/snapshot")
async def capture_snapshot(
    camera_id: str,
    quality: int = Query(85, ge=1, le=100, description="Calidad JPEG")
):
    """
    Capturar un snapshot del stream actual.
    
    Args:
        camera_id: ID de la cámara
        quality: Calidad JPEG (1-100)
        
    Returns:
        URL o datos del snapshot
    """
    try:
        # TODO: Implementar captura real de snapshot
        # Por ahora devolver respuesta de ejemplo
        
        snapshot_id = f"snap_{uuid.uuid4()}"
        
        return create_response(
            success=True,
            data={
                "snapshot_id": snapshot_id,
                "camera_id": camera_id,
                "timestamp": datetime.utcnow().isoformat(),
                "quality": quality,
                "format": "jpeg",
                "size_bytes": 145678,
                "url": f"/api/snapshots/{snapshot_id}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error capturando snapshot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error capturando snapshot"
        )


@router.get("/ws/status")
async def get_websocket_status():
    """
    Obtener estado de las conexiones WebSocket.
    
    Returns:
        Estadísticas del ConnectionManager
    """
    try:
        stats = manager.get_stats()
        
        # Agregar información adicional
        stats["server_time"] = datetime.utcnow().isoformat()
        stats["supported_formats"] = [f.value for f in StreamFormat]
        stats["max_connections_per_camera"] = 10  # TODO: Obtener de config
        
        return create_response(
            success=True,
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estado WebSocket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# === WebSocket Endpoints ===

@router.websocket("/stream/{camera_id}")
async def websocket_stream(websocket: WebSocket, camera_id: str):
    """
    WebSocket endpoint para streaming de video de una cámara.
    
    Args:
        websocket: Conexión WebSocket
        camera_id: ID de la cámara a transmitir
        
    Protocolo de mensajes con validación usando schemas.
    """
    # Generar ID único para el cliente
    client_id = f"client_{uuid.uuid4()}"
    
    logger.info(f"Nueva conexión WebSocket: {client_id} para cámara {camera_id}")
    
    # Aceptar conexión
    await websocket.accept()
    
    # Registrar cliente
    await manager.connect(websocket, client_id)
    
    try:
        # Enviar mensaje de bienvenida
        welcome_msg = {
            "type": "connection",
            "data": {
                "client_id": client_id,
                "camera_id": camera_id,
                "status": "connected",
                "supported_actions": [action.value for action in WSMessageType]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_json(welcome_msg)
        
        # Loop principal de mensajes
        while True:
            # Recibir mensaje
            try:
                raw_message = await websocket.receive_text()
                message_data = json.loads(raw_message)
            except json.JSONDecodeError:
                error_msg = create_error_message(
                    error_code="INVALID_JSON",
                    message="Mensaje JSON inválido",
                    recoverable=True
                )
                await websocket.send_json(error_msg)
                continue
            
            # Validar mensaje
            client_msg = validate_ws_message(message_data)
            if not client_msg:
                error_msg = create_error_message(
                    error_code="INVALID_MESSAGE",
                    message="Estructura de mensaje inválida",
                    details={"received": message_data},
                    recoverable=True
                )
                await websocket.send_json(error_msg)
                continue
            
            # Procesar acción
            try:
                await _handle_client_action(
                    websocket, client_id, camera_id, client_msg
                )
            except Exception as e:
                logger.error(f"Error procesando acción {client_msg.action}: {e}")
                error_msg = create_error_message(
                    error_code="ACTION_FAILED",
                    message=f"Error procesando acción: {str(e)}",
                    request_id=client_msg.request_id,
                    recoverable=True
                )
                await websocket.send_json(error_msg)
                
    except WebSocketDisconnect:
        logger.info(f"Cliente {client_id} desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket stream: {e}")
        try:
            error_msg = create_error_message(
                error_code="INTERNAL_ERROR",
                message="Error interno del servidor",
                recoverable=False
            )
            await websocket.send_json(error_msg)
        except:
            pass
    finally:
        # Asegurar limpieza
        await manager.disconnect(client_id)
        await stream_manager.cleanup_stream(camera_id, client_id)


async def _handle_client_action(
    websocket: WebSocket,
    client_id: str,
    camera_id: str,
    message: WSClientMessage
):
    """
    Maneja las acciones del cliente.
    
    Args:
        websocket: Conexión WebSocket
        client_id: ID del cliente
        camera_id: ID de la cámara
        message: Mensaje del cliente
    """
    action = message.action
    params = message.params or {}
    
    if action == WSMessageType.START_STREAM:
        # Validar parámetros de stream
        try:
            stream_params = StartStreamRequest(**params)
        except Exception as e:
            raise ValueError(f"Parámetros de stream inválidos: {e}")
        
        # Iniciar stream
        success = await stream_manager.start_stream(
            camera_id=camera_id,
            client_id=client_id,
            quality=stream_params.quality,
            fps=stream_params.fps,
            format=stream_params.format.value,
            resolution=stream_params.resolution,
            audio=stream_params.audio
        )
        
        # Enviar confirmación
        response = {
            "type": "stream_status",
            "data": {
                "camera_id": camera_id,
                "status": "started" if success else "failed",
                "quality": stream_params.quality,
                "format": stream_params.format.value
            },
            "request_id": message.request_id
        }
        await websocket.send_json(response)
        
    elif action == WSMessageType.STOP_STREAM:
        # Detener stream
        await stream_manager.stop_stream(camera_id, client_id)
        
        response = {
            "type": "stream_status",
            "data": {
                "camera_id": camera_id,
                "status": "stopped"
            },
            "request_id": message.request_id
        }
        await websocket.send_json(response)
        
    elif action == WSMessageType.PAUSE_STREAM:
        # Pausar stream
        await stream_manager.pause_stream(camera_id, client_id)
        
        response = {
            "type": "stream_status",
            "data": {
                "camera_id": camera_id,
                "status": "paused"
            },
            "request_id": message.request_id
        }
        await websocket.send_json(response)
        
    elif action == WSMessageType.RESUME_STREAM:
        # Reanudar stream
        await stream_manager.resume_stream(camera_id, client_id)
        
        response = {
            "type": "stream_status",
            "data": {
                "camera_id": camera_id,
                "status": "resumed"
            },
            "request_id": message.request_id
        }
        await websocket.send_json(response)
        
    elif action == WSMessageType.PTZ_COMMAND:
        # Validar comando PTZ
        try:
            ptz_cmd = PTZCommandRequest(**params)
        except Exception as e:
            raise ValueError(f"Comando PTZ inválido: {e}")
        
        # TODO: Ejecutar comando PTZ real
        response = {
            "type": "ptz_response",
            "data": {
                "camera_id": camera_id,
                "action": ptz_cmd.action.value,
                "status": "executed"
            },
            "request_id": message.request_id
        }
        await websocket.send_json(response)
        
    elif action == WSMessageType.PING:
        # Responder con PONG
        response = {
            "type": "pong",
            "data": {
                "client_time": message.timestamp.isoformat(),
                "server_time": datetime.utcnow().isoformat()
            },
            "request_id": message.request_id
        }
        await websocket.send_json(response)
        
    else:
        raise ValueError(f"Acción no soportada: {action}")


@router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint para eventos del sistema.
    
    Args:
        websocket: Conexión WebSocket
        
    Envía eventos en tiempo real sobre el estado del sistema.
    """
    client_id = f"events_{uuid.uuid4()}"
    
    logger.info(f"Nueva conexión de eventos: {client_id}")
    
    # Aceptar conexión
    await websocket.accept()
    
    # Registrar cliente para eventos
    await manager.connect(websocket, client_id, is_event_client=True)
    
    try:
        # Enviar evento de conexión
        connect_event = create_event_message(
            event_type=EventType.CONNECTION_RESTORED,
            source="system",
            title="Conectado al stream de eventos",
            severity="info",
            data={"client_id": client_id}
        )
        await websocket.send_json(connect_event)
        
        # Mantener conexión viva
        while True:
            # Esperar mensajes del cliente (principalmente PING)
            try:
                raw_message = await websocket.receive_text()
                message_data = json.loads(raw_message)
                
                # Solo procesar PING
                if message_data.get("action") == "ping":
                    pong_response = {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_json(pong_response)
                    
            except json.JSONDecodeError:
                # Ignorar mensajes inválidos en eventos
                pass
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info(f"Cliente de eventos {client_id} desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket eventos: {e}")
    finally:
        await manager.disconnect(client_id)


@router.websocket("/control")
async def websocket_control(websocket: WebSocket):
    """
    WebSocket endpoint para control remoto de cámaras.
    
    Args:
        websocket: Conexión WebSocket
        
    Permite control PTZ y configuración en tiempo real.
    """
    client_id = f"control_{uuid.uuid4()}"
    
    logger.info(f"Nueva conexión de control: {client_id}")
    
    # Aceptar conexión
    await websocket.accept()
    
    # Verificar permisos (TODO: Implementar autenticación)
    
    try:
        # Enviar capacidades de control
        capabilities = {
            "type": "control_capabilities",
            "data": {
                "ptz_enabled": True,
                "audio_control": True,
                "recording_control": True,
                "supported_commands": [
                    "ptz", "audio", "recording", "snapshot", "preset"
                ]
            }
        }
        await websocket.send_json(capabilities)
        
        # Procesar comandos de control
        while True:
            raw_message = await websocket.receive_text()
            
            try:
                message_data = json.loads(raw_message)
                client_msg = validate_ws_message(message_data)
                
                if not client_msg:
                    continue
                
                # Procesar comando de control
                # TODO: Implementar lógica real de control
                
                response = {
                    "type": "control_response",
                    "data": {
                        "action": client_msg.action.value,
                        "status": "executed",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    "request_id": client_msg.request_id
                }
                await websocket.send_json(response)
                
            except Exception as e:
                logger.error(f"Error procesando comando de control: {e}")
                error_msg = create_error_message(
                    error_code="CONTROL_ERROR",
                    message=str(e),
                    recoverable=True
                )
                await websocket.send_json(error_msg)
                
    except WebSocketDisconnect:
        logger.info(f"Cliente de control {client_id} desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket control: {e}")
    finally:
        # Limpiar recursos de control
        pass