"""
Testeador de protocolo Dahua SDK para cámaras IP.
Implementa pruebas de autenticación usando el puerto SDK propietario de Dahua.
"""

import socket
from typing import Tuple, Optional, List
from .base_protocol_tester import BaseProtocolTester

# cspell:disable
class DahuaSDKTester(BaseProtocolTester):
    """
    Testeador específico para protocolo Dahua SDK.
    
    Implementa pruebas de autenticación usando conexión TCP
    al puerto SDK propietario de Dahua (37777).
    """
    
    def get_supported_ports(self) -> List[int]:
        """Puertos Dahua SDK soportados."""
        return [37777]
    
    def test_authentication(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str], List[str], List[str]]:
        """
        Prueba autenticación Dahua SDK con timeout corto.
        
        Args:
            ip: Dirección IP
            port: Puerto Dahua SDK
            
        Returns:
            Tupla con (éxito, método_auth, error, urls_válidas, urls_probadas)
        """
        if not self._validate_credentials():
            return False, None, "Credenciales no configuradas", [], []
        
        try:
            # Conexión TCP al puerto SDK de Dahua con timeout corto
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(min(self.timeout, 2.0))  # Máximo 2 segundos
            sock.connect((ip, port))
            
            # Enviar mensaje de login básico (simplificado)
            # En un escenario real se usaría el protocolo completo de Dahua
            login_data = f"{self.username}:{self.password}".encode()
            sock.send(login_data)
            
            # Timeout corto para recibir respuesta
            sock.settimeout(1.0)
            response = sock.recv(1024)
            sock.close()
            
            # Análisis básico de respuesta
            if len(response) > 0:
                return True, "Dahua SDK", None, [f"tcp://{ip}:{port}"], [f"tcp://{ip}:{port}"]
            
        except socket.timeout:
            return False, None, "Timeout en Dahua SDK", [], [f"tcp://{ip}:{port}"]
        except Exception as e:
            return False, None, self._format_error_message("Error Dahua SDK", e), [], [f"tcp://{ip}:{port}"]
        
        return False, None, "Dahua SDK no accesible", [], [f"tcp://{ip}:{port}"] 