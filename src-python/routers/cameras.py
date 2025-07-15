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

# Forzar recarga - v2
_FORCE_RELOAD = 2

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

def get_mock_cameras() -> dict:
    """
    Obtener datos mock de cámaras.
    Retorna una copia nueva cada vez para evitar mutaciones persistentes.
    """
    return {
        "cam_192.168.1.172": CameraInfo(
            camera_id="cam_192.168.1.172",
            display_name="Cámara Dahua Real",
            brand="Dahua",
            model="Dahua IP Camera",
            ip="192.168.1.172",
            is_connected=False,
            is_streaming=False,
            status="disconnected",
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
            is_connected=False,
            is_streaming=False,
            status="disconnected",
            last_updated=datetime.utcnow().isoformat() + "Z",
            capabilities=["RTSP", "HTTP"]
        ),
        "cam_192.168.1.103": CameraInfo(
            camera_id="cam_192.168.1.103",
            display_name="Cámara Entrada Principal",
            brand="Hikvision",
            model="DS-2CD2043G2-I",
            ip="192.168.1.103",
            is_connected=False,
            is_streaming=False,
            status="disconnected",
            last_updated=datetime.utcnow().isoformat() + "Z",
            capabilities=["ONVIF", "RTSP", "PTZ", "AI"]
        ),
        "cam_192.168.1.104": CameraInfo(
            camera_id="cam_192.168.1.104",
            display_name="Cámara Pasillo",
            brand="Xiaomi",
            model="Mi Home Security 360",
            ip="192.168.1.104",
            is_connected=False,
            is_streaming=False,
            status="disconnected",
            last_updated=datetime.utcnow().isoformat() + "Z",
            capabilities=["RTSP", "HTTP", "MJPEG"]
        ),
        "cam_192.168.1.105": CameraInfo(
            camera_id="cam_192.168.1.105",
            display_name="Cámara Jardín Trasero",
            brand="Reolink",
            model="RLC-810A",
            ip="192.168.1.105",
            is_connected=False,
            is_streaming=False,
            status="disconnected",
            last_updated=datetime.utcnow().isoformat() + "Z",
            capabilities=["ONVIF", "RTSP", "AI", "PoE"]
        )
    }

# Cache temporal para simular persistencia durante la sesión
_camera_states = {}


# === Endpoints ===

