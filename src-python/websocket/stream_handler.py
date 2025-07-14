"""
Manejador de streaming de video por WebSocket.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import base64
import numpy as np
import cv2

from fastapi import WebSocket
from .connection_manager import manager, WebSocketConnection

logger = logging.getLogger(__name__)


class StreamHandler:
    """Maneja streaming de video para una cámara específica."""
    
    def __init__(self, camera_id: str, websocket: WebSocket, client_id: str):
        self.camera_id = camera_id
        self.websocket = websocket
        self.client_id = client_id
        self.connection = manager.get_connection(client_id)
        
        # Estado del stream
        self.is_streaming = False
        self.quality = "medium"
        self.fps = 30
        self.format = "jpeg"
        
        # Métricas
        self.frame_count = 0
        self.start_time = None
        self.last_frame_time = None
        
        # Control de FPS
        self.frame_interval = 1.0 / self.fps
        self.last_sent_time = 0
        
    async def handle_message(self, message: dict) -> None:
        """
        Procesar mensaje recibido del cliente.
        
        Args:
            message: Mensaje JSON del cliente
        """
        action = message.get("action")
        params = message.get("params", {})
        
        logger.info(f"Stream handler recibió: {action} para cámara {self.camera_id}")
        
        if action == "start_stream":
            await self.start_stream(params)
        elif action == "stop_stream":
            await self.stop_stream()
        elif action == "update_quality":
            await self.update_quality(params.get("quality", "medium"))
        elif action == "update_fps":
            await self.update_fps(params.get("fps", 30))
        else:
            await self.send_error(f"Acción desconocida: {action}")
    
    async def start_stream(self, params: Dict[str, Any]) -> None:
        """
        Iniciar streaming de video.
        
        Args:
            params: Parámetros del stream
        """
        if self.is_streaming:
            await self.send_status("already_streaming")
            return
        
        # Configurar parámetros
        self.quality = params.get("quality", "medium")
        self.fps = params.get("fps", 30)
        self.format = params.get("format", "jpeg")
        self.frame_interval = 1.0 / self.fps
        
        # Iniciar streaming
        self.is_streaming = True
        self.start_time = datetime.utcnow()
        self.frame_count = 0
        
        await self.send_status("stream_started")
        
        # Iniciar loop de streaming
        asyncio.create_task(self.stream_loop())
        
        logger.info(f"Stream iniciado: {self.camera_id} - {self.quality} @ {self.fps}fps")
    
    async def stop_stream(self) -> None:
        """Detener streaming de video."""
        if not self.is_streaming:
            await self.send_status("not_streaming")
            return
        
        self.is_streaming = False
        await self.send_status("stream_stopped")
        
        logger.info(f"Stream detenido: {self.camera_id}")
    
    async def update_quality(self, quality: str) -> None:
        """
        Actualizar calidad del stream.
        
        Args:
            quality: Nueva calidad (low, medium, high)
        """
        if quality not in ["low", "medium", "high"]:
            await self.send_error("Calidad inválida")
            return
        
        self.quality = quality
        await self.send_status("quality_updated", {"quality": quality})
        
        logger.info(f"Calidad actualizada: {self.camera_id} - {quality}")
    
    async def update_fps(self, fps: int) -> None:
        """
        Actualizar FPS del stream.
        
        Args:
            fps: Nuevos FPS (1-60)
        """
        if not 1 <= fps <= 60:
            await self.send_error("FPS debe estar entre 1 y 60")
            return
        
        self.fps = fps
        self.frame_interval = 1.0 / fps
        await self.send_status("fps_updated", {"fps": fps})
        
        logger.info(f"FPS actualizado: {self.camera_id} - {fps}")
    
    async def stream_loop(self) -> None:
        """Loop principal de streaming."""
        try:
            while self.is_streaming and self.connection:
                # Generar frame simulado
                frame = await self.generate_mock_frame()
                
                # Control de FPS
                current_time = asyncio.get_event_loop().time()
                time_since_last = current_time - self.last_sent_time
                
                if time_since_last < self.frame_interval:
                    await asyncio.sleep(self.frame_interval - time_since_last)
                
                # Enviar frame
                await self.send_frame(frame)
                
                self.last_sent_time = asyncio.get_event_loop().time()
                self.frame_count += 1
                
        except Exception as e:
            logger.error(f"Error en stream loop: {e}")
            self.is_streaming = False
            await self.send_error(f"Error en streaming: {str(e)}")
    
    async def generate_mock_frame(self) -> str:
        """
        Generar frame simulado para testing.
        
        Returns:
            Frame en base64
        """
        # Crear imagen con OpenCV
        height = 480 if self.quality == "low" else (720 if self.quality == "medium" else 1080)
        width = int(height * 16 / 9)
        
        # Crear imagen con patrón
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Color de fondo que cambia
        hue = (self.frame_count * 2) % 180
        img[:] = cv2.cvtColor(
            np.array([[[hue, 255, 255]]], dtype=np.uint8), 
            cv2.COLOR_HSV2BGR
        )[0][0]
        
        # Agregar texto
        text = f"Camera: {self.camera_id}"
        cv2.putText(img, text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        text = f"Frame: {self.frame_count}"
        cv2.putText(img, text, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        
        text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        cv2.putText(img, text, (50, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Codificar a base64
        if self.format == "jpeg":
            quality = 60 if self.quality == "low" else (80 if self.quality == "medium" else 95)
            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        else:  # png
            _, buffer = cv2.imencode('.png', img)
        
        return base64.b64encode(buffer).decode('utf-8')
    
    async def send_frame(self, frame_data: str) -> None:
        """
        Enviar frame al cliente.
        
        Args:
            frame_data: Frame en base64
        """
        metrics = self.calculate_metrics()
        
        message = {
            "type": "frame",
            "camera_id": self.camera_id,
            "data": frame_data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "frame_number": self.frame_count,
            "metrics": metrics
        }
        
        await self.connection.send_json(message)
    
    async def send_status(self, status: str, data: Optional[Dict] = None) -> None:
        """
        Enviar estado al cliente.
        
        Args:
            status: Estado a enviar
            data: Datos adicionales opcionales
        """
        message = {
            "type": "status",
            "camera_id": self.camera_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if data:
            message["data"] = data
        
        await self.connection.send_json(message)
    
    async def send_error(self, error: str) -> None:
        """
        Enviar error al cliente.
        
        Args:
            error: Mensaje de error
        """
        message = {
            "type": "error",
            "camera_id": self.camera_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        await self.connection.send_json(message)
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calcular métricas del stream.
        
        Returns:
            Diccionario con métricas
        """
        if not self.start_time:
            return {}
        
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        actual_fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        return {
            "fps": round(actual_fps, 1),
            "target_fps": self.fps,
            "quality": self.quality,
            "format": self.format,
            "frames_sent": self.frame_count,
            "uptime_seconds": round(elapsed, 1)
        }


