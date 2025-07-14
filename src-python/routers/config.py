"""
Router para endpoints de configuración.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from api.dependencies import create_response
from api.config import settings

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/config",
    tags=["config"],
    responses={404: {"description": "Configuración no encontrada"}}
)


# === Modelos Pydantic ===

class AppConfig(BaseModel):
    """Configuración de la aplicación."""
    # General
    app_name: str = Field(default="Universal Camera Viewer")
    theme: str = Field(default="light", pattern="^(light|dark)$")
    language: str = Field(default="es", pattern="^(es|en)$")
    
    # Streaming
    default_quality: str = Field(default="medium", pattern="^(low|medium|high)$")
    default_fps: int = Field(default=30, ge=1, le=60)
    buffer_size: int = Field(default=10, ge=1, le=100)
    auto_reconnect: bool = Field(default=True)
    reconnect_interval: int = Field(default=5, ge=1, le=60)
    
    # UI
    grid_columns: int = Field(default=3, ge=1, le=6)
    show_fps_overlay: bool = Field(default=True)
    show_timestamp: bool = Field(default=True)
    fullscreen_on_double_click: bool = Field(default=True)
    
    # Network
    scan_timeout: int = Field(default=5, ge=1, le=30)
    concurrent_connections: int = Field(default=4, ge=1, le=16)
    
    # Storage
    save_snapshots: bool = Field(default=True)
    snapshot_format: str = Field(default="jpeg", pattern="^(jpeg|png|webp)$")
    snapshot_quality: int = Field(default=85, ge=1, le=100)
    max_snapshots: int = Field(default=100, ge=1, le=1000)
    
    # Advanced
    debug_mode: bool = Field(default=False)
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "app_name": "Universal Camera Viewer",
                "theme": "light",
                "default_quality": "medium",
                "default_fps": 30,
                "grid_columns": 3,
                "auto_reconnect": True
            }
        }


class ConfigUpdate(BaseModel):
    """Actualización parcial de configuración."""
    key: str = Field(..., description="Clave de configuración a actualizar")
    value: Any = Field(..., description="Nuevo valor")
    category: Optional[str] = Field(None, description="Categoría de la configuración")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "theme",
                "value": "dark",
                "category": "ui"
            }
        }


class ConfigCategory(BaseModel):
    """Categoría de configuración."""
    name: str
    display_name: str
    description: str
    settings: Dict[str, Any]


# === Configuración mock ===

MOCK_CONFIG = AppConfig()


# === Endpoints ===

@router.get("/", response_model=AppConfig)
async def get_config():
    """
    Obtener configuración completa de la aplicación.
    
    Returns:
        Configuración actual
    """
    logger.info("Obteniendo configuración completa")
    
    # TODO: Integrar con ConfigService real
    return MOCK_CONFIG


@router.get("/categories")
async def get_config_categories():
    """
    Obtener configuración organizada por categorías.
    
    Returns:
        Configuración agrupada por categorías
    """
    categories = [
        ConfigCategory(
            name="general",
            display_name="General",
            description="Configuración general de la aplicación",
            settings={
                "app_name": MOCK_CONFIG.app_name,
                "theme": MOCK_CONFIG.theme,
                "language": MOCK_CONFIG.language
            }
        ),
        ConfigCategory(
            name="streaming",
            display_name="Streaming",
            description="Configuración de streaming de video",
            settings={
                "default_quality": MOCK_CONFIG.default_quality,
                "default_fps": MOCK_CONFIG.default_fps,
                "buffer_size": MOCK_CONFIG.buffer_size,
                "auto_reconnect": MOCK_CONFIG.auto_reconnect,
                "reconnect_interval": MOCK_CONFIG.reconnect_interval
            }
        ),
        ConfigCategory(
            name="ui",
            display_name="Interfaz de Usuario",
            description="Configuración de la interfaz",
            settings={
                "grid_columns": MOCK_CONFIG.grid_columns,
                "show_fps_overlay": MOCK_CONFIG.show_fps_overlay,
                "show_timestamp": MOCK_CONFIG.show_timestamp,
                "fullscreen_on_double_click": MOCK_CONFIG.fullscreen_on_double_click
            }
        ),
        ConfigCategory(
            name="network",
            display_name="Red",
            description="Configuración de red y escaneo",
            settings={
                "scan_timeout": MOCK_CONFIG.scan_timeout,
                "concurrent_connections": MOCK_CONFIG.concurrent_connections
            }
        ),
        ConfigCategory(
            name="storage",
            display_name="Almacenamiento",
            description="Configuración de almacenamiento de datos",
            settings={
                "save_snapshots": MOCK_CONFIG.save_snapshots,
                "snapshot_format": MOCK_CONFIG.snapshot_format,
                "snapshot_quality": MOCK_CONFIG.snapshot_quality,
                "max_snapshots": MOCK_CONFIG.max_snapshots
            }
        ),
        ConfigCategory(
            name="advanced",
            display_name="Avanzado",
            description="Configuración avanzada y debugging",
            settings={
                "debug_mode": MOCK_CONFIG.debug_mode,
                "log_level": MOCK_CONFIG.log_level
            }
        )
    ]
    
    return create_response(
        success=True,
        data=[cat.model_dump() for cat in categories]
    )


@router.get("/{key}")
async def get_config_value(key: str):
    """
    Obtener valor específico de configuración.
    
    Args:
        key: Clave de configuración
        
    Returns:
        Valor de la configuración
    """
    if not hasattr(MOCK_CONFIG, key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuración '{key}' no encontrada"
        )
    
    value = getattr(MOCK_CONFIG, key)
    
    return create_response(
        success=True,
        data={
            "key": key,
            "value": value,
            "type": type(value).__name__
        }
    )


@router.put("/")
async def update_config(update: ConfigUpdate):
    """
    Actualizar un valor de configuración.
    
    Args:
        update: Clave y valor a actualizar
        
    Returns:
        Configuración actualizada
    """
    logger.info(f"Actualizando configuración: {update.key} = {update.value}")
    
    # Validar que la clave existe
    if not hasattr(MOCK_CONFIG, update.key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuración '{update.key}' no encontrada"
        )
    
    # Validar tipo
    current_value = getattr(MOCK_CONFIG, update.key)
    if type(update.value) != type(current_value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo inválido. Se esperaba {type(current_value).__name__}, "
                   f"se recibió {type(update.value).__name__}"
        )
    
    # Actualizar valor
    setattr(MOCK_CONFIG, update.key, update.value)
    
    return create_response(
        success=True,
        data={
            "key": update.key,
            "value": update.value,
            "previous_value": current_value,
            "message": "Configuración actualizada exitosamente"
        }
    )


@router.put("/batch")
async def update_config_batch(updates: Dict[str, Any]):
    """
    Actualizar múltiples valores de configuración.
    
    Args:
        updates: Diccionario con claves y valores a actualizar
        
    Returns:
        Resultado de las actualizaciones
    """
    logger.info(f"Actualizando {len(updates)} configuraciones")
    
    results = []
    errors = []
    
    for key, value in updates.items():
        try:
            if not hasattr(MOCK_CONFIG, key):
                errors.append({
                    "key": key,
                    "error": "Configuración no encontrada"
                })
                continue
            
            current_value = getattr(MOCK_CONFIG, key)
            if type(value) != type(current_value):
                errors.append({
                    "key": key,
                    "error": f"Tipo inválido. Se esperaba {type(current_value).__name__}"
                })
                continue
            
            setattr(MOCK_CONFIG, key, value)
            results.append({
                "key": key,
                "value": value,
                "previous_value": current_value
            })
            
        except Exception as e:
            errors.append({
                "key": key,
                "error": str(e)
            })
    
    return create_response(
        success=len(errors) == 0,
        data={
            "updated": results,
            "errors": errors,
            "message": f"{len(results)} configuraciones actualizadas, {len(errors)} errores"
        }
    )


@router.post("/reset")
async def reset_config():
    """
    Restablecer configuración a valores por defecto.
    
    Returns:
        Estado de la operación
    """
    logger.warning("Restableciendo configuración a valores por defecto")
    
    global MOCK_CONFIG
    MOCK_CONFIG = AppConfig()
    
    return create_response(
        success=True,
        data={
            "message": "Configuración restablecida a valores por defecto",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


@router.post("/export")
async def export_config():
    """
    Exportar configuración actual.
    
    Returns:
        Configuración en formato exportable
    """
    logger.info("Exportando configuración")
    
    export_data = {
        "version": settings.app_version,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "config": MOCK_CONFIG.model_dump()
    }
    
    return create_response(
        success=True,
        data=export_data
    )


@router.post("/import")
async def import_config(import_data: Dict[str, Any]):
    """
    Importar configuración desde archivo.
    
    Args:
        import_data: Datos de configuración a importar
        
    Returns:
        Estado de la importación
    """
    logger.info("Importando configuración")
    
    try:
        # Validar estructura
        if "config" not in import_data:
            raise ValueError("Formato de importación inválido")
        
        # Crear nueva configuración desde datos importados
        new_config = AppConfig(**import_data["config"])
        
        # Actualizar configuración global
        global MOCK_CONFIG
        MOCK_CONFIG = new_config
        
        return create_response(
            success=True,
            data={
                "message": "Configuración importada exitosamente",
                "imported_from_version": import_data.get("version", "unknown"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al importar configuración: {str(e)}"
        )