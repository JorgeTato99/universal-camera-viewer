"""
Router para endpoints de configuración.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from api.dependencies import create_response
from api.config import settings
from utils.exceptions import ServiceError, ValidationError
from api.schemas.requests.config_requests import (
    ConfigUpdateRequest,
    BatchConfigUpdateRequest,
    ConfigImportRequest,
    ConfigValidateRequest
)
from api.schemas.responses.config_responses import (
    ConfigValueResponse,
    ConfigUpdateResponse,
    BatchConfigUpdateResponse,
    ConfigCategoryResponse,
    ConfigExportResponse,
    ConfigImportResponse,
    ConfigResetResponse,
    ConfigValidationResponse,
    ConfigSchemaResponse,
    ConfigDiffResponse
)
from api.validators import validate_config_key

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


# Los modelos ahora están en los schemas


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
    try:
        logger.info("Obteniendo configuración completa")
        
        # TODO: Integrar con ConfigService real
        return MOCK_CONFIG
        
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo configuración: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de configuración temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado obteniendo configuración: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/categories", response_model=List[ConfigCategoryResponse])
async def get_config_categories():
    """
    Obtener configuración organizada por categorías.
    
    Returns:
        Configuración agrupada por categorías
    """
    categories = [
        ConfigCategoryResponse(
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
    
    return categories


@router.get("/{key}", response_model=ConfigValueResponse)
async def get_config_value(key: str):
    """
    Obtener valor específico de configuración.
    
    Args:
        key: Clave de configuración
        
    Returns:
        Valor de la configuración
    """
    try:
        # Validar clave
        try:
            key = validate_config_key(key)
        except ValueError as e:
            logger.warning(f"Clave de configuración inválida: {key}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
        if not hasattr(MOCK_CONFIG, key):
            logger.warning(f"Configuración no encontrada: {key}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuración '{key}' no encontrada"
            )
        
        value = getattr(MOCK_CONFIG, key)
        logger.debug(f"Obteniendo configuración {key}: {value}")
        
        return ConfigValueResponse(
            key=key,
            value=value,
            type=type(value).__name__
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado obteniendo configuración {key}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/", response_model=ConfigUpdateResponse)
async def update_config(update: ConfigUpdateRequest):
    """
    Actualizar un valor de configuración.
    
    Args:
        update: Clave y valor a actualizar
        
    Returns:
        Configuración actualizada
    """
    try:
        # La validación de la clave ya se hace en el schema
            
        logger.info(f"Actualizando configuración: {update.key} = {update.value}")
        
        # Validar que la clave existe
        if not hasattr(MOCK_CONFIG, update.key):
            logger.warning(f"Configuración no encontrada: {update.key}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuración '{update.key}' no encontrada"
            )
        
        # Validar tipo
        current_value = getattr(MOCK_CONFIG, update.key)
        if type(update.value) != type(current_value):
            logger.warning(
                f"Tipo inválido para {update.key}: esperado {type(current_value).__name__}, "
                f"recibido {type(update.value).__name__}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo inválido. Se esperaba {type(current_value).__name__}, "
                       f"se recibió {type(update.value).__name__}"
            )
        
        # Validar valores según el tipo de campo
        try:
            # Crear instancia temporal para validar
            temp_dict = MOCK_CONFIG.model_dump()
            temp_dict[update.key] = update.value
            AppConfig(**temp_dict)  # Esto validará usando los Field validators
        except ValueError as e:
            logger.warning(f"Valor inválido para {update.key}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Valor inválido para '{update.key}': {str(e)}"
            )
        
        # Actualizar valor
        setattr(MOCK_CONFIG, update.key, update.value)
        logger.info(f"Configuración {update.key} actualizada exitosamente")
        
        return ConfigUpdateResponse(
            key=update.key,
            value=update.value,
            previous_value=current_value,
            message="Configuración actualizada exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado actualizando configuración: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/batch", response_model=BatchConfigUpdateResponse)
async def update_config_batch(request: BatchConfigUpdateRequest):
    """
    Actualizar múltiples valores de configuración.
    
    Args:
        request: Request con diccionario de actualizaciones
        
    Returns:
        Resultado de las actualizaciones
    """
    logger.info(f"Actualizando {len(request.updates)} configuraciones")
    
    results = []
    errors = []
    
    for key, value in request.updates.items():
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
    
    return BatchConfigUpdateResponse(
        updated=results,
        errors=errors,
        message=f"{len(results)} configuraciones actualizadas, {len(errors)} errores"
    )


@router.post("/reset", response_model=ConfigResetResponse)
async def reset_config():
    """
    Restablecer configuración a valores por defecto.
    
    Returns:
        Estado de la operación
    """
    logger.warning("Restableciendo configuración a valores por defecto")
    
    global MOCK_CONFIG
    MOCK_CONFIG = AppConfig()
    
    return ConfigResetResponse(
        message="Configuración restablecida a valores por defecto",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.post("/export", response_model=ConfigExportResponse)
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
    
    return ConfigExportResponse(
        version=settings.app_version,
        exported_at=datetime.utcnow().isoformat() + "Z",
        config=MOCK_CONFIG.model_dump()
    )


@router.get("/category/{category}", response_model=Dict[str, Any])
async def get_config_by_category(category: str):
    """
    Obtener configuración de una categoría específica.
    
    Args:
        category: Nombre de la categoría (general, streaming, ui, network, storage, advanced)
        
    Returns:
        Configuración de la categoría
    """
    try:
        valid_categories = ["general", "streaming", "ui", "network", "storage", "advanced"]
        
        if category not in valid_categories:
            logger.warning(f"Categoría inválida: {category}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría '{category}' no encontrada. Categorías válidas: {', '.join(valid_categories)}"
            )
        
        logger.info(f"Obteniendo configuración de categoría: {category}")
        
        # Mapear campos por categoría
        category_fields = {
            "general": ["app_name", "theme", "language"],
            "streaming": ["default_quality", "default_fps", "buffer_size", "auto_reconnect", "reconnect_interval"],
            "ui": ["grid_columns", "show_fps_overlay", "show_timestamp", "fullscreen_on_double_click"],
            "network": ["scan_timeout", "concurrent_connections"],
            "storage": ["save_snapshots", "snapshot_format", "snapshot_quality", "max_snapshots"],
            "advanced": ["debug_mode", "log_level"]
        }
        
        settings = {}
        for field in category_fields[category]:
            settings[field] = getattr(MOCK_CONFIG, field)
        
        return create_response(
            success=True,
            data={
                "category": category,
                "settings": settings
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo configuración de categoría {category}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/validate", response_model=ConfigValidationResponse)
async def validate_config_value(request: ConfigValidateRequest):
    """
    Validar un valor de configuración sin aplicarlo.
    
    Args:
        request: Request con clave y valor a validar
        
    Returns:
        Resultado de la validación
    """
    try:
        if not hasattr(MOCK_CONFIG, request.key):
            logger.warning(f"Clave de configuración no encontrada: {request.key}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuración '{request.key}' no encontrada"
            )
        
        current_value = getattr(MOCK_CONFIG, request.key)
        
        # Validar tipo
        if type(request.value) != type(current_value):
            return ConfigValidationResponse(
                key=request.key,
                value=request.value,
                valid=False,
                current_value=current_value,
                error=f"Tipo inválido. Se esperaba {type(current_value).__name__}, se recibió {type(request.value).__name__}"
            )
        
        # Validar usando el modelo
        try:
            temp_dict = MOCK_CONFIG.model_dump()
            temp_dict[request.key] = request.value
            AppConfig(**temp_dict)
            
            return ConfigValidationResponse(
                key=request.key,
                value=request.value,
                valid=True,
                current_value=current_value,
                error=None
            )
            
        except ValueError as e:
            return ConfigValidationResponse(
                key=request.key,
                value=request.value,
                valid=False,
                current_value=current_value,
                error=str(e)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validando configuración {request.key}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/schema", response_model=ConfigSchemaResponse)
async def get_config_schema():
    """
    Obtener el esquema de configuración con tipos y validaciones.
    
    Returns:
        Esquema JSON de la configuración
    """
    try:
        logger.info("Obteniendo esquema de configuración")
        
        # Obtener esquema JSON del modelo Pydantic
        schema = AppConfig.model_json_schema()
        
        # Agregar información adicional
        enhanced_schema = {
            "schema": schema,
            "categories": {
                "general": ["app_name", "theme", "language"],
                "streaming": ["default_quality", "default_fps", "buffer_size", "auto_reconnect", "reconnect_interval"],
                "ui": ["grid_columns", "show_fps_overlay", "show_timestamp", "fullscreen_on_double_click"],
                "network": ["scan_timeout", "concurrent_connections"],
                "storage": ["save_snapshots", "snapshot_format", "snapshot_quality", "max_snapshots"],
                "advanced": ["debug_mode", "log_level"]
            }
        }
        
        return ConfigSchemaResponse(
            config_schema=schema,
            categories={
                "general": ["app_name", "theme", "language"],
                "streaming": ["default_quality", "default_fps", "buffer_size", "auto_reconnect", "reconnect_interval"],
                "ui": ["grid_columns", "show_fps_overlay", "show_timestamp", "fullscreen_on_double_click"],
                "network": ["scan_timeout", "concurrent_connections"],
                "storage": ["save_snapshots", "snapshot_format", "snapshot_quality", "max_snapshots"],
                "advanced": ["debug_mode", "log_level"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo esquema de configuración: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/diff", response_model=ConfigDiffResponse)
async def get_config_diff():
    """
    Obtener diferencias entre configuración actual y valores por defecto.
    
    Returns:
        Lista de configuraciones modificadas
    """
    try:
        logger.info("Calculando diferencias de configuración")
        
        # Crear configuración por defecto
        default_config = AppConfig()
        current_dict = MOCK_CONFIG.model_dump()
        default_dict = default_config.model_dump()
        
        # Encontrar diferencias
        differences = []
        for key, current_value in current_dict.items():
            default_value = default_dict.get(key)
            if current_value != default_value:
                differences.append({
                    "key": key,
                    "current_value": current_value,
                    "default_value": default_value,
                    "type": type(current_value).__name__
                })
        
        return ConfigDiffResponse(
            total_settings=len(current_dict),
            modified_count=len(differences),
            differences=differences
        )
        
    except Exception as e:
        logger.error(f"Error calculando diferencias de configuración: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/import", response_model=ConfigImportResponse)
async def import_config(request: ConfigImportRequest):
    """
    Importar configuración desde archivo.
    
    Args:
        request: Request con datos de configuración a importar
        
    Returns:
        Estado de la importación
    """
    try:
        logger.info("Importando configuración")
        
        # La validación de estructura ya se hace en el schema
        
        # Crear nueva configuración desde datos importados
        new_config = AppConfig(**request.config)
        
        # Actualizar configuración global
        global MOCK_CONFIG
        
        # Guardar configuración anterior para rollback
        previous_config = MOCK_CONFIG.model_dump()
        
        MOCK_CONFIG = new_config
        
        imported_version = request.version or "unknown"
        logger.info(f"Configuración importada exitosamente desde versión {imported_version}")
        
        return ConfigImportResponse(
            message="Configuración importada exitosamente",
            imported_from_version=imported_version,
            imported_at=request.exported_at or "unknown",
            timestamp=datetime.utcnow().isoformat() + "Z",
            changes_count=len([k for k, v in new_config.model_dump().items() 
                             if previous_config.get(k) != v])
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Error de validación al importar configuración: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inesperado importando configuración: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )