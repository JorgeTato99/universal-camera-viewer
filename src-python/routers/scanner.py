"""
Router para endpoints de escaneo de red.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid
import asyncio
import ipaddress
import logging

from api.dependencies import create_response
from api.config import settings
from utils.exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/scanner",
    tags=["scanner"],
    responses={404: {"description": "Escaneo no encontrado"}}
)


# === Modelos Pydantic ===

class ScanRange(BaseModel):
    """Rango de IPs para escanear."""
    start_ip: str = Field(..., description="IP inicial del rango")
    end_ip: str = Field(..., description="IP final del rango")
    port: Optional[int] = Field(None, description="Puerto específico a escanear")
    
    @validator('start_ip', 'end_ip')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"IP inválida: {v}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_ip": "192.168.1.1",
                "end_ip": "192.168.1.254",
                "port": 80
            }
        }


class ScanRequest(BaseModel):
    """Request para iniciar escaneo."""
    ranges: List[ScanRange] = Field(..., description="Rangos de IP a escanear")
    protocols: Optional[List[str]] = Field(
        default=["ONVIF", "RTSP"],
        description="Protocolos a buscar"
    )
    timeout: Optional[int] = Field(
        default=3,
        ge=1,
        le=30,
        description="Timeout por conexión en segundos"
    )
    max_threads: Optional[int] = Field(
        default=10,
        ge=1,
        le=50,
        description="Máximo de hilos concurrentes"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "ranges": [
                    {
                        "start_ip": "192.168.1.1",
                        "end_ip": "192.168.1.254"
                    }
                ],
                "protocols": ["ONVIF", "RTSP"],
                "timeout": 3,
                "max_threads": 10
            }
        }


class ScanProgress(BaseModel):
    """Progreso del escaneo."""
    scan_id: str
    status: str = Field(..., description="Estado: idle, scanning, completed, cancelled, error")
    progress: float = Field(..., ge=0, le=100, description="Porcentaje de progreso")
    total_ips: int = Field(..., description="Total de IPs a escanear")
    scanned_ips: int = Field(..., description="IPs escaneadas hasta ahora")
    found_cameras: int = Field(..., description="Cámaras encontradas")
    elapsed_time: float = Field(..., description="Tiempo transcurrido en segundos")
    estimated_time_remaining: Optional[float] = Field(None, description="Tiempo estimado restante")
    current_ip: Optional[str] = Field(None, description="IP actualmente escaneando")


class QuickScanRequest(BaseModel):
    """Request para escaneo rápido."""
    ip: str = Field(..., description="IP a escanear")
    ports: Optional[List[int]] = Field(
        default=[80, 554, 8000, 8080, 2020, 5543],
        description="Puertos a probar"
    )
    
    @validator('ip')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"IP inválida: {v}")


class DetectProtocolsRequest(BaseModel):
    """Request para detectar protocolos."""
    ip: str = Field(..., description="IP de la cámara")
    port: Optional[int] = Field(None, description="Puerto específico")
    
    @validator('ip')
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"IP inválida: {v}")


# === Importar servicios reales ===
import sys
from pathlib import Path
# Agregar src-python al path si es necesario
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.scan_service import scan_service
from models.scan_model import ScanMethod, ScanRange as ScanRangeModel


# === Modelo local para compatibilidad ===
from pydantic import BaseModel, Field

class ScanRange(BaseModel):
    """Rango de IPs para escanear (compatibilidad)."""
    start_ip: str = Field(..., description="IP inicial del rango")
    end_ip: str = Field(..., description="IP final del rango")
    port: Optional[int] = Field(None, description="Puerto específico a escanear")

# === Funciones auxiliares ===

def calculate_total_ips(ranges: List[ScanRange]) -> int:
    """Calcular total de IPs en los rangos."""
    total = 0
    for range_obj in ranges:
        start = ipaddress.ip_address(range_obj.start_ip)
        end = ipaddress.ip_address(range_obj.end_ip)
        if start > end:
            start, end = end, start
        total += int(end) - int(start) + 1
    return total


# === Endpoints ===

@router.post("/scan", response_model=ScanProgressResponse)
async def start_scan(
    request: ScanNetworkRequest,
    background_tasks: BackgroundTasks
):
    """
    Iniciar un nuevo escaneo de red.
    
    Args:
        request: Configuración del escaneo
        
    Returns:
        ID del escaneo iniciado
    """
    try:
        # Validar que se proporcione subnet o ip_range
        if not request.subnet and not request.ip_range:
            logger.warning("No se proporcionó subnet ni rango de IPs")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar subnet o ip_range para escanear"
            )
        
        # Calcular total de IPs
        total_ips = calculate_total_ips_from_request(request)
        if total_ips > 10000:
            logger.warning(f"Demasiadas IPs para escanear: {total_ips}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Demasiadas IPs para escanear ({total_ips}). Máximo permitido: 10,000"
            )
        
        logger.info(f"Iniciando escaneo de {total_ips} IPs")
        
        # Configurar rangos de escaneo
        scan_ranges = []
        
        # Determinar puertos a escanear
        if request.ports:
            ports = request.ports
        else:
            # Puertos por defecto para cámaras IP
            ports = [80, 554, 8080, 8000, 2020, 5543, 443, 37777]
        
        if request.subnet:
            # Convertir subnet a rango
            ips = parse_subnet(request.subnet)
            if ips:
                scan_range = ScanRangeModel(
                    start_ip=ips[0],
                    end_ip=ips[-1],
                    ports=ports,
                    timeout=request.timeout
                )
                scan_ranges.append(scan_range)
        else:
            # Usar ip_range
            start_ip, end_ip = parse_ip_range(request.ip_range)
            scan_range = ScanRangeModel(
                start_ip=start_ip,
                end_ip=end_ip,
                ports=ports,
                timeout=request.timeout
            )
            scan_ranges.append(scan_range)
        
        # Determinar métodos de escaneo
        methods = [ScanMethod.PORT_SCAN]
        if request.detect_brand:
            methods.append(ScanMethod.PROTOCOL_DETECTION)
        
        # Iniciar escaneo usando el servicio real
        scan_id = await scan_service.start_scan(
            ranges=scan_ranges,
            methods=methods,
            max_concurrent=request.concurrent_scans,
            include_offline=False
        )
        
        logger.info(f"Escaneo iniciado con ID: {scan_id}, escaneando {total_ips} IPs")
        
        # Crear respuesta inicial de progreso
        initial_progress = ScanProgressResponse(
            scan_id=scan_id,
            status=ScanStatus.SCANNING,
            total_ips=total_ips,
            scanned_ips=0,
            cameras_found=0,
            progress_percentage=0.0,
            elapsed_time_seconds=0.0,
            estimated_time_remaining_seconds=total_ips * request.timeout / request.concurrent_scans,
            current_ip=None
        )
        
        return initial_progress
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error de validación iniciando escaneo: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ServiceError as e:
        logger.error(f"Error de servicio iniciando escaneo: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de escaneo temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado iniciando escaneo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/scan/{scan_id}/progress", response_model=ScanProgressResponse)
async def get_scan_progress(
    scan_id: str,
    request: ScanStatusRequest = ScanStatusRequest()
):
    """
    Obtener progreso del escaneo.
    
    Args:
        scan_id: ID del escaneo
        
    Returns:
        Estado actual del escaneo
    """
    try:
        # Obtener estado desde el servicio real
        scan_status = await scan_service.get_scan_status(scan_id)
        
        if not scan_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Escaneo {scan_id} no encontrado"
            )
        
        # Obtener el modelo de escaneo para acceder al progreso
        if scan_id in scan_service.active_scans:
            scan_model = scan_service.active_scans[scan_id]
            progress_data = scan_model.progress
            
            # Construir respuesta de progreso
            return ScanProgressResponse(
                scan_id=scan_id,
                status=ScanStatus(scan_status["status"]),
                total_ips=progress_data.total_ips,
                scanned_ips=progress_data.scanned_ips,
                cameras_found=progress_data.cameras_found,
                progress_percentage=progress_data.overall_progress_percentage,
                elapsed_time_seconds=progress_data.elapsed_time,
                estimated_time_remaining_seconds=progress_data.estimated_remaining,
                current_ip=progress_data.current_ip
            )
        else:
            # Si el escaneo terminó, devolver estado final
            return ScanProgressResponse(
                scan_id=scan_id,
                status=ScanStatus(scan_status["status"]),
                total_ips=scan_status.get("total_ips", 0),
                scanned_ips=scan_status.get("scanned_ips", 0),
                cameras_found=scan_status.get("cameras_found", 0),
                progress_percentage=100.0,
                elapsed_time_seconds=scan_status.get("elapsed_time", 0),
                estimated_time_remaining_seconds=0,
                current_ip=None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo progreso: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo progreso: {str(e)}"
        )


@router.post("/scan/{scan_id}/stop")
async def stop_scan(scan_id: str):
    """
    Detener un escaneo en progreso.
    
    Args:
        scan_id: ID del escaneo
        
    Returns:
        Confirmación de detención
    """
    try:
        # Verificar si el escaneo existe
        scan_status = await scan_service.get_scan_status(scan_id)
        
        if not scan_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Escaneo {scan_id} no encontrado"
            )
        
        # Verificar estado actual
        if scan_status["status"] not in ["idle", "scanning", "preparing", "processing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El escaneo ya está en estado: {scan_status['status']}"
            )
        
        # Detener el escaneo
        success = await scan_service.stop_scan(scan_id)
        
        if success:
            return create_response(
                success=True,
                data={
                    "scan_id": scan_id,
                    "status": "cancelled",
                    "message": "Escaneo detenido exitosamente"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo detener el escaneo"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deteniendo escaneo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deteniendo escaneo: {str(e)}"
        )


@router.get("/scan/{scan_id}/results", response_model=ScanResultsResponse)
async def get_scan_results(scan_id: str):
    """
    Obtener resultados del escaneo.
    
    Args:
        scan_id: ID del escaneo
        
    Returns:
        Resultados del escaneo
    """
    try:
        # Obtener estado del escaneo
        scan_status = await scan_service.get_scan_status(scan_id)
        
        if not scan_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Escaneo {scan_id} no encontrado"
            )
        
        # Verificar que el escaneo haya terminado
        if scan_status["status"] not in ["completed", "cancelled", "error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El escaneo aún está en progreso: {scan_status['status']}"
            )
        
        # Obtener resultados
        results = await scan_service.get_scan_results(scan_id)
        detected_cameras = []
        
        if not results:
            # Si no hay resultados guardados, intentar obtener del modelo activo
            if scan_id in scan_service.active_scans:
                scan_model = scan_service.active_scans[scan_id]
                camera_results = scan_model.get_camera_results()
                
                # Formatear resultados para el frontend
                for camera_data in camera_results:
                    detected_cameras.append(DetectedCamera(
                        ip=camera_data['ip'],
                        mac_address=None,  # TODO: Obtener MAC si es posible
                        hostname=None,     # TODO: Resolver hostname
                        open_ports=camera_data['open_ports'],
                        detected_brand="Unknown",  # Se detectará después
                        detected_model=None,
                        protocols=camera_data['all_protocols'],
                        confidence=0.8,  # TODO: Calcular confianza real
                        response_time_ms=camera_data.get('response_time_ms', 100.0)
                    ))
        else:
            # Formatear resultados guardados
            for ip, scan_result in results.items():
                if scan_result.get('has_camera_protocols'):
                    detected_cameras.append(DetectedCamera(
                        ip=ip,
                        mac_address=scan_result.get('mac_address'),
                        hostname=scan_result.get('hostname'),
                        open_ports=scan_result.get('open_ports', []),
                        detected_brand="Unknown",
                        detected_model=None,
                        protocols=scan_result.get('camera_protocols', []),
                        confidence=0.8,
                        response_time_ms=scan_result.get('response_time_ms', 100.0)
                    ))
        
        # Construir respuesta completa
        return ScanResultsResponse(
            scan_id=scan_id,
            status=ScanStatus(scan_status["status"]),
            subnet=None,  # TODO: Obtener del modelo si es posible
            ip_range=None,  # TODO: Obtener del modelo si es posible
            total_ips_scanned=scan_status.get("total_ips", 0),
            cameras_found=len(detected_cameras),
            detected_cameras=detected_cameras,
            scan_duration_seconds=scan_status.get("elapsed_time", 0),
            start_time=datetime.utcnow(),  # TODO: Obtener del modelo
            end_time=datetime.utcnow() if scan_status["status"] in ["completed", "cancelled", "error"] else None,
            error_message=scan_status.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo resultados: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo resultados: {str(e)}"
        )


@router.post("/quick-scan", response_model=QuickScanResponse)
async def quick_scan(request: QuickScanRequest):
    """
    Escaneo rápido de una IP específica.
    
    Args:
        request: IP y puertos a escanear
        
    Returns:
        Cámaras encontradas en esa IP
    """
    logger.info(f"Escaneo rápido de {request.ip}")
    
    try:
        # Crear rango de escaneo para una sola IP
        scan_range = ScanRangeModel(
            start_ip=request.ip,
            end_ip=request.ip,
            ports=request.ports,
            timeout=3.0  # Timeout más corto para escaneo rápido
        )
        
        # Iniciar escaneo usando el servicio real
        scan_id = await scan_service.start_scan(
            ranges=[scan_range],
            methods=[ScanMethod.PORT_SCAN, ScanMethod.PROTOCOL_DETECTION],
            max_concurrent=len(request.ports),  # Un thread por puerto
            include_offline=True  # Incluir resultados aunque no responda ping
        )
        
        # Esperar a que termine (máximo 10 segundos)
        max_wait = 10.0
        wait_interval = 0.5
        elapsed = 0.0
        
        while elapsed < max_wait:
            status = await scan_service.get_scan_status(scan_id)
            if status and status["status"] in ["completed", "cancelled", "error"]:
                break
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
        
        # Obtener resultados
        results = await scan_service.get_scan_results(scan_id)
        
        # Determinar red local (simulado)
        local_network = "192.168.1.0/24"  # TODO: Detectar red real
        gateway_ip = "192.168.1.1"  # TODO: Detectar gateway real
        
        detected_cameras = []
        if results:
            # Buscar cámaras en los resultados
            for ip, scan_result in results.items():
                if scan_result.get('open_ports'):
                    # Se encontraron puertos abiertos, es posible que sea una cámara
                    detected_cameras.append(DetectedCamera(
                        ip=ip,
                        mac_address=scan_result.get('mac_address'),
                        hostname=scan_result.get('hostname'),
                        open_ports=scan_result.get('open_ports', []),
                        detected_brand="Unknown",
                        detected_model=None,
                        protocols=scan_result.get('camera_protocols', []),
                        confidence=0.8,
                        response_time_ms=scan_result.get('response_time_ms', 100.0)
                    ))
        
        return QuickScanResponse(
            local_network=local_network,
            gateway_ip=gateway_ip,
            scan_completed=True,
            cameras_found=len(detected_cameras),
            detected_cameras=detected_cameras,
            scan_time_seconds=elapsed
        )
        
    except Exception as e:
        logger.error(f"Error en escaneo rápido: {e}")
        # Devolver lista vacía en caso de error
        return create_response(
            success=True,
            data={"cameras": []}
        )


@router.post("/detect-protocols")
async def detect_protocols(
    ip: str,
    port: Optional[int] = None
):
    """
    Detectar protocolos soportados por una cámara.
    
    Args:
        request: IP y puerto de la cámara
        
    Returns:
        Lista de protocolos detectados
    """
    logger.info(f"Detectando protocolos en {ip}")
    
    try:
        # Validar IP
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IP inválida: {ip}"
            )
        
        # Si se especifica un puerto, escanear solo ese puerto
        # Si no, escanear puertos comunes de cámaras
        if port:
            ports = [port]
        else:
            ports = [80, 554, 8080, 8000, 2020, 5543, 443, 37777]
        
        # Crear rango de escaneo
        scan_range = ScanRangeModel(
            start_ip=ip,
            end_ip=ip,
            ports=ports,
            timeout=5.0
        )
        
        # Ejecutar escaneo con detección de protocolos
        scan_id = await scan_service.start_scan(
            ranges=[scan_range],
            methods=[ScanMethod.PORT_SCAN, ScanMethod.PROTOCOL_DETECTION],
            max_concurrent=len(ports),
            include_offline=True
        )
        
        # Esperar resultados (máximo 15 segundos)
        max_wait = 15.0
        wait_interval = 0.5
        elapsed = 0.0
        
        while elapsed < max_wait:
            status = await scan_service.get_scan_status(scan_id)
            if status and status["status"] in ["completed", "cancelled", "error"]:
                break
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
        
        # Obtener resultados
        results = await scan_service.get_scan_results(scan_id)
        
        protocols = []
        if results and ip in results:
            scan_result = results[ip]
            # Obtener protocolos detectados
            protocols = scan_result.get('camera_protocols', [])
            
            # Si no se detectaron protocolos pero hay puertos abiertos,
            # inferir protocolos basados en los puertos
            if not protocols and scan_result.get('open_ports'):
                for port in scan_result['open_ports']:
                    if port == 80 or port == 8080:
                        protocols.extend(["HTTP", "ONVIF"])
                    elif port == 554:
                        protocols.append("RTSP")
                    elif port == 8000:
                        protocols.extend(["HTTP", "ONVIF"])
                    elif port == 2020:
                        protocols.append("ONVIF")
                    elif port == 443:
                        protocols.append("HTTPS")
                    elif port == 37777:
                        protocols.append("AMCREST")
                
                # Eliminar duplicados
                protocols = list(set(protocols))
        
        return create_response(
            success=True,
            data={"protocols": protocols}
        )
        
    except Exception as e:
        logger.error(f"Error detectando protocolos: {e}")
        # Devolver lista vacía en caso de error
        return create_response(
            success=True,
            data={"protocols": []}
        )


@router.get("/recommended-config")
async def get_recommended_config():
    """DEPRECATED: Este endpoint será removido en futuras versiones."""
    """
    Obtener configuración recomendada de escaneo basada en la red actual.
    
    Returns:
        Configuración de escaneo sugerida
    """
    try:
        import socket
        import netifaces
        
        # Intentar detectar la red local actual
        ranges = []
        
        try:
            # Obtener interfaces de red
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info.get('addr', '')
                        netmask = addr_info.get('netmask', '')
                        
                        # Ignorar loopback
                        if ip.startswith('127.'):
                            continue
                        
                        # Calcular rango de red
                        try:
                            network = ipaddress.ip_network(f"{ip}/{netmask}", strict=False)
                            # Solo redes privadas
                            if network.is_private:
                                ranges.append(ScanRange(
                                    start_ip=str(network.network_address + 1),
                                    end_ip=str(network.broadcast_address - 1)
                                ))
                        except:
                            pass
        except:
            # Si falla la detección, usar rangos comunes
            logger.warning("No se pudo detectar la red local, usando rangos por defecto")
        
        # Si no se detectaron rangos, usar los más comunes
        if not ranges:
            ranges = [
                ScanRange(start_ip="192.168.1.1", end_ip="192.168.1.254"),
                ScanRange(start_ip="192.168.0.1", end_ip="192.168.0.254")
            ]
        
        # Convertir a formato nuevo
        subnet = None
        ip_range = None
        
        if ranges and len(ranges) > 0:
            first_range = ranges[0]
            # Intentar convertir a subnet
            try:
                start_ip = ipaddress.ip_address(first_range.start_ip)
                end_ip = ipaddress.ip_address(first_range.end_ip)
                # Si es un rango /24 completo, usar formato subnet
                if int(end_ip) - int(start_ip) == 253:  # 254 hosts - 1
                    subnet = f"{start_ip}/24"
                else:
                    ip_range = f"{first_range.start_ip}-{first_range.end_ip}"
            except:
                ip_range = f"{first_range.start_ip}-{first_range.end_ip}"
        
        config = {
            "subnet": subnet,
            "ip_range": ip_range,
            "ports": [80, 554, 8080, 8000, 2020],
            "timeout": 3.0,
            "concurrent_scans": 20,
            "detect_brand": True
        }
        
        return create_response(
            success=True,
            data=config
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración recomendada: {e}", exc_info=True)
        # Devolver configuración por defecto
        config = {
            "subnet": "192.168.1.0/24",
            "ip_range": None,
            "ports": [80, 554, 8080, 8000, 2020],
            "timeout": 3.0,
            "concurrent_scans": 10,
            "detect_brand": True
        }
        
        return create_response(
            success=True,
            data=config
        )


@router.get("/history", response_model=ScanHistoryResponse)
async def get_scan_history(
    limit: int = 10,
    offset: int = 0
):
    """
    Obtener historial de escaneos realizados.
    
    Args:
        limit: Número máximo de resultados
        offset: Offset para paginación
        
    Returns:
        Historial de escaneos con resultados
    """
    try:
        # TODO: Implementar persistencia de historial
        # Por ahora devolver escaneos recientes en memoria
        recent_scans = []
        
        # Agregar escaneos completados
        for scan_id, results in list(scan_service.scan_results.items())[-limit:]:
            status = await scan_service.get_scan_status(scan_id)
            if status:
                recent_scans.append(ScanHistoryEntry(
                    scan_id=scan_id,
                    scan_type="network",
                    start_time=datetime.utcnow(),  # TODO: Guardar tiempo real
                    end_time=datetime.utcnow() if status["status"] in ["completed", "cancelled", "error"] else None,
                    status=ScanStatus(status["status"]),
                    subnet_or_range="192.168.1.0/24",  # TODO: Guardar rango real
                    cameras_found=status.get("cameras_found", 0),
                    total_ips=status.get("total_ips", 0)
                ))
        
        return ScanHistoryResponse(
            total_scans=len(recent_scans),
            recent_scans=recent_scans
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/statistics", response_model=ScanStatisticsResponse)
async def get_scan_statistics():
    """
    Obtener estadísticas de escaneos.
    
    Returns:
        Estadísticas agregadas de todos los escaneos
    """
    try:
        # TODO: Implementar estadísticas reales desde DB
        # Por ahora devolver datos de ejemplo
        
        total_scans = len(scan_service.scan_results)
        total_cameras = 0
        brands_count = {}
        
        # Contar cámaras y marcas
        for scan_results in scan_service.scan_results.values():
            for ip, result in scan_results.items():
                if result.get('has_camera_protocols'):
                    total_cameras += 1
                    # TODO: Detectar marca real
                    brand = "Unknown"
                    brands_count[brand] = brands_count.get(brand, 0) + 1
        
        return ScanStatisticsResponse(
            total_scans_performed=total_scans,
            total_cameras_discovered=total_cameras,
            unique_cameras=len(set()),  # TODO: Implementar deduplicación
            most_common_brands=brands_count,
            average_scan_duration_seconds=180.0,  # TODO: Calcular promedio real
            success_rate=0.95  # TODO: Calcular tasa real
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/active-scans")
async def get_active_scans():
    """
    Obtener lista de escaneos activos.
    
    Returns:
        Lista de escaneos en progreso
    """
    try:
        active_scans = []
        
        # Obtener escaneos activos del servicio
        for scan_id, scan_model in scan_service.active_scans.items():
            progress = scan_model.progress
            active_scans.append({
                "scan_id": scan_id,
                "status": scan_model.status.value,
                "progress": progress.overall_progress_percentage,
                "total_ips": progress.total_ips,
                "scanned_ips": progress.scanned_ips,
                "found_cameras": progress.cameras_found,
                "started_at": scan_model.started_at.isoformat() + "Z" if scan_model.started_at else None
            })
        
        return create_response(
            success=True,
            data={
                "total": len(active_scans),
                "scans": active_scans
            }
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo escaneos activos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/scan/{scan_id}")
async def delete_scan_results(scan_id: str):
    """
    Eliminar resultados de un escaneo completado.
    
    Args:
        scan_id: ID del escaneo
        
    Returns:
        Confirmación de eliminación
    """
    try:
        # Verificar que el escaneo existe
        scan_status = await scan_service.get_scan_status(scan_id)
        
        if not scan_status:
            logger.warning(f"Escaneo no encontrado para eliminar: {scan_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Escaneo {scan_id} no encontrado"
            )
        
        # Verificar que no esté activo
        if scan_status["status"] in ["scanning", "preparing", "processing"]:
            logger.warning(f"Intento de eliminar escaneo activo: {scan_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar un escaneo en progreso"
            )
        
        # Eliminar de la memoria
        if scan_id in scan_service.scan_results:
            del scan_service.scan_results[scan_id]
            logger.info(f"Resultados del escaneo {scan_id} eliminados")
        
        return create_response(
            success=True,
            data={
                "scan_id": scan_id,
                "message": "Resultados del escaneo eliminados exitosamente"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando resultados del escaneo {scan_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )