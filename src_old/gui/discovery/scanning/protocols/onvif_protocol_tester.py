"""
Testeador de protocolo ONVIF para cámaras IP.
Implementa pruebas de autenticación ONVIF usando endpoints estándar.
"""

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from typing import Tuple, Optional, List
from .base_protocol_tester import BaseProtocolTester

# cspell:disable
class ONVIFProtocolTester(BaseProtocolTester):
    """
    Testeador específico para protocolo ONVIF.
    
    Implementa pruebas de autenticación ONVIF probando
    endpoints estándar con Basic y Digest Auth.
    """
    
    def get_supported_ports(self) -> List[int]:
        """Puertos ONVIF soportados."""
        return [2020]
    
    def test_authentication(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str], List[str], List[str]]:
        """
        Prueba autenticación ONVIF en endpoints estándar.
        
        Args:
            ip: Dirección IP
            port: Puerto ONVIF
            
        Returns:
            Tupla con (éxito, método_auth, error, urls_válidas, urls_probadas)
        """
        if not self._validate_credentials():
            return False, None, "Credenciales no configuradas", [], []
        
        # Endpoints ONVIF comunes
        onvif_paths = [
            "/onvif/device_service",
            "/onvif/device",
            "/onvif/Device",
            "/Device",
            "/onvif/"
        ]
        
        tested_urls = []
        valid_urls = []
        
        try:
            for path in onvif_paths:
                if not self.is_testing:
                    break
                    
                url = f"http://{ip}:{port}{path}"
                tested_urls.append(url)
                
                try:
                    # Probar con autenticación Digest
                    response = requests.get(
                        url,
                        auth=HTTPDigestAuth(self.username, self.password),
                        timeout=min(self.timeout, 2.0),
                        allow_redirects=False
                    )
                    
                    if self._is_valid_onvif_response(response):
                        valid_urls.append(url)
                        return True, "ONVIF Digest", None, valid_urls, tested_urls
                    
                    # Probar con Basic Auth
                    response = requests.get(
                        url,
                        auth=HTTPBasicAuth(self.username, self.password),
                        timeout=min(self.timeout, 2.0),
                        allow_redirects=False
                    )
                    
                    if self._is_valid_onvif_response(response):
                        valid_urls.append(url)
                        return True, "ONVIF Basic", None, valid_urls, tested_urls
                        
                except requests.exceptions.Timeout:
                    continue
                except Exception:
                    continue
                    
        except Exception as e:
            return False, None, self._format_error_message("Error ONVIF", e), [], tested_urls
        
        return False, None, "ONVIF no accesible", [], tested_urls
    
    def _is_valid_onvif_response(self, response: requests.Response) -> bool:
        """
        Verifica si la respuesta es válida para ONVIF.
        
        Args:
            response: Respuesta HTTP
            
        Returns:
            True si es una respuesta ONVIF válida
        """
        # Códigos de estado que pueden indicar ONVIF válido
        if response.status_code in [200, 400, 500]:
            # Buscar indicadores ONVIF en el contenido
            content_lower = response.text.lower()
            return 'soap' in content_lower or 'onvif' in content_lower
        
        return False 