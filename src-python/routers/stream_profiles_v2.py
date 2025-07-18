"""
Router para gestión de perfiles de streaming de cámaras V2.

Version actualizada con nuevos schemas de validación.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime
import logging

from api.dependencies import create_response
from api.schemas.requests.stream_profile_requests import (
    CreateStreamProfileRequest,
    UpdateStreamProfileRequest,
    ApplyProfileRequest,
    CloneProfileRequest,
    TestProfileRequest,
    StreamQuality,
    VideoCodec,
    StreamProtocol
)
from api.schemas.responses.stream_profile_responses import (
    StreamProfileInfo,
    StreamProfileDetailResponse,
    ProfileListResponse,
    ProfileApplicationResult,
    ProfileTestResult,
    ProfileStatistics,
    ProfileCompatibilityResponse,
    ProfileStatus
)
from api.dependencies.validation_deps import validate_camera_exists
from services.camera_manager_service import camera_manager_service
from utils.exceptions import (
    CameraNotFoundError,
    ServiceError
)

logger = logging.getLogger(__name__)

# Crear router principal
router = APIRouter(
    prefix="/stream-profiles",
    tags=["stream-profiles"],
    responses={404: {"description": "Perfil no encontrado"}}
)


# === Endpoints Globales ===

@router.get("/", response_model=ProfileListResponse)
async def list_all_profiles(
    quality: Optional[StreamQuality] = None,
    is_default: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Listar todos los perfiles de streaming disponibles.
    
    Args:
        quality: Filtrar por calidad
        is_default: Filtrar solo perfiles por defecto
        limit: Número máximo de resultados
        offset: Offset para paginación
        
    Returns:
        Lista de perfiles disponibles
    """
    try:
        logger.info("Listando todos los perfiles de streaming")
        
        # TODO: Implementar obtención desde servicio/DB
        # Por ahora devolver perfiles de ejemplo
        profiles = [
            StreamProfileInfo(
                profile_id="default_high",
                name="Alta Calidad",
                description="Máxima calidad disponible",
                quality="high",
                is_default=True,
                is_system=True,
                created_at=datetime.utcnow(),
                updated_at=None
            ),
            StreamProfileInfo(
                profile_id="default_medium",
                name="Calidad Media",
                description="Balance entre calidad y ancho de banda",
                quality="medium",
                is_default=True,
                is_system=True,
                created_at=datetime.utcnow(),
                updated_at=None
            ),
            StreamProfileInfo(
                profile_id="default_low",
                name="Baja Calidad",
                description="Mínimo uso de ancho de banda",
                quality="low",
                is_default=True,
                is_system=True,
                created_at=datetime.utcnow(),
                updated_at=None
            )
        ]
        
        # Aplicar filtros
        if quality:
            profiles = [p for p in profiles if p.quality == quality]
        if is_default is not None:
            profiles = [p for p in profiles if p.is_default == is_default]
        
        # Aplicar paginación
        total = len(profiles)
        profiles = profiles[offset:offset + limit]
        
        return ProfileListResponse(
            total=total,
            profiles=profiles
        )
        
    except Exception as e:
        logger.error(f"Error listando perfiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=StreamProfileDetailResponse)
async def create_profile(
    request: CreateStreamProfileRequest
):
    """
    Crear un nuevo perfil de streaming global.
    
    Los perfiles globales pueden ser usados por cualquier cámara.
    
    Args:
        request: Datos del nuevo perfil
        
    Returns:
        Perfil creado con todos sus detalles
    """
    try:
        logger.info(f"Creando perfil global '{request.name}'")
        
        # TODO: Implementar creación en servicio/DB
        # Por ahora devolver perfil de ejemplo
        profile_id = f"prof_{int(datetime.utcnow().timestamp())}"
        
        profile = StreamProfileDetailResponse(
            profile_id=profile_id,
            name=request.name,
            description=request.description,
            quality=request.quality,
            codec=request.codec or VideoCodec.AUTO,
            protocol=request.protocol or StreamProtocol.RTSP,
            resolution=request.resolution,
            fps=request.fps,
            bitrate=request.bitrate,
            audio_enabled=request.audio_enabled,
            custom_settings=request.custom_settings or {},
            is_default=False,
            is_system=False,
            cameras_using=0,
            created_at=datetime.utcnow(),
            updated_at=None
        )
        
        logger.info(f"Perfil {profile_id} creado exitosamente")
        
        return profile
        
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creando perfil: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{profile_id}", response_model=StreamProfileDetailResponse)
async def get_profile_details(
    profile_id: str
):
    """
    Obtener detalles completos de un perfil.
    
    Args:
        profile_id: ID del perfil
        
    Returns:
        Detalles completos del perfil
    """
    try:
        logger.info(f"Obteniendo detalles del perfil {profile_id}")
        
        # TODO: Implementar obtención desde servicio/DB
        # Por ahora devolver perfil de ejemplo
        if profile_id.startswith("default_"):
            quality = profile_id.replace("default_", "")
            profile = StreamProfileDetailResponse(
                profile_id=profile_id,
                name=f"{quality.capitalize()} Calidad",
                description=f"Perfil de {quality} calidad del sistema",
                quality=quality,
                codec=VideoCodec.H264,
                protocol=StreamProtocol.RTSP,
                resolution="1920x1080" if quality == "high" else "1280x720",
                fps=25 if quality == "high" else 15,
                bitrate=4000 if quality == "high" else 2000,
                audio_enabled=True,
                custom_settings={},
                is_default=True,
                is_system=True,
                cameras_using=5,
                created_at=datetime.utcnow(),
                updated_at=None
            )
            return profile
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Perfil {profile_id} no encontrado"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo perfil: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{profile_id}", response_model=StreamProfileDetailResponse)
async def update_profile(
    profile_id: str,
    request: UpdateStreamProfileRequest
):
    """
    Actualizar un perfil existente.
    
    Solo se actualizan los campos proporcionados.
    No se pueden modificar perfiles del sistema.
    
    Args:
        profile_id: ID del perfil a actualizar
        request: Datos a actualizar
        
    Returns:
        Perfil actualizado
    """
    try:
        logger.info(f"Actualizando perfil {profile_id}")
        
        # Validar que no sea un perfil del sistema
        if profile_id.startswith("default_"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No se pueden modificar perfiles del sistema"
            )
        
        # TODO: Implementar actualización en servicio/DB
        # Por ahora devolver perfil actualizado de ejemplo
        profile = StreamProfileDetailResponse(
            profile_id=profile_id,
            name=request.name or "Perfil Actualizado",
            description=request.description or "Perfil personalizado actualizado",
            quality=request.quality or StreamQuality.MEDIUM,
            codec=request.codec or VideoCodec.H264,
            protocol=request.protocol or StreamProtocol.RTSP,
            resolution=request.resolution or "1280x720",
            fps=request.fps or 20,
            bitrate=request.bitrate or 2500,
            audio_enabled=request.audio_enabled if request.audio_enabled is not None else True,
            custom_settings=request.custom_settings or {},
            is_default=False,
            is_system=False,
            cameras_using=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        logger.info(f"Perfil {profile_id} actualizado exitosamente")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando perfil: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: str
):
    """
    Eliminar un perfil.
    
    No se pueden eliminar perfiles del sistema o perfiles en uso.
    
    Args:
        profile_id: ID del perfil a eliminar
    """
    try:
        logger.info(f"Eliminando perfil {profile_id}")
        
        # Validar que no sea un perfil del sistema
        if profile_id.startswith("default_"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No se pueden eliminar perfiles del sistema"
            )
        
        # TODO: Verificar que no esté en uso
        # TODO: Implementar eliminación en servicio/DB
        
        logger.info(f"Perfil {profile_id} eliminado exitosamente")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando perfil: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{profile_id}/apply", response_model=ProfileApplicationResult)
