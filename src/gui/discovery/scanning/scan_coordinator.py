"""
Coordinador de escaneo que orquesta los diferentes testeadores de protocolos.
Implementa el patrón Strategy para seleccionar el testeador apropiado por puerto.
"""

import threading
from typing import Dict, List, Optional, Callable
from .scan_result import PortResult
from .protocols import (
    HTTPProtocolTester, 
    RTSPProtocolTester, 
    ONVIFProtocolTester, 
    DahuaSDKTester
)

# cspell:disable
class ScanCoordinator:
    """
    Coordinador que orquesta las pruebas de autenticación usando diferentes testeadores.
    
    Implementa el patrón Strategy para seleccionar automáticamente
    el testeador apropiado según el puerto y protocolo.
    """
    
    def __init__(self, username: str = "", password: str = "", timeout: float = 3.0):
        """
        Inicializa el coordinador de escaneo.
        
        Args:
            username: Usuario para autenticación
            password: Contraseña para autenticación
            timeout: Timeout en segundos
        """
        self.username = username
        self.password = password
        self.timeout = timeout
        
        # Inicializar testeadores
        self._initialize_testers()
        
        # Mapeo de puertos a testeadores
        self._port_to_tester_map = self._build_port_mapping()
        
        # Callback para progreso
        self.progress_callback: Optional[Callable] = None
    
    def _initialize_testers(self):
        """Inicializa todos los testeadores de protocolos."""
        self.http_tester = HTTPProtocolTester(self.username, self.password, self.timeout)
        self.rtsp_tester = RTSPProtocolTester(self.username, self.password, self.timeout)
        self.onvif_tester = ONVIFProtocolTester(self.username, self.password, self.timeout)
        self.dahua_sdk_tester = DahuaSDKTester(self.username, self.password, self.timeout)
        
        self.all_testers = [
            self.http_tester,
            self.rtsp_tester,
            self.onvif_tester,
            self.dahua_sdk_tester
        ]
    
    def _build_port_mapping(self) -> Dict[int, object]:
        """
        Construye el mapeo de puertos a testeadores.
        
        Returns:
            Diccionario que mapea puerto -> testeador
        """
        port_mapping = {}
        
        for tester in self.all_testers:
            for port in tester.get_supported_ports():
                port_mapping[port] = tester
        
        return port_mapping
    
    def set_credentials(self, username: str, password: str):
        """
        Actualiza las credenciales en todos los testeadores.
        
        Args:
            username: Nuevo usuario
            password: Nueva contraseña
        """
        self.username = username
        self.password = password
        
        for tester in self.all_testers:
            tester.set_credentials(username, password)
    
    def set_timeout(self, timeout: float):
        """
        Actualiza el timeout en todos los testeadores.
        
        Args:
            timeout: Nuevo timeout en segundos
        """
        self.timeout = timeout
        
        for tester in self.all_testers:
            tester.set_timeout(timeout)
    
    def set_intensity_level(self, level: str):
        """
        Establece el nivel de intensidad para testeadores que lo soporten.
        
        Args:
            level: Nivel de intensidad ('basic', 'medium', 'high', 'maximum')
        """
        # Solo el HTTP tester soporta niveles de intensidad
        if hasattr(self.http_tester, 'set_intensity_level'):
            self.http_tester.set_intensity_level(level)
    
    def set_progress_callback(self, callback: Callable):
        """
        Establece el callback para reportar progreso.
        
        Args:
            callback: Función callback para progreso
        """
        self.progress_callback = callback
    
    def test_port_authentication(self, ip: str, port_result: PortResult) -> bool:
        """
        Prueba autenticación en un puerto específico usando el testeador apropiado.
        
        Args:
            ip: Dirección IP
            port_result: Resultado del puerto a probar
            
        Returns:
            True si se realizó la prueba (independientemente del resultado)
        """
        port = port_result.port
        
        # Marcar que se probó autenticación
        port_result.auth_tested = True
        
        # Buscar testeador apropiado
        tester = self._port_to_tester_map.get(port)
        
        if not tester:
            port_result.auth_error = f"No hay testeador disponible para puerto {port}"
            return False
        
        # Reportar progreso si hay callback
        if self.progress_callback:
            self.progress_callback(0, 1, f"Probando autenticación {tester.__class__.__name__} en puerto {port}...")
        
        try:
            # Ejecutar prueba con timeout general
            def auth_worker():
                """Worker que ejecuta la autenticación."""
                try:
                    success, method, error, valid_urls, tested_urls = tester.test_authentication(ip, port)
                    port_result.auth_success = success
                    port_result.auth_method = method
                    port_result.auth_error = error
                    port_result.valid_urls = valid_urls or []
                    port_result.tested_urls = tested_urls or []
                except Exception as e:
                    port_result.auth_error = f"Error en prueba: {str(e)}"
            
            # Ejecutar autenticación con timeout máximo de 12 segundos
            auth_thread = threading.Thread(target=auth_worker, daemon=True)
            auth_thread.start()
            auth_thread.join(timeout=12.0)
            
            # Si el hilo sigue vivo después del timeout, marcar como error
            if auth_thread.is_alive():
                port_result.auth_error = f"Timeout en autenticación del puerto {port} (>12s)"
                port_result.auth_success = False
                
                # Detener el testeador
                tester.stop_testing()
            
            return True
            
        except Exception as e:
            port_result.auth_error = f"Error coordinando prueba: {str(e)}"
            return False
    
    def stop_all_testing(self):
        """Detiene todas las pruebas en curso."""
        for tester in self.all_testers:
            tester.stop_testing()
    
    def get_supported_ports(self) -> List[int]:
        """
        Obtiene todos los puertos soportados por los testeadores.
        
        Returns:
            Lista de puertos soportados
        """
        all_ports = set()
        for tester in self.all_testers:
            all_ports.update(tester.get_supported_ports())
        return sorted(list(all_ports))
    
    def get_tester_for_port(self, port: int) -> Optional[object]:
        """
        Obtiene el testeador apropiado para un puerto específico.
        
        Args:
            port: Puerto a consultar
            
        Returns:
            Testeador apropiado o None si no hay ninguno
        """
        return self._port_to_tester_map.get(port) 