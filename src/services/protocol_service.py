#!/usr/bin/env python3
"""
ProtocolService - Servicio de gestión de protocolos de conexión de cámaras.

Proporciona funcionalidades unificadas para:
- Conexiones ONVIF, RTSP, HTTP/CGI
- Detección automática de protocolos soportados
- Streaming de video en tiempo real
- Captura de snapshots
- Gestión de credenciales por protocolo
"""

import asyncio
import cv2
import logging
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple, Union, Callable
import threading
import time

# Importaciones opcionales para protocolos específicos
try:
    from onvif import ONVIFCamera
    from onvif.exceptions import ONVIFError
    ONVIF_AVAILABLE = True
except ImportError:
    ONVIF_AVAILABLE = False

try:
    import rtsp
    RTSP_AVAILABLE = True
except ImportError:
    RTSP_AVAILABLE = False

from ..models import CameraModel, ConnectionConfig


class ProtocolType(Enum):
    """Tipos de protocolo soportados."""
    ONVIF = "onvif"
    RTSP = "rtsp"
    HTTP = "http"
    AMCREST = "amcrest"
    TPLINK = "tplink"
    STEREN = "steren"
    GENERIC = "generic"


class ConnectionState(Enum):
    """Estados de conexión."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    ERROR = "error"


@dataclass
class StreamingConfig:
    """Configuración de streaming."""
    resolution: str = "1920x1080"
    fps: int = 30
    quality: str = "high"
    codec: str = "H264"
    channel: int = 1
    subtype: int = 0


@dataclass
class ProtocolCapabilities:
    """Capacidades de un protocolo específico."""
    supports_streaming: bool = True
    supports_snapshots: bool = True
    supports_ptz: bool = False
    supports_audio: bool = False
    max_resolution: str = "1920x1080"
    supported_codecs: List[str] = None
    
    def __post_init__(self):
        if self.supported_codecs is None:
            self.supported_codecs = ["H264"]


class BaseProtocolHandler(ABC):
    """
    Clase base abstracta para manejadores de protocolos de cámara.
    
    Define la interfaz común para todos los protocolos de conexión.
    """
    
    def __init__(self, config: ConnectionConfig, streaming_config: StreamingConfig = None):
        """
        Inicializa el manejador de protocolo.
        
        Args:
            config: Configuración de conexión
            streaming_config: Configuración de streaming
        """
        self.config = config
        self.streaming_config = streaming_config or StreamingConfig()
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Estado interno
        self._state = ConnectionState.DISCONNECTED
        self._connection_handle: Optional[Any] = None
        self._stream_handle: Optional[cv2.VideoCapture] = None
        self._last_frame_time: Optional[datetime] = None
        self._frame_count = 0
        self._fps = 0.0
        
        # Threading para streaming
        self._streaming_thread: Optional[threading.Thread] = None
        self._streaming_active = False
        self._frame_callbacks: List[Callable[[Any], None]] = []
        
    @property
    def state(self) -> ConnectionState:
        """Estado actual de la conexión."""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Indica si está conectado."""
        return self._state in [ConnectionState.CONNECTED, ConnectionState.STREAMING]
    
    @property
    def is_streaming(self) -> bool:
        """Indica si está haciendo streaming."""
        return self._state == ConnectionState.STREAMING
    
    @property
    def current_fps(self) -> float:
        """FPS actual del streaming."""
        return self._fps
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establece conexión con la cámara.
        
        Returns:
            True si la conexión fue exitosa
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Cierra la conexión con la cámara.
        
        Returns:
            True si se desconectó correctamente
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Prueba la conexión sin establecerla permanentemente.
        
        Returns:
            True si la conexión es posible
        """
        pass
    
    @abstractmethod
    async def capture_snapshot(self) -> Optional[bytes]:
        """
        Captura un snapshot de la cámara.
        
        Returns:
            Datos de imagen en bytes o None si falla
        """
        pass
    
    @abstractmethod
    async def start_streaming(self) -> bool:
        """
        Inicia el streaming de video.
        
        Returns:
            True si el streaming se inició exitosamente
        """
        pass
    
    @abstractmethod
    async def stop_streaming(self) -> bool:
        """
        Detiene el streaming de video.
        
        Returns:
            True si el streaming se detuvo exitosamente
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> ProtocolCapabilities:
        """
        Obtiene las capacidades del protocolo.
        
        Returns:
            Capacidades del protocolo
        """
        pass
    
    def add_frame_callback(self, callback: Callable[[Any], None]):
        """Agrega callback para frames recibidos."""
        self._frame_callbacks.append(callback)
    
    def remove_frame_callback(self, callback: Callable[[Any], None]):
        """Remueve callback de frames."""
        if callback in self._frame_callbacks:
            self._frame_callbacks.remove(callback)
    
    def _notify_frame_callbacks(self, frame: Any):
        """Notifica a todos los callbacks de frame."""
        for callback in self._frame_callbacks:
            try:
                callback(frame)
            except Exception as e:
                self.logger.error(f"Error en callback de frame: {str(e)}")
    
    def _set_state(self, new_state: ConnectionState):
        """Cambia el estado de la conexión."""
        old_state = self._state
        self._state = new_state
        if old_state != new_state:
            self.logger.info(f"Estado cambiado: {old_state.value} → {new_state.value}")


