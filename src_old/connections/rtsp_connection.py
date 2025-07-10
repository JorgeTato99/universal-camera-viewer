"""
Implementación de conexión RTSP para cámaras Dahua.
Utiliza OpenCV para la captura de video en tiempo real.
"""

import cv2
import logging
from typing import Optional, Dict, Any
import numpy as np
from .base_connection import BaseConnection

# cspell:disable
class RTSPConnection(BaseConnection):
    """
    Implementación concreta de conexión RTSP para cámaras Dahua.
    Hereda de BaseConnection e implementa todos los métodos abstractos.
    """
    
    def __init__(self, config_manager):
        """
        Inicializa la conexión RTSP con configuración.
        
        Args:
            config_manager: Instancia del gestor de configuración
        """
        super().__init__(config_manager)
        self.logger = logging.getLogger("RTSPConnection")
        
        # Configuración específica RTSP
        self.camera_ip = getattr(config_manager, 'camera_ip', '192.168.1.172')
        self.username = getattr(config_manager, 'camera_user', 'admin')
        self.password = getattr(config_manager, 'camera_password', '')
        self.port = getattr(config_manager, 'rtsp_port', 554)
        self.channel = getattr(config_manager, 'channel', 1)
        self.subtype = getattr(config_manager, 'subtype', 0)
        self.rtsp_url = self._build_rtsp_url()
        
    def _build_rtsp_url(self) -> str:
        """
        Construye la URL RTSP completa para la conexión.
        
        Returns:
            URL RTSP formateada con credenciales y parámetros
        """
        return (f"rtsp://{self.username}:{self.password}@{self.camera_ip}:{self.port}/"
                f"cam/realmonitor?channel={self.channel}&subtype={self.subtype}")
    
    def connect(self) -> bool:
        """
        Establece la conexión RTSP con la cámara usando OpenCV.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
            
        Raises:
            ConnectionError: Si no se puede establecer la conexión
        """
        try:
            if not self.username or not self.password:
                self.logger.error("Credenciales inválidas para conexión RTSP")
                return False
            
            self.logger.info(f"Intentando conectar RTSP a {self.camera_ip}:{self.port}")
            
            # Crear capturador de video OpenCV
            self.connection_handle = cv2.VideoCapture(self.rtsp_url)
            
            # Configurar buffer para reducir latencia
            self.connection_handle.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Verificar si la conexión fue exitosa
            if self.connection_handle.isOpened():
                # Intentar leer un frame para confirmar la conexión
                ret, _ = self.connection_handle.read()
                if ret:
                    self.is_connected = True
                    self.logger.info(f"Conexión RTSP establecida exitosamente a {self.camera_ip}")
                    return True
                else:
                    self.logger.error("No se pudo leer frame inicial de la cámara")
                    self._cleanup_connection()
                    return False
            else:
                self.logger.error(f"No se pudo abrir stream RTSP: {self.rtsp_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al conectar RTSP: {str(e)}")
            self._cleanup_connection()
            return False
    
    def disconnect(self) -> bool:
        """
        Cierra la conexión RTSP y libera recursos.
        
        Returns:
            True si se desconectó correctamente, False en caso contrario
        """
        try:
            if self.connection_handle is not None:
                self.connection_handle.release()
                self.connection_handle = None
            
            self.is_connected = False
            self.logger.info(f"Conexión RTSP cerrada para {self.camera_ip}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al desconectar RTSP: {str(e)}")
            return False
    
    def is_alive(self) -> bool:
        """
        Verifica si la conexión RTSP está activa.
        
        Returns:
            True si la conexión está activa, False en caso contrario
        """
        if not self.is_connected or self.connection_handle is None:
            return False
        
        try:
            # Verificar si el capturador sigue abierto
            return self.connection_handle.isOpened()
        except Exception:
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Obtiene un frame de video de la cámara RTSP.
        
        Returns:
            Array numpy con el frame BGR, None si no se puede obtener
        """
        if not self.is_alive():
            self.logger.warning("Intentando obtener frame sin conexión activa")
            return None
        
        try:
            ret, frame = self.connection_handle.read()
            if ret and frame is not None:
                return frame
            else:
                self.logger.warning("No se pudo leer frame de la cámara RTSP")
                return None
                
        except Exception as e:
            self.logger.error(f"Error al obtener frame RTSP: {str(e)}")
            return None
    
    def get_frame_properties(self) -> Dict[str, Any]:
        """
        Obtiene las propiedades del stream de video.
        
        Returns:
            Diccionario con propiedades del stream (ancho, alto, fps, etc.)
        """
        if not self.is_alive():
            return {}
        
        try:
            properties = {
                "width": int(self.connection_handle.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self.connection_handle.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": self.connection_handle.get(cv2.CAP_PROP_FPS),
                "fourcc": int(self.connection_handle.get(cv2.CAP_PROP_FOURCC)),
                "buffer_size": int(self.connection_handle.get(cv2.CAP_PROP_BUFFERSIZE))
            }
            return properties
            
        except Exception as e:
            self.logger.error(f"Error al obtener propiedades del stream: {str(e)}")
            return {}
    
    def save_snapshot(self, filename: str) -> bool:
        """
        Captura y guarda un snapshot de la cámara.
        
        Args:
            filename: Nombre del archivo donde guardar la imagen
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        frame = self.get_frame()
        if frame is not None:
            try:
                success = cv2.imwrite(filename, frame)
                if success:
                    self.logger.info(f"Snapshot guardado como {filename}")
                    return True
                else:
                    self.logger.error(f"Error al guardar snapshot en {filename}")
                    return False
            except Exception as e:
                self.logger.error(f"Error al guardar snapshot: {str(e)}")
                return False
        else:
            self.logger.error("No se pudo obtener frame para el snapshot")
            return False
    
    def _cleanup_connection(self) -> None:
        """
        Limpia recursos de conexión en caso de error.
        Método privado para manejo interno de errores.
        """
        if self.connection_handle is not None:
            try:
                self.connection_handle.release()
            except Exception:
                pass
            finally:
                self.connection_handle = None
        self.is_connected = False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Extiende la información base con detalles específicos de RTSP.
        
        Returns:
            Diccionario con información completa de la conexión RTSP
        """
        base_info = super().get_connection_info()
        rtsp_info = {
            "rtsp_url": self.rtsp_url.replace(self.credentials.get("password", ""), "***"),
            "port": self.port,
            "channel": self.channel,
            "subtype": self.subtype,
            "stream_properties": self.get_frame_properties() if self.is_alive() else {}
        }
        
        return {**base_info, **rtsp_info} 