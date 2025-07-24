"""
Router WebSocket para eventos de publicación en tiempo real.

Expone el endpoint /ws/publishing para comunicación bidireccional
con el frontend sobre el estado de publicaciones y métricas.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import logging
import json
from datetime import datetime

from websocket.handlers.publishing_handler import get_publishing_ws_handler
from websocket.connection_manager import manager
from services.logging_service import get_secure_logger


logger = get_secure_logger("api.routers.publishing_websocket")
router = APIRouter()


@router.websocket("/publishing")
async def publishing_websocket(websocket: WebSocket):
    """
    WebSocket endpoint para eventos de publicación.
    
    Permite a los clientes:
    - Suscribirse a eventos de publicación de cámaras específicas
    - Recibir actualizaciones de estado en tiempo real
    - Recibir métricas de streaming
    - Controlar publicaciones remotamente
    
    Protocolo de mensajes compatible con el handler existente:
    - Cliente -> Servidor:
      {
        "type": "subscribe_camera",
        "camera_id": "cam-192-168-1-100"
      }
      
      {
        "type": "start_publishing",
        "camera_id": "cam-192-168-1-100",
        "force_restart": false
      }
      
    - Servidor -> Cliente:
      {
        "type": "subscribed",
        "camera_id": "cam-192-168-1-100",
        "current_status": { ... },
        "timestamp": "2025-01-24T01:00:00Z"
      }
    """
    # Generar ID de cliente
    client_id = str(id(websocket))
    
    # Conectar al manager (esto acepta la conexión)
    connection = await manager.connect(websocket, client_id)
    
    logger.info(f"Cliente WebSocket conectado para publicación: {client_id}")
    
    try:
        # Obtener handler de publicación
        handler = get_publishing_ws_handler()
        
        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Conectado al servicio de publicación",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Procesar mensajes del cliente
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Delegar procesamiento al handler
                response = await handler.handle_message(client_id, message)
                
                if response:
                    await websocket.send_json(response)
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "Mensaje JSON inválido",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            except Exception as e:
                logger.error(f"Error procesando mensaje WebSocket: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "error": "Error procesando mensaje",
                    "details": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
                
    except WebSocketDisconnect:
        logger.info(f"Cliente WebSocket desconectado: {client_id}")
        
    except Exception as e:
        logger.error(f"Error en WebSocket de publicación: {str(e)}")
        
    finally:
        # Limpiar suscripciones
        try:
            await handler.handle_client_disconnect(client_id)
        except:
            pass
            
        # Desconectar del manager
        await manager.disconnect(client_id)


