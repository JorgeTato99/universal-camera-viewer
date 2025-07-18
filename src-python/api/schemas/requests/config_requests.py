"""
Schemas de request para endpoints de configuración.

Modelos Pydantic para validar datos de entrada en configuración.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from api.validators import validate_config_key


class ConfigUpdateRequest(BaseModel):
    """Request para actualizar un valor de configuración."""
    
    key: str = Field(..., description="Clave de configuración a actualizar")
    value: Any = Field(..., description="Nuevo valor")
    category: Optional[str] = Field(None, description="Categoría de la configuración")
    
    @validator('key')
    def validate_key(cls, v):
        """Valida que la clave sea alfanumérica con guiones bajos."""
        return validate_config_key(v)
    
    @validator('category')
    def validate_category(cls, v):
        """Valida categoría si se proporciona."""
        if v is not None:
            valid_categories = ['general', 'streaming', 'ui', 'network', 'storage', 'advanced']
            if v not in valid_categories:
                raise ValueError(f"Categoría debe ser una de: {', '.join(valid_categories)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "theme",
                "value": "dark",
                "category": "ui"
            }
        }


class BatchConfigUpdateRequest(BaseModel):
    """Request para actualizar múltiples valores de configuración."""
    
    updates: Dict[str, Any] = Field(
        ..., 
        description="Diccionario con claves y valores a actualizar",
        min_items=1,
        max_items=50
    )
    
    @validator('updates')
    def validate_updates(cls, v):
        """Valida todas las claves del diccionario."""
        for key in v.keys():
            validate_config_key(key)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "updates": {
                    "theme": "dark",
                    "language": "es",
                    "grid_columns": 4
                }
            }
        }


class ConfigImportRequest(BaseModel):
    """Request para importar configuración."""
    
    version: Optional[str] = Field(None, description="Versión de la configuración")
    exported_at: Optional[str] = Field(None, description="Fecha de exportación")
    config: Dict[str, Any] = Field(..., description="Datos de configuración a importar")
    
    @validator('config')
    def validate_config_not_empty(cls, v):
        """Valida que la configuración no esté vacía."""
        if not v:
            raise ValueError("La configuración no puede estar vacía")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "0.8.2",
                "exported_at": "2024-01-15T10:30:00Z",
                "config": {
                    "app_name": "Universal Camera Viewer",
                    "theme": "light",
                    "default_quality": "medium"
                }
            }
        }


class ConfigValidateRequest(BaseModel):
    """Request para validar un valor de configuración."""
    
    key: str = Field(..., description="Clave de configuración")
    value: Any = Field(..., description="Valor a validar")
    
    @validator('key')
    def validate_key(cls, v):
        """Valida formato de la clave."""
        return validate_config_key(v)