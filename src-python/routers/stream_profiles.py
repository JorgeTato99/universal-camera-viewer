"""
Router para gestión de perfiles de streaming de cámaras.

Proporciona endpoints para crear, actualizar, eliminar y gestionar
perfiles de streaming (main, sub, third) con diferentes configuraciones
de calidad, resolución, FPS y bitrate.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime
import logging

from api.dependencies import create_response
from api.models.camera_models import (
    CreateStreamProfileRequest,
    UpdateStreamProfileRequest,
    StreamProfileDetailResponse,
    StreamProfileListResponse,
    StreamType,
    VideoCodec,
    StreamQuality
)
from services.camera_manager_service import camera_manager_service
from utils.exceptions import (
    CameraNotFoundError,
    ServiceError
)

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/cameras/{camera_id}/stream-profiles",
    tags=["stream-profiles"],
    responses={404: {"description": "Cámara o perfil no encontrado"}}
)


# === Funciones auxiliares ===

def _validate_resolution(resolution: str) -> tuple[int, int]:
    """
    Valida y parsea una resolución.
    
    Args:
        resolution: String en formato "WIDTHxHEIGHT"
        
    Returns:
        Tupla (width, height)
        
    Raises:
        ValueError: Si el formato es inválido o valores fuera de rango
    """
    try:
        if 'x' not in resolution:
            raise ValueError("Debe usar formato WIDTHxHEIGHT (ej: 1920x1080)")
        
        parts = resolution.split('x')
        if len(parts) != 2:
            raise ValueError("Formato incorrecto, use WIDTHxHEIGHT")
        
        width, height = int(parts[0]), int(parts[1])
        
        # Validar rangos razonables
        if width < 160 or width > 7680:
            raise ValueError(f"Ancho {width} fuera de rango (160-7680)")
        if height < 120 or height > 4320:
            raise ValueError(f"Alto {height} fuera de rango (120-4320)")
        
        return width, height
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error parseando resolución '{resolution}': {e}")


def _calculate_recommended_bitrate(width: int, height: int, fps: int, codec: str) -> int:
    """
    Calcula el bitrate recomendado basado en resolución, FPS y codec.
    
    Args:
        width: Ancho en píxeles
        height: Alto en píxeles
        fps: Frames por segundo
        codec: Codec de video
        
    Returns:
        Bitrate recomendado en kbps
    """
    # Píxeles totales
    pixels = width * height
    
    # Factor base por resolución
    if pixels >= 8294400:  # 4K (3840x2160)
        base_bitrate = 15000
    elif pixels >= 2073600:  # 1080p (1920x1080)
        base_bitrate = 5000
    elif pixels >= 921600:   # 720p (1280x720)
        base_bitrate = 2500
    elif pixels >= 409920:   # 480p (854x480)
        base_bitrate = 1200
    else:
        base_bitrate = 600
    
    # Ajuste por FPS
    fps_factor = fps / 30.0
    
    # Ajuste por codec
    codec_factor = 1.0 if codec == "H264" else 0.7  # H265 es más eficiente
    
    return int(base_bitrate * fps_factor * codec_factor)


# === Endpoints ===

@router.get("/", response_model=StreamProfileListResponse)
async def list_stream_profiles(
    camera_id: str,
    stream_type: Optional[StreamType] = None,
    is_active: bool = True
):
    """
    Listar todos los perfiles de streaming de una cámara.
    
    Los perfiles definen configuraciones específicas para diferentes
    calidades de streaming (HD, SD, móvil, etc.).
    
    Args:
        camera_id: ID único de la cámara (UUID)
        stream_type: Filtrar por tipo de stream (main, sub, third, mobile)
        is_active: Si solo mostrar perfiles activos
        
    Returns:
        StreamProfileListResponse: Lista de perfiles con información completa
        
    Raises:
        HTTPException 404: Si la cámara no existe
        HTTPException 500: Error interno del servidor
    """
    try:
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        logger.info(f"Listando perfiles de streaming para cámara: {camera_id}")
        
        profiles = await camera_manager_service.get_stream_profiles(camera_id)
        
        # Filtrar por tipo si se especifica
        if stream_type:
            profiles = [p for p in profiles if p.get('stream_type') == stream_type.value]
        
        # Filtrar por estado si se especifica
        if is_active:
            profiles = [p for p in profiles if p.get('is_active', True)]
        
        # Construir respuesta
        profile_responses = []
        for profile in profiles:
            try:
                profile_responses.append(StreamProfileDetailResponse(
                    profile_id=profile['profile_id'],
                    profile_name=profile['profile_name'],
                    profile_token=profile.get('profile_token'),
                    stream_type=profile['stream_type'],
                    encoding=profile['encoding'],
                    resolution=profile['resolution'],
                    framerate=profile['framerate'],
                    bitrate=profile['bitrate'],
                    quality=profile['quality'],
                    gop_interval=profile.get('gop_interval'),
                    channel=profile.get('channel', 1),
                    subtype=profile.get('subtype', 0),
                    is_default=profile['is_default'],
                    is_active=profile['is_active'],
                    endpoint_id=profile.get('endpoint_id'),
                    created_at=profile['created_at'],
                    updated_at=profile['updated_at']
                ))
            except Exception as e:
                logger.warning(f"Error procesando perfil {profile.get('profile_id')}: {e}")
        
        response_data = StreamProfileListResponse(
            total=len(profile_responses),
            profiles=profile_responses
        )
        
        logger.info(f"Devolviendo {len(profile_responses)} perfiles para cámara {camera_id}")
        
        return create_response(
            success=True,
            data=response_data.dict()
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio listando perfiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado listando perfiles para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=StreamProfileDetailResponse)
async def create_stream_profile(
    camera_id: str,
    request: CreateStreamProfileRequest
):
    """
    Crear un nuevo perfil de streaming para una cámara.
    
    Si es el primer perfil o se marca como 'is_default', se establecerá
    automáticamente como el perfil predeterminado. Solo puede haber un
    perfil predeterminado por tipo de stream.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        request: Datos del nuevo perfil de streaming
        
    Returns:
        StreamProfileDetailResponse: Perfil creado
        
    Raises:
        HTTPException 400: Datos inválidos o perfil duplicado
        HTTPException 404: Si la cámara no existe
        HTTPException 409: Si ya existe un perfil con el mismo nombre
        HTTPException 500: Error interno del servidor
    """
    try:
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        # Validar resolución
        width, height = _validate_resolution(request.resolution)
        
        # Validar coherencia de parámetros
        if request.bitrate < 64:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El bitrate mínimo es 64 kbps"
            )
        
        if request.bitrate > 50000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El bitrate máximo es 50000 kbps (50 Mbps)"
            )
        
        # Validar que GOP no sea mayor que FPS * 10 (10 segundos)
        if request.gop_interval and request.gop_interval > request.fps * 10:
            logger.warning(
                f"GOP interval muy alto ({request.gop_interval}) para {request.fps} FPS. "
                f"Máximo recomendado: {request.fps * 10}"
            )
        
        # Calcular bitrate recomendado si es muy bajo
        recommended_bitrate = _calculate_recommended_bitrate(
            width, height, request.fps, request.codec.value
        )
        if request.bitrate < recommended_bitrate * 0.3:
            logger.warning(
                f"Bitrate muy bajo ({request.bitrate} kbps) para {request.resolution}@{request.fps}fps. "
                f"Recomendado: {recommended_bitrate} kbps"
            )
        
        logger.info(f"Creando perfil '{request.profile_name}' para cámara {camera_id}")
        
        # Preparar datos del perfil
        profile_data = {
            'profile_name': request.profile_name.strip(),
            'stream_type': request.stream_type.value,
            'resolution': request.resolution,
            'framerate': request.fps,
            'bitrate': request.bitrate,
            'encoding': request.codec.value,
            'quality': request.quality.value,
            'gop_interval': request.gop_interval,
            'channel': request.channel,
            'subtype': request.subtype,
            'is_default': request.is_default
        }
        
        profile = await camera_manager_service.add_stream_profile(camera_id, profile_data)
        
        profile_response = StreamProfileDetailResponse(
            profile_id=profile['profile_id'],
            profile_name=profile['profile_name'],
            profile_token=profile.get('profile_token'),
            stream_type=profile['stream_type'],
            encoding=profile['encoding'],
            resolution=profile['resolution'],
            framerate=profile['framerate'],
            bitrate=profile['bitrate'],
            quality=profile['quality'],
            gop_interval=profile.get('gop_interval'),
            channel=profile.get('channel', 1),
            subtype=profile.get('subtype', 0),
            is_default=profile['is_default'],
            is_active=profile['is_active'],
            endpoint_id=profile.get('endpoint_id'),
            created_at=profile['created_at'],
            updated_at=profile['updated_at']
        )
        
        logger.info(f"Perfil {profile['profile_id']} creado exitosamente para cámara {camera_id}")
        
        return create_response(
            success=True,
            data=profile_response.dict()
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada al crear perfil: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Datos inválidos al crear perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio creando perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado creando perfil para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{profile_id}", response_model=StreamProfileDetailResponse)
async def update_stream_profile(
    camera_id: str,
    profile_id: int,
    request: UpdateStreamProfileRequest
):
    """
    Actualizar un perfil de streaming existente.
    
    Solo se actualizan los campos proporcionados. Si se marca como default,
    se quitará el flag default de otros perfiles del mismo tipo de stream.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        profile_id: ID del perfil a actualizar
        request: Datos a actualizar
        
    Returns:
        StreamProfileDetailResponse: Perfil actualizado
        
    Raises:
        HTTPException 400: Datos inválidos
        HTTPException 404: Si la cámara o perfil no existe
        HTTPException 500: Error interno del servidor
    """
    try:
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        logger.info(f"Actualizando perfil {profile_id} de cámara {camera_id}")
        
        # Preparar actualizaciones
        updates = {}
        
        if request.profile_name is not None:
            updates['profile_name'] = request.profile_name.strip()
        
        if request.resolution is not None:
            width, height = _validate_resolution(request.resolution)
            updates['resolution'] = request.resolution
        
        if request.fps is not None:
            if request.fps < 1 or request.fps > 120:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="FPS debe estar entre 1 y 120"
                )
            updates['framerate'] = request.fps
            
        if request.bitrate is not None:
            if request.bitrate < 64 or request.bitrate > 50000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bitrate debe estar entre 64 y 50000 kbps"
                )
            updates['bitrate'] = request.bitrate
            
        if request.codec is not None:
            updates['encoding'] = request.codec.value
            
        if request.quality is not None:
            updates['quality'] = request.quality.value
            
        if request.gop_interval is not None:
            updates['gop_interval'] = request.gop_interval
            
        if request.is_default is not None:
            updates['is_default'] = request.is_default
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron campos para actualizar"
            )
        
        profile = await camera_manager_service.update_stream_profile(
            camera_id, profile_id, updates
        )
        
        profile_response = StreamProfileDetailResponse(
            profile_id=profile['profile_id'],
            profile_name=profile['profile_name'],
            profile_token=profile.get('profile_token'),
            stream_type=profile['stream_type'],
            encoding=profile['encoding'],
            resolution=profile['resolution'],
            framerate=profile['framerate'],
            bitrate=profile['bitrate'],
            quality=profile['quality'],
            gop_interval=profile.get('gop_interval'),
            channel=profile.get('channel', 1),
            subtype=profile.get('subtype', 0),
            is_default=profile['is_default'],
            is_active=profile['is_active'],
            endpoint_id=profile.get('endpoint_id'),
            created_at=profile['created_at'],
            updated_at=profile['updated_at']
        )
        
        logger.info(f"Perfil {profile_id} actualizado exitosamente")
        
        return create_response(
            success=True,
            data=profile_response.dict()
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        if "no encontrad" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio actualizando perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado actualizando perfil {profile_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stream_profile(
    camera_id: str,
    profile_id: int
):
    """
    Eliminar un perfil de streaming.
    
    No se puede eliminar el único perfil activo de una cámara.
    Si se elimina el perfil default, se asignará otro como default.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        profile_id: ID del perfil a eliminar
        
    Raises:
        HTTPException 400: Si es el único perfil activo
        HTTPException 404: Si la cámara o perfil no existe
        HTTPException 500: Error interno del servidor
    """
    try:
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        logger.info(f"Eliminando perfil {profile_id} de cámara {camera_id}")
        
        await camera_manager_service.delete_stream_profile(camera_id, profile_id)
        
        logger.info(f"Perfil {profile_id} eliminado exitosamente")
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Error de validación al eliminar: {e}")
        if "no encontrad" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio eliminando perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado eliminando perfil {profile_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{profile_id}/set-default")
async def set_default_profile(
    camera_id: str,
    profile_id: int
):
    """
    Establecer un perfil como predeterminado.
    
    Solo puede haber un perfil default por tipo de stream.
    El perfil debe estar activo para ser marcado como default.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        profile_id: ID del perfil
        
    Returns:
        Confirmación de la operación
        
    Raises:
        HTTPException 400: Si el perfil no está activo
        HTTPException 404: Si la cámara o perfil no existe
        HTTPException 500: Error interno del servidor
    """
    try:
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        logger.info(f"Estableciendo perfil {profile_id} como default para cámara {camera_id}")
        
        success = await camera_manager_service.set_default_stream_profile(camera_id, profile_id)
        
        return create_response(
            success=success,
            data={
                "camera_id": camera_id,
                "profile_id": profile_id,
                "message": "Perfil establecido como predeterminado"
            }
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        if "no encontrad" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio estableciendo default: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado estableciendo perfil default: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{profile_id}/test", response_model=dict)
async def test_stream_profile(
    camera_id: str,
    profile_id: int,
    duration: int = 5
):
    """
    Probar un perfil de streaming.
    
    Intenta conectar y obtener algunos frames usando la configuración
    del perfil para validar que funciona correctamente.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        profile_id: ID del perfil a probar
        duration: Duración de la prueba en segundos (default: 5)
        
    Returns:
        Resultado de la prueba con métricas
        
    Raises:
        HTTPException 404: Si la cámara o perfil no existe
        HTTPException 500: Error interno del servidor
    """
    try:
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        # Limitar duración de prueba
        if duration < 1 or duration > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La duración debe estar entre 1 y 30 segundos"
            )
        
        logger.info(f"Probando perfil {profile_id} de cámara {camera_id} por {duration} segundos")
        
        result = await camera_manager_service.test_stream_profile(
            camera_id, profile_id, duration
        )
        
        return create_response(
            success=result.get('success', False),
            data=result
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        if "no encontrad" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio probando perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado probando perfil {profile_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )