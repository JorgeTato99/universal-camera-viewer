#!/usr/bin/env python3
"""
Constantes centralizadas de la aplicación.

Define valores constantes utilizados en toda la aplicación
para evitar hardcoding y facilitar mantenimiento.
"""

from typing import Dict, List, Tuple


# === Puertos por defecto ===
class DefaultPorts:
    """Puertos por defecto para diferentes protocolos."""
    RTSP = 554
    RTSP_ALTERNATE = 8554
    ONVIF = 80
    ONVIF_ALTERNATE = 8080
    HTTP = 80
    HTTPS = 443
    # Puertos específicos por marca
    STEREN_RTSP = 5543
    TPLINK_ONVIF = 2020
    DAHUA_ONVIF = 80
    STEREN_ONVIF = 8000


# === Credenciales por defecto ===
class DefaultCredentials:
    """Credenciales por defecto por marca."""
    # NOTA: Estas son credenciales por defecto de fábrica
    # El usuario debe cambiarlas por sus propias credenciales
    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "admin"
    
    # Credenciales específicas por marca (solo para referencia)
    BRAND_DEFAULTS = {
        "dahua": {"username": "admin", "password": "admin"},
        "tplink": {"username": "admin", "password": "admin"},
        "steren": {"username": "admin", "password": "admin"},
        "hikvision": {"username": "admin", "password": "12345"},
        "generic": {"username": "admin", "password": "admin"},
    }


# === URLs y Paths RTSP ===
class RTSPPaths:
    """Paths RTSP comunes por marca."""
    
    # Paths genéricos
    GENERIC_PATHS = [
        "/stream",
        "/video",
        "/h264",
        "/live",
        "/cam/realmonitor",
        "/MediaInput/h264",
        "/11",
        "/12",
        "/ch1-s1",
        "/live/ch00_0",
        "/user={username}_password={password}_channel=1_stream=0.sdp",
        "/cam/realmonitor?channel=1&subtype=0",
        "/Streaming/Channels/101",
        "/h264Preview_01_main",
        "/live/main",
        "/stream1"
    ]
    
    # Paths específicos por marca
    BRAND_PATHS = {
        "dahua": [
            "/cam/realmonitor?channel=1&subtype=0",
            "/cam/realmonitor?channel=1&subtype=1",
        ],
        "tplink": [
            "/stream1",
            "/stream2",
            "/h264_stream",
        ],
        "steren": [
            "/11",
            "/12",
            "/user={username}_password={password}_channel=1_stream=0.sdp",
        ],
        "hikvision": [
            "/Streaming/Channels/101",
            "/Streaming/Channels/102",
            "/h264/ch1/main/av_stream",
        ],
    }


# === Timeouts ===
class Timeouts:
    """Timeouts en segundos para diferentes operaciones."""
    CONNECTION_DEFAULT = 10.0
    CONNECTION_QUICK = 5.0
    SCAN_PORT = 2.0
    SCAN_NETWORK = 300.0  # 5 minutos
    STREAM_CONNECT = 15.0
    FRAME_CAPTURE = 1.0
    HTTP_REQUEST = 10.0
    PING = 5.0


# === Límites del sistema ===
class SystemLimits:
    """Límites para proteger el sistema."""
    MAX_CONCURRENT_CONNECTIONS = 10
    MAX_CAMERAS_PER_SCAN = 100
    MAX_FRAME_BUFFER_SIZE = 30
    MAX_FPS = 60
    MIN_FPS = 1
    MAX_RETRY_ATTEMPTS = 3
    MAX_ERROR_LOG_SIZE = 1000


# === Configuración de red ===
class NetworkConfig:
    """Configuración de red por defecto."""
    DEFAULT_SUBNET_MASK = "255.255.255.0"
    MULTICAST_GROUP = "239.255.255.250"
    ONVIF_PROBE_TYPES = [
        "dn:NetworkVideoTransmitter",
        "tds:Device",
    ]
    WS_DISCOVERY_TIMEOUT = 5.0


