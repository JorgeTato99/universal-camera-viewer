"""
Router para gestión de paths de publicación en MediaMTX.

Proporciona endpoints para crear, listar, actualizar y probar paths
de publicación, incluyendo soporte para plantillas y paths predefinidos.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from services.publishing.mediamtx_paths_service import get_mediamtx_paths_service
from services.camera_manager_service import camera_manager_service
from api.dependencies import get_current_user
from utils.exceptions import ValidationError, ServiceError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/publishing/paths", tags=["publishing-paths"])


# ==================== Modelos de Request/Response ====================

class PathMetadata(BaseModel):
    """Metadata estructurada para paths de publicación."""
    description: Optional[str] = Field(None, description="Descripción del path")
    created_by: Optional[str] = Field(None, description="Usuario que creó el path")
    tags: Optional[List[str]] = Field(None, description="Etiquetas asociadas")
    custom_properties: Optional[Dict[str, str]] = Field(None, description="Propiedades personalizadas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Path principal para cámara de entrada",
                "created_by": "admin",
                "tags": ["entrada", "principal"],
                "custom_properties": {"location": "lobby", "priority": "high"}
            }
        }

class PathCreateRequest(BaseModel):
    """Request para crear un path."""
    path_name: str = Field(..., description="Nombre del path", min_length=3, max_length=50)
    camera_id: str = Field(..., description="ID de la cámara asociada")
    is_permanent: bool = Field(False, description="Si el path es permanente/predefinido")
    auth_required: bool = Field(False, description="Si requiere autenticación")
    auth_username: Optional[str] = Field(None, description="Usuario para autenticación")
    auth_password: Optional[str] = Field(None, description="Contraseña para autenticación")
    recording_enabled: bool = Field(False, description="Si la grabación está habilitada")
    recording_path: Optional[str] = Field(None, description="Ruta para grabaciones")
    metadata: Optional[PathMetadata] = Field(None, description="Metadata estructurada del path")


class PathUpdateRequest(BaseModel):
    """Request para actualizar un path."""
    auth_required: Optional[bool] = Field(None, description="Si requiere autenticación")
    auth_username: Optional[str] = Field(None, description="Usuario para autenticación")
    auth_password: Optional[str] = Field(None, description="Contraseña para autenticación")
    recording_enabled: Optional[bool] = Field(None, description="Si la grabación está habilitada")
    recording_path: Optional[str] = Field(None, description="Ruta para grabaciones")
    is_active: Optional[bool] = Field(None, description="Si el path está activo")
    metadata: Optional[PathMetadata] = Field(None, description="Metadata estructurada del path")


class PathTestRequest(BaseModel):
    """Request para probar un path."""
    test_type: str = Field(
        "availability",
        description="Tipo de prueba: availability, format, connectivity, publish"
    )
    duration_seconds: Optional[int] = Field(
        5,
        description="Duración de la prueba en segundos (solo para tipo 'publish')",
        ge=1,
        le=30
    )


class PathAvailabilityRequest(BaseModel):
    """Request para verificar disponibilidad de paths."""
    paths: List[str] = Field(..., description="Lista de paths a verificar", min_items=1, max_items=10)
    check_mediamtx: bool = Field(True, description="Si verificar también en el servidor MediaMTX")


class PathResponse(BaseModel):
    """Response con información de un path."""
    path_id: str = Field(..., description="ID único del path")
    path_name: str = Field(..., description="Nombre del path")
    camera_id: Optional[str] = Field(None, description="ID de la cámara asociada")
    is_permanent: bool = Field(..., description="Si el path es permanente")
    is_active: bool = Field(..., description="Si el path está activo")
    auth_required: bool = Field(..., description="Si requiere autenticación")
    recording_enabled: bool = Field(..., description="Si la grabación está habilitada")
    created_at: str = Field(..., description="Fecha de creación ISO 8601")
    updated_at: Optional[str] = Field(None, description="Fecha de última actualización ISO 8601")
    last_used_at: Optional[str] = Field(None, description="Fecha de último uso ISO 8601")
    metadata: PathMetadata = Field(default_factory=PathMetadata, description="Metadata estructurada del path")


class PathTemplateResponse(BaseModel):
    """Response con información de una plantilla."""
    template_id: str = Field(..., description="ID de la plantilla")
    name: str = Field(..., description="Nombre de la plantilla")
    pattern: str = Field(..., description="Patrón de la plantilla")
    description: str = Field(..., description="Descripción de la plantilla")
    example: str = Field(..., description="Ejemplo de path generado")


class PathAvailabilityResponse(BaseModel):
    """Response de verificación de disponibilidad."""
    available: bool = Field(..., description="Si el path está disponible")
    path: str = Field(..., description="Path verificado")
    reason: Optional[str] = Field(None, description="Razón si no está disponible")
    suggestions: List[str] = Field(default_factory=list, description="Paths alternativos sugeridos")


class PathDeleteResponse(BaseModel):
    """Response para eliminación de path."""
    success: bool = Field(..., description="Si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    path_id: str = Field(..., description="ID del path eliminado")
    

class PathTestDetails(BaseModel):
    """Detalles de una prueba de path."""
    availability_check: Optional[bool] = Field(None, description="Resultado de verificación de disponibilidad")
    format_validation: Optional[bool] = Field(None, description="Resultado de validación de formato")
    connectivity_test: Optional[bool] = Field(None, description="Resultado de prueba de conectividad")
    publish_test: Optional[bool] = Field(None, description="Resultado de prueba de publicación")
    response_time_ms: Optional[float] = Field(None, description="Tiempo de respuesta en milisegundos")
    error_details: Optional[str] = Field(None, description="Detalles del error si hubo")
    warnings: Optional[List[str]] = Field(None, description="Advertencias encontradas")
    

class PathTestResponse(BaseModel):
    """Response de prueba de path."""
    path_id: str = Field(..., description="ID o nombre del path probado")
    test_type: str = Field(..., description="Tipo de prueba ejecutada")
    success: bool = Field(..., description="Si la prueba fue exitosa")
    message: str = Field(..., description="Mensaje del resultado")
    details: PathTestDetails = Field(..., description="Detalles de la prueba")
    timestamp: str = Field(..., description="Timestamp de la prueba ISO 8601")


class PathWarning(BaseModel):
    """Advertencia sobre un path."""
    path_name: str = Field(..., description="Nombre del path")
    last_used: Optional[str] = Field(None, description="Última vez usado ISO 8601")
    days_inactive: int = Field(..., description="Días de inactividad")
    suggestion: str = Field(..., description="Sugerencia de acción")


class PathStatistics(BaseModel):
    """Estadísticas de uso de paths."""
    total_paths: int = Field(..., description="Total de paths registrados")
    active_paths: int = Field(..., description="Paths actualmente activos")
    predefined_paths: int = Field(..., description="Paths predefinidos/permanentes")
    dynamic_paths: int = Field(..., description="Paths dinámicos")
    warnings: int = Field(..., description="Número de advertencias activas")
    instance_id: str = Field(..., description="ID de la instancia UCV")
    hostname: str = Field(..., description="Hostname del servidor")


# ==================== Endpoints ====================

@router.get("/", response_model=List[PathResponse])
async def list_paths(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=200, description="Número máximo de registros"),
    camera_id: Optional[str] = Query(None, description="Filtrar por ID de cámara"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    is_permanent: Optional[bool] = Query(None, description="Filtrar por paths permanentes"),
    search: Optional[str] = Query(None, description="Buscar en nombre del path"),
    current_user: dict = Depends(get_current_user)
) -> List[PathResponse]:
    """
    Lista todos los paths de publicación con filtros opcionales.
    
    Incluye tanto paths predefinidos como dinámicos.
    """
    try:
        # TODO: Implementar query a BD con filtros
        # Por ahora retornar lista mock
        paths = []
        
        # Agregar algunos paths de ejemplo
        example_path = PathResponse(
            path_id="550e8400-e29b-41d4-a716-446655440000",
            path_name="ucv_abc123_cam_entrance",
            camera_id="cam-entrance-001",
            is_permanent=True,
            is_active=True,
            auth_required=False,
            recording_enabled=False,
            created_at=datetime.now().isoformat(),
            metadata={"description": "Cámara de entrada principal"}
        )
        paths.append(example_path)
        
        return paths
        
    except Exception as e:
        logger.error(f"Error listando paths: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PathResponse)
async def create_path(
    request: PathCreateRequest,
    current_user: dict = Depends(get_current_user)
) -> PathResponse:
    """
    Crea un nuevo path de publicación.
    
    Puede ser un path predefinido (permanente) o dinámico.
    """
    try:
        paths_service = get_mediamtx_paths_service()
        
        # Verificar que la cámara existe
        camera = await camera_manager_service.get_camera(request.camera_id)
        if not camera:
            raise HTTPException(
                status_code=404,
                detail=f"Cámara {request.camera_id} no encontrada"
            )
        
        # Crear path si es permanente
        if request.is_permanent:
            path_data = await paths_service.create_predefined_path(
                path_name=request.path_name,
                camera_id=request.camera_id,
                config={
                    "auth_required": request.auth_required,
                    "auth_username": request.auth_username,
                    "auth_password": request.auth_password,
                    "recording_enabled": request.recording_enabled,
                    "recording_path": request.recording_path,
                    "metadata": request.metadata
                }
            )
        else:
            # Para paths dinámicos, solo verificar disponibilidad
            availability = await paths_service.check_availability(request.path_name)
            if not availability["available"]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Path no disponible: {availability['reason']}"
                )
            
            # TODO: Guardar en BD
            path_data = {
                "path_id": "generated-id",
                "path_name": request.path_name,
                "camera_id": request.camera_id,
                "created_at": datetime.now().isoformat()
            }
        
        return PathResponse(
            path_id=path_data["path_id"],
            path_name=request.path_name,
            camera_id=request.camera_id,
            is_permanent=request.is_permanent,
            is_active=True,
            auth_required=request.auth_required,
            recording_enabled=request.recording_enabled,
            created_at=path_data["created_at"],
            metadata=request.metadata or {}
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{path_id}", response_model=PathResponse)
async def update_path(
    path_id: str,
    request: PathUpdateRequest,
    current_user: dict = Depends(get_current_user)
) -> PathResponse:
    """
    Actualiza la configuración de un path existente.
    
    Solo se pueden actualizar los campos proporcionados.
    """
    try:
        # TODO: Implementar actualización en BD
        # Por ahora retornar mock actualizado
        
        return PathResponse(
            path_id=path_id,
            path_name=f"path_{path_id[:8]}",
            is_permanent=True,
            is_active=request.is_active if request.is_active is not None else True,
            auth_required=request.auth_required if request.auth_required is not None else False,
            recording_enabled=request.recording_enabled if request.recording_enabled is not None else False,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            metadata=request.metadata or {}
        )
        
    except Exception as e:
        logger.error(f"Error actualizando path {path_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{path_id}", response_model=PathDeleteResponse)
async def delete_path(
    path_id: str,
    current_user: dict = Depends(get_current_user)
) -> PathDeleteResponse:
    """
    Elimina un path de publicación.
    
    Solo se pueden eliminar paths no permanentes que no estén en uso.
    """
    try:
        # TODO: Implementar eliminación en BD
        # Verificar que no está en uso actualmente
        # Verificar que no es permanente
        
        return PathDeleteResponse(
            success=True,
            message=f"Path {path_id} eliminado correctamente",
            path_id=path_id
        )
        
    except Exception as e:
        logger.error(f"Error eliminando path {path_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{path_id}/test", response_model=PathTestResponse)
async def test_path(
    path_id: str,
    request: PathTestRequest,
    current_user: dict = Depends(get_current_user)
) -> PathTestResponse:
    """
    Ejecuta pruebas sobre un path de publicación.
    
    Tipos de prueba disponibles:
    - **availability**: Verifica si el path está disponible
    - **format**: Valida el formato del path
    - **connectivity**: Prueba conexión con MediaMTX
    - **publish**: Intenta publicar temporalmente (requiere duration_seconds)
    """
    try:
        paths_service = get_mediamtx_paths_service()
        
        # Ejecutar prueba
        result = await paths_service.test_path(path_id, request.test_type)
        
        return PathTestResponse(
            path_id=path_id,
            test_type=request.test_type,
            success=result["success"],
            message=result["message"],
            details=PathTestDetails(
                availability_check=result.get("details", {}).get("availability_check"),
                format_validation=result.get("details", {}).get("format_validation"),
                connectivity_test=result.get("details", {}).get("connectivity_test"),
                publish_test=result.get("details", {}).get("publish_test"),
                response_time_ms=result.get("details", {}).get("response_time_ms"),
                error_details=result.get("details", {}).get("error_details"),
                warnings=result.get("details", {}).get("warnings", [])
            ),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error probando path {path_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[PathTemplateResponse])
async def get_path_templates(
    current_user: dict = Depends(get_current_user)
) -> List[PathTemplateResponse]:
    """
    Obtiene las plantillas predefinidas para generación de paths.
    
    Las plantillas facilitan la creación de paths con patrones comunes.
    """
    try:
        paths_service = get_mediamtx_paths_service()
        templates = paths_service.get_templates()
        
        return [
            PathTemplateResponse(
                template_id=t.template_id,
                name=t.name,
                pattern=t.pattern,
                description=t.description,
                example=t.example
            )
            for t in templates
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo plantillas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available/{camera_id}")
async def get_available_path(
    camera_id: str,
    template_id: str = Query("instance_aware", description="ID de la plantilla a usar"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Obtiene un path disponible sugerido para una cámara.
    
    Usa la plantilla especificada para generar un path único.
    """
    try:
        paths_service = get_mediamtx_paths_service()
        
        # Obtener cámara
        camera = await camera_manager_service.get_camera(camera_id)
        if not camera:
            raise HTTPException(
                status_code=404,
                detail=f"Cámara {camera_id} no encontrada"
            )
        
        # Generar path sugerido
        suggested_path = await paths_service.get_suggested_path(camera, template_id)
        
        return {
            "camera_id": camera_id,
            "suggested_path": suggested_path,
            "template_id": template_id
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo path disponible: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-availability", response_model=List[PathAvailabilityResponse])
async def check_paths_availability(
    request: PathAvailabilityRequest = Body(...),
    current_user: dict = Depends(get_current_user)
) -> List[PathAvailabilityResponse]:
    """
    Verifica la disponibilidad de múltiples paths.
    
    Útil para validar paths antes de crear configuraciones.
    """
    try:
        paths_service = get_mediamtx_paths_service()
        results = []
        
        for path in request.paths:
            availability = await paths_service.check_availability(
                path,
                check_mediamtx=request.check_mediamtx
            )
            
            results.append(PathAvailabilityResponse(
                available=availability["available"],
                path=path,
                reason=availability.get("reason"),
                suggestions=availability.get("suggestions", [])
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error verificando disponibilidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/warnings", response_model=List[PathWarning])
async def get_path_warnings(
    days_threshold: int = Query(30, ge=7, le=365, description="Días de inactividad para considerar un path como antiguo"),
    current_user: dict = Depends(get_current_user)
) -> List[PathWarning]:
    """
    Obtiene advertencias sobre paths antiguos no utilizados.
    
    Ayuda a identificar paths que pueden ser eliminados para liberar espacio.
    """
    try:
        paths_service = get_mediamtx_paths_service()
        warnings_data = await paths_service.get_old_paths_warnings(days_threshold)
        
        return [
            PathWarning(
                path_name=w["path_name"],
                last_used=w.get("last_used"),
                days_inactive=w["days_inactive"],
                suggestion=w["suggestion"]
            )
            for w in warnings_data
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo advertencias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=PathStatistics)
async def get_path_statistics(
    current_user: dict = Depends(get_current_user)
) -> PathStatistics:
    """
    Obtiene estadísticas generales sobre el uso de paths.
    
    Incluye información sobre la instancia actual de UCV.
    """
    try:
        paths_service = get_mediamtx_paths_service()
        stats = await paths_service.get_path_statistics()
        
        return PathStatistics(**stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Inicializar servicio al importar
async def _init_paths_service():
    """Inicializa el servicio de paths."""
    try:
        service = get_mediamtx_paths_service()
        await service.initialize()
    except Exception as e:
        logger.error(f"Error inicializando servicio de paths: {e}")


# TODO: Llamar _init_paths_service() cuando la aplicación inicie