"""
Camera Model - MVP Architecture
===============================

Modelo de dominio que representa una cámara IP con toda su configuración,
estado de conexión, capacidades y metadatos. Este es el model principal 
de la aplicación en la arquitectura MVP.

Responsabilidades:
- Encapsular datos y lógica de una cámara individual
- Gestionar estado de conexión y streaming
- Validar configuración de cámara
- Proporcionar interfaz limpia para Presenters
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import ipaddress

from utils.exceptions import (
    ValidationError,
    InvalidIPAddressError,
    MissingRequiredFieldError,
    InvalidPortError
)
from utils.constants import DefaultPorts, DefaultCredentials, SystemLimits
from utils.id_generator import generate_camera_id


class ConnectionStatus(Enum):
    """Estados de conexión de una cámara."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    STREAMING = "streaming"
    UNAVAILABLE = "unavailable"


class ProtocolType(Enum):
    """Tipos de protocolo soportados."""
    RTSP = "rtsp"
    ONVIF = "onvif"
    HTTP = "http"
    AMCREST = "amcrest"
    GENERIC = "generic"


@dataclass
class ConnectionConfig:
    """Configuración de conexión de cámara."""
    ip: str
    username: str
    password: str
    rtsp_port: int = DefaultPorts.RTSP
    onvif_port: int = DefaultPorts.ONVIF
    http_port: int = DefaultPorts.HTTP
    timeout: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    auth_type: str = "basic"  # basic, digest, etc.
    
    def __post_init__(self):
        """Validación post-inicialización."""
        if not self.ip:
            raise MissingRequiredFieldError("ip", "ConnectionConfig")
        
        # Validar formato de IP
        try:
            ipaddress.ip_address(self.ip)
        except ValueError:
            raise InvalidIPAddressError(self.ip)
            
        if not self.username:
            raise MissingRequiredFieldError("username", "ConnectionConfig")
            
        # Validar puertos
        if not (1 <= self.rtsp_port <= 65535):
            raise InvalidPortError(self.rtsp_port)
        if not (1 <= self.onvif_port <= 65535):
            raise InvalidPortError(self.onvif_port)
        if not (1 <= self.http_port <= 65535):
            raise InvalidPortError(self.http_port)


@dataclass 
class StreamConfig:
    """Configuración de streaming de cámara."""
    channel: int = 1
    subtype: int = 0
    resolution: str = "1920x1080"
    codec: str = "H264" 
    fps: int = 30
    bitrate: int = 2048
    quality: str = "high"
    
    def get_display_resolution(self) -> str:
        """Obtiene resolución en formato display-friendly."""
        return self.resolution.replace("x", " × ")


@dataclass
class CameraCapabilities:
    """Capacidades y características de la cámara."""
    supported_protocols: List[ProtocolType] = field(default_factory=list)
    max_resolution: str = "1920x1080"
    supported_codecs: List[str] = field(default_factory=lambda: ["H264"])
    has_ptz: bool = False
    has_audio: bool = False
    has_ir: bool = False
    onvif_version: Optional[str] = None
    
    def supports_protocol(self, protocol: ProtocolType) -> bool:
        """Verifica si la cámara soporta un protocolo."""
        return protocol in self.supported_protocols


@dataclass
class ConnectionStats:
    """Estadísticas de conexión de la cámara."""
    connection_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    last_connection_time: Optional[datetime] = None
    last_error: Optional[str] = None
    total_uptime: timedelta = field(default_factory=lambda: timedelta())
    average_response_time: float = 0.0
    
    def get_success_rate(self) -> float:
        """Calcula tasa de éxito de conexión."""
        if self.connection_attempts == 0:
            return 0.0
        return (self.successful_connections / self.connection_attempts) * 100
    
    def record_connection_attempt(self, success: bool, error: Optional[str] = None):
        """Registra un intento de conexión."""
        self.connection_attempts += 1
        if success:
            self.successful_connections += 1
            self.last_connection_time = datetime.now()
        else:
            self.failed_connections += 1
            self.last_error = error