# === Configuración de streaming ===
class StreamingConfig:
    """Configuración por defecto para streaming."""
    DEFAULT_TARGET_FPS = 30
    DEFAULT_BUFFER_SIZE = 5
    DEFAULT_VIDEO_CODEC = "h264"
    DEFAULT_TRANSPORT = "tcp"
    JPEG_QUALITY = 85
    MAX_FRAME_SIZE = 10 * 1024 * 1024  # 10MB


# === Marcas soportadas ===
class SupportedBrands:
    """Marcas de cámaras soportadas."""
    ALL = ["dahua", "tplink", "steren", "hikvision", "generic"]
    
    # Información adicional por marca
    BRAND_INFO = {
        "dahua": {
            "name": "Dahua",
            "default_onvif_port": DefaultPorts.DAHUA_ONVIF,
            "default_rtsp_port": DefaultPorts.RTSP,
            "supports_onvif": True,
            "supports_rtsp": True,
        },
        "tplink": {
            "name": "TP-Link Tapo",
            "default_onvif_port": DefaultPorts.TPLINK_ONVIF,
            "default_rtsp_port": DefaultPorts.RTSP,
            "supports_onvif": True,
            "supports_rtsp": True,
        },
        "steren": {
            "name": "Steren CCTV",
            "default_onvif_port": DefaultPorts.STEREN_ONVIF,
            "default_rtsp_port": DefaultPorts.STEREN_RTSP,
            "supports_onvif": True,
            "supports_rtsp": True,
        },
        "hikvision": {
            "name": "Hikvision",
            "default_onvif_port": DefaultPorts.ONVIF,
            "default_rtsp_port": DefaultPorts.RTSP,
            "supports_onvif": True,
            "supports_rtsp": True,
        },
        "generic": {
            "name": "Generic/Unknown",
            "default_onvif_port": DefaultPorts.ONVIF,
            "default_rtsp_port": DefaultPorts.RTSP,
            "supports_onvif": True,
            "supports_rtsp": True,
        },
    }


# === Mensajes de error comunes ===
class ErrorMessages:
    """Mensajes de error estandarizados."""
    CONNECTION_REFUSED = "Conexión rechazada. Verifique que la cámara esté encendida y accesible."
    AUTHENTICATION_FAILED = "Autenticación fallida. Verifique usuario y contraseña."
    TIMEOUT = "Tiempo de espera agotado. La cámara no responde."
    INVALID_IP = "Dirección IP inválida."
    CAMERA_NOT_FOUND = "Cámara no encontrada."
    STREAM_NOT_AVAILABLE = "Stream no disponible."
    NETWORK_ERROR = "Error de red. Verifique su conexión."
    UNKNOWN_ERROR = "Error desconocido. Por favor intente nuevamente."


# === Patrones de validación ===
class ValidationPatterns:
    """Expresiones regulares para validación."""
    IP_ADDRESS = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    PORT_RANGE = (1, 65535)
    USERNAME_PATTERN = r"^[a-zA-Z0-9_-]{1,32}$"
    RTSP_URL = r"^rtsp://.*$"


# === Configuración de UI ===
class UIConfig:
    """Configuración de interfaz de usuario."""
    MAX_CAMERAS_PER_PAGE = 12
    THUMBNAIL_UPDATE_INTERVAL = 5.0  # segundos
    SCAN_PROGRESS_UPDATE_INTERVAL = 0.5  # segundos
    CONNECTION_STATUS_CHECK_INTERVAL = 30.0  # segundos
    

# === Configuración de logging ===
class LoggingConfig:
    """Configuración de logging."""
    DEFAULT_LEVEL = "INFO"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_LOG_FILES = 5
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    

__all__ = [
    'DefaultPorts',
    'DefaultCredentials',
    'RTSPPaths',
    'Timeouts',
    'SystemLimits',
    'NetworkConfig',
    'StreamingConfig',
    'SupportedBrands',
    'ErrorMessages',
    'ValidationPatterns',
    'UIConfig',
    'LoggingConfig',
]