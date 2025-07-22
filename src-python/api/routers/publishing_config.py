"""
Endpoints REST para gestión de configuraciones MediaMTX.

Permite crear, modificar y eliminar configuraciones de publicación.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime

from api.models.publishing_models import MediaMTXConfigRequest
from models.publishing import PublishConfiguration
from services.database import get_publishing_db_service
from utils.exceptions import ServiceError
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Modelos de respuesta
class ConfigurationResponse(BaseModel):
    """
    Respuesta con configuración MediaMTX.
    
    Temporalmente mantiene compatibilidad con frontend.
    TODO: Migrar a usar MediaMTXServerResponse de mediamtx_responses.py
    """
    id: int = Field(..., description="ID único de la configuración")
    name: str = Field(..., description="Nombre de la configuración", alias="config_name")
    mediamtx_url: str = Field(..., description="URL del servidor MediaMTX")
    api_url: Optional[str] = Field(None, description="URL de la API MediaMTX")
    api_enabled: bool = Field(False, description="Si la API está habilitada")
    username: Optional[str] = Field(None, description="Usuario para autenticación")
    auth_enabled: bool = Field(False, description="Si requiere autenticación")
    use_tcp: bool = Field(True, description="Forzar transporte TCP")
    max_reconnects: int = Field(3, description="Máximo de intentos de reconexión")
    reconnect_delay: float = Field(5.0, description="Segundos entre reconexiones")
    publish_path_template: str = Field("camera_{camera_id}", description="Template para paths")
    is_active: bool = Field(False, description="Si está activa")
    created_at: Optional[str] = Field(None, description="Fecha de creación")
    updated_at: Optional[str] = Field(None, description="Última actualización")
    
    class Config:
        populate_by_name = True  # Permite usar tanto 'name' como 'config_name'


class ConfigurationListResponse(BaseModel):
    """Lista de configuraciones."""
    total: int
    items: List[ConfigurationResponse]


router = APIRouter(
    prefix="/api/publishing/config",
    tags=["publishing-config"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=ConfigurationListResponse,
    summary="Listar configuraciones"
)
async def list_configurations():
    """
    Lista todas las configuraciones MediaMTX disponibles.
    
    Returns:
        ConfigurationListResponse con todas las configuraciones
    """
    logger.debug("Obteniendo lista de configuraciones MediaMTX")
    
    try:
        db_service = get_publishing_db_service()
        await db_service.initialize()
        
        # Obtener todas las configuraciones
        all_configs = await db_service.get_all_configurations()
        
        items = []
        for config_data in all_configs:
            items.append(ConfigurationResponse(
                id=config_data['config_id'],
                name=config_data['config_name'],  # Se mapeará a 'config_name' por el alias
                mediamtx_url=config_data['mediamtx_url'],
                api_url=config_data['api_url'],
                api_enabled=config_data['api_enabled'],
                username=config_data['username'],
                auth_enabled=config_data['auth_enabled'],
                use_tcp=config_data['use_tcp'],
                max_reconnects=config_data['max_reconnects'],
                reconnect_delay=config_data['reconnect_delay'],
                publish_path_template=config_data['publish_path_template'],
                is_active=config_data['is_active'],
                created_at=config_data['created_at'],
                updated_at=config_data['updated_at']
            ))
            
        return ConfigurationListResponse(
            total=len(items),
            items=items
        )
        
    except Exception as e:
        logger.exception("Error obteniendo configuraciones")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo configuraciones"
        )


@router.get(
    "/active",
    response_model=ConfigurationResponse,
    summary="Obtener configuración activa"
)
async def get_active_configuration():
    """
    Obtiene la configuración MediaMTX actualmente activa.
    
    Returns:
        ConfigurationResponse con la configuración activa
        
    Raises:
        404: Si no hay configuración activa
    """
    logger.debug("Obteniendo configuración MediaMTX activa")
    
    try:
        db_service = get_publishing_db_service()
        await db_service.initialize()
        
        config_data = await db_service.get_active_configuration()
        
        if not config_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay configuración activa"
            )
            
        config = config_data['config']
        return ConfigurationResponse(
            id=config_data['config_id'],
            name=config_data['config_name'],
            mediamtx_url=config.mediamtx_url,
            api_url=config.get_api_url(),
            api_enabled=config.api_enabled,
            username=config.username,
            auth_enabled=config.auth_enabled,
            use_tcp=config.use_tcp,
            max_reconnects=config.max_reconnects,
            reconnect_delay=config.reconnect_delay,
            publish_path_template=config.publish_path_template,
            is_active=True,
            created_at=config_data.get('created_at'),
            updated_at=config_data.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error obteniendo configuración activa")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo configuración activa"
        )


@router.post(
    "/",
    response_model=ConfigurationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear configuración"
)
async def create_configuration(
    request: MediaMTXConfigRequest,
    set_active: bool = False
):
    """
    Crea una nueva configuración MediaMTX.
    
    Args:
        request: Datos de la configuración
        set_active: Si establecer como configuración activa
        
    Returns:
        ConfigurationResponse con la configuración creada
        
    Raises:
        409: Si el nombre ya existe
    """
    logger.info(f"Creando configuración MediaMTX: {request.name}")
    
    try:
        db_service = get_publishing_db_service()
        await db_service.initialize()
        
        # Verificar si ya existe
        existing = await db_service.get_configuration_by_name(request.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una configuración con el nombre '{request.name}'"
            )
            
        # Crear configuración
        config = PublishConfiguration(
            mediamtx_url=request.mediamtx_url,
            api_url=request.api_url,
            api_enabled=request.api_enabled,
            username=request.username,
            password=request.password,
            auth_enabled=request.auth_enabled,
            use_tcp=request.use_tcp,
            max_reconnects=request.max_reconnects,
            reconnect_delay=request.reconnect_delay,
            publish_path_template=request.publish_path_template
        )
        
        # Guardar en BD
        config_id = await db_service.save_configuration(
            config,
            name=request.name,
            set_active=set_active,
            created_by="api"  # TODO: Obtener usuario real
        )
        
        logger.info(f"Configuración '{request.name}' creada con ID {config_id}")
        
        return ConfigurationResponse(
            id=config_id,
            name=request.name,
            mediamtx_url=config.mediamtx_url,
            api_url=config.api_url,
            api_enabled=config.api_enabled,
            username=config.username,
            auth_enabled=config.auth_enabled,
            use_tcp=config.use_tcp,
            max_reconnects=config.max_reconnects,
            reconnect_delay=config.reconnect_delay,
            publish_path_template=config.publish_path_template,
            is_active=set_active,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creando configuración")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creando configuración"
        )


@router.put(
    "/{config_name}",
    response_model=ConfigurationResponse,
    summary="Actualizar configuración"
)
async def update_configuration(
    config_name: str,
    request: MediaMTXConfigRequest
):
    """
    Actualiza una configuración existente.
    
    Args:
        config_name: Nombre de la configuración a actualizar
        request: Nuevos datos de configuración
        
    Returns:
        ConfigurationResponse con la configuración actualizada
        
    Raises:
        404: Si la configuración no existe
    """
    logger.info(f"Actualizando configuración: {config_name}")
    
    try:
        db_service = get_publishing_db_service()
        await db_service.initialize()
        
        # Obtener configuración completa con metadatos
        all_configs = await db_service.get_all_configurations()
        existing_config = None
        for cfg in all_configs:
            if cfg['config_name'] == config_name:
                existing_config = cfg
                break
                
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe configuración con nombre '{config_name}'"
            )
            
        # Actualizar configuración
        config = PublishConfiguration(
            mediamtx_url=request.mediamtx_url,
            api_url=request.api_url,
            api_enabled=request.api_enabled,
            username=request.username,
            password=request.password,
            auth_enabled=request.auth_enabled,
            use_tcp=request.use_tcp,
            max_reconnects=request.max_reconnects,
            reconnect_delay=request.reconnect_delay,
            publish_path_template=request.publish_path_template
        )
        
        # Guardar cambios
        await db_service.save_configuration(
            config,
            name=config_name,
            set_active=False,  # No cambiar estado activo
            created_by="api"
        )
        
        logger.info(f"Configuración '{config_name}' actualizada")
        
        return ConfigurationResponse(
            id=existing_config['config_id'],
            name=config_name,
            mediamtx_url=config.mediamtx_url,
            api_url=config.api_url,
            api_enabled=config.api_enabled,
            username=config.username,
            auth_enabled=config.auth_enabled,
            use_tcp=config.use_tcp,
            max_reconnects=config.max_reconnects,
            reconnect_delay=config.reconnect_delay,
            publish_path_template=config.publish_path_template,
            is_active=existing_config['is_active'],
            created_at=existing_config['created_at'],
            updated_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error actualizando configuración")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error actualizando configuración"
        )


@router.delete(
    "/{config_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar configuración"
)
async def delete_configuration(config_name: str):
    """
    Elimina una configuración MediaMTX.
    
    Args:
        config_name: Nombre de la configuración a eliminar
        
    Raises:
        404: Si la configuración no existe
        409: Si la configuración está en uso
    """
    logger.info(f"Eliminando configuración: {config_name}")
    
    try:
        db_service = get_publishing_db_service()
        await db_service.initialize()
        
        deleted = await db_service.delete_configuration(config_name)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe configuración con nombre '{config_name}'"
            )
            
        logger.info(f"Configuración '{config_name}' eliminada")
        
    except HTTPException:
        raise
    except ServiceError as e:
        if e.error_code == "CONFIG_IN_USE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error eliminando configuración")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error eliminando configuración"
        )


@router.post(
    "/{config_name}/activate",
    response_model=ConfigurationResponse,
    summary="Activar configuración"
)
async def activate_configuration(config_name: str):
    """
    Activa una configuración MediaMTX.
    
    Solo puede haber una configuración activa a la vez.
    
    Args:
        config_name: Nombre de la configuración a activar
        
    Returns:
        ConfigurationResponse con la configuración activada
        
    Raises:
        404: Si la configuración no existe
    """
    logger.info(f"Activando configuración: {config_name}")
    
    try:
        db_service = get_publishing_db_service()
        await db_service.initialize()
        
        # Obtener configuración completa con metadatos
        all_configs = await db_service.get_all_configurations()
        existing_config = None
        for cfg in all_configs:
            if cfg['config_name'] == config_name:
                existing_config = cfg
                break
                
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe configuración con nombre '{config_name}'"
            )
            
        # Obtener la configuración actual
        config = await db_service.get_configuration_by_name(config_name)
        
        # Reactivar con set_active=True y obtener el ID actualizado
        config_id = await db_service.save_configuration(
            config,
            name=config_name,
            set_active=True,
            created_by="api"
        )
        
        logger.info(f"Configuración '{config_name}' activada")
        
        return ConfigurationResponse(
            id=config_id,
            name=config_name,
            mediamtx_url=config.mediamtx_url,
            api_url=config.api_url,
            api_enabled=config.api_enabled,
            username=config.username,
            auth_enabled=config.auth_enabled,
            use_tcp=config.use_tcp,
            max_reconnects=config.max_reconnects,
            reconnect_delay=config.reconnect_delay,
            publish_path_template=config.publish_path_template,
            is_active=True,
            created_at=existing_config['created_at'],
            updated_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error activando configuración")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activando configuración"
        )