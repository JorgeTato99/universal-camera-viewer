"""
Modelos de datos para los resultados de escaneo de puertos.
Contiene las clases PortResult y ScanResult extraídas del archivo original.
"""

from dataclasses import dataclass, field
from typing import List, Optional

# cspell:disable
@dataclass
class PortResult:
    """
    Resultado del escaneo de un puerto específico.
    Contiene información sobre el estado del puerto y autenticación.
    """
    port: int
    is_open: bool
    service_name: str
    response_time: float
    banner: Optional[str] = None
    auth_tested: bool = False
    auth_success: bool = False
    auth_method: Optional[str] = None
    auth_error: Optional[str] = None
    valid_urls: List[str] = field(default_factory=list)
    tested_urls: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Inicializar listas vacías si son None."""
        if self.valid_urls is None:
            self.valid_urls = []
        if self.tested_urls is None:
            self.tested_urls = []


@dataclass  
class ScanResult:
    """
    Resultado completo del escaneo de un host.
    Contiene información agregada de todos los puertos escaneados.
    """
    target_ip: str
    total_ports_scanned: int
    open_ports: List[PortResult]
    closed_ports: List[PortResult]
    scan_duration: float
    is_alive: bool
    credentials_tested: bool = False
    successful_auths: int = 0
    
    @property
    def open_ports_count(self) -> int:
        """Número de puertos abiertos."""
        return len(self.open_ports)
    
    @property
    def closed_ports_count(self) -> int:
        """Número de puertos cerrados."""
        return len(self.closed_ports)
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito de autenticación (0.0 - 1.0)."""
        if not self.credentials_tested or self.open_ports_count == 0:
            return 0.0
        return self.successful_auths / self.open_ports_count
    
    def get_ports_by_service(self, service_name: str) -> List[PortResult]:
        """
        Obtiene puertos filtrados por nombre de servicio.
        
        Args:
            service_name: Nombre del servicio a filtrar
            
        Returns:
            Lista de puertos que coinciden con el servicio
        """
        return [port for port in self.open_ports if service_name.lower() in port.service_name.lower()]
    
    def get_authenticated_ports(self) -> List[PortResult]:
        """
        Obtiene solo los puertos con autenticación exitosa.
        
        Returns:
            Lista de puertos con autenticación exitosa
        """
        return [port for port in self.open_ports if port.auth_success] 