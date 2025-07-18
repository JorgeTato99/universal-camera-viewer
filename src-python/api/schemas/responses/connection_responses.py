"""
Schemas de response para endpoints de conexión.

Modelos para estructurar las respuestas de conexión.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ConnectionStatusResponse(BaseModel):
    """Respuesta de estado de conexión."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    is_connected: bool = Field(..., description="Si está conectada")
    connection_time: Optional[datetime] = Field(None, description="Tiempo de conexión")
    protocol: Optional[str] = Field(None, description="Protocolo actual")
    stream_active: bool = Field(False, description="Si hay stream activo")
    error: Optional[str] = Field(None, description="Último error si existe")
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_connected": True,
                "connection_time": "2024-01-15T10:30:00Z",
                "protocol": "ONVIF",
                "stream_active": True,
                "error": None
            }
        }


class TestConnectionResponse(BaseModel):
    """Respuesta de prueba de conexión."""
    
    success: bool = Field(..., description="Si la prueba fue exitosa")
    camera_id: str = Field(..., description="ID de la cámara")
    protocol: str = Field(..., description="Protocolo probado")
    response_time_ms: Optional[float] = Field(None, description="Tiempo de respuesta en ms")
    error: Optional[str] = Field(None, description="Error si falló")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "protocol": "RTSP",
                "response_time_ms": 125.5,
                "error": None,
                "details": {
                    "stream_available": True,
                    "authentication": "digest"
                }
            }
        }


class ConnectionOperationResponse(BaseModel):
    """Respuesta de operación de conexión."""
    
    success: bool = Field(..., description="Si la operación fue exitosa")
    camera_id: str = Field(..., description="ID de la cámara")
    operation: str = Field(..., description="Operación realizada")
    message: str = Field(..., description="Mensaje descriptivo")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "operation": "connect",
                "message": "Cámara conectada exitosamente",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class BatchConnectionResponse(BaseModel):
    """Respuesta de operaciones de conexión en lote."""
    
    total_requested: int = Field(..., description="Total de operaciones solicitadas")
    successful: int = Field(..., description="Operaciones exitosas")
    failed: int = Field(..., description="Operaciones fallidas")
    results: List[ConnectionOperationResponse] = Field(..., description="Resultados individuales")
    
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


class ConnectionMetricsResponse(BaseModel):
    """Respuesta con métricas de conexión."""
    
    camera_id: str = Field(..., description="ID de la cámara")
    total_connections: int = Field(..., description="Total de conexiones")
    successful_connections: int = Field(..., description="Conexiones exitosas")
    failed_connections: int = Field(..., description="Conexiones fallidas")
    average_connection_time_ms: Optional[float] = Field(None, description="Tiempo promedio de conexión")
    last_connection_attempt: Optional[datetime] = Field(None, description="Último intento")
    last_successful_connection: Optional[datetime] = Field(None, description="Última conexión exitosa")
    uptime_seconds: Optional[int] = Field(None, description="Tiempo activo en segundos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_connections": 150,
                "successful_connections": 148,
                "failed_connections": 2,
                "average_connection_time_ms": 125.5,
                "last_connection_attempt": "2024-01-15T10:30:00Z",
                "last_successful_connection": "2024-01-15T10:30:00Z",
                "uptime_seconds": 3600
            }
        }


class ActiveConnectionsResponse(BaseModel):
    """Respuesta con lista de conexiones activas."""
    
    total_active: int = Field(..., description="Total de conexiones activas")
    connections: List[ConnectionStatusResponse] = Field(..., description="Lista de conexiones")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_active": 2,
                "connections": [
                    {
                        "camera_id": "123e4567-e89b-12d3-a456-426614174000",
                        "is_connected": True,
                        "connection_time": "2024-01-15T10:30:00Z",
                        "protocol": "ONVIF",
                        "stream_active": True,
                        "error": None
                    }
                ]
            }
        }