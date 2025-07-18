"""
Schemas de response para endpoints de escaneo.

Modelos para estructurar las respuestas de escaneo de red.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ScanStatus(str, Enum):
    """Estados posibles de un escaneo."""
    IDLE = "idle"
    SCANNING = "scanning"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class DetectedCamera(BaseModel):
    """Información de una cámara detectada en el escaneo."""
    
    ip: str = Field(..., description="Dirección IP de la cámara")
    mac_address: Optional[str] = Field(None, description="Dirección MAC si se detectó")
    hostname: Optional[str] = Field(None, description="Hostname si se resolvió")
    open_ports: List[int] = Field(..., description="Puertos abiertos encontrados")
    detected_brand: Optional[str] = Field(None, description="Marca detectada")
    detected_model: Optional[str] = Field(None, description="Modelo detectado")
    protocols: List[str] = Field(..., description="Protocolos detectados")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza de detección")
    response_time_ms: float = Field(..., description="Tiempo de respuesta promedio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ip": "192.168.1.100",
                "mac_address": "00:12:34:56:78:90",
                "hostname": "camera-front-door",
                "open_ports": [80, 554, 8080],
                "detected_brand": "Dahua",
                "detected_model": "DH-IPC-HFW2431S",
                "protocols": ["ONVIF", "RTSP", "HTTP"],
                "confidence": 0.95,
                "response_time_ms": 125.5
            }
        }


class ScanProgressResponse(BaseModel):
    """Respuesta con el progreso del escaneo."""
    
    scan_id: str = Field(..., description="ID único del escaneo")
    status: ScanStatus = Field(..., description="Estado actual del escaneo")
    total_ips: int = Field(..., description="Total de IPs a escanear")
    scanned_ips: int = Field(..., description="IPs ya escaneadas")
    cameras_found: int = Field(..., description="Cámaras encontradas hasta ahora")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Porcentaje completado")
    elapsed_time_seconds: float = Field(..., description="Tiempo transcurrido")
    estimated_time_remaining_seconds: Optional[float] = Field(None, description="Tiempo estimado restante")
    current_ip: Optional[str] = Field(None, description="IP siendo escaneada actualmente")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "scan_123e4567-e89b-12d3",
                "status": "scanning",
                "total_ips": 254,
                "scanned_ips": 127,
                "cameras_found": 5,
                "progress_percentage": 50.0,
                "elapsed_time_seconds": 120.0,
                "estimated_time_remaining_seconds": 120.0,
                "current_ip": "192.168.1.128"
            }
        }


class ScanResultsResponse(BaseModel):
    """Respuesta con los resultados completos del escaneo."""
    
    scan_id: str = Field(..., description="ID único del escaneo")
    status: ScanStatus = Field(..., description="Estado final del escaneo")
    subnet: Optional[str] = Field(None, description="Subred escaneada")
    ip_range: Optional[str] = Field(None, description="Rango de IP escaneado")
    total_ips_scanned: int = Field(..., description="Total de IPs escaneadas")
    cameras_found: int = Field(..., description="Total de cámaras encontradas")
    detected_cameras: List[DetectedCamera] = Field(..., description="Lista de cámaras detectadas")
    scan_duration_seconds: float = Field(..., description="Duración total del escaneo")
    start_time: datetime = Field(..., description="Hora de inicio")
    end_time: Optional[datetime] = Field(None, description="Hora de finalización")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "scan_123e4567-e89b-12d3",
                "status": "completed",
                "subnet": "192.168.1.0/24",
                "ip_range": None,
                "total_ips_scanned": 254,
                "cameras_found": 3,
                "detected_cameras": [
                    {
                        "ip": "192.168.1.100",
                        "mac_address": "00:12:34:56:78:90",
                        "hostname": "camera-front",
                        "open_ports": [80, 554],
                        "detected_brand": "Dahua",
                        "detected_model": None,
                        "protocols": ["ONVIF", "RTSP"],
                        "confidence": 0.95,
                        "response_time_ms": 125.5
                    }
                ],
                "scan_duration_seconds": 245.3,
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T10:04:05Z",
                "error_message": None
            }
        }


class QuickScanResponse(BaseModel):
    """Respuesta del escaneo rápido."""
    
    local_network: str = Field(..., description="Red local detectada")
    gateway_ip: str = Field(..., description="IP del gateway")
    scan_completed: bool = Field(..., description="Si el escaneo se completó")
    cameras_found: int = Field(..., description="Número de cámaras encontradas")
    detected_cameras: List[DetectedCamera] = Field(..., description="Cámaras detectadas")
    scan_time_seconds: float = Field(..., description="Tiempo de escaneo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "local_network": "192.168.1.0/24",
                "gateway_ip": "192.168.1.1",
                "scan_completed": True,
                "cameras_found": 2,
                "detected_cameras": [
                    {
                        "ip": "192.168.1.100",
                        "mac_address": "00:12:34:56:78:90",
                        "hostname": None,
                        "open_ports": [80, 554],
                        "detected_brand": "TP-Link",
                        "detected_model": "Tapo C200",
                        "protocols": ["ONVIF", "RTSP"],
                        "confidence": 0.90,
                        "response_time_ms": 150.0
                    }
                ],
                "scan_time_seconds": 30.5
            }
        }


class ScanHistoryEntry(BaseModel):
    """Entrada del historial de escaneos."""
    
    scan_id: str = Field(..., description="ID del escaneo")
    scan_type: str = Field(..., description="Tipo de escaneo (network/quick)")
    start_time: datetime = Field(..., description="Hora de inicio")
    end_time: Optional[datetime] = Field(None, description="Hora de fin")
    status: ScanStatus = Field(..., description="Estado del escaneo")
    subnet_or_range: str = Field(..., description="Subred o rango escaneado")
    cameras_found: int = Field(..., description="Cámaras encontradas")
    total_ips: int = Field(..., description="Total de IPs escaneadas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "scan_123e4567",
                "scan_type": "network",
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T10:04:05Z",
                "status": "completed",
                "subnet_or_range": "192.168.1.0/24",
                "cameras_found": 3,
                "total_ips": 254
            }
        }


class ScanHistoryResponse(BaseModel):
    """Respuesta del historial de escaneos."""
    
    total_scans: int = Field(..., description="Total de escaneos en historial")
    recent_scans: List[ScanHistoryEntry] = Field(..., description="Escaneos recientes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_scans": 15,
                "recent_scans": [
                    {
                        "scan_id": "scan_123e4567",
                        "scan_type": "network",
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T10:04:05Z",
                        "status": "completed",
                        "subnet_or_range": "192.168.1.0/24",
                        "cameras_found": 3,
                        "total_ips": 254
                    }
                ]
            }
        }


class ScanStatisticsResponse(BaseModel):
    """Estadísticas de escaneos."""
    
    total_scans_performed: int = Field(..., description="Total de escaneos realizados")
    total_cameras_discovered: int = Field(..., description="Total de cámaras descubiertas")
    unique_cameras: int = Field(..., description="Cámaras únicas encontradas")
    most_common_brands: Dict[str, int] = Field(..., description="Marcas más comunes")
    average_scan_duration_seconds: float = Field(..., description="Duración promedio")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Tasa de éxito")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_scans_performed": 50,
                "total_cameras_discovered": 120,
                "unique_cameras": 15,
                "most_common_brands": {
                    "Dahua": 45,
                    "Hikvision": 30,
                    "TP-Link": 25,
                    "Other": 20
                },
                "average_scan_duration_seconds": 180.5,
                "success_rate": 0.96
            }
        }