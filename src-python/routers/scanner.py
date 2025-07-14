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


# === Estado global de escaneos (mock) ===

ACTIVE_SCANS: Dict[str, Dict[str, Any]] = {}


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


async def mock_scan_process(scan_id: str, request: ScanRequest):
    """Proceso mock de escaneo."""
    scan_data = ACTIVE_SCANS[scan_id]
    scan_data["status"] = "scanning"
    scan_data["start_time"] = datetime.utcnow()
    
    total_ips = scan_data["total_ips"]
    
    # Simular escaneo
    for i in range(total_ips):
        if scan_data["status"] == "cancelled":
            break
            
        # Actualizar progreso
        scan_data["scanned_ips"] = i + 1
        scan_data["progress"] = ((i + 1) / total_ips) * 100
        
        # Simular encontrar cámaras aleatoriamente
        if i % 15 == 0 and i > 0:  # ~6.7% de probabilidad
            scan_data["found_cameras"] += 1
            scan_data["cameras"].append({
                "camera_id": f"cam_192.168.1.{i}",
                "display_name": f"Cámara {i}",
                "brand": "Unknown",
                "ip": f"192.168.1.{i}",
                "is_connected": False,
                "is_streaming": False,
                "status": "discovered",
                "last_updated": datetime.utcnow().isoformat() + "Z"
            })
        
        # Simular delay
        await asyncio.sleep(0.1)  # 0.1 segundos por IP
        
        # Actualizar tiempo estimado
        elapsed = (datetime.utcnow() - scan_data["start_time"]).total_seconds()
        scan_data["elapsed_time"] = elapsed
        if scan_data["scanned_ips"] > 0:
            avg_time_per_ip = elapsed / scan_data["scanned_ips"]
            remaining_ips = total_ips - scan_data["scanned_ips"]
            scan_data["estimated_time_remaining"] = avg_time_per_ip * remaining_ips
    
    # Finalizar escaneo
    if scan_data["status"] != "cancelled":
        scan_data["status"] = "completed"
    scan_data["end_time"] = datetime.utcnow()
    scan_data["duration_seconds"] = (scan_data["end_time"] - scan_data["start_time"]).total_seconds()


# === Endpoints ===

@router.post("/scan")
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """
    Iniciar un nuevo escaneo de red.
    
    Args:
        request: Configuración del escaneo
        
    Returns:
        ID del escaneo iniciado
    """
    logger.info("Iniciando nuevo escaneo de red")
    
    # Generar ID único
    scan_id = str(uuid.uuid4())
    
    # Calcular total de IPs
    total_ips = calculate_total_ips(request.ranges)
    
    # Crear estado inicial
    scan_data = {
        "scan_id": scan_id,
        "status": "idle",
        "progress": 0.0,
        "total_ips": total_ips,
        "scanned_ips": 0,
        "found_cameras": 0,
        "elapsed_time": 0.0,
        "estimated_time_remaining": None,
        "current_ip": None,
        "cameras": [],
        "request": request.dict(),
        "start_time": None,
        "end_time": None,
        "duration_seconds": 0.0
    }
    
    ACTIVE_SCANS[scan_id] = scan_data
    
    # Iniciar escaneo en background
    background_tasks.add_task(mock_scan_process, scan_id, request)
    
    return create_response(
        success=True,
        data={"scan_id": scan_id}
    )


