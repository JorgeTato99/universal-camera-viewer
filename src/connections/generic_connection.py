"""
Conexión genérica para cámaras chinas sin marca específica.
Implementa conexión RTSP directa para cámaras que solo exponen puerto 554.
"""

import cv2
import logging
from typing import Optional, Dict, Any, List
from .base_connection import BaseConnection


class GenericConnection(BaseConnection):
    """
    Conexión genérica para cámaras chinas sin marca específica.
    Especializada en conexiones RTSP directas cuando solo está disponible puerto 554.
    Implementa múltiples patrones de URL RTSP comunes en cámaras chinas.
    """
    
    def __init__(self, config_manager):
        """
        Inicializa la conexión genérica.
        
        Args:
            config_manager: Instancia del gestor de configuración
        """
        super().__init__(config_manager)
        self.logger = logging.getLogger("GenericConnection")
        
        # Configuración específica para cámaras genéricas
        # Priorizar variables de entorno específicas de generic si están disponibles
        self.camera_ip = getattr(config_manager, 'generic_ip', None) or getattr(config_manager, 'camera_ip', '192.168.1.100')
        self.username = getattr(config_manager, 'generic_user', None) or getattr(config_manager, 'camera_user', 'admin')
        self.password = getattr(config_manager, 'generic_password', None) or getattr(config_manager, 'camera_password', '')
        self.rtsp_port = getattr(config_manager, 'rtsp_port', 554)
        
        # URLs de stream comunes para cámaras chinas genéricas
        self.stream_urls = self._generate_stream_urls()
        
        # Estado de conexión
        self.current_stream_url = None
        self.rtsp_connection = None
        
    def _generate_stream_urls(self) -> List[str]:
        """
        Genera lista de URLs RTSP comunes para probar con cámaras chinas.
        
        Returns:
            Lista de URLs RTSP ordenadas por probabilidad de éxito
        """
        urls = []
        base_auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        base_url = f"rtsp://{base_auth}{self.camera_ip}:{self.rtsp_port}"
        
        # Patrones más comunes en cámaras chinas genéricas
        patterns = [
            "/stream1",           # Patrón más común
            "/stream2",           # Stream secundario
            "/live/stream1",      # Variante con /live
            "/live/stream2",      # Stream secundario con /live
            "/stream",            # Patrón simple
            "/live",              # Muy simple
            "/live/main",         # Main stream
            "/live/sub",          # Sub stream
            "/h264",              # Por codec
            "/h264_stream",       # Codec específico
            "/video",             # Genérico
            "/cam/realmonitor?channel=1&subtype=0",  # Estilo Dahua
            "/cam/realmonitor?channel=1&subtype=1",  # Dahua sub
            "/user={}&password={}&channel=1&stream=0".format(self.username, self.password),  # Con credenciales en URL
            "/user={}&password={}&channel=1&stream=1".format(self.username, self.password),  # Sub con credenciales
            "/",                  # Root path - último intento
        ]
        
        # Generar URLs completas
        for pattern in patterns:
            urls.append(f"{base_url}{pattern}")
        
        # URLs sin autenticación como fallback
        if base_auth:
            no_auth_base = f"rtsp://{self.camera_ip}:{self.rtsp_port}"
            fallback_patterns = ["/stream1", "/live", "/stream", "/"]
            for pattern in fallback_patterns:
                urls.append(f"{no_auth_base}{pattern}")
        
        return urls
    
    def connect(self) -> bool:
        """
        Establece la conexión RTSP probando múltiples URLs comunes.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            self.logger.info(f"🔌 Iniciando conexión genérica a {self.camera_ip}:{self.rtsp_port}")
            
            # Probar cada URL en orden de probabilidad
            for i, url in enumerate(self.stream_urls, 1):
                try:
                    # Ocultar credenciales en logs
                    safe_url = url.replace(f"{self.username}:{self.password}@", "***:***@") if self.username and self.password else url
                    self.logger.info(f"🎯 Probando URL {i}/{len(self.stream_urls)}: {safe_url}")
                    
                    # Crear capturador OpenCV
                    cap = cv2.VideoCapture(url)
                    
                    # Configurar timeout y buffer
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10 segundos timeout
                    
                    if cap.isOpened():
                        # Intentar leer un frame para confirmar
                        ret, frame = cap.read()
                        
                        if ret and frame is not None:
                            # ¡Conexión exitosa!
                            self.rtsp_connection = cap
                            self.current_stream_url = url
                            self.is_connected = True
                            
                            # Obtener información del stream
                            height, width = frame.shape[:2]
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            
                            self.logger.info(f"✅ Conexión genérica exitosa:")
                            self.logger.info(f"   URL: {safe_url}")
                            self.logger.info(f"   Resolución: {width}x{height}")
                            self.logger.info(f"   FPS: {fps}")
                            
                            return True
                        else:
                            # Conexión abierta pero sin frame
                            cap.release()
                            self.logger.warning(f"⚠️  URL abierta pero sin frame: {safe_url}")
                    else:
                        # No se pudo abrir
                        cap.release()
                        
                except Exception as e:
                    self.logger.warning(f"❌ Error con URL {safe_url}: {str(e)}")
                    continue
            
            self.logger.error("❌ No se pudo establecer conexión con ninguna URL RTSP")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error general en conexión genérica: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """
        Cierra la conexión RTSP y libera recursos.
        
        Returns:
            True si se desconectó correctamente
        """
        try:
            if self.rtsp_connection is not None:
                self.rtsp_connection.release()
                self.rtsp_connection = None
            
            self.is_connected = False
            self.current_stream_url = None
            self.logger.info(f"🔌 Conexión genérica cerrada para {self.camera_ip}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error al desconectar: {str(e)}")
            return False
    
    def is_alive(self) -> bool:
        """
        Verifica si la conexión está activa.
        
        Returns:
            True si la conexión está activa
        """
        if not self.is_connected or self.rtsp_connection is None:
            return False
        
        try:
            return self.rtsp_connection.isOpened()
        except Exception:
            return False
    
    def get_frame(self) -> Optional[Any]:
        """
        Obtiene un frame del stream de video.
        
        Returns:
            Frame de video o None si no está disponible
        """
        if not self.is_alive():
            return None
        
        try:
            ret, frame = self.rtsp_connection.read()
            if ret and frame is not None:
                return frame
            else:
                self.logger.warning("⚠️  No se pudo leer frame del stream genérico")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error al obtener frame: {str(e)}")
            return None
    
    def get_frame_properties(self) -> Dict[str, Any]:
        """
        Obtiene propiedades del stream de video.
        
        Returns:
            Diccionario con propiedades del stream
        """
        if not self.is_alive():
            return {}
        
        try:
            properties = {
                "width": int(self.rtsp_connection.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self.rtsp_connection.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": self.rtsp_connection.get(cv2.CAP_PROP_FPS),
                "fourcc": int(self.rtsp_connection.get(cv2.CAP_PROP_FOURCC)),
                "buffer_size": int(self.rtsp_connection.get(cv2.CAP_PROP_BUFFERSIZE))
            }
            return properties
            
        except Exception as e:
            self.logger.error(f"❌ Error al obtener propiedades: {str(e)}")
            return {}
    
    def save_snapshot(self, filename: str) -> bool:
        """
        Guarda un snapshot del frame actual.
        
        Args:
            filename: Nombre del archivo donde guardar
            
        Returns:
            True si se guardó exitosamente
        """
        frame = self.get_frame()
        if frame is not None:
            try:
                success = cv2.imwrite(filename, frame)
                if success:
                    self.logger.info(f"📸 Snapshot guardado: {filename}")
                    return True
                else:
                    self.logger.error(f"❌ Error al guardar snapshot: {filename}")
                    return False
            except Exception as e:
                self.logger.error(f"❌ Error guardando snapshot: {str(e)}")
                return False
        else:
            self.logger.error("❌ No hay frame disponible para snapshot")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Obtiene información completa de la conexión.
        
        Returns:
            Diccionario con información de la conexión
        """
        base_info = super().get_connection_info()
        generic_info = {
            "connection_type": "generic",
            "rtsp_port": self.rtsp_port,
            "current_stream_url": self.current_stream_url.replace(f"{self.username}:{self.password}@", "***:***@") if self.current_stream_url and self.username and self.password else self.current_stream_url,
            "total_urls_tested": len(self.stream_urls),
            "stream_properties": self.get_frame_properties() if self.is_alive() else {}
        }
        
        return {**base_info, **generic_info}
    
    def get_supported_urls(self) -> List[str]:
        """
        Obtiene la lista de URLs soportadas (para debugging).
        
        Returns:
            Lista de URLs que se probaron
        """
        # Versión segura sin credenciales
        safe_urls = []
        for url in self.stream_urls:
            if self.username and self.password:
                safe_url = url.replace(f"{self.username}:{self.password}@", "***:***@")
            else:
                safe_url = url
            safe_urls.append(safe_url)
        
        return safe_urls 