class CameraModel:
    """
    Modelo principal de cámara para arquitectura MVP.
    
    Encapsula toda la lógica de dominio relacionada con una cámara individual,
    incluyendo configuración, estado, capacidades y estadísticas.
    """
    
    def __init__(self, 
                 brand: str,
                 model: str,
                 display_name: str,
                 connection_config: ConnectionConfig,
                 stream_config: Optional[StreamConfig] = None,
                 capabilities: Optional[CameraCapabilities] = None,
                 camera_id: Optional[str] = None):
        """
        Inicializa el modelo de cámara.
        
        Args:
            brand: Marca de la cámara (dahua, tplink, etc.)
            model: Modelo específico (hero-k51h, etc.)
            display_name: Nombre de visualización
            connection_config: Configuración de conexión
            stream_config: Configuración de streaming
            capabilities: Capacidades de la cámara
        """
        self.logger = logging.getLogger(f"{__name__}.{brand}")
        
        # Identificación
        self.brand = brand
        self.model = model
        self.display_name = display_name
        self.camera_id = camera_id or generate_camera_id()  # UUID único e inmutable
        
        # Configuración
        self.connection_config = connection_config
        self.stream_config = stream_config or StreamConfig()
        self.capabilities = capabilities or CameraCapabilities()
        
        # Estado
        self._status = ConnectionStatus.DISCONNECTED
        self._status_lock = threading.Lock()
        self._is_streaming = False
        self._current_protocol: Optional[ProtocolType] = None
        
        # Estadísticas
        self.stats = ConnectionStats()
        
        # Metadatos
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.metadata: Dict[str, Any] = {}
        
        # Nuevos campos para persistencia 3FN
        self.mac_address: Optional[str] = None
        self.firmware_version: Optional[str] = None
        self.hardware_version: Optional[str] = None
        self.serial_number: Optional[str] = None
        self.location: Optional[str] = None
        self.description: Optional[str] = None
        self.is_active: bool = True
        
        # URLs descubiertas/configuradas
        self.discovered_endpoints: Dict[str, Dict[str, Any]] = {}
        # Formato: {'rtsp_main': {'url': 'rtsp://...', 'verified': True, 'priority': 0}}
        
        # Perfiles de streaming disponibles
        self.stream_profiles: List[Dict[str, Any]] = []
        
        # Protocolos configurados
        self.protocol_configs: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info(f"Camera model initialized: {self.display_name}")
    
    # === Propiedades de Estado ===
    
    @property
    def status(self) -> ConnectionStatus:
        """Estado actual de conexión (thread-safe)."""
        with self._status_lock:
            return self._status
    
    @status.setter
    def status(self, new_status: ConnectionStatus):
        """Establece estado de conexión (thread-safe)."""
        with self._status_lock:
            old_status = self._status
            self._status = new_status
            self.last_updated = datetime.now()
            
            if old_status != new_status:
                self.logger.info(f"Status changed: {old_status.value} → {new_status.value}")
    
    @property
    def is_connected(self) -> bool:
        """Indica si la cámara está conectada."""
        return self.status in [ConnectionStatus.CONNECTED, ConnectionStatus.STREAMING]
    
    @property
    def is_streaming(self) -> bool:
        """Indica si la cámara está transmitiendo."""
        return self._is_streaming and self.status == ConnectionStatus.STREAMING
    
    @property
    def current_protocol(self) -> Optional[ProtocolType]:
        """Protocolo actualmente en uso."""
        return self._current_protocol
    
    # === Gestión de Conexión ===
    
    def can_connect_with_protocol(self, protocol: ProtocolType) -> bool:
        """
        Verifica si se puede conectar usando un protocolo específico.
        
        Args:
            protocol: Protocolo a verificar
            
        Returns:
            True si es posible conectar con ese protocolo
        """
        return self.capabilities.supports_protocol(protocol)
    
    def get_available_protocols(self) -> List[ProtocolType]:
        """Obtiene lista de protocolos disponibles para esta cámara."""
        return self.capabilities.supported_protocols.copy()
    
    def set_connection_status(self, status: ConnectionStatus, protocol: Optional[ProtocolType] = None, error: Optional[str] = None):
        """
        Establece estado de conexión con contexto adicional.
        
        Args:
            status: Nuevo estado
            protocol: Protocolo usado (si aplica)
            error: Mensaje de error (si aplica)
        """
        self.status = status
        
        if protocol:
            self._current_protocol = protocol
        
        # Registrar estadísticas
        if status == ConnectionStatus.CONNECTED:
            self.stats.record_connection_attempt(True)
        elif status == ConnectionStatus.ERROR:
            self.stats.record_connection_attempt(False, error)
    
    def start_streaming(self, protocol: ProtocolType) -> bool:
        """
        Inicia streaming de video.
        
        Args:
            protocol: Protocolo a usar
            
        Returns:
            True si se puede iniciar streaming
        """
        if not self.is_connected:
            self.logger.warning("Cannot start streaming: camera not connected")
            return False
        
        if not self.can_connect_with_protocol(protocol):
            self.logger.warning(f"Cannot stream with protocol {protocol.value}")
            return False
        
        self._is_streaming = True
        self._current_protocol = protocol
        self.status = ConnectionStatus.STREAMING
        
        self.logger.info(f"Streaming started with {protocol.value}")
        return True
    
    def stop_streaming(self):
        """Detiene streaming de video."""
        if self._is_streaming:
            self._is_streaming = False
            self.status = ConnectionStatus.CONNECTED
            self.logger.info("Streaming stopped")
    
    # === Configuración ===
    
    def update_connection_config(self, **kwargs):
        """
        Actualiza configuración de conexión.
        
        Args:
            **kwargs: Campos a actualizar
        """
        for key, value in kwargs.items():
            if hasattr(self.connection_config, key):
                setattr(self.connection_config, key, value)
                self.last_updated = datetime.now()
                self.logger.info(f"Connection config updated: {key} = {value}")
    
    def update_stream_config(self, **kwargs):
        """
        Actualiza configuración de streaming.
        
        Args:
            **kwargs: Campos a actualizar
        """
        for key, value in kwargs.items():
            if hasattr(self.stream_config, key):
                setattr(self.stream_config, key, value)
                self.last_updated = datetime.now()
                self.logger.info(f"Stream config updated: {key} = {value}")
    
    # === URLs y Endpoints ===
    
    def add_discovered_endpoint(self, endpoint_type: str, url: str, 
                              verified: bool = False, priority: int = 0) -> None:
        """
        Agrega un endpoint descubierto.
        
        Args:
            endpoint_type: Tipo de endpoint (rtsp_main, snapshot, etc)
            url: URL completa
            verified: Si fue verificada exitosamente
            priority: Prioridad de uso (0 = mayor prioridad)
        """
        self.discovered_endpoints[endpoint_type] = {
            'url': url,
            'verified': verified,
            'priority': priority,
            'discovered_at': datetime.now().isoformat()
        }
        self.last_updated = datetime.now()
        self.logger.info(f"Endpoint agregado: {endpoint_type} = {url}")
    
    def get_endpoint_url(self, endpoint_type: str) -> Optional[str]:
        """
        Obtiene URL de un endpoint específico.
        
        Args:
            endpoint_type: Tipo de endpoint
            
        Returns:
            URL si existe, None si no
        """
        endpoint = self.discovered_endpoints.get(endpoint_type)
        return endpoint['url'] if endpoint else None
    
    def get_verified_endpoints(self) -> Dict[str, str]:
        """
        Obtiene solo los endpoints verificados.
        
        Returns:
            Dict con endpoints verificados {tipo: url}
        """
        return {
            ep_type: ep_data['url']
            for ep_type, ep_data in self.discovered_endpoints.items()
            if ep_data.get('verified', False)
        }
    
    def add_stream_profile(self, profile_name: str, **kwargs) -> None:
        """
        Agrega un perfil de streaming.
        
        Args:
            profile_name: Nombre del perfil
            **kwargs: Configuración del perfil
        """
        profile = {
            'profile_name': profile_name,
            'stream_type': kwargs.get('stream_type', 'main'),
            'resolution': kwargs.get('resolution'),
            'fps': kwargs.get('fps'),
            'bitrate': kwargs.get('bitrate'),
            'codec': kwargs.get('codec'),
            'channel': kwargs.get('channel', 1),
            'subtype': kwargs.get('subtype', 0),
            'is_default': kwargs.get('is_default', False)
        }
        self.stream_profiles.append(profile)
        self.last_updated = datetime.now()
        self.logger.info(f"Perfil de streaming agregado: {profile_name}")
    
    def get_rtsp_url(self, url_pattern: Optional[str] = None) -> str:
        """
        Construye URL RTSP para esta cámara.
        
        Args:
            url_pattern: Patrón de URL personalizado
            
        Returns:
            URL RTSP completa
        """
        # Primero intentar con endpoint descubierto
        discovered_url = self.get_endpoint_url('rtsp_main')
        if discovered_url:
            return discovered_url
            
        # Si no, construir URL
        if not url_pattern:
            url_pattern = "/stream1"  # Patrón genérico
        
        # Formatear patrón con configuración
        formatted_path = url_pattern.format(
            channel=self.stream_config.channel,
            subtype=self.stream_config.subtype
        )
        
        # Construir URL completa
        auth_part = ""
        if self.connection_config.username and self.connection_config.password:
            auth_part = f"{self.connection_config.username}:{self.connection_config.password}@"
        
        rtsp_url = f"rtsp://{auth_part}{self.connection_config.ip}:{self.connection_config.rtsp_port}{formatted_path}"
        
        return rtsp_url
    
    def get_onvif_url(self) -> str:
        """Construye URL ONVIF para esta cámara."""
        return f"http://{self.connection_config.ip}:{self.connection_config.onvif_port}/onvif/device_service"
    
    def get_http_url(self, endpoint: str = "") -> str:
        """
        Construye URL HTTP para esta cámara.
        
        Args:
            endpoint: Endpoint específico
            
        Returns:
            URL HTTP completa
        """
        return f"http://{self.connection_config.ip}:{self.connection_config.http_port}{endpoint}"
    
    # === Validación ===
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """
        Valida la configuración completa de la cámara.
        
        Returns:
            Tupla (es_válida, lista_errores)
        """
        errors = []
        
        # Validar configuración de conexión
        try:
            # Validar IP básica
            if not self.connection_config.ip:
                errors.append("IP address is required")
            
            # Validar puertos
            ports = [self.connection_config.rtsp_port, 
                    self.connection_config.onvif_port, 
                    self.connection_config.http_port]
            for port in ports:
                if not (1 <= port <= 65535):
                    errors.append(f"Invalid port: {port}")
            
            # Validar protocolos
            if not self.capabilities.supported_protocols:
                errors.append("No supported protocols configured")
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    # === Propiedades de Compatibilidad para Servicios ===
    
    @property
    def ip(self) -> str:
        """IP de la cámara (compatibilidad con servicios)."""
        return self.connection_config.ip
    
    @property
    def username(self) -> str:
        """Username (compatibilidad con servicios)."""
        return self.connection_config.username
    
    @property
    def password(self) -> str:
        """Password (compatibilidad con servicios)."""
        return self.connection_config.password
    
    @property
    def protocol(self) -> Optional[ProtocolType]:
        """Protocolo actual (compatibilidad con servicios)."""
        return self._current_protocol
    
    @protocol.setter
    def protocol(self, value: ProtocolType):
        """Establece protocolo (compatibilidad con servicios)."""
        self._current_protocol = value
    
    @property
    def connection_status(self) -> ConnectionStatus:
        """Estado de conexión (alias para status)."""
        return self.status
    
    @connection_status.setter
    def connection_status(self, value: ConnectionStatus):
        """Establece estado de conexión (alias para status)."""
        self.status = value
    
    @property
    def last_connection_attempt(self) -> Optional[datetime]:
        """Último intento de conexión (compatibilidad con servicios)."""
        return self.stats.last_connection_time
    
    @last_connection_attempt.setter
    def last_connection_attempt(self, value: datetime):
        """Establece último intento de conexión."""
        self.stats.last_connection_time = value

    # === Serialización ===
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el modelo a diccionario para serialización.
        
        Returns:
            Diccionario con todos los datos del modelo
        """
        return {
            'camera_id': self.camera_id,
            'brand': self.brand,
            'model': self.model,
            'display_name': self.display_name,
            'connection_config': {
                'ip': self.connection_config.ip,
                'username': self.connection_config.username,
                'password': self.connection_config.password,  # TODO: Encriptar
                'rtsp_port': self.connection_config.rtsp_port,
                'onvif_port': self.connection_config.onvif_port,
                'http_port': self.connection_config.http_port,
                'timeout': self.connection_config.timeout,
                'max_retries': self.connection_config.max_retries,
                'retry_delay': self.connection_config.retry_delay,
            },
            'stream_config': {
                'channel': self.stream_config.channel,
                'subtype': self.stream_config.subtype,
                'resolution': self.stream_config.resolution,
                'codec': self.stream_config.codec,
                'fps': self.stream_config.fps,
                'bitrate': self.stream_config.bitrate,
                'quality': self.stream_config.quality,
            },
            'capabilities': {
                'supported_protocols': [p.value for p in self.capabilities.supported_protocols],
                'max_resolution': self.capabilities.max_resolution,
                'supported_codecs': self.capabilities.supported_codecs,
                'has_ptz': self.capabilities.has_ptz,
                'has_audio': self.capabilities.has_audio,
                'has_ir': self.capabilities.has_ir,
                'onvif_version': self.capabilities.onvif_version,
            },
            'status': {
                'current_status': self.status.value,
                'is_connected': self.is_connected,
                'is_streaming': self.is_streaming,
                'current_protocol': self.current_protocol.value if self.current_protocol else None,
            },
            'stats': {
                'connection_attempts': self.stats.connection_attempts,
                'successful_connections': self.stats.successful_connections,
                'failed_connections': self.stats.failed_connections,
                'success_rate': self.stats.get_success_rate(),
                'last_connection_time': self.stats.last_connection_time.isoformat() if self.stats.last_connection_time else None,
                'last_error': self.stats.last_error,
            },
            'metadata': {
                'created_at': self.created_at.isoformat(),
                'last_updated': self.last_updated.isoformat(),
                'custom_metadata': self.metadata,
            },
            # Nuevos campos para persistencia 3FN
            'hardware_info': {
                'mac_address': self.mac_address,
                'firmware_version': self.firmware_version,
                'hardware_version': self.hardware_version,
                'serial_number': self.serial_number,
            },
            'location_info': {
                'location': self.location,
                'description': self.description,
                'is_active': self.is_active,
            },
            'discovered_endpoints': self.discovered_endpoints,
            'stream_profiles': self.stream_profiles,
            'protocol_configs': self.protocol_configs,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CameraModel':
        """
        Crea modelo desde diccionario.
        
        Args:
            data: Diccionario con datos del modelo
            
        Returns:
            Instancia de CameraModel
        """
        # Reconstruir objetos de configuración
        connection_config = ConnectionConfig(**data['connection_config'])
        stream_config = StreamConfig(**data['stream_config'])
        
        # Reconstruir capabilities
        caps_data = data['capabilities']
        capabilities = CameraCapabilities(
            supported_protocols=[ProtocolType(p) for p in caps_data['supported_protocols']],
            max_resolution=caps_data['max_resolution'],
            supported_codecs=caps_data['supported_codecs'],
            has_ptz=caps_data['has_ptz'],
            has_audio=caps_data['has_audio'],
            has_ir=caps_data['has_ir'],
            onvif_version=caps_data['onvif_version'],
        )
        
        # Crear instancia
        camera = cls(
            brand=data['brand'],
            model=data['model'],
            display_name=data['display_name'],
            connection_config=connection_config,
            stream_config=stream_config,
            capabilities=capabilities
        )
        
        # Restaurar estado y estadísticas
        camera.camera_id = data['camera_id']
        camera.status = ConnectionStatus(data['status']['current_status'])
        camera._is_streaming = data['status']['is_streaming']
        if data['status']['current_protocol']:
            camera._current_protocol = ProtocolType(data['status']['current_protocol'])
        
        # Restaurar stats
        stats_data = data['stats']
        camera.stats.connection_attempts = stats_data['connection_attempts']
        camera.stats.successful_connections = stats_data['successful_connections']
        camera.stats.failed_connections = stats_data['failed_connections']
        if stats_data['last_connection_time']:
            camera.stats.last_connection_time = datetime.fromisoformat(stats_data['last_connection_time'])
        camera.stats.last_error = stats_data['last_error']
        
        # Restaurar metadata
        metadata = data['metadata']
        camera.created_at = datetime.fromisoformat(metadata['created_at'])
        camera.last_updated = datetime.fromisoformat(metadata['last_updated'])
        camera.metadata = metadata['custom_metadata']
        
        return camera
    
    def __str__(self) -> str:
        """Representación string del modelo."""
        return f"CameraModel({self.display_name}, {self.connection_config.ip}, {self.status.value})"
    
    def __repr__(self) -> str:
        """Representación detallada del modelo."""
        return f"CameraModel(brand='{self.brand}', model='{self.model}', ip='{self.connection_config.ip}', status='{self.status.value}')" 