"""
Módulo para conexión ONVIF a cámaras Dahua.
Implementa funcionalidades de snapshot y streaming usando el protocolo ONVIF estándar.
"""

import cv2
import logging
import requests
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urlparse

try:
    from onvif import ONVIFCamera
    from onvif.exceptions import ONVIFError
    ONVIF_AVAILABLE = True
except ImportError:
    ONVIF_AVAILABLE = False

from .base_connection import BaseConnection


class ONVIFConnection(BaseConnection):
    """
    Conexión ONVIF para cámaras Dahua.
    
    Implementa el protocolo ONVIF estándar para acceso a funcionalidades
    avanzadas de cámaras incluyendo snapshots, streaming y PTZ.
    """
    
    def __init__(self, config_manager):
        """
        Inicializa la conexión ONVIF.
        
        Args:
            config_manager: Instancia del gestor de configuración
        """
        super().__init__(config_manager)
        
        # Detectar automáticamente la configuración según la marca
        # Intentar primero atributos de TP-Link, luego Dahua
        if hasattr(config_manager, 'tplink_ip') and config_manager.tplink_ip:
            # Configuración TP-Link
            self.camera_ip = config_manager.tplink_ip
            self.username = getattr(config_manager, 'tplink_user', 'admin')
            self.password = getattr(config_manager, 'tplink_password', '')
            self.port = getattr(config_manager, 'onvif_port', 2020)  # Puerto común TP-Link
            self._is_tplink = True  # Marca para detección posterior
        else:
            # Configuración Dahua (por defecto)
            self.camera_ip = getattr(config_manager, 'camera_ip', '192.168.1.172')
            self.username = getattr(config_manager, 'camera_user', 'admin')
            self.password = getattr(config_manager, 'camera_password', '')
            self.port = getattr(config_manager, 'onvif_port', 80)  # Puerto común Dahua
            self._is_tplink = False  # Marca para detección posterior
            
        self.ip = self.camera_ip
        
        if not ONVIF_AVAILABLE:
            raise ImportError("Dependencias ONVIF no disponibles. Instala: pip install onvif-zeep")
        
        self._camera: Optional[ONVIFCamera] = None
        self._media_service = None
        self._device_service = None
        self._profiles = []
        self._snapshot_uri: Optional[str] = None
        self._stream_uri: Optional[str] = None
        self._connected = False  # Inicializar correctamente
        self._video_capture: Optional[cv2.VideoCapture] = None  # Stream persistente
        
        self.logger = logging.getLogger("ONVIFConnection")
    
    def connect(self) -> bool:
        """
        Establece la conexión ONVIF con la cámara.
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            self.logger.info(f"Iniciando conexión ONVIF a {self.ip}:{self.port}")
            
            # Crear instancia de cámara ONVIF
            # Usar el directorio temporal por defecto de la librería
            self._camera = ONVIFCamera(
                self.ip,
                self.port,
                self.username,
                self.password
                # Sin wsdl_dir - usar el por defecto de la librería
            )
            
            # Crear servicios básicos
            self._device_service = self._camera.create_devicemgmt_service()
            self._media_service = self._camera.create_media_service()
            
            # Verificar conexión obteniendo información del dispositivo
            device_info = self._device_service.GetDeviceInformation()
            self.logger.info(f"Conectado a {device_info.Manufacturer} {device_info.Model}")
            
            # Obtener perfiles de media
            self._profiles = self._media_service.GetProfiles()
            self.logger.info(f"Perfiles encontrados: {len(self._profiles)}")
            
            # Configurar URIs de snapshot y stream
            self._setup_media_uris()
            
            self._connected = True
            self.is_connected = True  # Atributo de BaseConnection
            return True
            
        except ONVIFError as e:
            # Verificar si es error de autenticación por el mensaje
            if "auth" in str(e).lower() or "unauthorized" in str(e).lower():
                self.logger.error("Error de autenticación ONVIF")
            else:
                self.logger.error(f"Error ONVIF: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error de conexión ONVIF: {str(e)}")
            return False
    
    def _setup_media_uris(self) -> None:
        """
        Configura las URIs de snapshot y streaming desde los perfiles.
        """
        if not self._profiles:
            self.logger.warning("No hay perfiles de media disponibles")
            return
        
        try:
            # Usar el primer perfil por defecto
            profile = self._profiles[0]
            profile_token = self._get_profile_token(profile)
            
            # Configurar Snapshot URI
            try:
                snapshot_uri = self._media_service.GetSnapshotUri({'ProfileToken': profile_token})
                self._snapshot_uri = snapshot_uri.Uri
                self.logger.info(f"Snapshot URI configurada: {self._snapshot_uri}")
            except Exception as e:
                self.logger.warning(f"No se pudo obtener Snapshot URI: {str(e)}")
            
            # Configurar Stream URI
            try:
                stream_uri = self._media_service.GetStreamUri({
                    'StreamSetup': {
                        'Stream': 'RTP-Unicast',
                        'Transport': {'Protocol': 'RTSP'}
                    },
                    'ProfileToken': profile_token
                })
                self._stream_uri = stream_uri.Uri
                self.logger.info(f"Stream URI configurada: {self._stream_uri}")
            except Exception as e:
                self.logger.warning(f"No se pudo obtener Stream URI: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error configurando URIs de media: {str(e)}")
    
    def _get_profile_token(self, profile) -> str:
        """
        Obtiene el token del perfil manejando diferentes formatos.
        
        Args:
            profile: Objeto perfil ONVIF
            
        Returns:
            Token del perfil
        """
        # Intentar diferentes atributos de token
        if hasattr(profile, '_token'):
            return profile._token
        elif hasattr(profile, 'token'):
            return profile.token
        else:
            # Último recurso: usar el nombre como token
            return getattr(profile, 'Name', 'MainProfile')
    
    def get_snapshot(self, save_path: Optional[str] = None) -> Optional[bytes]:
        """
        Captura un snapshot de la cámara vía ONVIF.
        
        Args:
            save_path: Ruta opcional para guardar la imagen
            
        Returns:
            Datos de la imagen en bytes o None si falla
        """
        if not self._connected or not self._snapshot_uri:
            self.logger.error("Conexión ONVIF no establecida o Snapshot URI no disponible")
            return None
        
        try:
            # Realizar petición HTTP al snapshot URI
            response = requests.get(
                self._snapshot_uri,
                auth=requests.auth.HTTPDigestAuth(self.username, self.password),
                timeout=10
            )
            
            if response.status_code == 200:
                image_data = response.content
                
                # Guardar si se especifica ruta
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(image_data)
                    self.logger.info(f"Snapshot guardado en: {save_path}")
                
                return image_data
            else:
                self.logger.error(f"Error HTTP al obtener snapshot: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturando snapshot ONVIF: {str(e)}")
            return None
    
    def save_snapshot(self, filename: str) -> bool:
        """
        Guarda un snapshot de la cámara vía ONVIF.
        Método de compatibilidad que utiliza get_snapshot internamente.
        
        Args:
            filename: Nombre del archivo donde guardar el snapshot
            
        Returns:
            True si el snapshot fue guardado exitosamente
        """
        try:
            snapshot_data = self.get_snapshot(filename)
            return snapshot_data is not None
        except Exception as e:
            self.logger.error(f"Error en save_snapshot ONVIF: {str(e)}")
            return False
    
    def get_video_stream(self) -> Optional[cv2.VideoCapture]:
        """
        Obtiene el stream de video vía ONVIF.
        Mantiene la conexión abierta para mejor performance.
        
        Returns:
            Objeto VideoCapture configurado o None si falla
        """
        if not self._connected:
            self.logger.error("Conexión ONVIF no establecida")
            return None
        
        # Configurar nivel de logging de OpenCV (suprimir warnings FFmpeg)
        try:
            # Intentar configurar log level si está disponible (OpenCV >= 4.0)
            cv2.setLogLevel(3)  # Nivel ERROR (0=SILENT, 1=FATAL, 2=ERROR, 3=WARNING, etc.)
        except:
            # Si no funciona, continuar sin configuración de logs
            pass
        
        # Si ya tenemos un stream abierto y funcional, devolverlo
        if self._video_capture and self._video_capture.isOpened():
            return self._video_capture
        
        # Crear nuevo stream
        self._video_capture = self._create_optimized_stream()
        return self._video_capture
    
    def _create_optimized_stream(self) -> Optional[cv2.VideoCapture]:
        """
        Crea un stream optimizado para ONVIF.
        
        Returns:
            VideoCapture optimizado o None si falla
        """
        # Suprimir warnings verbosos de FFmpeg/OpenCV
        try:
            # Intentar configurar log level si está disponible (OpenCV >= 4.0)
            cv2.setLogLevel(3)  # Nivel ERROR (0=SILENT, 1=FATAL, 2=ERROR, 3=WARNING, etc.)
        except:
            # Si no funciona, continuar sin configuración de logs
            pass
        
        # Intentar usar Stream URI si está disponible
        if self._stream_uri:
            try:
                cap = cv2.VideoCapture(self._stream_uri)
                if cap.isOpened():
                    # Configurar buffers para mejor performance
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo
                    cap.set(cv2.CAP_PROP_FPS, 30)  # FPS objetivo
                    self.logger.info("Stream ONVIF optimizado abierto exitosamente")
                    return cap
                else:
                    self.logger.warning("No se pudo abrir stream ONVIF directo")
            except Exception as e:
                self.logger.warning(f"Error con stream ONVIF directo: {str(e)}")
        
        # Fallback: probar múltiples URLs RTSP según la marca
        rtsp_urls = self._get_rtsp_urls()
        for rtsp_url in rtsp_urls:
            try:
                # Ocultar contraseña en logs
                safe_url = rtsp_url.replace(self.password, "***") if self.password else rtsp_url
                self.logger.info(f"Probando URL RTSP: {safe_url}")
                
                cap = cv2.VideoCapture(rtsp_url)
                if cap.isOpened():
                    # Optimizaciones para RTSP via ONVIF
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo para latencia baja
                    cap.set(cv2.CAP_PROP_FPS, 30)  # FPS objetivo
                    # Configurar formato preferido
                    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
                    self.logger.info(f"Stream RTSP exitoso con URL: {safe_url}")
                    return cap
                else:
                    self.logger.warning(f"No se pudo abrir stream con URL: {safe_url}")
            except Exception as e:
                self.logger.warning(f"Error con URL {safe_url}: {str(e)}")
        
        self.logger.error("No se pudo establecer ningún stream RTSP")
        return None
    
    def _get_rtsp_urls(self) -> List[str]:
        """
        Obtiene lista de URLs RTSP posibles según la marca detectada.
        
        Returns:
            Lista de URLs RTSP para probar
        """
        try:
            # Detectar marca basándose en la configuración utilizada
            if hasattr(self, '_is_tplink') or (hasattr(self, 'port') and self.port == 2020):
                # URLs para TP-Link Tapo
                return [
                    f"rtsp://{self.username}:{self.password}@{self.ip}:554/stream1",  # Stream principal
                    f"rtsp://{self.username}:{self.password}@{self.ip}:554/stream2",  # Stream secundario
                    f"rtsp://{self.ip}:554/stream1",  # Sin credenciales (fallback)
                ]
            else:
                # URLs para Dahua
                return [
                    f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=0",
                    f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=1",
                ]
        except Exception as e:
            self.logger.error(f"Error obteniendo URLs RTSP: {str(e)}")
            return []

    def _build_rtsp_url(self) -> Optional[str]:
        """
        Construye URL RTSP basada en información ONVIF y marca de cámara.
        Método legacy - usar _get_rtsp_urls() para múltiples URLs.
        
        Returns:
            URL RTSP construida o None
        """
        urls = self._get_rtsp_urls()
        return urls[0] if urls else None
    
    def get_device_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada del dispositivo vía ONVIF.
        
        Returns:
            Diccionario con información del dispositivo
        """
        if not self._connected or not self._device_service:
            return None
        
        try:
            device_info = self._device_service.GetDeviceInformation()
            return {
                'manufacturer': device_info.Manufacturer,
                'model': device_info.Model,
                'firmware': device_info.FirmwareVersion,
                'serial': device_info.SerialNumber,
                'hardware': getattr(device_info, 'HardwareId', 'N/A')
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo información del dispositivo: {str(e)}")
            return None
    
    def get_profiles(self) -> list:
        """
        Obtiene la lista de perfiles de media disponibles.
        
        Returns:
            Lista de perfiles ONVIF
        """
        return self._profiles.copy() if self._profiles else []
    
    def disconnect(self) -> bool:
        """
        Cierra la conexión ONVIF.
        
        Returns:
            True si se desconectó correctamente
        """
        if self._connected:
            try:
                # Limpiar referencias
                self._camera = None
                self._media_service = None
                self._device_service = None
                self._profiles = []
                self._snapshot_uri = None
                self._stream_uri = None
                
                # Cerrar stream de video si existe
                if self._video_capture:
                    self._video_capture.release()
                    self._video_capture = None
                
                self._connected = False
                self.is_connected = False  # Atributo de BaseConnection
                self.logger.info("Conexión ONVIF cerrada")
                return True
                
            except Exception as e:
                self.logger.error(f"Error cerrando conexión ONVIF: {str(e)}")
                return False
        
        return True
    
    def is_alive(self) -> bool:
        """
        Verifica si la conexión ONVIF está activa.
        
        Returns:
            True si la conexión está activa
        """
        if not self._connected or not self._device_service:
            return False
        
        try:
            # Intentar una operación simple para verificar conectividad
            self._device_service.GetDeviceInformation()
            return True
        except Exception:
            return False
    
    def get_frame(self) -> Optional[Any]:
        """
        Obtiene un frame del stream ONVIF de manera optimizada.
        
        Returns:
            Frame de video como array numpy o None si falla
        """
        # Usar el stream persistente para mejor performance
        if not self._video_capture or not self._video_capture.isOpened():
            self._video_capture = self.get_video_stream()
        
        if self._video_capture and self._video_capture.isOpened():
            ret, frame = self._video_capture.read()
            if ret:
                return frame
            else:
                # Si falló la lectura, intentar reconectar
                self.logger.warning("Error leyendo frame, intentando reconectar...")
                self._video_capture.release()
                self._video_capture = None
                return None
        
        return None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect() 