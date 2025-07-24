"""
Schemas Pydantic para gestión de servidores MediaMTX.

Define las estructuras de datos para las operaciones CRUD
de servidores MediaMTX remotos, incluyendo validación y
serialización.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


class MediaMTXServerBase(BaseModel):
    """Schema base para servidores MediaMTX."""
    
    server_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre único del servidor"
    )
    rtsp_url: str = Field(
        ...,
        description="URL RTSP del servidor (rtsp://...)"
    )
    rtsp_port: int = Field(
        8554,
        ge=1,
        le=65535,
        description="Puerto RTSP"
    )
    api_url: str = Field(
        ...,
        description="URL de la API del servidor (http://... o https://...)"
    )
    api_port: int = Field(
        8000,
        ge=1,
        le=65535,
        description="Puerto de la API"
    )
    api_enabled: bool = Field(
        True,
        description="Si la API está habilitada"
    )
    username: Optional[str] = Field(
        None,
        max_length=100,
        description="Usuario para autenticación"
    )
    auth_enabled: bool = Field(
        True,
        description="Si requiere autenticación"
    )
    use_tcp: bool = Field(
        True,
        description="Usar TCP en lugar de UDP para RTSP"
    )
    max_reconnects: int = Field(
        3,
        ge=0,
        le=10,
        description="Número máximo de reintentos"
    )
    reconnect_delay: float = Field(
        5.0,
        ge=0.1,
        le=60.0,
        description="Delay entre reintentos en segundos"
    )
    publish_path_template: str = Field(
        "ucv_{camera_code}",
        description="Plantilla para paths de publicación"
    )
    health_check_interval: int = Field(
        30,
        ge=10,
        le=300,
        description="Intervalo de health check en segundos"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadatos adicionales del servidor"
    )
    
    @field_validator('rtsp_url')
    def validate_rtsp_url(cls, v: str) -> str:
        """Valida que la URL RTSP tenga formato correcto."""
        if not v.startswith('rtsp://'):
            raise ValueError('RTSP URL debe comenzar con rtsp://')
        
        # Validación básica de URL
        pattern = r'^rtsp://[a-zA-Z0-9\.\-]+(?:\:[0-9]+)?(?:/.*)?$'
        if not re.match(pattern, v):
            raise ValueError('Formato de RTSP URL inválido')
        
        return v
    
    @field_validator('api_url')
    def validate_api_url(cls, v: str) -> str:
        """Valida que la API URL tenga formato correcto."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('API URL debe comenzar con http:// o https://')
        
        # Validación básica de URL
        pattern = r'^https?://[a-zA-Z0-9\.\-]+(?:\:[0-9]+)?(?:/.*)?$'
        if not re.match(pattern, v):
            raise ValueError('Formato de API URL inválido')
        
        return v


class MediaMTXServerCreate(MediaMTXServerBase):
    """Schema para crear un servidor MediaMTX."""
    
    password: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Contraseña para autenticación"
    )
    is_active: bool = Field(
        True,
        description="Si el servidor está activo"
    )
    is_default: bool = Field(
        False,
        description="Si es el servidor por defecto"
    )
    
    @field_validator('password')
    def validate_password(cls, v: Optional[str], info) -> Optional[str]:
        """Valida que la contraseña sea requerida si auth está habilitada."""
        # En Pydantic v2, usar info.data para acceder a otros campos
        auth_enabled = info.data.get('auth_enabled', True)
        username = info.data.get('username')
        
        if auth_enabled and username and not v:
            raise ValueError('La contraseña es requerida cuando la autenticación está habilitada')
        
        return v


class MediaMTXServerUpdate(BaseModel):
    """Schema para actualizar un servidor MediaMTX."""
    
    server_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100
    )
    rtsp_url: Optional[str] = None
    rtsp_port: Optional[int] = Field(None, ge=1, le=65535)
    api_url: Optional[str] = None
    api_port: Optional[int] = Field(None, ge=1, le=65535)
    api_enabled: Optional[bool] = None
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=1, max_length=200)
    auth_enabled: Optional[bool] = None
    use_tcp: Optional[bool] = None
    max_reconnects: Optional[int] = Field(None, ge=0, le=10)
    reconnect_delay: Optional[float] = Field(None, ge=0.1, le=60.0)
    publish_path_template: Optional[str] = None
    health_check_interval: Optional[int] = Field(None, ge=10, le=300)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator('rtsp_url')
    def validate_rtsp_url(cls, v: Optional[str]) -> Optional[str]:
        """Valida URL RTSP si se proporciona."""
        if v is not None and not v.startswith('rtsp://'):
            raise ValueError('RTSP URL debe comenzar con rtsp://')
        return v
    
    @field_validator('api_url')
    def validate_api_url(cls, v: Optional[str]) -> Optional[str]:
        """Valida API URL si se proporciona."""
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('API URL debe comenzar con http:// o https://')
        return v


class MediaMTXServerResponse(MediaMTXServerBase):
    """Schema de respuesta para servidores MediaMTX."""
    
    server_id: int = Field(..., description="ID único del servidor")
    is_active: bool = Field(..., description="Si el servidor está activo")
    is_default: bool = Field(..., description="Si es el servidor por defecto")
    is_authenticated: bool = Field(False, description="Si hay sesión activa")
    auth_expires_at: Optional[datetime] = Field(None, description="Expiración del token")
    last_health_status: str = Field("unknown", description="Último estado de salud")
    last_health_check: Optional[datetime] = Field(None, description="Última verificación")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    
    # Métricas opcionales
    metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Métricas agregadas del servidor"
    )
    
    class Config:
        """Configuración del modelo."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MediaMTXServerStatus(BaseModel):
    """Schema para estado detallado del servidor."""
    
    server: MediaMTXServerResponse = Field(..., description="Información del servidor")
    connection: Dict[str, Any] = Field(..., description="Estado de conexión")
    authentication: Dict[str, Any] = Field(..., description="Estado de autenticación")
    publications: Dict[str, Any] = Field(..., description="Estadísticas de publicación")
    health: Dict[str, Any] = Field(..., description="Estado de salud")


class MediaMTXServerTestResult(BaseModel):
    """Schema para resultado de prueba de conexión."""
    
    success: bool = Field(..., description="Si la prueba fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    latency_ms: Optional[int] = Field(None, description="Latencia en milisegundos")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")


class MediaMTXServerListResponse(BaseModel):
    """Schema para respuesta paginada de servidores."""
    
    total: int = Field(..., description="Total de servidores")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    items: list[MediaMTXServerResponse] = Field(..., description="Lista de servidores")