async def apply_profile_to_camera(
    profile_id: str,
    request: ApplyProfileRequest
):
    """
    Aplicar un perfil a una cámara específica.
    
    Args:
        profile_id: ID del perfil a aplicar
        request: Datos de aplicación (camera_id, persist, etc)
        
    Returns:
        Resultado de la aplicación
    """
    try:
        # Validar que la cámara existe
        camera_id = request.camera_id
        # TODO: Validar con servicio real
        
        logger.info(f"Aplicando perfil {profile_id} a cámara {camera_id}")
        
        # TODO: Implementar aplicación real
        # Por ahora devolver resultado de ejemplo
        result = ProfileApplicationResult(
            camera_id=camera_id,
            profile_id=profile_id,
            success=True,
            status=ProfileStatus.ACTIVE,
            message="Perfil aplicado exitosamente",
            stream_url=f"rtsp://camera-{camera_id}/stream",
            error=None
        )
        
        if request.test_duration:
            result.status = ProfileStatus.TESTING
            result.message = f"Perfil en prueba por {request.test_duration} segundos"
        
        return result
        
    except Exception as e:
        logger.error(f"Error aplicando perfil: {e}", exc_info=True)
        return ProfileApplicationResult(
            camera_id=request.camera_id,
            profile_id=profile_id,
            success=False,
            status=ProfileStatus.ERROR,
            message="Error aplicando perfil",
            stream_url=None,
            error=str(e)
        )


