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

# RTSP no es un paquete real, se maneja con cv2
RTSP_AVAILABLE = True  # cv2 maneja RTSP directamente

try:
    from ..models import CameraModel, ConnectionConfig
except ImportError:
    # Fallback para ejecución directa
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from models import CameraModel, ConnectionConfig


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
    supported_codecs: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.supported_codecs is None:
            self.supported_codecs = ["H264"]


class BaseProtocolHandler(ABC):
    """
    Clase base abstracta para manejadores de protocolos de cámara.
    
    Define la interfaz común para todos los protocolos de conexión.
    """
    
    def __init__(self, config: ConnectionConfig, streaming_config: Optional[StreamingConfig] = None):
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
    
    async def get_device_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del dispositivo.
        
        Returns:
            Información del dispositivo o None si no está disponible
        """
        # Implementación por defecto - información básica
        return {
            'ip': self.config.ip,
            'protocol': self.__class__.__name__,
            'status': self.state.value,
            'connected': self.is_connected
        }
    
    async def ptz_control(self, action: str, speed: int = 3) -> bool:
        """
        Controla movimientos PTZ de la cámara.
        
        Args:
            action: Acción PTZ ('up', 'down', 'left', 'right', 'zoom_in', 'zoom_out', 'stop')
            speed: Velocidad del movimiento (1-8)
            
        Returns:
            True si el comando fue enviado exitosamente
        """
        # Implementación por defecto - no soportado
        self.logger.warning(f"PTZ control not supported by {self.__class__.__name__}")
        return False
    
    def get_mjpeg_stream_url(self, channel: int = 0, subtype: int = 0) -> Optional[str]:
        """
        Obtiene URL de stream MJPEG.
        
        Args:
            channel: Canal de la cámara
            subtype: Subtipo de stream
            
        Returns:
            URL del stream MJPEG o None
        """
        # Implementación por defecto - no soportado
        self.logger.warning(f"MJPEG streaming not supported by {self.__class__.__name__}")
        return None
    
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
    
    def __init__(self, config: ConnectionConfig, streaming_config: Optional[StreamingConfig] = None):
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
            self.logger.info(f"Conectando ONVIF a {self.config.ip}:{self.config.onvif_port}")
            
            # Crear cámara ONVIF en thread separado para evitar bloqueo
            loop = asyncio.get_event_loop()
            self._camera = await loop.run_in_executor(
                None,
                self._create_onvif_camera
            )
            
            if not self._camera:
                raise ConnectionError("No se pudo crear cámara ONVIF")
            
            # Crear servicios
            self._device_service = self._camera.create_devicemgmt_service()
            self._media_service = self._camera.create_media_service()
            
            # Verificar conexión
            device_info = await loop.run_in_executor(
                None,
                self._device_service.GetDeviceInformation
            )
            
            if device_info and hasattr(device_info, 'Manufacturer') and hasattr(device_info, 'Model'):
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
    
    def _create_onvif_camera(self) -> Optional[ONVIFCamera]:
        """Crea la instancia de cámara ONVIF (operación bloqueante)."""
        try:
            return ONVIFCamera(
                self.config.ip,
                self.config.onvif_port,
                self.config.username,
                self.config.password
            )
        except Exception as e:
            self.logger.error(f"Error creando cámara ONVIF: {str(e)}")
            return None
    
    async def _setup_media_uris(self):
        """Configura URIs de snapshot y streaming."""
        if not self._profiles or not self._media_service:
            self.logger.warning("No hay perfiles de media disponibles")
            return
        
        try:
            # Usar primer perfil
            profile = self._profiles[0]
            profile_token = self._get_profile_token(profile)
            
            # Configurar snapshot URI
            if self._media_service:
                try:
                    loop = asyncio.get_event_loop()
                    media_service = self._media_service  # Variable local para el linter
                    snapshot_uri = await loop.run_in_executor(
                        None,
                        lambda: media_service.GetSnapshotUri({'ProfileToken': profile_token})
                    )
                    if snapshot_uri and hasattr(snapshot_uri, 'Uri'):
                        self._snapshot_uri = snapshot_uri.Uri
                        self.logger.info(f"Snapshot URI: {self._snapshot_uri}")
                except Exception as e:
                    self.logger.warning(f"No se pudo obtener Snapshot URI: {str(e)}")
            
            # Configurar stream URI
            if self._media_service:
                try:
                    media_service = self._media_service  # Variable local para el linter
                    stream_uri = await loop.run_in_executor(
                        None,
                        lambda: media_service.GetStreamUri({
                            'StreamSetup': {
                                'Stream': 'RTP-Unicast',
                                'Transport': {'Protocol': 'RTSP'}
                            },
                            'ProfileToken': profile_token
                        })
                    )
                    if stream_uri and hasattr(stream_uri, 'Uri'):
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
                    self.config.onvif_port,
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
        
        if not self._snapshot_uri:
            return None
            
        try:
            from requests.auth import HTTPDigestAuth
            loop = asyncio.get_event_loop()
            snapshot_uri = str(self._snapshot_uri)  # Cast para el linter
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    snapshot_uri,
                    auth=HTTPDigestAuth(self.config.username, self.config.password),
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
        
        if not self._stream_uri:
            return False
            
        try:
            # Crear captura de video en thread separado
            loop = asyncio.get_event_loop()
            stream_uri = str(self._stream_uri)  # Cast para el linter
            self._stream_handle = await loop.run_in_executor(
                None,
                lambda: cv2.VideoCapture(stream_uri)
            )
            
            if not self._stream_handle or not self._stream_handle.isOpened():
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
            
            if test_cap and test_cap.isOpened():
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
            "dahua": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/cam/realmonitor?channel=1&subtype=0",
            "tplink": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/stream1",
            "hikvision": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/Streaming/Channels/101",
            "generic": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/stream"
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
            
            is_open = test_cap and test_cap.isOpened()
            if test_cap:
                test_cap.release()
            return is_open
            
        except Exception:
            return False
    
    async def capture_snapshot(self) -> Optional[bytes]:
        """Captura snapshot desde stream RTSP."""
        if not self.is_connected or not self._connection_handle:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            cap = await loop.run_in_executor(
                None,
                lambda: cv2.VideoCapture(str(self._connection_handle))
            )
            
            if not cap:
                return None
                
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
        if not self.is_connected or not self._connection_handle:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            self._stream_handle = await loop.run_in_executor(
                None,
                lambda: cv2.VideoCapture(str(self._connection_handle))
            )
            
            if not self._stream_handle or not self._stream_handle.isOpened():
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
    Servicio principal para gestión de protocolos de conexión de cámaras.
    
    Proporciona una interfaz unificada para:
    - Crear conexiones con diferentes protocolos
    - Detectar protocolos soportados
    - Gestionar conexiones activas
    - Obtener información de dispositivos
    - Testing y diagnóstico
    """
    
    def __init__(self):
        """Inicializa el servicio de protocolos."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Manejadores de protocolos disponibles
        self._protocol_handlers = {
            ProtocolType.ONVIF: self._get_onvif_handler,
            ProtocolType.RTSP: self._get_rtsp_handler,
            ProtocolType.AMCREST: self._get_amcrest_handler,
        }
        
        # Conexiones activas
        self._active_connections: Dict[str, BaseProtocolHandler] = {}
        
        # Cache para información de dispositivos
        self._device_info_cache: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("ProtocolService initialized")

    def get_supported_protocols(self) -> List[ProtocolType]:
        """Obtiene lista de protocolos soportados."""
        return list(self._protocol_handlers.keys())

    async def detect_protocols(self, config: ConnectionConfig) -> List[ProtocolType]:
        """
        Detecta automáticamente protocolos soportados por una cámara.
        
        Args:
            config: Configuración de conexión
            
        Returns:
            Lista de protocolos soportados
        """
        supported_protocols = []
        
        for protocol in self._protocol_handlers.keys():
            try:
                handler = self._create_handler(protocol, config)
                if await handler.test_connection():
                    supported_protocols.append(protocol)
                    self.logger.info(f"Protocol {protocol.value} detected for {config.ip}")
            except Exception as e:
                self.logger.debug(f"Protocol {protocol.value} not supported: {e}")
        
        return supported_protocols

    async def create_connection(self, camera_id: str, protocol: ProtocolType, 
                              config: ConnectionConfig, 
                              streaming_config: Optional[StreamingConfig] = None) -> Optional[BaseProtocolHandler]:
        """
        Crea una conexión con la cámara usando el protocolo especificado.
        
        Args:
            camera_id: Identificador único de la cámara
            protocol: Protocolo a usar
            config: Configuración de conexión
            streaming_config: Configuración de streaming opcional
            
        Returns:
            Manejador de protocolo conectado o None si falla
        """
        try:
            # Verificar si ya existe una conexión activa
            if camera_id in self._active_connections:
                existing_handler = self._active_connections[camera_id]
                if existing_handler.is_connected:
                    self.logger.info(f"Connection already active for {camera_id}")
                    return existing_handler
                else:
                    # Limpiar conexión anterior
                    await existing_handler.disconnect()
                    del self._active_connections[camera_id]
            
            # Crear nuevo manejador
            handler = self._create_handler(protocol, config, streaming_config)
            
            # Intentar conectar
            if await handler.connect():
                self._active_connections[camera_id] = handler
                self.logger.info(f"Connection established for {camera_id} using {protocol.value}")
                return handler
            else:
                self.logger.error(f"Failed to connect {camera_id} using {protocol.value}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating connection for {camera_id}: {e}")
            return None

    def _create_handler(self, protocol: ProtocolType, config: ConnectionConfig, 
                       streaming_config: Optional[StreamingConfig] = None) -> BaseProtocolHandler:
        """
        Crea un manejador de protocolo específico.
        
        Args:
            protocol: Protocolo a usar
            config: Configuración de conexión
            streaming_config: Configuración de streaming opcional
            
        Returns:
            Manejador de protocolo creado
        """
        # Buscar protocolo por valor en lugar de por identidad de objeto
        matching_protocol = None
        for available_protocol in self._protocol_handlers.keys():
            if available_protocol.value == protocol.value:
                matching_protocol = available_protocol
                break
        
        if matching_protocol is None:
            raise ValueError(f"Protocol {protocol.value} not supported")
        
        # Usar el protocolo encontrado en el diccionario
        protocol = matching_protocol
        
        # Obtener la función que devuelve la clase del handler
        handler_factory = self._protocol_handlers[protocol]
        handler_class = handler_factory()
        return handler_class(config, streaming_config)

    async def disconnect_camera(self, camera_id: str) -> bool:
        """
        Desconecta una cámara específica.
        
        Args:
            camera_id: Identificador de la cámara
            
        Returns:
            True si se desconectó correctamente
        """
        if camera_id in self._active_connections:
            handler = self._active_connections[camera_id]
            try:
                success = await handler.disconnect()
                if success:
                    del self._active_connections[camera_id]
                    self.logger.info(f"Camera {camera_id} disconnected")
                return success
            except Exception as e:
                self.logger.error(f"Error disconnecting {camera_id}: {e}")
                return False
        return True

    def get_handler(self, camera_id: str) -> Optional[BaseProtocolHandler]:
        """Obtiene el manejador de una cámara específica."""
        return self._active_connections.get(camera_id)

    def get_active_connections(self) -> Dict[str, BaseProtocolHandler]:
        """Obtiene todas las conexiones activas."""
        return self._active_connections.copy()

    async def cleanup(self):
        """Limpia todas las conexiones activas."""
        for camera_id in list(self._active_connections.keys()):
            await self.disconnect_camera(camera_id)
        self._device_info_cache.clear()

    # ==========================================
    # MÉTODOS NUEVOS PARA COMPATIBILIDAD COMPLETA
    # ==========================================

    async def get_device_info(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada del dispositivo.
        
        Args:
            camera_id: Identificador de la cámara
            
        Returns:
            Información del dispositivo o None si no está disponible
        """
        # Verificar cache primero
        if camera_id in self._device_info_cache:
            return self._device_info_cache[camera_id].copy()
        
        handler = self.get_handler(camera_id)
        if not handler:
            self.logger.warning(f"No active handler for {camera_id}")
            return None
        
        try:
            # Intentar obtener información del dispositivo
            if hasattr(handler, 'get_device_info'):
                device_info = await handler.get_device_info()
                if device_info:
                    # Cache para futuras consultas
                    self._device_info_cache[camera_id] = device_info.copy()
                    return device_info
            
            # Fallback: información básica de conexión
            return {
                'ip': handler.config.ip,
                'protocol': handler.__class__.__name__,
                'status': handler.state.value,
                'connected': handler.is_connected
            }
            
        except Exception as e:
            self.logger.error(f"Error getting device info for {camera_id}: {e}")
            return None

    async def get_onvif_profiles(self, camera_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene perfiles ONVIF detallados.
        
        Args:
            camera_id: Identificador de la cámara
            
        Returns:
            Lista de perfiles ONVIF o None si no está disponible
        """
        handler = self.get_handler(camera_id)
        if not handler or not hasattr(handler, '_profiles'):
            self.logger.warning(f"No ONVIF profiles available for {camera_id}")
            return None
        
        try:
            # Verificar que es un handler ONVIF
            if not hasattr(handler, '_get_profile_token'):
                self.logger.warning(f"Handler is not ONVIF for {camera_id}")
                return None
            
            profiles = []
            for profile in handler._profiles:  # type: ignore
                profile_data = {
                    'token': handler._get_profile_token(profile),  # type: ignore
                    'name': getattr(profile, 'Name', 'Unknown'),
                    'fixed': getattr(profile, 'fixed', False)
                }
                
                # Información de video
                if hasattr(profile, 'VideoEncoderConfiguration'):
                    venc = profile.VideoEncoderConfiguration
                    profile_data['video'] = {
                        'encoding': getattr(venc, 'Encoding', 'Unknown'),
                        'resolution': {
                            'width': getattr(venc.Resolution, 'Width', 0) if hasattr(venc, 'Resolution') else 0,
                            'height': getattr(venc.Resolution, 'Height', 0) if hasattr(venc, 'Resolution') else 0
                        } if hasattr(venc, 'Resolution') else None,
                        'quality': getattr(venc, 'Quality', 0),
                        'framerate': getattr(venc.RateControl, 'FrameRateLimit', 0) if hasattr(venc, 'RateControl') else 0,
                        'bitrate': getattr(venc.RateControl, 'BitrateLimit', 0) if hasattr(venc, 'RateControl') else 0
                    }
                
                # Información de audio
                if hasattr(profile, 'AudioEncoderConfiguration'):
                    aenc = profile.AudioEncoderConfiguration
                    profile_data['audio'] = {
                        'encoding': getattr(aenc, 'Encoding', 'Unknown'),
                        'bitrate': getattr(aenc, 'Bitrate', 0),
                        'samplerate': getattr(aenc, 'SampleRate', 0)
                    }
                
                # URLs de stream y snapshot
                if hasattr(handler, '_stream_uri') and getattr(handler, '_stream_uri', None):
                    profile_data['stream_uri'] = str(getattr(handler, '_stream_uri'))
                if hasattr(handler, '_snapshot_uri') and getattr(handler, '_snapshot_uri', None):
                    profile_data['snapshot_uri'] = str(getattr(handler, '_snapshot_uri'))
                
                profiles.append(profile_data)
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"Error obteniendo perfiles ONVIF: {e}")
            return None

    def create_test_connection(self, ip: str, protocol: str, credentials: dict) -> Optional[BaseProtocolHandler]:
        """
        Método de conveniencia para testing rápido.
        
        Args:
            ip: Dirección IP de la cámara
            protocol: Protocolo a usar ('onvif', 'rtsp', 'amcrest')
            credentials: Credenciales {'username': 'admin', 'password': 'password'}
            
        Returns:
            Manejador de protocolo o None si falla
        """
        try:
            # Convertir string a ProtocolType
            protocol_type = ProtocolType(protocol.lower())
            
            # Crear configuración
            config = ConnectionConfig(
                ip=ip,
                username=credentials.get('username', 'admin'),
                password=credentials.get('password', '')
            )
            
            # Crear handler sin conectar
            handler = self._create_handler(protocol_type, config)
            
            self.logger.info(f"Test connection created for {ip} using {protocol}")
            return handler
            
        except Exception as e:
            self.logger.error(f"Error creating test connection for {ip}: {e}")
            return None

    async def test_connection_async(self, ip: str, protocol: str, credentials: dict) -> bool:
        """
        Prueba conexión de forma asíncrona.
        
        Args:
            ip: Dirección IP de la cámara
            protocol: Protocolo a usar
            credentials: Credenciales
            
        Returns:
            True si la conexión es posible
        """
        try:
            handler = self.create_test_connection(ip, protocol, credentials)
            if handler:
                return await handler.test_connection()
            return False
        except Exception as e:
            self.logger.error(f"Error testing connection for {ip}: {e}")
            return False

    async def get_device_info_async(self, ip: str, protocol: str, credentials: dict) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del dispositivo de forma asíncrona.
        
        Args:
            ip: Dirección IP de la cámara
            protocol: Protocolo a usar
            credentials: Credenciales
            
        Returns:
            Información del dispositivo o None
        """
        try:
            handler = self.create_test_connection(ip, protocol, credentials)
            if handler and await handler.connect():
                device_info = await handler.get_device_info()
                await handler.disconnect()
                return device_info
            return None
        except Exception as e:
            self.logger.error(f"Error getting device info for {ip}: {e}")
            return None

    async def ptz_control(self, camera_id: str, action: str, speed: int = 3) -> bool:
        """
        Controla movimientos PTZ de la cámara.
        
        Args:
            camera_id: Identificador de la cámara
            action: Acción PTZ ('up', 'down', 'left', 'right', 'zoom_in', 'zoom_out', 'stop')
            speed: Velocidad del movimiento (1-8)
            
        Returns:
            True si el comando fue enviado exitosamente
        """
        handler = self.get_handler(camera_id)
        if not handler:
            self.logger.warning(f"No active handler for {camera_id}")
            return False
        
        try:
            if hasattr(handler, 'ptz_control'):
                return await handler.ptz_control(action, speed)
            else:
                self.logger.warning(f"PTZ control not supported for {camera_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error in PTZ control for {camera_id}: {e}")
            return False

    def get_mjpeg_stream_url(self, camera_id: str, channel: int = 0, subtype: int = 0) -> Optional[str]:
        """
        Obtiene URL de stream MJPEG.
        
        Args:
            camera_id: Identificador de la cámara
            channel: Canal de la cámara
            subtype: Subtipo de stream
            
        Returns:
            URL del stream MJPEG o None
        """
        handler = self.get_handler(camera_id)
        if not handler:
            self.logger.warning(f"No active handler for {camera_id}")
            return None
        
        try:
            if hasattr(handler, 'get_mjpeg_stream_url'):
                return handler.get_mjpeg_stream_url(channel, subtype)
            else:
                self.logger.warning(f"MJPEG streaming not supported for {camera_id}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting MJPEG URL for {camera_id}: {e}")
            return None

    def _detect_brand_from_ip(self, ip: str) -> str:
        """
        Detecta marca de cámara basado en IP o configuración.
        
        Args:
            ip: Dirección IP de la cámara
            
        Returns:
            Marca detectada ('dahua', 'tplink', 'steren', 'generic')
        """
        # Lógica simple de detección - se puede mejorar
        # Por ahora retornar 'dahua' como default
        return "dahua"

    def _get_onvif_handler(self):
        """Obtiene manejador ONVIF."""
        return ONVIFProtocolHandler

    def _get_rtsp_handler(self):
        """Obtiene manejador RTSP."""
        return RTSPProtocolHandler

    def _get_amcrest_handler(self):
        """Obtiene manejador Amcrest."""
        # Por ahora retornar RTSP como fallback para Amcrest
        # TODO: Implementar AmcrestProtocolHandler específico
        return RTSPProtocolHandler 