@router.get("/")
async def list_cameras():
    """
    Listar todas las cámaras configuradas.
    
    Returns:
        Lista de cámaras con su información actual
    """
    logger.info("Listando cámaras desde base de datos")
    
    try:
        # Intentar obtener datos reales de la base de datos
        from services.camera_manager_service import camera_manager_service
        
        db_cameras = await camera_manager_service.list_cameras()
        
        if db_cameras:
            # Convertir a formato esperado por el frontend
            cameras = []
            for cam in db_cameras:
                # Buscar estado actual en memoria
                state = _camera_states.get(cam.camera_id, {})
                
                camera_info = CameraInfo(
                    id=cam.camera_id,
                    name=cam.display_name,
                    brand=cam.brand,
                    ip_address=cam.ip,
                    port=cam.connection_config.rtsp_port if hasattr(cam.connection_config, 'rtsp_port') else 554,
                    protocol=cam.protocol.value if hasattr(cam, 'protocol') and cam.protocol else "RTSP",
                    status=state.get("status", "disconnected"),
                    is_connected=state.get("is_connected", False),
                    is_streaming=state.get("is_streaming", False),
                    last_updated=state.get("last_updated", datetime.now())
                )
                cameras.append(camera_info)
            
            logger.info(f"Devolviendo {len(cameras)} cámaras desde base de datos")
            
            return create_response(
                success=True,
                data=[camera.model_dump() for camera in cameras]
            )
            
    except Exception as e:
        logger.warning(f"Error obteniendo cámaras de DB, usando mock: {e}")
    
    # Fallback a datos mock si no hay DB o hay error
    base_cameras = get_mock_cameras()
    logger.info(f"Usando datos mock: {len(base_cameras)} cámaras")
    
    # Aplicar estados guardados
    for camera_id, camera in base_cameras.items():
        if camera_id in _camera_states:
            state = _camera_states[camera_id]
            camera.is_connected = state.get("is_connected", False)
            camera.is_streaming = state.get("is_streaming", False)
            camera.status = state.get("status", "disconnected")
            camera.last_updated = state.get("last_updated", camera.last_updated)
    
    cameras = list(base_cameras.values())
    
    return create_response(
        success=True,
        data=[camera.model_dump() for camera in cameras]
    )


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
    
    try:
        # Intentar obtener de base de datos primero
        from services.camera_manager_service import camera_manager_service
        
        db_camera = await camera_manager_service.get_camera(camera_id)
        
        if db_camera:
            # Buscar estado actual en memoria
            state = _camera_states.get(camera_id, {})
            
            camera_info = CameraInfo(
                id=db_camera.camera_id,
                name=db_camera.display_name,
                brand=db_camera.brand,
                ip_address=db_camera.ip,
                port=db_camera.connection_config.rtsp_port if hasattr(db_camera.connection_config, 'rtsp_port') else 554,
                protocol=db_camera.protocol.value if hasattr(db_camera, 'protocol') and db_camera.protocol else "RTSP",
                status=state.get("status", "disconnected"),
                is_connected=state.get("is_connected", False),
                is_streaming=state.get("is_streaming", False),
                last_updated=state.get("last_updated", datetime.now())
            )
            
            logger.info(f"Devolviendo cámara {camera_id} desde base de datos")
            return camera_info
            
    except Exception as e:
        logger.warning(f"Error obteniendo cámara {camera_id} de DB: {e}")
    
    # Fallback a datos mock
    base_cameras = get_mock_cameras()
    
    if camera_id not in base_cameras:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    
    camera = base_cameras[camera_id]
    
    # Aplicar estado guardado si existe
    if camera_id in _camera_states:
        state = _camera_states[camera_id]
        camera.is_connected = state.get("is_connected", False)
        camera.is_streaming = state.get("is_streaming", False)
        camera.status = state.get("status", "disconnected")
        camera.last_updated = state.get("last_updated", camera.last_updated)
    
    return camera


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
    
    # Guardar estado de conexión
    _camera_states[request.camera_id] = {
        "is_connected": True,
        "is_streaming": False,
        "status": "connected",
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }
    
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
    
    base_cameras = get_mock_cameras()
    
    if camera_id not in base_cameras:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    
    # Actualizar estado guardado
    _camera_states[camera_id] = {
        "is_connected": False,
        "is_streaming": False,
        "status": "disconnected",
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }
    
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
    
    base_cameras = get_mock_cameras()
    
    if camera_id not in base_cameras:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    
    # Verificar si está conectada
    is_connected = False
    if camera_id in _camera_states:
        is_connected = _camera_states[camera_id].get("is_connected", False)
    
    if not is_connected:
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
    
    base_cameras = get_mock_cameras()
    
    if camera_id not in base_cameras:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    
    # Obtener estado actual
    is_streaming = False
    if camera_id in _camera_states:
        is_streaming = _camera_states[camera_id].get("is_streaming", False)
    
    return create_response(
        success=True,
        data={
            "camera_id": camera_id,
            "is_streaming": is_streaming,
            "status": "streaming" if is_streaming else "idle",
            "metrics": {
                "fps": 30 if is_streaming else 0,
                "resolution": "1920x1080" if is_streaming else None,
                "bitrate_kbps": 2048 if is_streaming else 0,
                "latency_ms": 45 if is_streaming else 0
            }
        }
    )


@router.post("/reset-states")
async def reset_camera_states():
    """
    Resetear todos los estados de las cámaras (útil para desarrollo).
    
    Returns:
        Confirmación del reset
    """
    global _camera_states
    _camera_states = {}
    logger.info("Estados de cámaras reseteados")
    
    return create_response(
        success=True,
        data={
            "message": "Estados de cámaras reseteados exitosamente"
        }
    )