class StreamManager:
    """Gestor global de streams activos."""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, StreamHandler]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def handle_stream_connection(
        self, 
        websocket: WebSocket, 
        camera_id: str, 
        client_id: str
    ) -> None:
        """
        Manejar nueva conexión de streaming.
        
        Args:
            websocket: WebSocket de FastAPI
            camera_id: ID de la cámara
            client_id: ID del cliente
        """
        # Conectar cliente
        connection = await manager.connect(websocket, client_id)
        
        # Unir a sala de la cámara
        await manager.join_room(client_id, f"camera_{camera_id}")
        
        # Crear handler
        handler = StreamHandler(camera_id, websocket, client_id)
        
        # Registrar stream
        if camera_id not in self.active_streams:
            self.active_streams[camera_id] = {}
        self.active_streams[camera_id][client_id] = handler
        
        self.logger.info(f"Cliente {client_id} conectado a stream de {camera_id}")
        
        try:
            # Loop de mensajes
            while True:
                # Recibir mensaje
                data = await websocket.receive_json()
                
                # Procesar mensaje
                await handler.handle_message(data)
                
        except Exception as e:
            self.logger.error(f"Error en conexión de stream: {e}")
        finally:
            # Limpiar al desconectar
            await self.cleanup_stream(camera_id, client_id)
    
    async def cleanup_stream(self, camera_id: str, client_id: str) -> None:
        """
        Limpiar stream al desconectar.
        
        Args:
            camera_id: ID de la cámara
            client_id: ID del cliente
        """
        # Detener stream si está activo
        if camera_id in self.active_streams:
            if client_id in self.active_streams[camera_id]:
                handler = self.active_streams[camera_id][client_id]
                if handler.is_streaming:
                    await handler.stop_stream()
                
                del self.active_streams[camera_id][client_id]
                
                # Eliminar diccionario de cámara si está vacío
                if not self.active_streams[camera_id]:
                    del self.active_streams[camera_id]
        
        # Desconectar del manager
        await manager.disconnect(client_id)
        
        self.logger.info(f"Cliente {client_id} desconectado de stream {camera_id}")
    
    def get_stream_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de streams activos.
        
        Returns:
            Estadísticas de streams
        """
        stats = {
            "active_cameras": len(self.active_streams),
            "total_clients": sum(len(clients) for clients in self.active_streams.values()),
            "cameras": {}
        }
        
        for camera_id, clients in self.active_streams.items():
            stats["cameras"][camera_id] = {
                "client_count": len(clients),
                "clients": []
            }
            
            for client_id, handler in clients.items():
                if handler.is_streaming:
                    stats["cameras"][camera_id]["clients"].append({
                        "client_id": client_id,
                        "metrics": handler.calculate_metrics()
                    })
        
        return stats


# Instancia global del stream manager
stream_manager = StreamManager()