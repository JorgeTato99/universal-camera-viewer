"""
Schemas de request para endpoints de escaneo.

Modelos Pydantic para validar datos de entrada en escaneo de red.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from api.validators import validate_ip_address, validate_port, validate_timeout


class ScanNetworkRequest(BaseModel):
    """Request para escanear la red en busca de cámaras."""
    
    subnet: Optional[str] = Field(None, description="Subred a escanear (ej: 192.168.1.0/24)")
    ip_range: Optional[str] = Field(None, description="Rango de IPs (ej: 192.168.1.1-192.168.1.254)")
    ports: Optional[List[int]] = Field(None, description="Puertos específicos a escanear")
    timeout: float = Field(5.0, description="Timeout por IP en segundos")
    concurrent_scans: int = Field(10, ge=1, le=50, description="Escaneos concurrentes")
    detect_brand: bool = Field(True, description="Intentar detectar marca de cámara")
    
    @validator('subnet')
    def validate_subnet(cls, v):
        """Valida formato de subred."""
        if v is not None:
            # Validar formato CIDR básico
            if '/' not in v:
                raise ValueError("Subred debe estar en formato CIDR (ej: 192.168.1.0/24)")
            
            try:
                ip_part, mask_part = v.split('/')
                validate_ip_address(ip_part)
                mask = int(mask_part)
                if mask < 8 or mask > 32:
                    raise ValueError("Máscara de red debe estar entre 8 y 32")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Formato de subred inválido: {str(e)}")
        return v
    
    @validator('ip_range')
    def validate_ip_range(cls, v):
        """Valida rango de IPs."""
        if v is not None:
            if '-' not in v:
                raise ValueError("Rango debe tener formato: IP_inicio-IP_fin")
            
            try:
                start_ip, end_ip = v.split('-')
                validate_ip_address(start_ip.strip())
                validate_ip_address(end_ip.strip())
            except ValueError as e:
                raise ValueError(f"Rango de IP inválido: {str(e)}")
        return v
    
    @validator('ports')
    def validate_ports(cls, v):
        """Valida lista de puertos."""
        if v is not None:
            for port in v:
                validate_port(port)
            if len(v) > 20:
                raise ValueError("Máximo 20 puertos por escaneo")
        return v
    
    @validator('timeout')
    def validate_timeout_value(cls, v):
        """Valida el timeout."""
        return validate_timeout(v, min_timeout=0.5, max_timeout=30.0)
    
    @validator('subnet', 'ip_range')
    def validate_scan_target(cls, v, values):
        """Valida que se proporcione subnet O ip_range, no ambos."""
        if v is not None:
            if 'subnet' in values and values['subnet'] is not None:
                if 'ip_range' in values and values['ip_range'] is not None:
                    raise ValueError("Proporcione subnet O ip_range, no ambos")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "subnet": "192.168.1.0/24",
                "ports": [80, 8080, 554, 2020, 8000],
                "timeout": 5.0,
                "concurrent_scans": 10,
                "detect_brand": True
            }
        }


class QuickScanRequest(BaseModel):
    """Request para escaneo rápido de red local."""
    
    timeout: float = Field(3.0, description="Timeout por IP en segundos")
    common_ports_only: bool = Field(True, description="Escanear solo puertos comunes")
    
    @validator('timeout')
    def validate_timeout_value(cls, v):
        """Valida el timeout."""
        return validate_timeout(v, min_timeout=0.5, max_timeout=10.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "timeout": 3.0,
                "common_ports_only": True
            }
        }


class ScanStatusRequest(BaseModel):
    """Request para consultar estado del escaneo."""
    
    include_results: bool = Field(True, description="Incluir resultados parciales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "include_results": True
            }
        }