"""
Testeador de protocolo HTTP para cámaras IP.
Implementa pruebas de autenticación HTTP específicas para diferentes marcas de cámaras.
"""

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from typing import Tuple, Optional, List
from .base_protocol_tester import BaseProtocolTester

# cspell:disable
class HTTPProtocolTester(BaseProtocolTester):
    """
    Testeador específico para protocolo HTTP.
    
    Implementa pruebas de autenticación HTTP usando tanto Basic Auth
    como Digest Auth, probando múltiples URLs específicas por marca.
    """
    
    def __init__(self, username: str = "", password: str = "", timeout: float = 3.0, intensity_level: str = "basic"):
        """
        Inicializa el testeador HTTP.
        
        Args:
            username: Usuario para autenticación
            password: Contraseña para autenticación
            timeout: Timeout en segundos
            intensity_level: Nivel de intensidad ('basic', 'medium', 'high', 'maximum')
        """
        super().__init__(username, password, timeout)
        self.intensity_level = intensity_level
        self.intensity_levels = {
            'basic': 10,
            'medium': 20,
            'high': 30,
            'maximum': 999
        }
    
    def get_supported_ports(self) -> List[int]:
        """Puertos HTTP soportados."""
        return [80, 443, 8000, 8080, 6667, 9000]
    
    def test_authentication(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str], List[str], List[str]]:
        """
        Prueba autenticación HTTP replicando la lógica del viewer exitoso.
        
        Args:
            ip: Dirección IP
            port: Puerto HTTP
            
        Returns:
            Tupla con (éxito, método_auth, error, urls_válidas, urls_probadas)
        """
        if not self._validate_credentials():
            return False, None, "Credenciales no configuradas", [], []
        
        valid_urls = []
        tested_urls = []
        
        try:
            # Obtener rutas según intensidad y puerto
            paths = self._get_priority_paths_for_port(port)
            
            # Crear sesión HTTP como en AmcrestConnection
            session = requests.Session()
            session.timeout = min(self.timeout, 2.0)
            
            # Configurar autenticación
            digest_auth = HTTPDigestAuth(self.username, self.password)
            basic_auth = HTTPBasicAuth(self.username, self.password)
            
            base_url = f"http://{ip}:{port}"
            
            for path in paths:
                if not self.is_testing:
                    break
                    
                url = f"{base_url}{path}"
                tested_urls.append(url)
                
                try:
                    # Probar primero con Digest Auth
                    session.auth = digest_auth
                    response = session.get(url, timeout=2.0, allow_redirects=False)
                    
                    if response.status_code == 200:
                        valid_urls.append(url)
                        if len(valid_urls) >= 3:
                            break
                        continue
                    
                    # Si Digest falla, probar Basic Auth
                    session.auth = basic_auth
                    response = session.get(url, timeout=2.0, allow_redirects=False)
                    
                    if response.status_code == 200:
                        valid_urls.append(url)
                        if len(valid_urls) >= 3:
                            break
                        continue
                    
                    # Probar sin autenticación para detectar servicios
                    session.auth = None
                    response = session.get(url, timeout=2.0, allow_redirects=False)
                    
                    # Considerar válido si hay contenido relevante
                    if (response.status_code in [200, 401, 403] or 
                        (response.status_code == 404 and 
                         any(keyword in response.text.lower() for keyword in 
                             ['camera', 'dahua', 'ipc', 'dvr', 'nvr', 'cgi-bin']))):
                        valid_urls.append(url)
                        if len(valid_urls) >= 3:
                            break
                    
                except requests.exceptions.Timeout:
                    continue
                except Exception:
                    continue
            
            session.close()
            
            if valid_urls:
                auth_method = "HTTP Digest/Basic"
                if len(valid_urls) > 1:
                    auth_method += f" ({len(valid_urls)} URLs válidas)"
                return True, auth_method, None, valid_urls, tested_urls
            else:
                return False, None, "No se encontraron URLs válidas", [], tested_urls
                
        except Exception as e:
            return False, None, self._format_error_message("Error HTTP", e), [], tested_urls
    
    def _get_priority_paths_for_port(self, port: int) -> List[str]:
        """
        Obtiene rutas priorizadas según el puerto y nivel de intensidad.
        
        Args:
            port: Puerto a probar
            
        Returns:
            Lista de rutas priorizadas
        """
        max_urls = self.intensity_levels[self.intensity_level]
        
        if port == 80:
            # URLs específicas para Dahua HTTP
            all_paths = [
                # URLs principales del viewer exitoso (PRIORIDAD MÁXIMA)
                "/cgi-bin/magicBox.cgi?action=getMachineName",
                "/cgi-bin/magicBox.cgi?action=getDeviceType", 
                "/cgi-bin/snapshot.cgi?channel=0",
                "/cgi-bin/mjpg/video.cgi?channel=0&subtype=0",
                
                # URLs Dahua comunes
                "/cgi-bin/magicBox.cgi?action=getSystemInfo",
                "/cgi-bin/magicBox.cgi?action=getSerialNo",
                "/cgi-bin/configManager.cgi?action=getConfig&name=General",
                "/cgi-bin/deviceManager.cgi?action=getDeviceInfo",
                
                # URLs ISAPI Dahua
                "/ISAPI/System/deviceInfo",
                "/ISAPI/System/status",
                "/ISAPI/Streaming/channels",
                "/ISAPI/Security/users",
                
                # URLs adicionales
                "/RPC2",
                "/cgi-bin/hi3510/",
                "/cgi-bin/snapshot.cgi",
                "/cgi-bin/mjpg/video.cgi",
                
                # URLs genéricas
                "/",
                "/index.html",
                "/login.html",
                "/admin/",
                "/cgi-bin/",
                "/api/",
                "/web/",
                "/ui/",
                "/setup/",
                "/config/"
            ]
        elif port == 8080:
            all_paths = [
                "/",
                "/index.html", 
                "/admin/",
                "/web/",
                "/ui/",
                "/cgi-bin/snapshot.cgi",
                "/api/v1/",
                "/setup/",
                "/config/",
                "/login"
            ]
        elif port == 6667:
            all_paths = [
                "/",
                "/cgi-bin/snapshot.cgi",
                "/snapshot.jpg",
                "/image.jpg",
                "/video.cgi",
                "/mjpg/video.cgi"
            ]
        elif port == 9000:
            all_paths = [
                "/",
                "/admin/",
                "/management/",
                "/api/",
                "/web/"
            ]
        else:
            # URLs genéricas para otros puertos
            all_paths = [
                "/",
                "/index.html",
                "/admin/",
                "/api/"
            ]
        
        return all_paths[:max_urls]
    
    def set_intensity_level(self, level: str):
        """
        Establece el nivel de intensidad para las pruebas.
        
        Args:
            level: Nivel de intensidad ('basic', 'medium', 'high', 'maximum')
        """
        if level in self.intensity_levels:
            self.intensity_level = level
        else:
            raise ValueError(f"Nivel inválido: {level}. Usar: {list(self.intensity_levels.keys())}") 