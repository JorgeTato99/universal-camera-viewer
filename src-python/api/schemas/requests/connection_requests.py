"""
Schemas de request para endpoints de conexión.

Modelos Pydantic para validar datos de entrada en conexiones.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from api.validators import validate_uuid, validate_timeout


class TestConnectionRequest(BaseModel):
    """Request para probar conexión a una cámara."""
    
    timeout: Optional[float] = Field(10.0, description="Timeout en segundos")
    
    @validator('timeout')
    def validate_timeout_value(cls, v):
        """Valida el valor del timeout."""
        if v is not None:
            return validate_timeout(v, min_timeout=1.0, max_timeout=60.0)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "timeout": 10.0
            }
        }


class DisconnectRequest(BaseModel):
    """Request para desconectar una cámara."""
    
    force: bool = Field(False, description="Forzar desconexión incluso si hay streams activos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "force": False
            }
        }


class ReconnectRequest(BaseModel):
    """Request para reconectar una cámara."""
    
    timeout: Optional[float] = Field(10.0, description="Timeout en segundos")
    retry_count: int = Field(3, ge=1, le=10, description="Número de reintentos")
    
    @validator('timeout')
    def validate_timeout_value(cls, v):
        """Valida el valor del timeout."""
        if v is not None:
            return validate_timeout(v, min_timeout=1.0, max_timeout=60.0)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "timeout": 10.0,
                "retry_count": 3
            }
        }


class BatchConnectionRequest(BaseModel):
    """Request para operaciones de conexión en lote."""
    
    camera_ids: List[str] = Field(..., description="Lista de IDs de cámaras")
    operation: str = Field(..., description="Operación a realizar")
    timeout: Optional[float] = Field(10.0, description="Timeout para cada operación")
    
    @validator('camera_ids')
    def validate_camera_ids(cls, v):
        """Valida la lista de IDs de cámaras."""
        if not v:
            raise ValueError("Debe proporcionar al menos un ID de cámara")
        if len(v) > 50:
            raise ValueError("Máximo 50 cámaras por operación batch")
        
        # Validar cada ID
        validated_ids = []
        for camera_id in v:
            validated_ids.append(validate_uuid(camera_id, "ID de cámara"))
        
        return validated_ids
    
    @validator('operation')
    def validate_operation(cls, v):
        """Valida la operación solicitada."""
        valid_operations = ['connect', 'disconnect', 'test', 'reconnect']
        if v not in valid_operations:
            raise ValueError(f"Operación debe ser una de: {', '.join(valid_operations)}")
        return v
    
    @validator('timeout')
    def validate_timeout_value(cls, v):
        """Valida el valor del timeout."""
        if v is not None:
            return validate_timeout(v, min_timeout=1.0, max_timeout=60.0)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "456e7890-e89b-12d3-a456-426614174001"
                ],
                "operation": "connect",
                "timeout": 10.0
            }
        }