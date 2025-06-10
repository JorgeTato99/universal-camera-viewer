"""
Conexión para cámaras TP-Link Tapo usando protocolo RTSP.
Implementa la conexión específica para cámaras TP-Link con soporte multi-stream.
"""

import cv2
import logging
from typing import Optional, Dict, Any, List, Tuple
from .base_connection import BaseConnection


class TPLinkConnection(BaseConnection):
    """
    Conexión específica para cámaras TP-Link Tapo.
    Soporta múltiples streams y configuraciones específicas de la marca.
    """
    
    def __init__(self, config_manager):
        """
        Inicializa la conexión TP-Link.
        
        Args:
            config_manager: Instancia del gestor de configuración
        """
        super().__init__(config_manager)
        self.logger = logging.getLogger("TPLinkConnection")
        
        # Configuración específica TP-Link
        self.camera_ip = getattr(config_manager, 'tplink_ip', '192.168.1.77')
        self.username = getattr(config_manager, 'tplink_user', 'admin')
        self.password = getattr(config_manager, 'tplink_password', '')
        self.rtsp_port = getattr(config_manager, 'rtsp_port', 554)
        
        # URLs de stream específicas para TP-Link Tapo
        self.stream_urls = {
            'main': f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/stream1",
            'sub': f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/stream2",
            'jpeg': f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.rtsp_port}/stream8"
        }
        
        self.current_stream_type = 'main'
        self.stream_qualities = {
            'main': 'HD (2560x1440)',
            'sub': 'SD (640x360)', 
            'jpeg': 'JPEG Stream'
        }
        
        # Inicializar connection como None
        self.connection = None
    
    def connect(self) -> bool:
        """
        Establece la conexión RTSP con la cámara TP-Link.
        Método abstracto requerido por BaseConnection.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        success = self._establish_connection()
        if success:
            self.is_connected = True
        return success
    
    def disconnect(self) -> bool:
        """
        Cierra la conexión RTSP con la cámara TP-Link.
        Método abstracto requerido por BaseConnection.
        
        Returns:
            True si se desconectó correctamente
        """
        try:
            self._close_connection()
            self.is_connected = False
            return True
        except Exception as e:
            self.logger.error(f"❌ Error desconectando TP-Link: {e}")
            return False
    
    def is_alive(self) -> bool:
        """
        Verifica si la conexión está activa.
        Método abstracto requerido por BaseConnection.
        
        Returns:
            True si la conexión está activa
        """
        if not self.is_connected or not self.connection:
            return False
        
        try:
            # Intentar leer un frame para verificar que la conexión está viva
            ret, frame = self.connection.read()
            
            # Si logramos leer, la conexión está viva
            # (incluso si el frame es None, significa que la conexión funciona)
            return ret or frame is not None
        except Exception:
            return False
        
    def _establish_connection(self) -> bool:
        """
        Establece la conexión RTSP con la cámara TP-Link.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            # Intentar conectar con stream principal primero
            for stream_type, url in self.stream_urls.items():
                self.logger.info(f"Intentando conectar TP-Link stream '{stream_type}'...")
                
                cap = cv2.VideoCapture(url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_FPS, 25)
                
                if cap.isOpened():
                    # Probar leer un frame
                    ret, frame = cap.read()
                    
                    if ret and frame is not None:
                        self.connection = cap
                        self.current_stream_type = stream_type
                        
                        # Obtener información del stream
                        height, width = frame.shape[:2]
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        self.logger.info(f"✅ Conexión TP-Link exitosa:")
                        self.logger.info(f"   Stream: {self.stream_qualities[stream_type]}")
                        self.logger.info(f"   Resolución: {width}x{height}")
                        self.logger.info(f"   FPS: {fps}")
                        
                        return True
                    else:
                        cap.release()
                else:
                    cap.release()
            
            self.logger.error("❌ No se pudo establecer conexión con ningún stream TP-Link")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error estableciendo conexión TP-Link: {e}")
            return False
    
    def _close_connection(self) -> None:
        """
        Cierra la conexión RTSP activa.
        """
        if self.connection:
            self.connection.release()
            self.connection = None
            self.logger.info("🔌 Conexión TP-Link cerrada")
    
    def get_frame(self) -> Optional[cv2.Mat]:
        """
        Obtiene un frame del stream de video.
        
        Returns:
            Frame de video en formato OpenCV o None si hay error
        """
        if not self.is_connected or not self.connection:
            return None
        
        try:
            ret, frame = self.connection.read()
            
            if ret and frame is not None:
                return frame
            else:
                self.logger.warning("⚠️ Frame vacío recibido de TP-Link")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo frame TP-Link: {e}")
            return None
    
    def capture_snapshot(self, filename: str) -> bool:
        """
        Captura un snapshot del stream actual.
        
        Args:
            filename: Nombre del archivo donde guardar el snapshot
            
        Returns:
            True si el snapshot fue guardado exitosamente
        """
        frame = self.get_frame()
        
        if frame is not None:
            try:
                success = cv2.imwrite(filename, frame)
                if success:
                    self.logger.info(f"📸 Snapshot TP-Link guardado: {filename}")
                    return True
                else:
                    self.logger.error(f"❌ Error guardando snapshot TP-Link: {filename}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"❌ Error capturando snapshot TP-Link: {e}")
                return False
        else:
            self.logger.warning("⚠️ No se pudo obtener frame para snapshot TP-Link")
            return False
    
    def save_snapshot(self, filename: str) -> bool:
        """
        Guarda un snapshot del stream actual.
        Método de compatibilidad que utiliza capture_snapshot internamente.
        
        Args:
            filename: Nombre del archivo donde guardar el snapshot
            
        Returns:
            True si el snapshot fue guardado exitosamente
        """
        return self.capture_snapshot(filename)
    
    def get_stream_info(self) -> Dict[str, Any]:
        """
        Obtiene información del stream actual.
        
        Returns:
            Diccionario con información del stream
        """
        if not self.is_connected:
            return {"error": "No conectado"}
        
        try:
            # Obtener un frame para determinar resolución
            frame = self.get_frame()
            
            if frame is not None:
                height, width = frame.shape[:2]
                fps = self.connection.get(cv2.CAP_PROP_FPS)
                
                return {
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "stream_type": self.current_stream_type,
                    "quality": self.stream_qualities[self.current_stream_type],
                    "camera_model": "TP-Link Tapo C520WS",
                    "protocol": "RTSP",
                    "url": self.stream_urls[self.current_stream_type].replace(self.password, "***")
                }
            else:
                return {"error": "No se pudo obtener frame"}
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo información del stream TP-Link: {e}")
            return {"error": str(e)}
    
    def switch_stream_quality(self, quality: str) -> bool:
        """
        Cambia la calidad del stream.
        
        Args:
            quality: Calidad deseada ('main', 'sub', 'jpeg')
            
        Returns:
            True si el cambio fue exitoso
        """
        if quality not in self.stream_urls:
            self.logger.error(f"❌ Calidad no válida: {quality}")
            return False
        
        if quality == self.current_stream_type:
            self.logger.info(f"ℹ️ Ya está usando stream '{quality}'")
            return True
        
        try:
            # Cerrar conexión actual
            was_connected = self.is_connected
            if was_connected:
                self._close_connection()
            
            # Cambiar a nueva URL
            self.current_stream_type = quality
            
            # Reconectar si estaba conectado
            if was_connected:
                return self._establish_connection()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error cambiando calidad de stream TP-Link: {e}")
            return False
    
    def get_available_streams(self) -> List[Dict[str, str]]:
        """
        Obtiene la lista de streams disponibles.
        
        Returns:
            Lista de diccionarios con información de streams disponibles
        """
        return [
            {
                "type": stream_type,
                "quality": quality,
                "url": url.replace(self.password, "***")
            }
            for stream_type, (quality, url) in zip(
                self.stream_urls.keys(),
                zip(self.stream_qualities.values(), self.stream_urls.values())
            )
        ]
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Prueba la conexión sin establecerla permanentemente.
        
        Returns:
            Tupla con (éxito, mensaje)
        """
        try:
            for stream_type, url in self.stream_urls.items():
                cap = cv2.VideoCapture(url)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        return True, f"Conexión exitosa - {self.stream_qualities[stream_type]} ({width}x{height})"
                
                cap.release()
            
            return False, "No se pudo conectar con ningún stream TP-Link"
            
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Obtiene información del dispositivo TP-Link.
        
        Returns:
            Diccionario con información del dispositivo
        """
        return {
            "manufacturer": "TP-Link",
            "model": "Tapo C520WS",
            "ip": self.camera_ip,
            "username": self.username,
            "protocol": "RTSP",
            "streams_available": len(self.stream_urls),
            "current_stream": self.stream_qualities.get(self.current_stream_type, "Unknown"),
            "supported_features": [
                "RTSP Streaming",
                "Multiple Quality Streams", 
                "Snapshot Capture",
                "Stream Quality Switching"
            ]
        } 