@router.get("/scan/{scan_id}/progress")
async def get_scan_progress(scan_id: str):
    """
    Obtener progreso del escaneo.
    
    Args:
        scan_id: ID del escaneo
        
    Returns:
        Estado actual del escaneo
    """
    if scan_id not in ACTIVE_SCANS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escaneo {scan_id} no encontrado"
        )
    
    scan_data = ACTIVE_SCANS[scan_id]
    
    progress = ScanProgress(
        scan_id=scan_id,
        status=scan_data["status"],
        progress=scan_data["progress"],
        total_ips=scan_data["total_ips"],
        scanned_ips=scan_data["scanned_ips"],
        found_cameras=scan_data["found_cameras"],
        elapsed_time=scan_data["elapsed_time"],
        estimated_time_remaining=scan_data.get("estimated_time_remaining"),
        current_ip=scan_data.get("current_ip")
    )
    
    return create_response(
        success=True,
        data=progress.dict()
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
    if scan_id not in ACTIVE_SCANS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escaneo {scan_id} no encontrado"
        )
    
    scan_data = ACTIVE_SCANS[scan_id]
    
    if scan_data["status"] not in ["idle", "scanning"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El escaneo ya está en estado: {scan_data['status']}"
        )
    
    scan_data["status"] = "cancelled"
    
    return create_response(
        success=True,
        data={
            "scan_id": scan_id,
            "status": "cancelled",
            "message": "Escaneo detenido exitosamente"
        }
    )


@router.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """
    Obtener resultados del escaneo.
    
    Args:
        scan_id: ID del escaneo
        
    Returns:
        Resultados del escaneo
    """
    if scan_id not in ACTIVE_SCANS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escaneo {scan_id} no encontrado"
        )
    
    scan_data = ACTIVE_SCANS[scan_id]
    
    if scan_data["status"] not in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El escaneo aún está en progreso: {scan_data['status']}"
        )
    
    return create_response(
        success=True,
        data={
            "scan_id": scan_id,
            "cameras": scan_data["cameras"],
            "total_scanned": scan_data["scanned_ips"],
            "duration_seconds": scan_data["duration_seconds"],
            "completed_at": scan_data["end_time"].isoformat() + "Z" if scan_data["end_time"] else None
        }
    )


@router.post("/quick-scan")
async def quick_scan(request: QuickScanRequest):
    """
    Escaneo rápido de una IP específica.
    
    Args:
        request: IP y puertos a escanear
        
    Returns:
        Cámaras encontradas en esa IP
    """
    logger.info(f"Escaneo rápido de {request.ip}")
    
    # Mock: simular encontrar una cámara si la IP termina en .172
    cameras = []
    if request.ip.endswith(".172"):
        cameras.append({
            "camera_id": f"cam_{request.ip}",
            "display_name": f"Cámara {request.ip}",
            "brand": "Dahua",
            "model": "Dahua IP Camera",
            "ip": request.ip,
            "is_connected": False,
            "is_streaming": False,
            "status": "discovered",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "capabilities": ["ONVIF", "RTSP"]
        })
    
    return create_response(
        success=True,
        data={"cameras": cameras}
    )


@router.post("/detect-protocols")
async def detect_protocols(request: DetectProtocolsRequest):
    """
    Detectar protocolos soportados por una cámara.
    
    Args:
        request: IP y puerto de la cámara
        
    Returns:
        Lista de protocolos detectados
    """
    logger.info(f"Detectando protocolos en {request.ip}")
    
    # Mock: devolver protocolos basados en el puerto
    protocols = []
    port = request.port or 80
    
    if port == 80:
        protocols = ["ONVIF", "HTTP"]
    elif port == 554:
        protocols = ["RTSP"]
    elif port == 8000:
        protocols = ["ONVIF", "HTTP"]
    elif port == 2020:
        protocols = ["ONVIF"]
    else:
        protocols = ["HTTP"]
    
    return create_response(
        success=True,
        data={"protocols": protocols}
    )


@router.get("/recommended-config")
async def get_recommended_config():
    """
    Obtener configuración recomendada de escaneo.
    
    Returns:
        Configuración de escaneo sugerida
    """
    # Detectar red local actual (mock)
    config = ScanRequest(
        ranges=[
            ScanRange(
                start_ip="192.168.1.1",
                end_ip="192.168.1.254"
            )
        ],
        protocols=["ONVIF", "RTSP"],
        timeout=3,
        max_threads=10
    )
    
    return create_response(
        success=True,
        data=config.dict()
    )