@router.post("/{profile_id}/test", response_model=ProfileTestResult)
async def test_profile(
    profile_id: str,
    request: TestProfileRequest
):
    """
    Probar un perfil con una cámara específica.
    
    Realiza una prueba temporal del perfil para evaluar
    su rendimiento y compatibilidad.
    
    Args:
        profile_id: ID del perfil a probar
        request: Parámetros de la prueba
        
    Returns:
        Resultado de la prueba con métricas
    """
    try:
        logger.info(f"Probando perfil {profile_id} con cámara {request.camera_id}")
        
        # TODO: Implementar prueba real
        # Por ahora devolver resultado de ejemplo
        
        # Simular métricas
        metrics = {}
        issues = []
        recommendations = []
        
        if request.collect_metrics:
            metrics = {
                "avg_fps": 24.8,
                "avg_bitrate_kbps": 3950,
                "dropped_frames": 2,
                "latency_ms": 120,
                "cpu_usage_percent": 15.5,
                "memory_usage_mb": 45.2,
                "network_usage_mbps": 4.1
            }
            
            # Generar issues y recomendaciones basadas en métricas
            if metrics["avg_fps"] < 25:
                issues.append("FPS por debajo del objetivo")
                recommendations.append("Considere reducir la resolución o bitrate")
            
            if metrics["latency_ms"] > 100:
                issues.append("Latencia alta detectada")
                recommendations.append("Verifique la conexión de red")
        
        result = ProfileTestResult(
            profile_id=profile_id,
            camera_id=request.camera_id,
            success=len(issues) == 0,
            duration_seconds=request.duration,
            metrics=metrics if request.collect_metrics else None,
            issues=issues,
            recommendations=recommendations
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error probando perfil: {e}", exc_info=True)
        return ProfileTestResult(
            profile_id=profile_id,
            camera_id=request.camera_id,
            success=False,
            duration_seconds=0,
            metrics=None,
            issues=[f"Error durante la prueba: {str(e)}"],
            recommendations=["Verifique la conexión con la cámara"]
        )


@router.post("/{profile_id}/clone", response_model=StreamProfileDetailResponse)
async def clone_profile(
    profile_id: str,
    request: CloneProfileRequest
):
    """
    Clonar un perfil existente.
    
    Crea una copia del perfil con un nuevo nombre.
    
    Args:
        profile_id: ID del perfil a clonar
        request: Datos del nuevo perfil
        
    Returns:
        Nuevo perfil clonado
    """
    try:
        logger.info(f"Clonando perfil {profile_id} como '{request.new_name}'")
        
        # TODO: Obtener perfil original y clonarlo
        # Por ahora crear perfil de ejemplo
        new_profile_id = f"prof_clone_{int(datetime.utcnow().timestamp())}"
        
        profile = StreamProfileDetailResponse(
            profile_id=new_profile_id,
            name=request.new_name,
            description=request.new_description or f"Clonado de {profile_id}",
            quality=StreamQuality.MEDIUM,
            codec=VideoCodec.H264,
            protocol=StreamProtocol.RTSP,
            resolution="1280x720",
            fps=20,
            bitrate=2500,
            audio_enabled=True,
            custom_settings={},
            is_default=False,
            is_system=False,
            cameras_using=0,
            created_at=datetime.utcnow(),
            updated_at=None
        )
        
        logger.info(f"Perfil clonado exitosamente: {new_profile_id}")
        
        return profile
        
    except Exception as e:
        logger.error(f"Error clonando perfil: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{profile_id}/statistics", response_model=ProfileStatistics)
async def get_profile_statistics(
    profile_id: str
):
    """
    Obtener estadísticas de uso de un perfil.
    
    Args:
        profile_id: ID del perfil
        
    Returns:
        Estadísticas de uso del perfil
    """
    try:
        logger.info(f"Obteniendo estadísticas del perfil {profile_id}")
        
        # TODO: Implementar obtención real de estadísticas
        # Por ahora devolver datos de ejemplo
        
        stats = ProfileStatistics(
            profile_id=profile_id,
            total_cameras=5,
            active_streams=3,
            total_usage_hours=1250.5,
            avg_performance_score=87.5,
            common_issues={
                "high_latency": 12,
                "dropped_frames": 5,
                "connection_lost": 2,
                "low_fps": 8
            }
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{profile_id}/compatibility/{camera_id}", response_model=ProfileCompatibilityResponse)
async def check_profile_compatibility(
    profile_id: str,
    camera_id: str = Depends(validate_camera_exists)
):
    """
    Verificar compatibilidad de un perfil con una cámara.
    
    Args:
        profile_id: ID del perfil
        camera_id: ID de la cámara
        
    Returns:
        Análisis de compatibilidad
    """
    try:
        logger.info(f"Verificando compatibilidad del perfil {profile_id} con cámara {camera_id}")
        
        # TODO: Implementar verificación real
        # Por ahora devolver compatibilidad de ejemplo
        
        compatibility = ProfileCompatibilityResponse(
            profile_id=profile_id,
            camera_id=camera_id,
            is_compatible=True,
            compatibility_score=85.0,
            supported_features=[
                "h264_codec",
                "1080p_resolution",
                "rtsp_protocol",
                "audio_stream",
                "25fps_support"
            ],
            unsupported_features=[
                "h265_codec",
                "4k_resolution"
            ],
            warnings=[
                "La cámara podría no alcanzar los 25 FPS en condiciones de poca luz",
                "El bitrate solicitado está cerca del límite máximo de la cámara"
            ]
        )
        
        return compatibility
        
    except Exception as e:
        logger.error(f"Error verificando compatibilidad: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# === Endpoints para cámaras específicas ===

@router.get("/cameras/{camera_id}/profiles", response_model=ProfileListResponse)
async def list_camera_profiles(
    camera_id: str = Depends(validate_camera_exists),
    include_compatible: bool = True
):
    """
    Listar perfiles aplicados y compatibles con una cámara.
    
    Args:
        camera_id: ID de la cámara
        include_compatible: Incluir perfiles compatibles no aplicados
        
    Returns:
        Lista de perfiles de la cámara
    """
    try:
        logger.info(f"Listando perfiles para cámara {camera_id}")
        
        # TODO: Implementar obtención real
        # Por ahora devolver perfiles de ejemplo
        
        profiles = []
        
        # Perfil actualmente aplicado
        profiles.append(StreamProfileInfo(
            profile_id=f"{camera_id}_current",
            name="Perfil Actual",
            description="Configuración activa de la cámara",
            quality="medium",
            is_default=False,
            is_system=False,
            created_at=datetime.utcnow(),
            updated_at=None
        ))
        
        # Perfiles compatibles
        if include_compatible:
            profiles.extend([
                StreamProfileInfo(
                    profile_id="default_high",
                    name="Alta Calidad",
                    description="Máxima calidad disponible",
                    quality="high",
                    is_default=True,
                    is_system=True,
                    created_at=datetime.utcnow(),
                    updated_at=None
                ),
                StreamProfileInfo(
                    profile_id="default_low",
                    name="Baja Calidad",
                    description="Mínimo uso de ancho de banda",
                    quality="low",
                    is_default=True,
                    is_system=True,
                    created_at=datetime.utcnow(),
                    updated_at=None
                )
            ])
        
        return ProfileListResponse(
            total=len(profiles),
            profiles=profiles
        )
        
    except Exception as e:
        logger.error(f"Error listando perfiles de cámara: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/cameras/{camera_id}/active-profile", response_model=StreamProfileDetailResponse)
async def get_camera_active_profile(
    camera_id: str = Depends(validate_camera_exists)
):
    """
    Obtener el perfil activo de una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Perfil actualmente activo
    """
    try:
        logger.info(f"Obteniendo perfil activo de cámara {camera_id}")
        
        # TODO: Implementar obtención real
        # Por ahora devolver perfil de ejemplo
        
        profile = StreamProfileDetailResponse(
            profile_id=f"{camera_id}_active",
            name="Perfil Activo",
            description="Configuración actualmente en uso",
            quality=StreamQuality.MEDIUM,
            codec=VideoCodec.H264,
            protocol=StreamProtocol.RTSP,
            resolution="1280x720",
            fps=20,
            bitrate=2500,
            audio_enabled=True,
            custom_settings={
                "gop": 40,
                "profile": "main"
            },
            is_default=False,
            is_system=False,
            cameras_using=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return profile
        
    except Exception as e:
        logger.error(f"Error obteniendo perfil activo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )