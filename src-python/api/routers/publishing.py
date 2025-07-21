"""
Endpoints REST para gestión de publicación a MediaMTX.

Expone funcionalidades de control y monitoreo de streams publicados.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime

from api.models.publishing_models import (
    StartPublishRequest,
    StopPublishRequest,
    PublishStatusResponse,
    PublishListResponse,
    MediaMTXConfigRequest
)
from api.schemas.requests.mediamtx_requests import HealthCheckRequest
from api.schemas.responses.mediamtx_responses import (
    SystemHealthResponse, ServerHealthStatus, AlertsListResponse, PublishingAlert
)
from presenters.publishing_presenter import get_publishing_presenter
from models.publishing import PublishConfiguration, PublisherProcess, PublishErrorType
from utils.exceptions import ServiceError
from services.database import get_publishing_db_service

# Configurar logger
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/publishing",
    tags=["publishing"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/start",
    response_model=PublishStatusResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Solicitud inválida o cámara ya publicando"},
        404: {"description": "Cámara no encontrada"},
        500: {"description": "Error interno del servidor"}
    }
)
async def start_publishing(
    request: StartPublishRequest,
    presenter = Depends(get_publishing_presenter)
) -> PublishStatusResponse:
    """
    Inicia la publicación de una cámara a MediaMTX.
    
    Inicia un proceso FFmpeg para realizar relay del stream RTSP
    de la cámara hacia el servidor MediaMTX.
    
    Args:
        request: Datos de la solicitud con camera_id y force_restart
        
    Returns:
        PublishStatusResponse con el estado actual de la publicación
        
    Raises:
        HTTPException: Si hay errores en la solicitud o el proceso
    """
    logger.info(f"API: Solicitud de publicación para cámara {request.camera_id} "
               f"(force_restart={request.force_restart})")
    
    try:
        # Delegar al presenter
        result = await presenter.start_publishing(
            camera_id=request.camera_id,
            force_restart=request.force_restart
        )
        
        if not result.success:
            # Determinar código de estado según tipo de error
            status_code = status.HTTP_400_BAD_REQUEST
            
            if result.error_type == PublishErrorType.STREAM_UNAVAILABLE:
                status_code = status.HTTP_404_NOT_FOUND
            elif result.error_type == PublishErrorType.ALREADY_PUBLISHING:
                status_code = status.HTTP_409_CONFLICT
            elif result.error_type in [PublishErrorType.PROCESS_CRASHED, PublishErrorType.UNKNOWN]:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                
            logger.warning(f"Fallo al iniciar publicación: {result.error} (tipo: {result.error_type})")
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": result.error or "Error iniciando publicación",
                    "error_type": result.error_type.value if result.error_type else None,
                    "camera_id": request.camera_id
                }
            )
        
        # Obtener estado actualizado
        process = await presenter.get_camera_status(request.camera_id)
        if not process:
            logger.error(f"No se pudo obtener estado después de iniciar para {request.camera_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo estado después de iniciar"
            )
            
        # Obtener path desde el presenter
        publish_path = result.publish_path
        if hasattr(presenter, '_config') and presenter._config:
            publish_path = presenter._config.get_publish_path(request.camera_id)
            
        response = PublishStatusResponse(
            camera_id=process.camera_id,
            status=process.status,
            publish_path=publish_path,
            uptime_seconds=process.uptime_seconds,
            error_count=process.error_count,
            last_error=process.last_error,
            metrics=process.metrics
        )
        
        logger.info(f"Publicación iniciada exitosamente para {request.camera_id}")
        return response
        
    except HTTPException:
        raise
    except ServiceError as e:
        logger.error(f"ServiceError en start_publishing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "error_code": e.error_code if hasattr(e, 'error_code') else None
            }
        )
    except Exception as e:
        logger.exception(f"Error inesperado en start_publishing para {request.camera_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post(
    "/stop",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Cámara no encontrada o no publicando"},
        500: {"description": "Error al detener publicación"}
    }
)
async def stop_publishing(
    request: StopPublishRequest,
    presenter = Depends(get_publishing_presenter)
) -> Dict[str, str]:
    """
    Detiene la publicación de una cámara.
    
    Termina el proceso FFmpeg asociado y libera recursos.
    
    Args:
        request: Datos con el camera_id a detener
        
    Returns:
        Mensaje de confirmación
        
    Raises:
        HTTPException: Si la cámara no está publicando
    """
    logger.info(f"API: Solicitud para detener publicación de cámara {request.camera_id}")
    
    try:
        success = await presenter.stop_publishing(request.camera_id)
        
        if not success:
            logger.warning(f"Cámara {request.camera_id} no está publicando")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Cámara no está publicando actualmente",
                    "camera_id": request.camera_id
                }
            )
            
        logger.info(f"Publicación detenida exitosamente para {request.camera_id}")
        return {
            "message": "Publicación detenida exitosamente",
            "camera_id": request.camera_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado deteniendo publicación para {request.camera_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al detener publicación"
        )


@router.get(
    "/status",
    response_model=PublishListResponse,
    responses={
        200: {"description": "Lista de todas las publicaciones"}
    }
)
async def get_publishing_status(
    presenter = Depends(get_publishing_presenter)
) -> PublishListResponse:
    """
    Obtiene el estado de todas las publicaciones.
    
    Retorna información detallada de todos los procesos de publicación,
    tanto activos como en error o detenidos recientemente.
    
    Returns:
        PublishListResponse con lista completa y estadísticas
    """
    logger.debug("API: Obteniendo estado de todas las publicaciones")
    
    try:
        all_processes = await presenter.get_all_status()
        
        items = []
        active_count = 0
        error_count = 0
        
        for camera_id, process in all_processes.items():
            # Obtener path desde la configuración
            publish_path = None
            if hasattr(presenter, '_config') and presenter._config:
                publish_path = presenter._config.get_publish_path(camera_id)
                
            status_item = PublishStatusResponse(
                camera_id=camera_id,
                status=process.status,
                publish_path=publish_path,
                uptime_seconds=process.uptime_seconds,
                error_count=process.error_count,
                last_error=process.last_error,
                metrics=process.metrics
            )
            items.append(status_item)
            
            # Contar por estado
            if process.is_active:
                active_count += 1
            elif process.status.value == "error":
                error_count += 1
                
        response = PublishListResponse(
            total=len(items),
            active=active_count,
            items=items
        )
        
        logger.info(f"Estado de publicaciones: Total={len(items)}, Activas={active_count}, "
                   f"En error={error_count}")
        
        return response
        
    except Exception as e:
        logger.exception("Error obteniendo estado de publicaciones")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estado de publicaciones"
        )


@router.get(
    "/status/{camera_id}",
    response_model=PublishStatusResponse,
    responses={
        200: {"description": "Estado de publicación de la cámara"},
        404: {"description": "Cámara no encontrada o sin publicación"}
    }
)
async def get_camera_publishing_status(
    camera_id: str,
    presenter = Depends(get_publishing_presenter)
) -> PublishStatusResponse:
    """
    Obtiene el estado de publicación de una cámara específica.
    
    Args:
        camera_id: Identificador único de la cámara
        
    Returns:
        PublishStatusResponse con estado detallado
        
    Raises:
        HTTPException: Si la cámara no existe o no tiene proceso
    """
    logger.debug(f"API: Obteniendo estado de publicación para cámara {camera_id}")
    
    try:
        # Validar entrada
        if not camera_id or not camera_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="camera_id no puede estar vacío"
            )
            
        process = await presenter.get_camera_status(camera_id)
        
        if not process:
            logger.debug(f"Cámara {camera_id} no tiene proceso de publicación")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Cámara no encontrada o sin proceso de publicación",
                    "camera_id": camera_id
                }
            )
        
        # Obtener path desde la configuración
        publish_path = None
        if hasattr(presenter, '_config') and presenter._config:
            publish_path = presenter._config.get_publish_path(camera_id)
            
        response = PublishStatusResponse(
            camera_id=process.camera_id,
            status=process.status,
            publish_path=publish_path,
            uptime_seconds=process.uptime_seconds,
            error_count=process.error_count,
            last_error=process.last_error,
            metrics=process.metrics
        )
        
        logger.info(f"Estado obtenido para {camera_id}: {process.status.value}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error obteniendo estado para {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estado de publicación"
        )


# === Endpoints de Health y Monitoreo ===

@router.get(
    "/health",
    response_model=SystemHealthResponse,
    summary="Estado de salud del sistema",
    description="""
    Obtiene el estado de salud global del sistema de publicación.
    
    Incluye:
    - Estado general del sistema
    - Salud de cada servidor MediaMTX
    - Publicaciones activas
    - Alertas y recomendaciones
    """
)
async def get_system_health() -> SystemHealthResponse:
    """
    Obtiene el estado de salud global del sistema.
    
    Returns:
        SystemHealthResponse con información detallada
    """
    logger.debug("Obteniendo estado de salud del sistema de publicación")
    
    try:
        from api.schemas.responses.mediamtx_responses import (
            SystemHealthResponse, ServerHealthStatus
        )
        from services.database.mediamtx_db_service import get_mediamtx_db_service
        
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # Obtener servidores configurados
        pub_db = get_publishing_db_service()
        await pub_db.initialize()
        configs = await pub_db.get_all_configurations()
        
        # Estado de cada servidor
        servers = []
        healthy_count = 0
        total_publications = 0
        total_viewers = 0
        active_alerts = []
        
        for config in configs:
            server_id = config['config_id']
            
            # Obtener estado de salud del servidor
            server_health = await db_service.get_server_health_status(server_id)
            
            if server_health:
                servers.append(ServerHealthStatus(**server_health))
                
                if server_health['health_status'] == 'healthy':
                    healthy_count += 1
                    
                total_publications += server_health['active_connections']
                
                # Agregar alertas si hay problemas
                if server_health['health_status'] == 'unhealthy':
                    active_alerts.append({
                        'severity': 'error',
                        'title': f"Servidor {server_health['server_name']} no responde",
                        'message': server_health.get('last_error', 'Sin conexión'),
                        'server_id': server_id
                    })
                elif server_health['error_count'] > 5:
                    active_alerts.append({
                        'severity': 'warning',
                        'title': f"Errores frecuentes en {server_health['server_name']}",
                        'message': f"{server_health['error_count']} errores en la última hora",
                        'server_id': server_id
                    })
        
        # Determinar estado general
        overall_status = 'healthy'
        if healthy_count == 0:
            overall_status = 'critical'
        elif healthy_count < len(servers):
            overall_status = 'degraded'
        
        # Recomendaciones
        recommendations = []
        if overall_status == 'critical':
            recommendations.append("Todos los servidores están fuera de línea. Verificar conectividad.")
        elif overall_status == 'degraded':
            recommendations.append("Algunos servidores presentan problemas. Revisar logs.")
        
        if total_publications > 50:
            recommendations.append("Alto número de publicaciones activas. Considerar balanceo de carga.")
        
        # Obtener total de viewers (sumando de todos los servidores)
        # TODO: Implementar consulta real
        total_viewers = total_publications * 3  # Mock: 3 viewers por publicación
        
        response = SystemHealthResponse(
            overall_status=overall_status,
            check_timestamp=datetime.utcnow(),
            total_servers=len(servers),
            healthy_servers=healthy_count,
            active_publications=total_publications,
            total_viewers=total_viewers,
            servers=servers,
            active_alerts=active_alerts,
            recommendations=recommendations
        )
        
        logger.info(f"Health check: {overall_status}, {healthy_count}/{len(servers)} servidores OK")
        
        return response
        
    except Exception as e:
        logger.exception("Error obteniendo estado de salud")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estado de salud"
        )


@router.post(
    "/servers/{server_id}/health-check",
    response_model=ServerHealthStatus,
    summary="Verificar servidor MediaMTX",
    description="Ejecuta un health check manual en un servidor específico"
)
async def check_server_health(
    server_id: int,
    request: HealthCheckRequest = HealthCheckRequest()
) -> ServerHealthStatus:
    """
    Ejecuta verificación de salud en un servidor.
    
    Args:
        server_id: ID del servidor a verificar
        request: Parámetros del health check
        
    Returns:
        ServerHealthStatus con resultado de la verificación
    """
    logger.info(f"Health check manual para servidor {server_id}")
    
    try:
        from api.schemas.requests.mediamtx_requests import HealthCheckRequest
        from api.schemas.responses.mediamtx_responses import ServerHealthStatus
        from services.database.mediamtx_db_service import get_mediamtx_db_service
        import aiohttp
        import asyncio
        
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        # Obtener configuración del servidor
        pub_db = get_publishing_db_service()
        await pub_db.initialize()
        configs = await pub_db.get_all_configurations()
        
        server_config = next((c for c in configs if c['config_id'] == server_id), None)
        
        if not server_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Servidor {server_id} no encontrado"
            )
        
        # Realizar checks
        rtsp_ok = False
        api_ok = None
        paths_ok = None
        error_msg = None
        warnings = []
        
        try:
            # Check RTSP
            if request.check_rtsp:
                # TODO: Implementar verificación real RTSP
                # Por ahora simulamos
                rtsp_ok = True
                
            # Check API REST
            if request.check_api and server_config['api_enabled']:
                api_url = server_config['api_url']
                if api_url:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                f"{api_url}/v3/config/global",
                                timeout=aiohttp.ClientTimeout(total=request.timeout_seconds)
                            ) as resp:
                                api_ok = resp.status == 200
                    except Exception as e:
                        api_ok = False
                        warnings.append(f"API check failed: {str(e)}")
                        
            # Check paths
            if request.check_paths:
                # TODO: Verificar paths configurados
                paths_ok = True
                
        except Exception as e:
            error_msg = str(e)
            
        # Determinar estado general
        health_status = 'healthy'
        if not rtsp_ok:
            health_status = 'unhealthy'
        elif api_ok is False or paths_ok is False:
            health_status = 'degraded'
            
        # Actualizar en BD
        await db_service.update_server_health_check(
            server_id=server_id,
            health_status=health_status,
            error=error_msg
        )
        
        # Obtener estado actualizado
        server_health = await db_service.get_server_health_status(server_id)
        
        if not server_health:
            # Crear respuesta manual si no hay datos
            server_health = {
                'server_id': server_id,
                'server_name': server_config['config_name'],
                'health_status': health_status,
                'last_check_time': datetime.utcnow(),
                'rtsp_server_ok': rtsp_ok,
                'api_server_ok': api_ok,
                'paths_ok': paths_ok,
                'active_connections': 0,
                'cpu_usage_percent': None,
                'memory_usage_mb': None,
                'uptime_seconds': None,
                'error_count': 0,
                'last_error': error_msg,
                'warnings': warnings
            }
        
        response = ServerHealthStatus(**server_health)
        
        logger.info(f"Health check completado para servidor {server_id}: {health_status}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error en health check de servidor {server_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error ejecutando health check"
        )


@router.get(
    "/servers/{server_id}/status",
    response_model=ServerHealthStatus,
    summary="Estado detallado de servidor",
    description="Obtiene el estado detallado de un servidor MediaMTX"
)
async def get_server_status(server_id: int) -> ServerHealthStatus:
    """
    Obtiene estado detallado de un servidor.
    
    Args:
        server_id: ID del servidor
        
    Returns:
        ServerHealthStatus con información completa
    """
    logger.debug(f"Obteniendo estado de servidor {server_id}")
    
    try:
        from api.schemas.responses.mediamtx_responses import ServerHealthStatus
        from services.database.mediamtx_db_service import get_mediamtx_db_service
        
        db_service = get_mediamtx_db_service()
        await db_service.initialize()
        
        server_health = await db_service.get_server_health_status(server_id)
        
        if not server_health:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Servidor {server_id} no encontrado"
            )
        
        response = ServerHealthStatus(**server_health)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error obteniendo estado de servidor {server_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estado del servidor"
        )


@router.get(
    "/alerts",
    response_model=AlertsListResponse,
    summary="Listar alertas activas",
    description="Obtiene todas las alertas activas del sistema de publicación"
)
async def get_active_alerts(
    include_acknowledged: bool = Query(
        False,
        description="Incluir alertas reconocidas"
    ),
    severity: Optional[str] = Query(
        None,
        regex="^(info|warning|error|critical)$",
        description="Filtrar por severidad"
    )
) -> AlertsListResponse:
    """
    Lista las alertas activas del sistema.
    
    Args:
        include_acknowledged: Si incluir alertas ya reconocidas
        severity: Filtrar por nivel de severidad
        
    Returns:
        AlertsListResponse con lista de alertas
    """
    logger.debug("Obteniendo alertas activas del sistema")
    
    try:
        from api.schemas.responses.mediamtx_responses import (
            AlertsListResponse, PublishingAlert
        )
        from datetime import datetime, timedelta
        
        # Por ahora generamos alertas de ejemplo
        # TODO: Implementar sistema real de alertas
        
        alerts = []
        
        # Alerta ejemplo 1: Error de publicación
        if not severity or severity in ['error', 'critical']:
            alerts.append(PublishingAlert(
                alert_id="alert-001",
                severity="error",
                category="connectivity",
                title="Fallo de conexión con servidor MediaMTX",
                message="El servidor 'MediaMTX-Prod' no responde desde hace 15 minutos",
                affected_resources=["server-1", "cam-001", "cam-002"],
                created_at=datetime.utcnow() - timedelta(minutes=15),
                acknowledged=False,
                acknowledged_by=None,
                acknowledged_at=None,
                auto_resolve=True,
                resolved=False,
                resolved_at=None
            ))
        
        # Alerta ejemplo 2: Alto uso de recursos
        if not severity or severity == 'warning':
            alerts.append(PublishingAlert(
                alert_id="alert-002",
                severity="warning",
                category="performance",
                title="Alto uso de CPU en publicaciones",
                message="El uso de CPU promedio supera el 80% en las últimas 2 horas",
                affected_resources=["system"],
                created_at=datetime.utcnow() - timedelta(hours=2),
                acknowledged=True,
                acknowledged_by="admin",
                acknowledged_at=datetime.utcnow() - timedelta(hours=1),
                auto_resolve=False,
                resolved=False,
                resolved_at=None
            ))
        
        # Filtrar por acknowledged si es necesario
        if not include_acknowledged:
            alerts = [a for a in alerts if not a.acknowledged]
        
        # Contar por severidad y categoría
        by_severity = {}
        by_category = {}
        
        for alert in alerts:
            by_severity[alert.severity] = by_severity.get(alert.severity, 0) + 1
            by_category[alert.category] = by_category.get(alert.category, 0) + 1
        
        response = AlertsListResponse(
            total=len(alerts),
            active_count=sum(1 for a in alerts if not a.resolved),
            critical_count=sum(1 for a in alerts if a.severity == 'critical'),
            items=alerts,
            by_severity=by_severity,
            by_category=by_category
        )
        
        logger.info(f"Alertas obtenidas: {response.total} total, "
                   f"{response.critical_count} críticas")
        
        return response
        
    except Exception as e:
        logger.exception("Error obteniendo alertas")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo alertas"
        )