class ONVIFProtocolHandler(BaseProtocolHandler):
    """
    Manejador de protocolo ONVIF.
    
    Implementa conexión completa usando el estándar ONVIF para cámaras compatibles.
    """
    
    def __init__(self, config: ConnectionConfig, streaming_config: StreamingConfig = None):
        """Inicializa el manejador ONVIF."""
        super().__init__(config, streaming_config)
        
        if not ONVIF_AVAILABLE:
            raise ImportError("Dependencias ONVIF no disponibles. Instala: pip install onvif-zeep")
        
        self._camera: Optional[ONVIFCamera] = None
        self._media_service = None
        self._device_service = None
        self._profiles = []
        self._snapshot_uri: Optional[str] = None
        self._stream_uri: Optional[str] = None
    
    async def connect(self) -> bool:
        """Establece conexión ONVIF."""
        self._set_state(ConnectionState.CONNECTING)
        
        try:
            self.logger.info(f"Conectando ONVIF a {self.config.ip}:{self.config.port}")
            
            # Crear cámara ONVIF en thread separado para evitar bloqueo
            loop = asyncio.get_event_loop()
            self._camera = await loop.run_in_executor(
                None,
                self._create_onvif_camera
            )
            
            # Crear servicios
            self._device_service = self._camera.create_devicemgmt_service()
            self._media_service = self._camera.create_media_service()
            
            # Verificar conexión
            device_info = await loop.run_in_executor(
                None,
                self._device_service.GetDeviceInformation
            )
            
            self.logger.info(f"Conectado a {device_info.Manufacturer} {device_info.Model}")
            
            # Obtener perfiles
            self._profiles = await loop.run_in_executor(
                None,
                self._media_service.GetProfiles
            )
            
            # Configurar URIs
            await self._setup_media_uris()
            
            self._set_state(ConnectionState.CONNECTED)
            return True
            
        except Exception as e:
            self.logger.error(f"Error de conexión ONVIF: {str(e)}")
            self._set_state(ConnectionState.ERROR)
            return False
    
    def _create_onvif_camera(self) -> ONVIFCamera:
        """Crea la instancia de cámara ONVIF (operación bloqueante)."""
        return ONVIFCamera(
            self.config.ip,
            self.config.port,
            self.config.username,
            self.config.password
        )
    
    async def _setup_media_uris(self):
        """Configura URIs de snapshot y streaming."""
        if not self._profiles:
            self.logger.warning("No hay perfiles de media disponibles")
            return
        
        try:
            # Usar primer perfil
            profile = self._profiles[0]
            profile_token = self._get_profile_token(profile)
            
            # Configurar snapshot URI
            try:
                loop = asyncio.get_event_loop()
                snapshot_uri = await loop.run_in_executor(
                    None,
                    lambda: self._media_service.GetSnapshotUri({'ProfileToken': profile_token})
                )
                self._snapshot_uri = snapshot_uri.Uri
                self.logger.info(f"Snapshot URI: {self._snapshot_uri}")
            except Exception as e:
                self.logger.warning(f"No se pudo obtener Snapshot URI: {str(e)}")
            
            # Configurar stream URI
            try:
                stream_uri = await loop.run_in_executor(
                    None,
                    lambda: self._media_service.GetStreamUri({
                        'StreamSetup': {
                            'Stream': 'RTP-Unicast',
                            'Transport': {'Protocol': 'RTSP'}
                        },
                        'ProfileToken': profile_token
                    })
                )
                self._stream_uri = stream_uri.Uri
                self.logger.info(f"Stream URI: {self._stream_uri}")
            except Exception as e:
                self.logger.warning(f"No se pudo obtener Stream URI: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error configurando URIs: {str(e)}")
    
    def _get_profile_token(self, profile) -> str:
        """Obtiene el token del perfil."""
        if hasattr(profile, '_token'):
            return profile._token
        elif hasattr(profile, 'token'):
            return profile.token
        else:
            return getattr(profile, 'Name', 'MainProfile')
    
    async def disconnect(self) -> bool:
        """Desconecta ONVIF."""
        try:
            # Detener streaming si está activo
            if self.is_streaming:
                await self.stop_streaming()
            
            # Limpiar recursos
            self._camera = None
            self._media_service = None
            self._device_service = None
            self._profiles = []
            self._snapshot_uri = None
            self._stream_uri = None
            
            self._set_state(ConnectionState.DISCONNECTED)
            self.logger.info("Desconectado ONVIF")
            return True
            
        except Exception as e:
            self.logger.error(f"Error desconectando ONVIF: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Prueba conexión ONVIF."""
        try:
            # Conexión temporal
            test_camera = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ONVIFCamera(
                    self.config.ip,
                    self.config.port,
                    self.config.username,
                    self.config.password
                )
            )
            
            # Probar servicio básico
            device_service = test_camera.create_devicemgmt_service()
            await asyncio.get_event_loop().run_in_executor(
                None,
                device_service.GetDeviceInformation
            )
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Test de conexión ONVIF falló: {str(e)}")
            return False
    
    async def capture_snapshot(self) -> Optional[bytes]:
        """Captura snapshot via ONVIF."""
        if not self.is_connected or not self._snapshot_uri:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    self._snapshot_uri,
                    auth=requests.auth.HTTPDigestAuth(self.config.username, self.config.password),
                    timeout=10
                )
            )
            
            if response.status_code == 200:
                return response.content
            else:
                self.logger.error(f"Error en snapshot: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturando snapshot: {str(e)}")
            return None
    
    async def start_streaming(self) -> bool:
        """Inicia streaming ONVIF/RTSP."""
        if not self.is_connected or not self._stream_uri:
            return False
        
        try:
            # Crear captura de video en thread separado
            loop = asyncio.get_event_loop()
            self._stream_handle = await loop.run_in_executor(
                None,
                lambda: cv2.VideoCapture(self._stream_uri)
            )
            
            if not self._stream_handle.isOpened():
                self.logger.error("No se pudo abrir stream de video")
                return False
            
            # Iniciar thread de streaming
            self._streaming_active = True
            self._streaming_thread = threading.Thread(
                target=self._streaming_worker,
                daemon=True
            )
            self._streaming_thread.start()
            
            self._set_state(ConnectionState.STREAMING)
            self.logger.info("Streaming ONVIF iniciado")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando streaming: {str(e)}")
            return False
    
    async def stop_streaming(self) -> bool:
        """Detiene streaming ONVIF."""
        try:
            self._streaming_active = False
            
            if self._streaming_thread and self._streaming_thread.is_alive():
                self._streaming_thread.join(timeout=5)
            
            if self._stream_handle:
                self._stream_handle.release()
                self._stream_handle = None
            
            self._set_state(ConnectionState.CONNECTED)
            self.logger.info("Streaming ONVIF detenido")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deteniendo streaming: {str(e)}")
            return False
    
    def _streaming_worker(self):
        """Worker thread para streaming de video."""
        frame_times = []
        
        while self._streaming_active and self._stream_handle:
            try:
                ret, frame = self._stream_handle.read()
                
                if ret and frame is not None:
                    # Calcular FPS
                    current_time = time.time()
                    frame_times.append(current_time)
                    
                    # Mantener ventana de 30 frames para FPS
                    if len(frame_times) > 30:
                        frame_times.pop(0)
                    
                    if len(frame_times) >= 2:
                        time_diff = frame_times[-1] - frame_times[0]
                        if time_diff > 0:
                            self._fps = (len(frame_times) - 1) / time_diff
                    
                    self._frame_count += 1
                    self._last_frame_time = datetime.now()
                    
                    # Notificar callbacks
                    self._notify_frame_callbacks(frame)
                else:
                    time.sleep(0.001)  # Evitar CPU intensivo
                    
            except Exception as e:
                if self._streaming_active:
                    self.logger.error(f"Error en streaming worker: {str(e)}")
                break
    
    def get_capabilities(self) -> ProtocolCapabilities:
        """Obtiene capacidades ONVIF."""
        return ProtocolCapabilities(
            supports_streaming=True,
            supports_snapshots=True,
            supports_ptz=True,
            supports_audio=True,
            max_resolution="1920x1080",
            supported_codecs=["H264", "H265", "MJPEG"]
        )


