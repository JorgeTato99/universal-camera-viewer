"""
Modelos Pydantic para la API de cámaras.

Define los esquemas de request/response para la nueva estructura 3FN.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ConnectionStatus(str, Enum):
    """Estados de conexión de una cámara."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    STREAMING = "streaming"
    UNAVAILABLE = "unavailable"


class ProtocolType(str, Enum):
    """Tipos de protocolo soportados."""
    RTSP = "rtsp"
    ONVIF = "onvif"
    HTTP = "http"
    AMCREST = "amcrest"
    GENERIC = "generic"


class AuthType(str, Enum):
    """Tipos de autenticación."""
    BASIC = "basic"
    DIGEST = "digest"
    BEARER = "bearer"
    CUSTOM = "custom"


# === Modelos de Request ===

class CredentialsRequest(BaseModel):
    """Credenciales para autenticación."""
    username: str = Field(..., min_length=1, description="Nombre de usuario")
    password: str = Field(..., min_length=1, description="Contraseña")
    auth_type: AuthType = Field(default=AuthType.BASIC, description="Tipo de autenticación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123",
                "auth_type": "basic"
            }
        }


class ProtocolConfigRequest(BaseModel):
    """Configuración de protocolo."""
    protocol_type: ProtocolType = Field(..., description="Tipo de protocolo")
    port: int = Field(..., ge=1, le=65535, description="Puerto del protocolo")
    is_enabled: bool = Field(default=True, description="Si está habilitado")
    is_primary: bool = Field(default=False, description="Si es el protocolo principal")
    version: Optional[str] = Field(None, description="Versión del protocolo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "protocol_type": "onvif",
                "port": 80,
                "is_enabled": True,
                "is_primary": True,
                "version": "2.0"
            }
        }


class EndpointRequest(BaseModel):
    """Endpoint/URL descubierto o configurado."""
    type: str = Field(..., description="Tipo de endpoint (rtsp_main, snapshot, etc)")
    url: str = Field(..., description="URL completa")
    protocol: Optional[ProtocolType] = Field(None, description="Protocolo usado")
    verified: bool = Field(default=False, description="Si fue verificada exitosamente")
    priority: int = Field(default=0, ge=0, description="Prioridad (0=mayor)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "rtsp_main",
                "url": "rtsp://192.168.1.50:554/cam/realmonitor?channel=1&subtype=0",
                "protocol": "rtsp",
                "verified": True,
                "priority": 0
            }
        }


class StreamProfileRequest(BaseModel):
    """Perfil de streaming."""
    profile_name: str = Field(..., description="Nombre del perfil")
    stream_type: str = Field(default="main", description="Tipo de stream (main/sub)")
    resolution: Optional[str] = Field(None, description="Resolución (1920x1080)")
    fps: Optional[int] = Field(None, ge=1, le=60, description="FPS")
    bitrate: Optional[int] = Field(None, ge=1, description="Bitrate en kbps")
    codec: Optional[str] = Field(None, description="Codec (H264/H265)")
    quality: Optional[str] = Field(None, description="Calidad (high/medium/low)")
    channel: int = Field(default=1, ge=1, description="Canal")
    subtype: int = Field(default=0, ge=0, description="Subtipo")
    is_default: bool = Field(default=False, description="Si es el perfil por defecto")


class CreateCameraRequest(BaseModel):
    """Request para crear una nueva cámara."""
    brand: str = Field(..., min_length=1, description="Marca de la cámara")
    model: str = Field(default="Unknown", description="Modelo de la cámara")
    display_name: str = Field(..., min_length=1, description="Nombre para mostrar")
    ip: str = Field(..., description="Dirección IP")
    location: Optional[str] = Field(None, description="Ubicación física")
    description: Optional[str] = Field(None, description="Descripción")
    
    # Credenciales
    credentials: CredentialsRequest
    
    # Protocolos opcionales
    protocols: Optional[List[ProtocolConfigRequest]] = Field(
        default=None, 
        description="Configuración de protocolos"
    )
    
    # Endpoints opcionales
    endpoints: Optional[List[EndpointRequest]] = Field(
        default=None,
        description="URLs conocidas"
    )
    
    # Perfiles de streaming opcionales
    stream_profiles: Optional[List[StreamProfileRequest]] = Field(
        default=None,
        description="Perfiles de streaming"
    )
    
    @validator('ip')
    def validate_ip(cls, v):
        """Valida formato de IP."""
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Dirección IP inválida')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand": "dahua",
                "model": "DH-IPC-HFW2431S",
                "display_name": "Cámara Principal",
                "ip": "192.168.1.50",
                "location": "Entrada principal",
                "description": "Cámara de seguridad entrada",
                "credentials": {
                    "username": "admin",
                    "password": "password123"
                },
                "protocols": [
                    {
                        "protocol_type": "onvif",
                        "port": 80,
                        "is_primary": True
                    },
                    {
                        "protocol_type": "rtsp",
                        "port": 554
                    }
                ]
            }
        }


