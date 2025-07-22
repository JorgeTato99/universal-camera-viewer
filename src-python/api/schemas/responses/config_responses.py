"""
Schemas de response para endpoints de configuración.

Modelos para estructurar las respuestas de configuración.
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from datetime import datetime


class ConfigUpdateInfo(BaseModel):
    """Información de actualización de configuración."""
    key: str = Field(..., description="Clave actualizada")
    value: Any = Field(..., description="Nuevo valor")
    previous_value: Any = Field(..., description="Valor anterior")


class ConfigError(BaseModel):
    """Error en actualización de configuración."""
    key: str = Field(..., description="Clave con error")
    error: str = Field(..., description="Mensaje de error")


class ConfigSettings(BaseModel):
    """Configuración general de la aplicación."""
    app_name: str = Field("Universal Camera Viewer", description="Nombre de la aplicación")
    theme: str = Field("light", description="Tema de la UI")
    language: str = Field("es", description="Idioma")
    default_quality: str = Field("medium", description="Calidad por defecto")
    grid_columns: int = Field(3, description="Columnas en la grilla")
    show_fps_overlay: bool = Field(True, description="Mostrar overlay de FPS")
    auto_connect: bool = Field(False, description="Conexión automática")
    recording_path: Optional[str] = Field(None, description="Ruta de grabaciones")
    
    class Config:
        extra = 'allow'  # Permitir configuraciones adicionales


class ConfigSchema(BaseModel):
    """Esquema JSON Schema de configuración."""
    title: str = Field(..., description="Título del esquema")
    type: str = Field(..., description="Tipo de esquema")
    properties: Dict[str, Dict[str, Any]] = Field(..., description="Propiedades del esquema")
    required: Optional[List[str]] = Field(None, description="Campos requeridos")
    

class ConfigDifference(BaseModel):
    """Diferencia entre configuraciones."""
    key: str = Field(..., description="Clave modificada")
    current_value: Any = Field(..., description="Valor actual")
    default_value: Any = Field(..., description="Valor por defecto")
    type: str = Field(..., description="Tipo de dato")


class ConfigValueResponse(BaseModel):
    """Respuesta para valor específico de configuración."""
    
    key: str = Field(..., description="Clave de configuración")
    value: Any = Field(..., description="Valor actual")
    type: str = Field(..., description="Tipo de dato")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "theme",
                "value": "dark",
                "type": "str"
            }
        }


class ConfigUpdateResponse(BaseModel):
    """Respuesta para actualización de configuración."""
    
    key: str = Field(..., description="Clave actualizada")
    value: Any = Field(..., description="Nuevo valor")
    previous_value: Any = Field(..., description="Valor anterior")
    message: str = Field(default="Configuración actualizada exitosamente")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "theme",
                "value": "dark",
                "previous_value": "light",
                "message": "Configuración actualizada exitosamente"
            }
        }


class BatchConfigUpdateResponse(BaseModel):
    """Respuesta para actualización batch de configuración."""
    
    updated: List[ConfigUpdateInfo] = Field(..., description="Configuraciones actualizadas")
    errors: List[ConfigError] = Field(..., description="Errores encontrados")
    message: str = Field(..., description="Resumen de la operación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "updated": [
                    {"key": "theme", "value": "dark", "previous_value": "light"},
                    {"key": "language", "value": "es", "previous_value": "en"}
                ],
                "errors": [
                    {"key": "invalid_key", "error": "Configuración no encontrada"}
                ],
                "message": "2 configuraciones actualizadas, 1 errores"
            }
        }


class ConfigCategoryResponse(BaseModel):
    """Respuesta para categoría de configuración."""
    
    name: str = Field(..., description="Nombre de la categoría")
    display_name: str = Field(..., description="Nombre para mostrar")
    description: str = Field(..., description="Descripción de la categoría")
    settings: ConfigSettings = Field(..., description="Valores de configuración")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "general",
                "display_name": "General",
                "description": "Configuración general de la aplicación",
                "settings": {
                    "app_name": "Universal Camera Viewer",
                    "theme": "light",
                    "language": "es"
                }
            }
        }


class ConfigExportResponse(BaseModel):
    """Respuesta para exportación de configuración."""
    
    version: str = Field(..., description="Versión de la aplicación")
    exported_at: str = Field(..., description="Fecha de exportación")
    config: ConfigSettings = Field(..., description="Configuración completa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "0.8.2",
                "exported_at": "2024-01-15T10:30:00Z",
                "config": {
                    "app_name": "Universal Camera Viewer",
                    "theme": "light",
                    "language": "es",
                    "default_quality": "medium"
                }
            }
        }


class ConfigImportResponse(BaseModel):
    """Respuesta para importación de configuración."""
    
    message: str = Field(..., description="Mensaje de estado")
    imported_from_version: str = Field(..., description="Versión de origen")
    imported_at: str = Field(..., description="Fecha original de exportación")
    timestamp: str = Field(..., description="Momento de importación")
    changes_count: int = Field(..., description="Número de cambios aplicados")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Configuración importada exitosamente",
                "imported_from_version": "0.8.1",
                "imported_at": "2024-01-14T15:00:00Z",
                "timestamp": "2024-01-15T10:30:00Z",
                "changes_count": 5
            }
        }


class ConfigResetResponse(BaseModel):
    """Respuesta para reset de configuración."""
    
    message: str = Field(..., description="Mensaje de confirmación")
    timestamp: str = Field(..., description="Momento del reset")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Configuración restablecida a valores por defecto",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ConfigValidationResponse(BaseModel):
    """Respuesta para validación de configuración."""
    
    key: str = Field(..., description="Clave validada")
    value: Any = Field(..., description="Valor propuesto")
    valid: bool = Field(..., description="Si el valor es válido")
    current_value: Optional[Any] = Field(None, description="Valor actual")
    error: Optional[str] = Field(None, description="Error si no es válido")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "grid_columns",
                "value": 8,
                "valid": False,
                "current_value": 3,
                "error": "ensure this value is less than or equal to 6"
            }
        }


class ConfigSchemaResponse(BaseModel):
    """Respuesta con esquema de configuración."""
    
    config_schema: ConfigSchema = Field(..., description="JSON Schema de configuración")
    categories: Dict[str, List[str]] = Field(..., description="Campos por categoría")
    
    class Config:
        json_schema_extra = {
            "example": {
                "config_schema": {
                    "title": "AppConfig",
                    "type": "object",
                    "properties": {
                        "theme": {
                            "type": "string",
                            "enum": ["light", "dark"]
                        }
                    }
                },
                "categories": {
                    "general": ["app_name", "theme", "language"],
                    "ui": ["grid_columns", "show_fps_overlay"]
                }
            }
        }


class ConfigDiffResponse(BaseModel):
    """Respuesta con diferencias de configuración."""
    
    total_settings: int = Field(..., description="Total de configuraciones")
    modified_count: int = Field(..., description="Configuraciones modificadas")
    differences: List[ConfigDifference] = Field(..., description="Lista de diferencias")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_settings": 20,
                "modified_count": 3,
                "differences": [
                    {
                        "key": "theme",
                        "current_value": "dark",
                        "default_value": "light",
                        "type": "str"
                    }
                ]
            }
        }