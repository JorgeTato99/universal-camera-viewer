"""
Router para endpoints WebSocket de streaming.
"""

import logging
import uuid
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from datetime import datetime

from websocket.connection_manager import manager
from websocket.stream_handler import stream_manager
from api.dependencies import create_response
from api.dependencies.rate_limit import rate_limit, websocket_rate_limit

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    tags=["websocket"],
    responses={404: {"description": "Stream no encontrado"}}
)


# === HTTP Endpoints para información de streams ===

@router.get("/streams")
async def get_active_streams():
    """
    Obtener información de todos los streams activos.
    
    Returns:
        Lista de streams activos con sus métricas
    """
    stats = stream_manager.get_stream_stats()
    
    return create_response(
        success=True,
        data=stats
    )


@router.get("/streams/{camera_id}")
async def get_camera_stream_info(camera_id: str):
    """
    Obtener información de streams activos para una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Información de streams de la cámara
    """
    stats = stream_manager.get_stream_stats()
    
    if camera_id not in stats["cameras"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay streams activos para la cámara {camera_id}"
        )
    
    return create_response(
        success=True,
        data={
            "camera_id": camera_id,
            "stream_info": stats["cameras"][camera_id]
        }
    )


@router.get("/ws/status")
async def get_websocket_status():
    """
    Obtener estado de las conexiones WebSocket.
    
    Returns:
        Estadísticas del ConnectionManager
    """
    stats = manager.get_stats()
    
    return create_response(
        success=True,
        data=stats
    )


# === WebSocket Endpoints ===

@router.websocket("/stream/{camera_id}")
@websocket_rate_limit("websocket_connect")  # 20/hour - limitar nuevas conexiones WS
async def websocket_stream(websocket: WebSocket, camera_id: str):
    """
    WebSocket endpoint para streaming de video de una cámara.
    
    Args:
        websocket: Conexión WebSocket
        camera_id: ID de la cámara a transmitir
        
    Protocolo de mensajes:
    
    Cliente → Servidor:
    ```json
    {
        "action": "start_stream",
        "params": {
            "quality": "high",
            "fps": 30,
            "format": "jpeg"
        }
    }
    ```
    
    Servidor → Cliente:
    ```json
    {
        "type": "frame",
        "camera_id": "cam_123",
        "data": "base64...",
        "timestamp": "2025-07-14T10:00:00Z",
        "frame_number": 1234,
        "metrics": {
            "fps": 29.5,
            "quality": "high"
        }
    }
    ```
    """
    # Generar ID único para el cliente
    client_id = f"client_{uuid.uuid4()}"
    
    logger.info(f"Nueva conexión WebSocket: {client_id} para cámara {camera_id}")
    
    try:
        # Manejar conexión de streaming
        await stream_manager.handle_stream_connection(websocket, camera_id, client_id)
        
    except WebSocketDisconnect:
        logger.info(f"Cliente {client_id} desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket stream: {e}")
    finally:
        # Asegurar limpieza
        await stream_manager.cleanup_stream(camera_id, client_id)


@router.websocket("/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint para eventos del sistema.
    
    Args:
        websocket: Conexión WebSocket
        
    Eventos enviados:
    - camera_connected
    - camera_disconnected
    - scan_progress
    - system_alert
    """
    # Generar ID único para el cliente
    client_id = f"events_{uuid.uuid4()}"
    
    logger.info(f"Nueva conexión a eventos: {client_id}")
    
    try:
        # Conectar cliente
        connection = await manager.connect(websocket, client_id)
        
        # Unir a sala de eventos globales
        await manager.join_room(client_id, "system_events")
        
        # Enviar evento de bienvenida
        await connection.send_json({
            "type": "system",
            "event": "connected",
            "message": "Conectado a eventos del sistema",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Mantener conexión abierta
        while True:
            # Esperar mensajes del cliente (principalmente ping/pong)
            data = await websocket.receive_json()
            
            # Responder a ping
            if data.get("type") == "ping":
                await connection.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            
    except WebSocketDisconnect:
        logger.info(f"Cliente de eventos {client_id} desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket events: {e}")
    finally:
        await manager.disconnect(client_id)


@router.websocket("/scanner")
async def websocket_scanner(websocket: WebSocket):
    """
    WebSocket endpoint para actualizaciones de escaneo en tiempo real.
    
    Args:
        websocket: Conexión WebSocket
        
    Mensajes enviados:
    - scan_started
    - scan_progress
    - camera_found
    - scan_completed
    """
    # Generar ID único para el cliente
    client_id = f"scanner_{uuid.uuid4()}"
    
    logger.info(f"Nueva conexión a scanner: {client_id}")
    
    try:
        # Conectar cliente
        connection = await manager.connect(websocket, client_id)
        
        # Unir a sala de scanner
        await manager.join_room(client_id, "scanner_updates")
        
        # Enviar estado inicial
        await connection.send_json({
            "type": "scanner",
            "status": "connected",
            "message": "Conectado a actualizaciones del scanner",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Simular actualizaciones de escaneo
        import asyncio
        scan_active = True
        cameras_found = 0
        
        # Loop de simulación
        for i in range(254):
            if not scan_active:
                break
                
            # Simular progreso
            progress = (i + 1) / 254
            
            # Enviar actualización de progreso
            await connection.send_json({
                "type": "scan_progress",
                "progress": progress,
                "current_ip": f"192.168.1.{i+1}",
                "ips_scanned": i + 1,
                "total_ips": 254,
                "cameras_found": cameras_found,
                "message": f"Escaneando 192.168.1.{i+1}...",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            # Simular encontrar cámaras
            if i in [99, 100, 101]:  # IPs donde "encontramos" cámaras
                cameras_found += 1
                await connection.send_json({
                    "type": "camera_found",
                    "camera": {
                        "ip": f"192.168.1.{i+1}",
                        "brand": ["Dahua", "TP-Link", "Steren"][cameras_found - 1],
                        "model": "Mock Camera",
                        "protocol": "ONVIF"
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            
            # Esperar un poco para simular tiempo de escaneo
            await asyncio.sleep(0.05)
            
            # Verificar si el cliente envió algo (como stop)
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                if data.get("action") == "stop_scan":
                    scan_active = False
                    await connection.send_json({
                        "type": "scan_stopped",
                        "message": "Escaneo detenido por el usuario",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
            except asyncio.TimeoutError:
                pass  # No hay mensajes, continuar
        
        # Enviar resultado final
        if scan_active:
            await connection.send_json({
                "type": "scan_completed",
                "total_scanned": 254,
                "cameras_found": cameras_found,
                "message": "Escaneo completado exitosamente",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        
    except WebSocketDisconnect:
        logger.info(f"Cliente scanner {client_id} desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket scanner: {e}")
    finally:
        await manager.disconnect(client_id)


# === Funciones auxiliares para emitir eventos ===

async def emit_camera_event(event_type: str, camera_data: Dict[str, Any]):
    """
    Emitir evento relacionado con cámaras a todos los clientes suscritos.
    
    Args:
        event_type: Tipo de evento (connected, disconnected, etc.)
        camera_data: Datos de la cámara
    """
    message = {
        "type": "camera_event",
        "event": event_type,
        "data": camera_data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    await manager.broadcast(message, room="system_events")


async def emit_system_alert(alert_type: str, message: str, severity: str = "info"):
    """
    Emitir alerta del sistema.
    
    Args:
        alert_type: Tipo de alerta
        message: Mensaje de la alerta
        severity: Severidad (info, warning, error)
    """
    alert = {
        "type": "system_alert",
        "alert_type": alert_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    await manager.broadcast(alert, room="system_events")