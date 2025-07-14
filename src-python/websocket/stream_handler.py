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
# Importaciones para streaming real
from presenters.streaming.video_stream_presenter import VideoStreamPresenter
from models import ConnectionConfig
from models.streaming import StreamProtocol

logger = logging.getLogger(__name__)


class WebSocketEventEmitter:
    """Emisor de eventos personalizado para WebSocket."""
    
    def __init__(self, frame_callback: Callable):
        self.frame_callback = frame_callback
    
    async def emit(self, event: str, data: Dict[str, Any]) -> None:
        """Emite evento genérico (no usado en este contexto)."""
        pass
    
    async def emit_frame_update(self, camera_id: str, frame_base64: str) -> None:
        """Emite actualización de frame."""
        await self.frame_callback(camera_id, frame_base64)
    
    async def emit_stream_status(self, camera_id: str, status: str, data: Optional[Dict] = None) -> None:
        """Emite estado del stream."""
        logger.info(f"Stream status: {camera_id} - {status}")
    
    async def emit_stream_metrics(self, camera_id: str, metrics: Dict[str, Any]) -> None:
        """Emite métricas del stream."""
        logger.debug(f"Stream metrics: {camera_id} - {metrics}")
    
    async def emit_error(self, camera_id: str, error_type: str, message: str) -> None:
        """Emite error."""
        logger.error(f"Stream error: {camera_id} - {error_type}: {message}")


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
        
        # Presenter para streaming real
        self.presenter = None
        self.use_real_stream = True  # Activar streaming real para cámara Dahua
        self.real_camera_config = None
        
        # Control de reintentos
        self.max_retries = 3
        self.retry_delay = 1.0  # Segundos
        self.connection_timeout = 10.0  # Timeout para conexión inicial
        
        # Estado de conexión
        self.is_connected = False
        self.last_error = None
        self.retry_count = 0
        
    async def handle_message(self, message: dict) -> None:
        """
        Procesar mensaje recibido del cliente.
        
        Args:
            message: Mensaje JSON del cliente
        """
        logger.info(f"[{self.camera_id}] Mensaje recibido: {message}")
        action = message.get("action")
        params = message.get("params", {})
        
        logger.info(f"[{self.camera_id}] Acción: {action}, Params: {params}")
        
        # Manejar mensajes de tipo ping
        if message.get("type") == "ping":
            # Responder con pong
            await self.send_status("pong")
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
            # Ignorar mensajes sin acción (como ping ya manejado arriba)
            logger.debug(f"[{self.camera_id}] Mensaje sin acción, ignorando")
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
            # Intentar streaming real para cámara Dahua
            if self.use_real_stream and self.camera_id == "cam_192.168.1.172":
                success = await self._try_real_stream()
                if success:
                    return
            
            # Si no es posible, usar frames simulados
            logger.info(f"Usando frames simulados para {self.camera_id}")
            while self.is_streaming and self.connection and self.websocket.client_state.value == 1:
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
    
    async def _check_camera_connectivity(self) -> bool:
        """
        Verificar si la cámara es accesible en la red.
        
        Returns:
            True si la cámara responde, False en caso contrario
        """
        import socket
        import subprocess
        import platform
        
        ip = "192.168.1.172"
        port = 554  # Puerto RTSP
        
        try:
            # Método 1: Verificar con socket TCP
            logger.info(f"🔍 Verificando conectividad con {ip}:{port}")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)  # Timeout de 3 segundos
            
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                logger.info(f"✅ Puerto {port} accesible en {ip}")
                return True
            else:
                logger.warning(f"⚠️ Puerto {port} no accesible en {ip}")
                
                # Método 2: Intentar ping
                logger.info(f"🏓 Intentando ping a {ip}...")
                
                # Comando ping según el sistema operativo
                param = '-n' if platform.system().lower() == 'windows' else '-c'
                command = ['ping', param, '1', '-w', '1000', ip] if platform.system().lower() == 'windows' else ['ping', param, '1', '-W', '1', ip]
                
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✅ Ping exitoso a {ip}")
                    logger.warning(f"⚠️ Pero puerto RTSP {port} cerrado. Verificar configuración de la cámara.")
                    return True  # La cámara responde, pero puede necesitar configuración
                else:
                    logger.error(f"❌ No hay respuesta de ping desde {ip}")
                    return False
                    
        except socket.timeout:
            logger.error(f"⏱️ Timeout verificando conectividad con {ip}:{port}")
            return False
        except Exception as e:
            logger.error(f"❌ Error verificando conectividad: {e}")
            return False
    
    async def _try_real_stream(self) -> bool:
        """
        Intentar streaming real desde la cámara con reintentos y mejor manejo de errores.
        
        Returns:
            True si el streaming real funciona, False si hay que usar mock
        """
        logger.info(f"🎥 Iniciando conexión real para cámara {self.camera_id}")
        
        # Validar conectividad primero
        if not await self._check_camera_connectivity():
            logger.error(f"❌ Cámara {self.camera_id} no accesible en la red")
            return False
        
        # Intentar conexión con reintentos
        for attempt in range(self.max_retries):
            try:
                self.retry_count = attempt
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Backoff exponencial
                    logger.info(f"🔄 Reintento {attempt + 1}/{self.max_retries} después de {delay}s")
                    await asyncio.sleep(delay)
                
                logger.info(f"📡 Intento {attempt + 1}: Conectando a cámara Dahua en 192.168.1.172")
                
                # Configuración para cámara Dahua
                config = ConnectionConfig(
                    ip="192.168.1.172",
                    username="admin",
                    password="3gfwb3ToWfeWNqm22223DGbzcH-4si",
                    rtsp_port=554,
                    onvif_port=80,
                    http_port=80,
                    timeout=10,
                    max_retries=3
                )
                
                # Agregar información adicional necesaria para el presenter
                # El presenter espera estos atributos adicionales
                config.protocol = StreamProtocol.RTSP  # type: ignore
                config.channel = 1  # type: ignore
                config.subtype = 0  # type: ignore
                config.port = 554  # type: ignore - Alias para rtsp_port
                config.brand = "dahua"  # type: ignore
                config.rtsp_path = "/cam/realmonitor?channel=1&subtype=0"  # type: ignore
                
                # Log detallado de configuración (sin password)
                logger.info(f"📋 Configuración RTSP:")
                logger.info(f"  - IP: {config.ip}")
                logger.info(f"  - Puerto RTSP: {config.rtsp_port}")
                logger.info(f"  - Usuario: {config.username}")
                logger.info(f"  - Protocolo: RTSP")
                logger.info(f"  - Canal: 1")
                logger.info(f"  - Subtipo: 0")
                logger.info(f"  - Timeout: {config.timeout}s")
                logger.info(f"  - Reintentos máximos: {config.max_retries}")
            
                # Crear presenter con emitter personalizado
                logger.info("🔧 Creando VideoStreamPresenter...")
                self.presenter = VideoStreamPresenter()
                
                # Crear una función de callback que se ejecute cuando lleguen frames
                async def on_frame_callback(camera_id: str, frame_data: str):
                    try:
                        # Verificar que el WebSocket sigue conectado antes de enviar
                        if not self.connection or self.websocket.client_state.value != 1:
                            logger.debug("WebSocket desconectado, ignorando frame")
                            return
                            
                        # frame_data ya viene en base64 desde el VideoStreamService
                        await self.send_frame(frame_data)
                        self.frame_count += 1
                        
                        # Log cada 30 frames para no saturar
                        if self.frame_count % 30 == 0:
                            logger.info(f"🎬 Frames enviados: {self.frame_count}")
                            
                        # Log el primer frame para confirmar recepción
                        if self.frame_count == 1:
                            logger.info(f"✅ Primer frame recibido! Tamaño: {len(frame_data)} bytes")
                    except Exception as e:
                        # Si el error es por WebSocket cerrado, detener el stream
                        if "WebSocket" in str(e) or "Cannot call" in str(e):
                            logger.info("WebSocket cerrado, deteniendo stream")
                            self.is_streaming = False
                        else:
                            logger.error(f"❌ Error procesando frame: {e}", exc_info=True)
                
                # Convertir callback async a sync ya que el servicio lo llama de forma síncrona
                def sync_frame_callback(camera_id: str, frame_data: str):
                    asyncio.create_task(on_frame_callback(camera_id, frame_data))
                
                # Configurar emitter para logs detallados
                event_emitter = WebSocketEventEmitter(
                    frame_callback=on_frame_callback
                )
                self.presenter._event_emitter = event_emitter
                
                # Intentar conectar con timeout
                logger.info("🔌 Conectando a la cámara...")
                try:
                    async with asyncio.timeout(self.connection_timeout):
                        # El presenter acepta el callback como parámetro
                        success = await self.presenter.start_camera_stream(
                            camera_id=f"cam_{config.ip.replace('.', '_')}",
                            connection_config=config,
                            protocol=StreamProtocol.RTSP,
                            options={
                                'targetFps': self.fps,
                                'bufferSize': 5
                            },
                            on_frame_callback=sync_frame_callback
                        )
                        
                    if not success:
                        error_msg = "Conexión rechazada por la cámara"
                        logger.error(f"❌ {error_msg}")
                        self.last_error = error_msg
                        if attempt < self.max_retries - 1:
                            continue  # Reintentar
                        return False
                        
                except asyncio.TimeoutError:
                    error_msg = f"Timeout de conexión ({self.connection_timeout}s)"
                    logger.error(f"⏱️ {error_msg}")
                    self.last_error = error_msg
                    if attempt < self.max_retries - 1:
                        continue  # Reintentar
                    return False
            
                # Conexión exitosa
                logger.info("✅ Conexión establecida con éxito")
                self.is_connected = True
                self.retry_count = 0
                
                logger.info("🎆 ¡Streaming real iniciado exitosamente!")
                await self.send_status("connected", {
                    "message": "Streaming real activo",
                    "camera_id": self.camera_id,
                    "protocol": "RTSP"
                })
                
                # Mantener el stream activo con monitoreo
                last_health_check = asyncio.get_event_loop().time()
                health_check_interval = 5.0  # Verificar salud cada 5 segundos
                
                while self.is_streaming and self.connection:
                    current_time = asyncio.get_event_loop().time()
                    
                    # Verificar salud del stream periódicamente
                    if current_time - last_health_check > health_check_interval:
                        # Verificar si sigue recibiendo frames
                        if self.frame_count == 0:
                            logger.warning("⚠️ No se están recibiendo frames")
                        else:
                            logger.debug(f"✅ Stream saludable: {self.frame_count} frames recibidos")
                        last_health_check = current_time
                    
                    await asyncio.sleep(0.1)
                
                # Stream terminado normalmente
                return True
                
            except asyncio.CancelledError:
                logger.info("🚫 Streaming cancelado por el usuario")
                raise
                
            except Exception as e:
                error_msg = f"Error durante streaming: {str(e)}"
                logger.error(f"💥 {error_msg}", exc_info=True)
                self.last_error = error_msg
                
                # Enviar error al cliente
                await self.send_error(error_msg)
                
                if attempt < self.max_retries - 1:
                    logger.info("🔄 Intentando reconectar...")
                    continue
                    
                return False
                
            finally:
                # Limpieza siempre
                if self.presenter and self.is_connected:
                    try:
                        logger.info("🧹 Limpiando recursos...")
                        # Detener streaming primero
                        self.is_streaming = False
                        # Detener el stream de la cámara específica
                        camera_id = f"cam_{config.ip.replace('.', '_')}"
                        await self.presenter.stop_camera_stream(camera_id)
                    except Exception as e:
                        logger.error(f"Error durante limpieza: {e}")
                    finally:
                        self.presenter = None
                        self.is_connected = False
        
        # Si llegamos aquí, todos los reintentos fallaron
        logger.error(f"🚫 Imposible conectar después de {self.max_retries} intentos")
        await self.send_error(f"No se pudo conectar a la cámara después de {self.max_retries} intentos")
        return False
    
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