class RTSPProtocolHandler(BaseProtocolHandler):
    """
    Manejador de protocolo RTSP directo.
    
    Implementa conexión RTSP para streaming de video sin ONVIF.
    """
    
    async def connect(self) -> bool:
        """Establece conexión RTSP."""
        self._set_state(ConnectionState.CONNECTING)
        
        try:
            # Construir URL RTSP
            rtsp_url = self._build_rtsp_url()
            
            # Probar conexión
            loop = asyncio.get_event_loop()
            test_cap = await loop.run_in_executor(
                None,
                lambda: cv2.VideoCapture(rtsp_url)
            )
            
            if test_cap.isOpened():
                test_cap.release()
                self._connection_handle = rtsp_url
                self._set_state(ConnectionState.CONNECTED)
                self.logger.info(f"Conectado RTSP: {rtsp_url}")
                return True
            else:
                raise ConnectionError("No se pudo abrir stream RTSP")
                
        except Exception as e:
            self.logger.error(f"Error de conexión RTSP: {str(e)}")
            self._set_state(ConnectionState.ERROR)
            return False
    
    def _build_rtsp_url(self) -> str:
        """Construye URL RTSP."""
        # URLs comunes por marca
        rtsp_patterns = {
            "dahua": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:554/cam/realmonitor?channel=1&subtype=0",
            "tplink": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:554/stream1",
            "hikvision": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:554/Streaming/Channels/101",
            "generic": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:554/stream"
        }
        
        # Detectar marca desde config o usar genérico
        brand = getattr(self.config, 'brand', 'generic').lower()
        return rtsp_patterns.get(brand, rtsp_patterns['generic'])
    
    async def disconnect(self) -> bool:
        """Desconecta RTSP."""
        try:
            if self.is_streaming:
                await self.stop_streaming()
            
            self._connection_handle = None
            self._set_state(ConnectionState.DISCONNECTED)
            return True
            
        except Exception as e:
            self.logger.error(f"Error desconectando RTSP: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Prueba conexión RTSP."""
        try:
            rtsp_url = self._build_rtsp_url()
            loop = asyncio.get_event_loop()
            test_cap = await loop.run_in_executor(
                None,
                lambda: cv2.VideoCapture(rtsp_url)
            )
            
            is_open = test_cap.isOpened()
            test_cap.release()
            return is_open
            
        except Exception:
            return False
    
    async def capture_snapshot(self) -> Optional[bytes]:
        """Captura snapshot desde stream RTSP."""
        if not self.is_connected:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            cap = await loop.run_in_executor(
                None,
                lambda: cv2.VideoCapture(self._connection_handle)
            )
            
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                # Convertir a bytes
                _, buffer = cv2.imencode('.jpg', frame)
                return buffer.tobytes()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error capturando snapshot RTSP: {str(e)}")
            return None
    
    async def start_streaming(self) -> bool:
        """Inicia streaming RTSP."""
        if not self.is_connected:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            self._stream_handle = await loop.run_in_executor(
                None,
                lambda: cv2.VideoCapture(self._connection_handle)
            )
            
            if not self._stream_handle.isOpened():
                return False
            
            self._streaming_active = True
            self._streaming_thread = threading.Thread(
                target=self._streaming_worker,
                daemon=True
            )
            self._streaming_thread.start()
            
            self._set_state(ConnectionState.STREAMING)
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando streaming RTSP: {str(e)}")
            return False
    
    async def stop_streaming(self) -> bool:
        """Detiene streaming RTSP."""
        try:
            self._streaming_active = False
            
            if self._streaming_thread:
                self._streaming_thread.join(timeout=5)
            
            if self._stream_handle:
                self._stream_handle.release()
                self._stream_handle = None
            
            self._set_state(ConnectionState.CONNECTED)
            return True
            
        except Exception as e:
            self.logger.error(f"Error deteniendo streaming RTSP: {str(e)}")
            return False
    
    def _streaming_worker(self):
        """Worker thread para streaming RTSP."""
        frame_times = []
        
        while self._streaming_active and self._stream_handle:
            try:
                ret, frame = self._stream_handle.read()
                
                if ret and frame is not None:
                    current_time = time.time()
                    frame_times.append(current_time)
                    
                    if len(frame_times) > 30:
                        frame_times.pop(0)
                    
                    if len(frame_times) >= 2:
                        time_diff = frame_times[-1] - frame_times[0]
                        if time_diff > 0:
                            self._fps = (len(frame_times) - 1) / time_diff
                    
                    self._frame_count += 1
                    self._last_frame_time = datetime.now()
                    
                    self._notify_frame_callbacks(frame)
                else:
                    time.sleep(0.001)
                    
            except Exception as e:
                if self._streaming_active:
                    self.logger.error(f"Error en streaming RTSP: {str(e)}")
                break
    
    def get_capabilities(self) -> ProtocolCapabilities:
        """Obtiene capacidades RTSP."""
        return ProtocolCapabilities(
            supports_streaming=True,
            supports_snapshots=True,
            supports_ptz=False,
            supports_audio=False,
            max_resolution="1920x1080",
            supported_codecs=["H264", "MJPEG"]
        )


class ProtocolService:
    """
    Servicio principal de gestión de protocolos de cámara.
    
    Coordina diferentes manejadores de protocolo y proporciona
    una interfaz unificada para conexiones de cámaras.
    """
    
    def __init__(self):
        """Inicializa el servicio de protocolos."""
        self.logger = logging.getLogger("ProtocolService")
        
        # Registro de manejadores de protocolo
        self._protocol_handlers: Dict[ProtocolType, type] = {
            ProtocolType.ONVIF: ONVIFProtocolHandler,
            ProtocolType.RTSP: RTSPProtocolHandler,
            # TODO: Agregar más protocolos según se implementen
        }
        
        # Instancias activas
        self._active_handlers: Dict[str, BaseProtocolHandler] = {}
        
    def get_supported_protocols(self) -> List[ProtocolType]:
        """Obtiene lista de protocolos soportados."""
        supported = []
        
        for protocol in self._protocol_handlers:
            if protocol == ProtocolType.ONVIF and not ONVIF_AVAILABLE:
                continue
            supported.append(protocol)
        
        return supported
    
    async def detect_protocols(self, config: ConnectionConfig) -> List[ProtocolType]:
        """
        Detecta protocolos soportados por una cámara.
        
        Args:
            config: Configuración de conexión
            
        Returns:
            Lista de protocolos detectados
        """
        detected = []
        
        for protocol in self.get_supported_protocols():
            try:
                handler = self._create_handler(protocol, config)
                if await handler.test_connection():
                    detected.append(protocol)
                    self.logger.info(f"Protocolo detectado: {protocol.value}")
            except Exception as e:
                self.logger.debug(f"Error probando {protocol.value}: {str(e)}")
        
        return detected
    
    async def create_connection(self, camera_id: str, protocol: ProtocolType, 
                              config: ConnectionConfig, 
                              streaming_config: StreamingConfig = None) -> Optional[BaseProtocolHandler]:
        """
        Crea una conexión usando el protocolo especificado.
        
        Args:
            camera_id: ID único de la cámara
            protocol: Protocolo a usar
            config: Configuración de conexión
            streaming_config: Configuración de streaming
            
        Returns:
            Manejador de protocolo conectado o None si falla
        """
        if protocol not in self._protocol_handlers:
            self.logger.error(f"Protocolo no soportado: {protocol}")
            return None
        
        try:
            handler = self._create_handler(protocol, config, streaming_config)
            
            if await handler.connect():
                self._active_handlers[camera_id] = handler
                self.logger.info(f"Conexión {protocol.value} establecida para {camera_id}")
                return handler
            else:
                self.logger.error(f"Falló conexión {protocol.value} para {camera_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creando conexión {protocol.value}: {str(e)}")
            return None
    
    def _create_handler(self, protocol: ProtocolType, config: ConnectionConfig, 
                       streaming_config: StreamingConfig = None) -> BaseProtocolHandler:
        """Crea instancia de manejador de protocolo."""
        handler_class = self._protocol_handlers[protocol]
        return handler_class(config, streaming_config)
    
    async def disconnect_camera(self, camera_id: str) -> bool:
        """
        Desconecta una cámara específica.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se desconectó exitosamente
        """
        if camera_id not in self._active_handlers:
            return True
        
        try:
            handler = self._active_handlers[camera_id]
            success = await handler.disconnect()
            
            if success:
                del self._active_handlers[camera_id]
                self.logger.info(f"Cámara {camera_id} desconectada")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error desconectando {camera_id}: {str(e)}")
            return False
    
    def get_handler(self, camera_id: str) -> Optional[BaseProtocolHandler]:
        """Obtiene el manejador activo para una cámara."""
        return self._active_handlers.get(camera_id)
    
    def get_active_connections(self) -> Dict[str, BaseProtocolHandler]:
        """Obtiene todas las conexiones activas."""
        return self._active_handlers.copy()
    
    async def cleanup(self):
        """Limpia todas las conexiones activas."""
        for camera_id in list(self._active_handlers.keys()):
            await self.disconnect_camera(camera_id)
        
        self.logger.info("ProtocolService limpio")


# Factory function singleton
_protocol_service_instance: Optional[ProtocolService] = None


def get_protocol_service() -> ProtocolService:
    """Obtiene la instancia singleton del ProtocolService."""
    global _protocol_service_instance
    if _protocol_service_instance is None:
        _protocol_service_instance = ProtocolService()
    return _protocol_service_instance 