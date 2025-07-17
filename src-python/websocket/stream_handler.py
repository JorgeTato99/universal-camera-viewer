"""
Manejador de streaming de video por WebSocket.

Este handler se encarga únicamente de la comunicación WebSocket,
delegando toda la lógica de negocio al servicio correspondiente.
"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, Optional
from datetime import datetime
import base64
import numpy as np
import cv2

from fastapi import WebSocket
from .connection_manager import manager, WebSocketConnection
from services.websocket_stream_service import websocket_stream_service
from models.streaming.stream_metrics import StreamMetrics

logger = logging.getLogger(__name__)


class StreamHandler:
    """
    Manejador de streaming de video para una cámara específica.
    
    Este handler actúa como un puente entre el WebSocket y el servicio
    de streaming, sin contener lógica de negocio.
    """
    
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
        
        # Modelo de métricas avanzadas
        self.metrics = StreamMetrics(stream_id=f"{camera_id}_{client_id}")
        
        # Control de FPS para frames simulados
        self.frame_interval = 1.0 / self.fps
        self.last_sent_time = 0
        
        # El servicio se inicializará cuando sea necesario
        self._service_initialized = False
        
    async def handle_message(self, message: dict) -> None:
        """
        Procesar mensaje recibido del cliente.
        
        Args:
            message: Mensaje JSON del cliente
        """
        logger.debug(f"[{self.camera_id}] Message received: {message}")
        action = message.get("action")
        params = message.get("params", {})
        
        logger.debug(f"[{self.camera_id}] Action: {action}, Params: {params}")
        
        # Manejar mensajes de heartbeat
        if message.get("type") == "ping":
            await self.send_pong()
            return
            
        if action == "start_stream":
            await self.start_stream(params)
        elif action == "stop_stream":
            await self.stop_stream()
        elif action == "update_quality":
            await self.update_quality(params.get("quality", "medium"))
        elif action == "update_fps":
            await self.update_fps(params.get("fps", 30))
        elif action is None:
            # Ignore messages without action (like ping already handled above)
            logger.debug(f"[{self.camera_id}] Message without action, ignoring")
        else:
            await self.send_error(f"Unrecognized action: {action}")
    
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
        
        logger.info(f"[{self.camera_id}] Stream started: {self.quality} @ {self.fps}fps")
    
    async def stop_stream(self) -> None:
        """Detener streaming de video."""
        if not self.is_streaming:
            await self.send_status("not_streaming")
            return
        
        self.is_streaming = False
        await self.send_status("stream_stopped")
        
        logger.info(f"[{self.camera_id}] Stream stopped")
    
    async def update_quality(self, quality: str) -> None:
        """
        Actualizar calidad del stream.
        
        Args:
            quality: Nueva calidad (low, medium, high)
        """
        if quality not in ["low", "medium", "high"]:
            await self.send_error("Invalid quality")
            return
        
        self.quality = quality
        await self.send_status("quality_updated", {"quality": quality})
        
        logger.info(f"[{self.camera_id}] Quality updated: {quality}")
    
    async def update_fps(self, fps: int) -> None:
        """
        Actualizar FPS del stream.
        
        Args:
            fps: Nuevos FPS (1-60)
        """
        if not 1 <= fps <= 60:
            await self.send_error("FPS must be between 1 and 60")
            return
        
        self.fps = fps
        self.frame_interval = 1.0 / fps
        await self.send_status("fps_updated", {"fps": fps})
        
        logger.info(f"[{self.camera_id}] FPS updated: {fps}")
    
    async def stream_loop(self) -> None:
        """Loop principal de streaming."""
        try:
            # Inicializar servicio si no está inicializado
            if not self._service_initialized:
                await self._initialize_service()
            
            # Intentar streaming real
            success = await self._try_real_stream()
            if success:
                return
            
            # Si no es posible, usar frames simulados
            logger.info(f"[{self.camera_id}] Usando frames simulados")
            await self._run_mock_stream()
                
        except Exception as e:
            logger.error(f"[{self.camera_id}] Error en stream loop: {e}")
            self.is_streaming = False
            await self.send_error(f"Streaming error: {str(e)}")
    
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
    
    async def send_frame(self, frame_data: str, capture_timestamp: Optional[float] = None) -> None:
        """
        Enviar frame al cliente.
        
        Args:
            frame_data: Frame en base64
            capture_timestamp: Timestamp de captura en milisegundos (opcional)
        """
        # Calcular latencia real si tenemos timestamp de captura
        real_latency = None
        if capture_timestamp:
            current_time_ms = time.time() * 1000  # Convertir a milisegundos
            real_latency = round(current_time_ms - capture_timestamp)
            
            # Actualizar latencia real en métricas
            self.metrics.update_latency(real_latency)
        
        # Obtener métricas (incluirá latencia simulada si no hay real)
        metrics = self.calculate_metrics()
        
        # Si tenemos latencia real, sobrescribir la simulada
        if real_latency is not None:
            metrics["latency"] = real_latency
            metrics["latency_type"] = "real"  # Indicar que es latencia real
        else:
            metrics["latency_type"] = "simulated"  # Indicar que es simulada
        
        message = {
            "type": "frame",
            "camera_id": self.camera_id,
            "data": frame_data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "frame_number": self.frame_count,
            "metrics": metrics
        }
        
        await self.connection.send_json(message)
    
    async def send_pong(self) -> None:
        """Enviar respuesta pong al ping del cliente."""
        message = {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
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
    
    async def send_status(self, status: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Enviar estado al cliente.
        
        Args:
            status: Estado del stream
            data: Datos adicionales opcionales
        """
        message = {
            "type": "status",
            "camera_id": self.camera_id,
            "status": status,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        await self.connection.send_json(message)
    
    async def _initialize_service(self) -> None:
        """
        Inicializa el servicio de streaming si no está inicializado.
        """
        if not self._service_initialized:
            await websocket_stream_service.initialize()
            self._service_initialized = True
    
    async def _try_real_stream(self) -> bool:
        """
        Intenta streaming real desde la cámara.
        
        Returns:
            True si el streaming real funciona, False si hay que usar mock
        """
        logger.info(f"Iniciando conexión real para cámara {self.camera_id}")
        
        try:
            # Configurar opciones del stream
            stream_config = {
                'fps': self.fps,
                'quality': self.quality,
                'buffer_size': 5,
                'check_connectivity': True
            }
            
            # Callback para frames
            async def on_frame_callback(camera_id: str, frame_data: str):
                try:
                    # Verificar que el WebSocket sigue conectado
                    if not self.connection or self.websocket.client_state.value != 1:
                        logger.debug("WebSocket desconectado, ignorando frame")
                        return
                    
                    # Enviar frame
                    await self.send_frame(frame_data)
                    self.frame_count += 1
                    
                    # Log cada 30 frames
                    if self.frame_count % 30 == 0:
                        logger.info(f"Frames enviados: {self.frame_count}")
                    
                    # Log el primer frame
                    if self.frame_count == 1:
                        logger.info(f"Primer frame recibido. Tamaño: {len(frame_data)} bytes")
                        
                except Exception as e:
                    if "WebSocket" in str(e) or "Cannot call" in str(e):
                        logger.info("WebSocket cerrado, deteniendo stream")
                        self.is_streaming = False
                    else:
                        logger.error(f"Error procesando frame: {e}")
            
            # Convertir callback async a sync
            def sync_frame_callback(camera_id: str, frame_data: str):
                asyncio.create_task(on_frame_callback(camera_id, frame_data))
            
            # Iniciar stream a través del servicio
            result = await websocket_stream_service.start_camera_stream(
                camera_id=self.camera_id,
                stream_config=stream_config,
                on_frame_callback=sync_frame_callback
            )
            
            if result['success']:
                logger.info("Streaming real iniciado exitosamente")
                await self.send_status("connected", {
                    "message": "Streaming real activo",
                    "camera_id": self.camera_id,
                    "protocol": result.get('protocol', 'RTSP')
                })
                
                # Mantener el stream activo
                last_health_check = asyncio.get_event_loop().time()
                health_check_interval = 5.0
                
                while self.is_streaming and self.connection:
                    current_time = asyncio.get_event_loop().time()
                    
                    # Verificar salud del stream
                    if current_time - last_health_check > health_check_interval:
                        metrics = await websocket_stream_service.get_stream_metrics(self.camera_id)
                        if metrics:
                            logger.debug(f"Stream saludable: {metrics.get('frames_processed', 0)} frames procesados")
                        else:
                            logger.warning("No se pueden obtener métricas del stream")
                        last_health_check = current_time
                    
                    await asyncio.sleep(0.1)
                
                return True
            else:
                error_msg = result.get('error', 'Error desconocido')
                logger.error(f"Error iniciando stream: {error_msg}")
                await self.send_error(error_msg)
                return False
                
        except asyncio.CancelledError:
            logger.info("Streaming cancelado")
            raise
        except Exception as e:
            logger.error(f"Error durante streaming: {e}")
            await self.send_error(str(e))
            return False
        finally:
            # Limpieza
            if websocket_stream_service.is_streaming(self.camera_id):
                await websocket_stream_service.stop_camera_stream(self.camera_id)
    
    async def _run_mock_stream(self) -> None:
        """Ejecuta streaming con frames simulados."""
        logger.info(f"Iniciando streaming simulado para {self.camera_id}")
        
        while self.is_streaming:
            try:
                # Control de FPS
                current_time = asyncio.get_event_loop().time()
                time_since_last = current_time - self.last_sent_time
                
                if time_since_last < self.frame_interval:
                    await asyncio.sleep(self.frame_interval - time_since_last)
                
                # Generar y enviar frame
                frame_data = await self.generate_mock_frame()
                await self.send_frame(frame_data)
                
                self.frame_count += 1
                self.last_sent_time = asyncio.get_event_loop().time()
                
            except Exception as e:
                logger.error(f"Error en mock stream: {e}")
                await asyncio.sleep(0.1)
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calcular métricas del stream.
        
        Returns:
            Diccionario con métricas incluyendo latencia
        """
        if not self.start_time:
            return {}
        
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        actual_fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        # Actualizar FPS en el modelo de métricas
        self.metrics.update_fps(actual_fps)
        
        # Calcular latencia simulada basada en calidad
        # Valores más realistas para cámaras IP
        latency_map = {
            "low": 150,     # 150ms para baja calidad
            "medium": 100,  # 100ms para calidad media  
            "high": 200     # 200ms para alta calidad (más datos = más latencia)
        }
        base_latency = latency_map.get(self.quality, 100)
        
        # Agregar variabilidad para simular condiciones reales de red
        # ±20ms de variación
        latency = base_latency + random.randint(-20, 20)
        latency = max(latency, 10)  # Mínimo 10ms para ser realista
        
        # Actualizar latencia en el modelo de métricas
        self.metrics.update_latency(latency)
        
        return {
            "fps": round(actual_fps, 1),
            "target_fps": self.fps,
            "quality": self.quality,
            "format": self.format,
            "frames_sent": self.frame_count,
            "uptime_seconds": round(elapsed, 1),
            "latency": latency,
            # Métricas adicionales del modelo
            "avg_fps": round(self.metrics.get_average_fps(), 1),
            "avg_latency": round(self.metrics.get_average_latency(), 1),
            "health_score": round(self.metrics.get_health_score(), 1)
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
        
        logger.info(f"Cliente {client_id} desconectado de stream {camera_id}")
    
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

# El servicio se inicializará cuando sea necesario, no al importar