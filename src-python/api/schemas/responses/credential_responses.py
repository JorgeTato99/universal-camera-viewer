"""
Schemas de response para endpoints de credenciales.

Modelos para estructurar las respuestas de credenciales.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CredentialBasicInfo(BaseModel):
    """Información básica de una credencial (sin datos sensibles)."""
    
    credential_id: int = Field(..., description="ID de la credencial")
    username: str = Field(..., description="Nombre de usuario")
    auth_type: str = Field(..., description="Tipo de autenticación")
    is_default: bool = Field(..., description="Si es la credencial por defecto")
    description: Optional[str] = Field(None, description="Descripción")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    
    class Config:
        json_schema_extra = {
            "example": {
                "credential_id": 1,
                "username": "admin",
                "auth_type": "digest",
                "is_default": True,
                "description": "Credenciales principales",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class CredentialDetailResponse(CredentialBasicInfo):
    """Respuesta detallada de una credencial."""
    
    usage_count: int = Field(0, description="Número de veces usada")
    last_used_at: Optional[datetime] = Field(None, description="Último uso")
    associated_cameras: int = Field(0, description="Número de cámaras asociadas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "credential_id": 1,
                "username": "admin",
                "auth_type": "digest",
                "is_default": True,
                "description": "Credenciales principales",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "usage_count": 15,
                "last_used_at": "2024-01-15T14:00:00Z",
                "associated_cameras": 3
            }
        }


class CredentialListResponse(BaseModel):
    """Respuesta para listado de credenciales."""
    
    total: int = Field(..., description="Total de credenciales")
    credentials: List[CredentialBasicInfo] = Field(..., description="Lista de credenciales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "credentials": [
                    {
                        "credential_id": 1,
                        "username": "admin",
                        "auth_type": "digest",
                        "is_default": True,
                        "description": "Credenciales principales",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ]
            }
        }


class CredentialOperationResponse(BaseModel):
    """Respuesta para operaciones sobre credenciales."""
    
    success: bool = Field(..., description="Si la operación fue exitosa")
    credential_id: int = Field(..., description="ID de la credencial")
    operation: str = Field(..., description="Operación realizada")
    message: str = Field(..., description="Mensaje descriptivo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "credential_id": 1,
                "operation": "create",
                "message": "Credencial creada exitosamente"
            }
        }


class TestCredentialResponse(BaseModel):
    """Respuesta de prueba de credenciales."""
    
    success: bool = Field(..., description="Si la prueba fue exitosa")
    auth_type: str = Field(..., description="Tipo de autenticación probado")
    test_url: Optional[str] = Field(None, description="URL probada")
    response_time_ms: Optional[float] = Field(None, description="Tiempo de respuesta")
    error: Optional[str] = Field(None, description="Error si falló")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "auth_type": "digest",
                "test_url": "http://192.168.1.100/api/auth",
                "response_time_ms": 250.5,
                "error": None,
                "details": {
                    "status_code": 200,
                    "headers_received": True
                }
            }
        }


class CameraCredentialAssociationResponse(BaseModel):
    """Respuesta para asociación de credencial con cámara."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    credential_id: int = Field(..., description="ID de la credencial")
    assigned_at: datetime = Field(..., description="Fecha de asignación")
    is_active: bool = Field(..., description="Si la asociación está activa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "credential_id": 1,
                "assigned_at": "2024-01-15T10:30:00Z",
                "is_active": True
            }
        }