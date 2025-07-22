"""
Schemas de response para endpoints de cámaras.

Estos modelos definen la estructura de las respuestas
que devuelve la API para operaciones con cámaras.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CameraBasicInfo(BaseModel):
    """Información básica de una cámara."""
    
    camera_id: str = Field(..., description="ID único de la cámara")
    display_name: str = Field(..., description="Nombre visible")
    ip_address: str = Field(..., description="Dirección IP")
    brand: str = Field(..., description="Marca")
    model: Optional[str] = Field(None, description="Modelo")
    status: str = Field(..., description="Estado actual")
    is_active: bool = Field(..., description="Si está activa")
    is_connected: bool = Field(..., description="Si está conectada")
    
    class Config:
        from_attributes = True


class CameraConnectionInfo(BaseModel):
    """Información de conexión de una cámara."""
    
    primary_protocol: str = Field(..., description="Protocolo principal")
    rtsp_port: Optional[int] = Field(None, description="Puerto RTSP")
    onvif_port: Optional[int] = Field(None, description="Puerto ONVIF")
    http_port: Optional[int] = Field(None, description="Puerto HTTP")
    has_credentials: bool = Field(..., description="Si tiene credenciales configuradas")
    last_connection_time: Optional[datetime] = Field(None, description="Última conexión exitosa")
    connection_errors: int = Field(0, description="Contador de errores de conexión")


class CameraCapabilitiesInfo(BaseModel):
    """Información de capacidades de una cámara."""
    
    supports_onvif: bool = Field(False, description="Soporta ONVIF")
    supports_rtsp: bool = Field(False, description="Soporta RTSP")
    supports_ptz: bool = Field(False, description="Soporta PTZ")
    supports_audio: bool = Field(False, description="Soporta audio")
    supports_motion_detection: bool = Field(False, description="Soporta detección de movimiento")
    max_resolution: Optional[str] = Field(None, description="Resolución máxima")
    max_fps: Optional[int] = Field(None, description="FPS máximo")


class CameraStatisticsInfo(BaseModel):
    """Estadísticas de uso de una cámara."""
    
    total_connections: int = Field(0, description="Total de conexiones")
    successful_connections: int = Field(0, description="Conexiones exitosas")
    failed_connections: int = Field(0, description="Conexiones fallidas")
    total_streaming_time: int = Field(0, description="Tiempo total de streaming (segundos)")
    total_snapshots: int = Field(0, description="Total de snapshots tomados")
    last_snapshot_time: Optional[datetime] = Field(None, description="Último snapshot")
    average_fps: float = Field(0.0, description="FPS promedio")
    bandwidth_usage: int = Field(0, description="Uso de ancho de banda (bytes)")


class CameraDetailResponse(BaseModel):
    """Respuesta detallada de una cámara."""
    
    # Información básica
    basic_info: CameraBasicInfo
    
    # Información de conexión
    connection_info: CameraConnectionInfo
    
    # Capacidades
    capabilities: CameraCapabilitiesInfo
    
    # Estadísticas
    statistics: CameraStatisticsInfo
    
    # Metadatos adicionales
    location: Optional[str] = Field(None, description="Ubicación física")
    description: Optional[str] = Field(None, description="Descripción")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    
    # URLs disponibles
    stream_urls: Dict[str, str] = Field(default_factory=dict, description="URLs de streaming disponibles")
    snapshot_url: Optional[str] = Field(None, description="URL para snapshots")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "basic_info": {
                    "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                    "display_name": "Cámara Principal",
                    "ip_address": "192.168.1.100",
                    "brand": "Dahua",
                    "model": "IPC-HDW2431T",
                    "status": "connected",
                    "is_active": True,
                    "is_connected": True
                },
                "connection_info": {
                    "primary_protocol": "ONVIF",
                    "rtsp_port": 554,
                    "onvif_port": 80,
                    "http_port": 80,
                    "has_credentials": True,
                    "last_connection_time": "2024-01-15T10:30:00Z",
                    "connection_errors": 0
                },
                "capabilities": {
                    "supports_onvif": True,
                    "supports_rtsp": True,
                    "supports_ptz": False,
                    "supports_audio": True,
                    "supports_motion_detection": True,
                    "max_resolution": "1920x1080",
                    "max_fps": 30
                },
                "statistics": {
                    "total_connections": 150,
                    "successful_connections": 148,
                    "failed_connections": 2,
                    "total_streaming_time": 36000,
                    "total_snapshots": 50,
                    "last_snapshot_time": "2024-01-15T10:00:00Z",
                    "average_fps": 25.5,
                    "bandwidth_usage": 1073741824
                },
                "location": "Entrada Principal",
                "description": "Cámara de vigilancia de la entrada",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "stream_urls": {
                    "main": "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0",
                    "sub": "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=1"
                },
                "snapshot_url": "http://192.168.1.100/cgi-bin/snapshot.cgi"
            }
        }


class CameraListResponse(BaseModel):
    """Respuesta para listado de cámaras."""
    
    total: int = Field(..., description="Total de cámaras")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Elementos por página")
    cameras: List[CameraBasicInfo] = Field(..., description="Lista de cámaras")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "page": 1,
                "page_size": 20,
                "cameras": [
                    {
                        "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                        "display_name": "Cámara Principal",
                        "ip_address": "192.168.1.100",
                        "brand": "Dahua",
                        "model": "IPC-HDW2431T",
                        "status": "connected",
                        "is_active": True,
                        "is_connected": True
                    }
                ]
            }
        }


class CameraOperationResponse(BaseModel):
    """Respuesta para operaciones sobre cámaras."""
    
    success: bool = Field(..., description="Si la operación fue exitosa")
    camera_id: str = Field(..., description="ID de la cámara")
    operation: str = Field(..., description="Operación realizada")
    message: str = Field(..., description="Mensaje descriptivo")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Momento de la operación")
    
    # Datos adicionales según la operación
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")


class BatchOperationResponse(BaseModel):
    """Respuesta para operaciones en lote."""
    
    total_requested: int = Field(..., description="Total de operaciones solicitadas")
    successful: int = Field(..., description="Operaciones exitosas")
    failed: int = Field(..., description="Operaciones fallidas")
    results: List[CameraOperationResponse] = Field(..., description="Resultados individuales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_requested": 3,
                "successful": 2,
                "failed": 1,
                "results": [
                    {
                        "success": True,
                        "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                        "operation": "connect",
                        "message": "Cámara conectada exitosamente",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                ]
            }
        }


class StreamUrlResponse(BaseModel):
    """Respuesta con URLs de streaming."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    stream_type: str = Field(..., description="Tipo de stream")
    url: str = Field(..., description="URL del stream")
    protocol: str = Field(..., description="Protocolo usado")
    is_verified: bool = Field(..., description="Si la URL fue verificada")
    requires_auth: bool = Field(..., description="Si requiere autenticación")
    
    # Información adicional
    resolution: Optional[str] = Field(None, description="Resolución del stream")
    fps: Optional[int] = Field(None, description="FPS del stream")
    codec: Optional[str] = Field(None, description="Codec usado")