"""
Schemas de request para endpoints de cámaras.

Estos modelos validan los datos de entrada para las operaciones
relacionadas con cámaras.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

from api.validators import (
    validate_uuid,
    validate_ip_address,
    validate_camera_name,
    validate_camera_brand,
    validate_camera_model,
    validate_username,
    validate_password,
    validate_port
)


class CreateCameraRequest(BaseModel):
    """Request para crear una nueva cámara."""
    
    # Información básica
    display_name: str = Field(..., description="Nombre visible de la cámara")
    ip: str = Field(..., description="Dirección IP de la cámara")
    brand: str = Field(default="Generic", description="Marca de la cámara")
    model: Optional[str] = Field(None, description="Modelo de la cámara")
    
    # Credenciales
    username: str = Field(..., description="Usuario para autenticación")
    password: str = Field(..., description="Contraseña para autenticación")
    auth_type: str = Field(default="basic", description="Tipo de autenticación")
    
    # Configuración de puertos
    rtsp_port: Optional[int] = Field(554, description="Puerto RTSP")
    onvif_port: Optional[int] = Field(80, description="Puerto ONVIF")
    http_port: Optional[int] = Field(80, description="Puerto HTTP")
    
    # Información adicional
    location: Optional[str] = Field(None, description="Ubicación física")
    description: Optional[str] = Field(None, description="Descripción adicional")
    
    # Validadores
    _validate_name = validator('display_name', allow_reuse=True)(validate_camera_name)
    _validate_ip = validator('ip', allow_reuse=True)(validate_ip_address)
    _validate_brand = validator('brand', allow_reuse=True)(validate_camera_brand)
    _validate_model = validator('model', allow_reuse=True)(validate_camera_model)
    _validate_username = validator('username', allow_reuse=True)(validate_username)
    _validate_password = validator('password', allow_reuse=True)(validate_password)
    
    @validator('rtsp_port', 'onvif_port', 'http_port')
    def validate_ports(cls, v):
        if v is not None:
            return validate_port(v)
        return v
    
    @validator('auth_type')
    def validate_auth_type(cls, v):
        valid_types = ['basic', 'digest', 'none']
        if v not in valid_types:
            raise ValueError(f"Tipo de autenticación debe ser uno de: {', '.join(valid_types)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "display_name": "Cámara Principal",
                "ip": "192.168.1.100",
                "brand": "Dahua",
                "model": "IPC-HDW2431T",
                "username": "admin",
                "password": "admin123",
                "auth_type": "digest",
                "rtsp_port": 554,
                "onvif_port": 80,
                "location": "Entrada Principal",
                "description": "Cámara de vigilancia de la entrada"
            }
        }


class UpdateCameraRequest(BaseModel):
    """Request para actualizar una cámara existente."""
    
    # Todos los campos son opcionales en actualización
    display_name: Optional[str] = Field(None, description="Nombre visible de la cámara")
    location: Optional[str] = Field(None, description="Ubicación física")
    description: Optional[str] = Field(None, description="Descripción adicional")
    is_active: Optional[bool] = Field(None, description="Si la cámara está activa")
    
    # Validadores para campos presentes
    @validator('display_name')
    def validate_name(cls, v):
        if v is not None:
            return validate_camera_name(v)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "display_name": "Cámara Actualizada",
                "location": "Nueva Ubicación",
                "is_active": True
            }
        }


class TestCameraConnectionRequest(BaseModel):
    """Request para probar conexión a una cámara."""
    
    ip: str = Field(..., description="IP de la cámara a probar")
    username: Optional[str] = Field(None, description="Usuario para autenticación")
    password: Optional[str] = Field(None, description="Contraseña para autenticación")
    brand: Optional[str] = Field("Generic", description="Marca de la cámara")
    protocol: Optional[str] = Field("RTSP", description="Protocolo a probar")
    port: Optional[int] = Field(None, description="Puerto específico")
    timeout: float = Field(10.0, ge=1.0, le=60.0, description="Timeout en segundos")
    
    _validate_ip = validator('ip', allow_reuse=True)(validate_ip_address)
    
    @validator('username')
    def validate_username_optional(cls, v):
        if v:
            return validate_username(v)
        return v
    
    @validator('password')
    def validate_password_optional(cls, v):
        if v:
            return validate_password(v)
        return v
    
    @validator('brand')
    def validate_brand_optional(cls, v):
        if v:
            return validate_camera_brand(v, allow_unknown=True)
        return v
    
    @validator('port')
    def validate_port_optional(cls, v):
        if v is not None:
            return validate_port(v)
        return v


class CameraFilterRequest(BaseModel):
    """Request para filtrar cámaras."""
    
    brand: Optional[str] = Field(None, description="Filtrar por marca")
    is_active: Optional[bool] = Field(None, description="Filtrar por estado activo")
    is_connected: Optional[bool] = Field(None, description="Filtrar por conexión")
    location: Optional[str] = Field(None, description="Filtrar por ubicación")
    protocol: Optional[str] = Field(None, description="Filtrar por protocolo soportado")
    
    # Paginación
    page: int = Field(1, ge=1, description="Número de página")
    page_size: int = Field(20, ge=1, le=100, description="Elementos por página")
    
    # Ordenamiento
    sort_by: Optional[str] = Field("display_name", description="Campo para ordenar")
    sort_order: Optional[str] = Field("asc", description="Orden: asc o desc")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError("Orden debe ser 'asc' o 'desc'")
        return v
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        valid_fields = ['display_name', 'ip', 'brand', 'created_at', 'updated_at']
        if v not in valid_fields:
            raise ValueError(f"Campo de ordenamiento debe ser uno de: {', '.join(valid_fields)}")
        return v


class BatchCameraOperationRequest(BaseModel):
    """Request para operaciones en lote sobre cámaras."""
    
    camera_ids: List[str] = Field(..., description="Lista de IDs de cámaras")
    operation: str = Field(..., description="Operación a realizar")
    
    @validator('camera_ids')
    def validate_camera_ids(cls, v):
        if not v:
            raise ValueError("Debe proporcionar al menos un ID de cámara")
        if len(v) > 100:
            raise ValueError("Máximo 100 cámaras por operación")
        
        # Validar cada ID
        for camera_id in v:
            validate_uuid(camera_id, "ID de cámara")
        
        return v
    
    @validator('operation')
    def validate_operation(cls, v):
        valid_operations = ['connect', 'disconnect', 'delete', 'activate', 'deactivate']
        if v not in valid_operations:
            raise ValueError(f"Operación debe ser una de: {', '.join(valid_operations)}")
        return v