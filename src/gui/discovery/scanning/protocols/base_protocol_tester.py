"""
Clase base abstracta para testeadores de protocolos.
Define la interfaz común que deben implementar todos los testeadores específicos.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, List

# cspell:disable
class BaseProtocolTester(ABC):
    """
    Clase base abstracta para testeadores de protocolos de cámaras IP.
    
    Implementa el patrón Template Method para definir el flujo común
    de pruebas de autenticación, permitiendo que las subclases
    implementen los detalles específicos de cada protocolo.
    """
    
    def __init__(self, username: str = "", password: str = "", timeout: float = 3.0):
        """
        Inicializa el testeador de protocolo.
        
        Args:
            username: Usuario para autenticación
            password: Contraseña para autenticación
            timeout: Timeout en segundos para las pruebas
        """
        self.username = username
        self.password = password
        self.timeout = timeout
        self.is_testing = True
    
    @abstractmethod
    def test_authentication(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str], List[str], List[str]]:
        """
        Prueba la autenticación en el protocolo específico.
        
        Args:
            ip: Dirección IP del host
            port: Puerto a probar
            
        Returns:
            Tupla con (éxito, método_auth, error, urls_válidas, urls_probadas)
        """
        pass
    
    @abstractmethod
    def get_supported_ports(self) -> List[int]:
        """
        Obtiene la lista de puertos soportados por este protocolo.
        
        Returns:
            Lista de puertos que maneja este testeador
        """
        pass
    
    def stop_testing(self):
        """Detiene las pruebas en curso."""
        self.is_testing = False
    
    def set_credentials(self, username: str, password: str):
        """
        Actualiza las credenciales para las pruebas.
        
        Args:
            username: Nuevo usuario
            password: Nueva contraseña
        """
        self.username = username
        self.password = password
    
    def set_timeout(self, timeout: float):
        """
        Actualiza el timeout para las pruebas.
        
        Args:
            timeout: Nuevo timeout en segundos
        """
        self.timeout = timeout
    
    def _validate_credentials(self) -> bool:
        """
        Valida que las credenciales estén configuradas.
        
        Returns:
            True si las credenciales son válidas
        """
        return bool(self.username and self.password)
    
    def _format_error_message(self, base_message: str, exception: Exception = None) -> str:
        """
        Formatea un mensaje de error consistente.
        
        Args:
            base_message: Mensaje base del error
            exception: Excepción opcional para incluir detalles
            
        Returns:
            Mensaje de error formateado
        """
        if exception:
            return f"{base_message}: {str(exception)}"
        return base_message 