class UpdateCameraRequest(BaseModel):
    """Request para actualizar una cámara."""
    display_name: Optional[str] = Field(None, min_length=1)
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Credenciales opcionales
    credentials: Optional[CredentialsRequest] = None
    
    # Endpoints para agregar/actualizar
    endpoints: Optional[List[EndpointRequest]] = None
    
    # Perfiles de streaming
    stream_profiles: Optional[List[StreamProfileRequest]] = None


class TestConnectionRequest(BaseModel):
    """Request para probar conexión sin guardar."""
    ip: str = Field(..., description="Dirección IP")
    username: str = Field(..., description="Usuario")
    password: str = Field(..., description="Contraseña")
    protocol: ProtocolType = Field(default=ProtocolType.ONVIF)
    port: Optional[int] = Field(None, description="Puerto")
    brand: Optional[str] = Field(default="Generic")


# === Modelos de Response ===

class CredentialsResponse(BaseModel):
    """Respuesta de credenciales (sin contraseña)."""
    username: str
    auth_type: AuthType
    is_configured: bool = Field(..., description="Si tiene contraseña configurada")


class ProtocolResponse(BaseModel):
    """Respuesta de configuración de protocolo."""
    protocol_id: Optional[int] = None
    protocol_type: ProtocolType
    port: int
    is_enabled: bool
    is_primary: bool
    version: Optional[str] = None


class EndpointResponse(BaseModel):
    """Respuesta de endpoint."""
    endpoint_id: Optional[int] = None
    type: str
    url: str
    protocol: Optional[ProtocolType] = None
    is_verified: bool
    last_verified: Optional[datetime] = None
    response_time_ms: Optional[int] = None
    priority: int


class StreamProfileResponse(BaseModel):
    """Respuesta de perfil de streaming."""
    profile_id: Optional[int] = None
    profile_name: str
    stream_type: str
    resolution: Optional[str] = None
    fps: Optional[int] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    quality: Optional[str] = None
    channel: int
    subtype: int
    is_default: bool


class CameraStatisticsResponse(BaseModel):
    """Estadísticas de una cámara."""
    total_connections: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    success_rate: float = 0.0
    total_uptime_minutes: int = 0
    average_fps: Optional[float] = None
    average_latency_ms: Optional[int] = None
    last_connection_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None


class CameraCapabilitiesResponse(BaseModel):
    """Capacidades de la cámara."""
    supported_protocols: List[ProtocolType] = []
    has_ptz: bool = False
    has_audio: bool = False
    has_ir: bool = False
    has_motion_detection: bool = False
    max_resolution: Optional[str] = None
    supported_codecs: List[str] = []


class CameraResponse(BaseModel):
    """Respuesta completa de una cámara."""
    # Identificación
    camera_id: str
    brand: str
    model: str
    display_name: str
    
    # Conexión
    ip_address: str
    mac_address: Optional[str] = None
    
    # Estado
    status: ConnectionStatus
    is_active: bool
    is_connected: bool
    is_streaming: bool
    
    # Hardware info
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Ubicación
    location: Optional[str] = None
    description: Optional[str] = None
    
    # Configuración
    credentials: Optional[CredentialsResponse] = None
    protocols: List[ProtocolResponse] = []
    endpoints: List[EndpointResponse] = []
    stream_profiles: List[StreamProfileResponse] = []
    
    # Capacidades
    capabilities: CameraCapabilitiesResponse
    
    # Estadísticas
    statistics: Optional[CameraStatisticsResponse] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "dahua_dh-ipc-hfw2431s_192168150",
                "brand": "dahua",
                "model": "DH-IPC-HFW2431S",
                "display_name": "Cámara Principal",
                "ip_address": "192.168.1.50",
                "status": "connected",
                "is_active": True,
                "is_connected": True,
                "is_streaming": False,
                "location": "Entrada principal",
                "credentials": {
                    "username": "admin",
                    "auth_type": "basic",
                    "is_configured": True
                },
                "protocols": [
                    {
                        "protocol_type": "onvif",
                        "port": 80,
                        "is_enabled": True,
                        "is_primary": True
                    }
                ],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "url": "rtsp://192.168.1.50:554/cam/realmonitor?channel=1&subtype=0",
                        "is_verified": True,
                        "priority": 0
                    }
                ],
                "capabilities": {
                    "supported_protocols": ["onvif", "rtsp"],
                    "has_ptz": False,
                    "has_audio": True
                },
                "created_at": "2025-07-15T10:00:00Z",
                "updated_at": "2025-07-15T10:00:00Z"
            }
        }


class CameraListResponse(BaseModel):
    """Respuesta para listado de cámaras."""
    total: int = Field(..., description="Total de cámaras")
    cameras: List[CameraResponse] = Field(..., description="Lista de cámaras")


class TestConnectionResponse(BaseModel):
    """Respuesta de prueba de conexión."""
    success: bool
    message: str
    discovered_endpoints: Optional[List[EndpointResponse]] = None
    detected_capabilities: Optional[CameraCapabilitiesResponse] = None