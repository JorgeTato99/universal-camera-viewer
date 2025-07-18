"""
Schemas de request para endpoints de protocolos.

Modelos Pydantic para validar datos de entrada en protocolos.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from api.validators import validate_ip_address, validate_port, validate_timeout


class DiscoverProtocolsRequest(BaseModel):
    """Request para descubrir protocolos de una cámara."""
    
    ip: str = Field(..., description="Dirección IP de la cámara")
    username: Optional[str] = Field(None, description="Usuario para autenticación")
    password: Optional[str] = Field(None, description="Contraseña para autenticación")
    timeout: float = Field(10.0, description="Timeout en segundos")
    protocols: Optional[List[str]] = Field(None, description="Protocolos específicos a probar")
    
    @validator('ip')
    def validate_ip(cls, v):
        """Valida la dirección IP."""
        return validate_ip_address(v)
    
    @validator('timeout')
    def validate_timeout_value(cls, v):
        """Valida el timeout."""
        return validate_timeout(v, min_timeout=1.0, max_timeout=60.0)
    
    @validator('protocols')
    def validate_protocols(cls, v):
        """Valida los protocolos solicitados."""
        if v is not None:
            valid_protocols = ['ONVIF', 'RTSP', 'HTTP', 'HTTPS']
            for protocol in v:
                if protocol not in valid_protocols:
                    raise ValueError(f"Protocolo '{protocol}' no válido. Debe ser uno de: {', '.join(valid_protocols)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "ip": "192.168.1.100",
                "username": "admin",
                "password": "admin123",
                "timeout": 10.0,
                "protocols": ["ONVIF", "RTSP"]
            }
        }


class TestProtocolRequest(BaseModel):
    """Request para probar un protocolo específico."""
    
    protocol: str = Field(..., description="Protocolo a probar")
    port: Optional[int] = Field(None, description="Puerto específico")
    path: Optional[str] = Field(None, description="Path específico para el protocolo")
    timeout: float = Field(5.0, description="Timeout en segundos")
    
    @validator('protocol')
    def validate_protocol(cls, v):
        """Valida el protocolo."""
        valid_protocols = ['ONVIF', 'RTSP', 'HTTP', 'HTTPS']
        if v not in valid_protocols:
            raise ValueError(f"Protocolo debe ser uno de: {', '.join(valid_protocols)}")
        return v
    
    @validator('port')
    def validate_port_value(cls, v):
        """Valida el puerto si se proporciona."""
        if v is not None:
            return validate_port(v)
        return v
    
    @validator('timeout')
    def validate_timeout_value(cls, v):
        """Valida el timeout."""
        return validate_timeout(v, min_timeout=0.5, max_timeout=30.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "protocol": "RTSP",
                "port": 554,
                "path": "/cam/realmonitor?channel=1&subtype=0",
                "timeout": 5.0
            }
        }


class UpdateProtocolConfigRequest(BaseModel):
    """Request para actualizar configuración de protocolo."""
    
    primary_protocol: Optional[str] = Field(None, description="Protocolo principal")
    rtsp_port: Optional[int] = Field(None, description="Puerto RTSP")
    onvif_port: Optional[int] = Field(None, description="Puerto ONVIF")
    http_port: Optional[int] = Field(None, description="Puerto HTTP")
    https_port: Optional[int] = Field(None, description="Puerto HTTPS")
    custom_paths: Optional[Dict[str, str]] = Field(None, description="Paths personalizados")
    
    @validator('primary_protocol')
    def validate_primary_protocol(cls, v):
        """Valida el protocolo principal."""
        if v is not None:
            valid_protocols = ['ONVIF', 'RTSP', 'HTTP', 'HTTPS']
            if v not in valid_protocols:
                raise ValueError(f"Protocolo principal debe ser uno de: {', '.join(valid_protocols)}")
        return v
    
    @validator('rtsp_port', 'onvif_port', 'http_port', 'https_port')
    def validate_ports(cls, v):
        """Valida los puertos."""
        if v is not None:
            return validate_port(v)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "primary_protocol": "ONVIF",
                "rtsp_port": 554,
                "onvif_port": 80,
                "custom_paths": {
                    "rtsp_main": "/cam/realmonitor?channel=1&subtype=0",
                    "rtsp_sub": "/cam/realmonitor?channel=1&subtype=1"
                }
            }
        }