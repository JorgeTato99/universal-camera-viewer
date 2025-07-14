"""
Router para endpoints de cámaras.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from api.dependencies import create_response
from api.config import settings

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/cameras",
    tags=["cameras"],
    responses={404: {"description": "Cámara no encontrada"}}
)


# === Modelos Pydantic para requests/responses ===

class ConnectionConfig(BaseModel):
    """Configuración de conexión para una cámara."""
    ip: str = Field(..., description="Dirección IP de la cámara")
    username: str = Field(..., description="Usuario para autenticación")
    password: str = Field(..., description="Contraseña para autenticación")
    protocol: str = Field(default="ONVIF", description="Protocolo de conexión")
    port: Optional[int] = Field(None, description="Puerto de conexión")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ip": "192.168.1.172",
                "username": "admin",
                "password": "your_password_here",
                "protocol": "ONVIF",
                "port": 80
            }
        }


class CameraInfo(BaseModel):
    """Información de una cámara."""
    camera_id: str
    display_name: str
    brand: str
    model: Optional[str] = None
    ip: str
    is_connected: bool
    is_streaming: bool
    status: str
    last_updated: str
    capabilities: Optional[List[str]] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "cam_192.168.1.100",
                "display_name": "Cámara Principal",
                "brand": "Dahua",
                "model": "IPC-HFW2431S",
                "ip": "192.168.1.100",
                "is_connected": True,
                "is_streaming": False,
                "status": "connected",
                "last_updated": "2025-07-14T10:00:00Z",
                "capabilities": ["ONVIF", "RTSP", "PTZ"]
            }
        }


class ConnectCameraRequest(BaseModel):
    """Request para conectar una cámara."""
    camera_id: str = Field(..., description="ID único de la cámara")
    connection_config: ConnectionConfig
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "cam_192.168.1.100",
                "connection_config": {
                    "ip": "192.168.1.100",
                    "username": "admin",
                    "password": "password123",
                    "protocol": "ONVIF"
                }
            }
        }


class SnapshotResponse(BaseModel):
    """Respuesta de captura de imagen."""
    camera_id: str
    timestamp: str
    image_data: str = Field(..., description="Imagen en base64")
    format: str = "jpeg"
    size_bytes: int


# === Datos mock para desarrollo ===

MOCK_CAMERAS = {
    "cam_192.168.1.172": CameraInfo(
        camera_id="cam_192.168.1.172",
        display_name="Cámara Dahua Real",
        brand="Dahua",
        model="Dahua IP Camera",
        ip="192.168.1.172",
        is_connected=True,
        is_streaming=False,
        status="connected",
        last_updated=datetime.utcnow().isoformat() + "Z",
        capabilities=["ONVIF", "RTSP", "PTZ"]
    ),
    "cam_192.168.1.101": CameraInfo(
        camera_id="cam_192.168.1.101",
        display_name="Cámara Patio",
        brand="TP-Link",
        model="Tapo C200",
        ip="192.168.1.101",
        is_connected=False,
        is_streaming=False,
        status="disconnected",
        last_updated=datetime.utcnow().isoformat() + "Z",
        capabilities=["ONVIF", "RTSP"]
    ),
    "cam_192.168.1.102": CameraInfo(
        camera_id="cam_192.168.1.102",
        display_name="Cámara Garaje",
        brand="Steren",
        model="CCTV-240",
        ip="192.168.1.102",
        is_connected=True,
        is_streaming=True,
        status="streaming",
        last_updated=datetime.utcnow().isoformat() + "Z",
        capabilities=["RTSP", "HTTP"]
    )
}


# === Endpoints ===

@router.get("/", response_model=List[CameraInfo])
async def list_cameras():
    """
    Listar todas las cámaras configuradas.
    
    Returns:
        Lista de cámaras con su información actual
    """
    logger.info("Listando cámaras")
    
    # TODO: Integrar con CameraPresenter real
    cameras = list(MOCK_CAMERAS.values())
    
    return cameras


@router.get("/{camera_id}", response_model=CameraInfo)
async def get_camera_info(camera_id: str):
    """
    Obtener información detallada de una cámara específica.
    
    Args:
        camera_id: ID único de la cámara
        
    Returns:
        Información completa de la cámara
        
    Raises:
        HTTPException: Si la cámara no existe
    """
    logger.info(f"Obteniendo información de cámara: {camera_id}")
    
    # TODO: Integrar con CameraPresenter real
    if camera_id not in MOCK_CAMERAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    
    return MOCK_CAMERAS[camera_id]


@router.post("/connect")
async def connect_camera(request: ConnectCameraRequest):
    """
    Conectar a una cámara.
    
    Args:
        request: Configuración de conexión
        
    Returns:
        Estado de la conexión
    """
    logger.info(f"Conectando a cámara: {request.camera_id}")
    
    # TODO: Integrar con CameraPresenter real
    # Simulación de conexión
    camera = MOCK_CAMERAS.get(request.camera_id)
    if not camera:
        # Crear nueva cámara
        camera = CameraInfo(
            camera_id=request.camera_id,
            display_name=f"Cámara {request.connection_config.ip}",
            brand="Unknown",
            ip=request.connection_config.ip,
            is_connected=True,
            is_streaming=False,
            status="connected",
            last_updated=datetime.utcnow().isoformat() + "Z",
            capabilities=[]
        )
        MOCK_CAMERAS[request.camera_id] = camera
    else:
        # Actualizar estado
        camera.is_connected = True
        camera.status = "connected"
        camera.last_updated = datetime.utcnow().isoformat() + "Z"
    
    return create_response(
        success=True,
        data={
            "camera_id": request.camera_id,
            "status": "connected",
            "message": f"Conectado exitosamente a {request.connection_config.ip}"
        }
    )


@router.delete("/{camera_id}/disconnect")
async def disconnect_camera(camera_id: str):
    """
    Desconectar una cámara.
    
    Args:
        camera_id: ID de la cámara a desconectar
        
    Returns:
        Estado de la desconexión
    """
    logger.info(f"Desconectando cámara: {camera_id}")
    
    # TODO: Integrar con CameraPresenter real
    if camera_id not in MOCK_CAMERAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    
    camera = MOCK_CAMERAS[camera_id]
    camera.is_connected = False
    camera.is_streaming = False
    camera.status = "disconnected"
    camera.last_updated = datetime.utcnow().isoformat() + "Z"
    
    return create_response(
        success=True,
        data={
            "camera_id": camera_id,
            "status": "disconnected",
            "message": "Cámara desconectada exitosamente"
        }
    )


@router.post("/{camera_id}/snapshot")
async def capture_snapshot(camera_id: str):
    """
    Capturar una imagen de la cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Imagen capturada en base64
    """
    logger.info(f"Capturando snapshot de cámara: {camera_id}")
    
    # TODO: Integrar con VideoStreamPresenter real
    if camera_id not in MOCK_CAMERAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    
    camera = MOCK_CAMERAS[camera_id]
    if not camera.is_connected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cámara no está conectada"
        )
    
    # Imagen mock en base64 (1x1 pixel transparente)
    mock_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    return create_response(
        success=True,
        data=SnapshotResponse(
            camera_id=camera_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            image_data=mock_image,
            format="png",
            size_bytes=len(mock_image)
        ).model_dump()
    )


@router.get("/{camera_id}/stream/status")
async def get_stream_status(camera_id: str):
    """
    Obtener estado del stream de una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Estado actual del streaming
    """
    logger.info(f"Obteniendo estado de stream: {camera_id}")
    
    # TODO: Integrar con VideoStreamPresenter real
    if camera_id not in MOCK_CAMERAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    
    camera = MOCK_CAMERAS[camera_id]
    
    return create_response(
        success=True,
        data={
            "camera_id": camera_id,
            "is_streaming": camera.is_streaming,
            "status": "streaming" if camera.is_streaming else "idle",
            "metrics": {
                "fps": 30 if camera.is_streaming else 0,
                "resolution": "1920x1080" if camera.is_streaming else None,
                "bitrate_kbps": 2048 if camera.is_streaming else 0,
                "latency_ms": 45 if camera.is_streaming else 0
            }
        }
    )