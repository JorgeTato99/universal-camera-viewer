"""
Schemas de response para endpoints de protocolos.

Modelos para estructurar las respuestas de protocolos.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ProtocolInfo(BaseModel):
    """Información de un protocolo."""
    
    protocol: str = Field(..., description="Nombre del protocolo")
    port: int = Field(..., description="Puerto usado")
    available: bool = Field(..., description="Si el protocolo está disponible")
    verified: bool = Field(..., description="Si fue verificado exitosamente")
    response_time_ms: Optional[float] = Field(None, description="Tiempo de respuesta")
    error: Optional[str] = Field(None, description="Error si falló")
    endpoints: Optional[List[str]] = Field(None, description="Endpoints descubiertos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "protocol": "RTSP",
                "port": 554,
                "available": True,
                "verified": True,
                "response_time_ms": 125.5,
                "error": None,
                "endpoints": [
                    "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0",
                    "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=1"
                ]
            }
        }


class ProtocolDiscoveryResponse(BaseModel):
    """Respuesta de descubrimiento de protocolos."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    ip_address: str = Field(..., description="IP de la cámara")
    discovered_protocols: List[ProtocolInfo] = Field(..., description="Protocolos descubiertos")
    primary_protocol: Optional[str] = Field(None, description="Protocolo recomendado")
    discovery_time: datetime = Field(default_factory=datetime.utcnow)
    total_time_ms: float = Field(..., description="Tiempo total de descubrimiento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "ip_address": "192.168.1.100",
                "discovered_protocols": [
                    {
                        "protocol": "ONVIF",
                        "port": 80,
                        "available": True,
                        "verified": True,
                        "response_time_ms": 150.0
                    }
                ],
                "primary_protocol": "ONVIF",
                "discovery_time": "2024-01-15T10:30:00Z",
                "total_time_ms": 2500.0
            }
        }


class ProtocolTestResponse(BaseModel):
    """Respuesta de prueba de protocolo."""
    
    protocol: str = Field(..., description="Protocolo probado")
    success: bool = Field(..., description="Si la prueba fue exitosa")
    port: int = Field(..., description="Puerto probado")
    path: Optional[str] = Field(None, description="Path probado")
    response_time_ms: Optional[float] = Field(None, description="Tiempo de respuesta")
    error: Optional[str] = Field(None, description="Error si falló")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "protocol": "RTSP",
                "success": True,
                "port": 554,
                "path": "/cam/realmonitor?channel=1&subtype=0",
                "response_time_ms": 125.5,
                "error": None,
                "details": {
                    "stream_available": True,
                    "codec": "H.264",
                    "resolution": "1920x1080"
                }
            }
        }


class ProtocolCapabilitiesResponse(BaseModel):
    """Respuesta con capacidades del protocolo."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    protocol: str = Field(..., description="Protocolo")
    capabilities: Dict[str, Any] = Field(..., description="Capacidades detectadas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "protocol": "ONVIF",
                "capabilities": {
                    "ptz": True,
                    "audio": True,
                    "events": True,
                    "analytics": False,
                    "profiles": ["Profile_1", "Profile_2"],
                    "services": {
                        "device": "http://192.168.1.100/onvif/device_service",
                        "media": "http://192.168.1.100/onvif/media_service",
                        "ptz": "http://192.168.1.100/onvif/ptz_service"
                    }
                }
            }
        }


class StreamEndpointInfo(BaseModel):
    """Información de un endpoint de streaming."""
    
    name: str = Field(..., description="Nombre del endpoint")
    url: str = Field(..., description="URL del stream")
    protocol: str = Field(..., description="Protocolo usado")
    stream_type: str = Field(..., description="Tipo de stream")
    verified: bool = Field(..., description="Si fue verificado")
    resolution: Optional[str] = Field(None, description="Resolución")
    fps: Optional[int] = Field(None, description="FPS")
    codec: Optional[str] = Field(None, description="Codec")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "rtsp_main",
                "url": "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0",
                "protocol": "RTSP",
                "stream_type": "main",
                "verified": True,
                "resolution": "1920x1080",
                "fps": 25,
                "codec": "H.264"
            }
        }


class ProtocolEndpointsResponse(BaseModel):
    """Respuesta con endpoints descubiertos."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    total_endpoints: int = Field(..., description="Total de endpoints")
    verified_endpoints: int = Field(..., description="Endpoints verificados")
    endpoints: List[StreamEndpointInfo] = Field(..., description="Lista de endpoints")
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_endpoints": 3,
                "verified_endpoints": 2,
                "endpoints": [
                    {
                        "name": "rtsp_main",
                        "url": "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0",
                        "protocol": "RTSP",
                        "stream_type": "main",
                        "verified": True,
                        "resolution": "1920x1080",
                        "fps": 25,
                        "codec": "H.264"
                    }
                ]
            }
        }