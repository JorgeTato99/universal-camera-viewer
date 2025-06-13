"""
Escáner principal de puertos refactorizado.
Implementa el escaneo básico de puertos y delega las pruebas de autenticación al coordinador.
"""

import socket
import time
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from .scan_result import PortResult, ScanResult
from .scan_coordinator import ScanCoordinator

# cspell:disable
class PortScanner:
    """
    Escáner principal de puertos para cámaras IP.
    
    Se enfoca únicamente en el escaneo básico de puertos,
    delegando las pruebas de autenticación al ScanCoordinator.
    """
    
    # Puertos comunes para cámaras IP
    CAMERA_PORTS = {
        80: "HTTP", 443: "HTTPS", 554: "RTSP", 2020: "ONVIF-TP-Link",
        5543: "RTSP-Alt", 8000: "HTTP-Alt", 8080: "HTTP-Proxy", 
        37777: "Dahua-SDK", 6667: "HTTP-Alt", 9000: "HTTP-Alt"
    }
    
    def __init__(self, username: str = "", password: str = "", timeout: int = 3):
        """
        Inicializa el escáner de puertos.
        
        Args:
            username: Usuario para autenticación
            password: Contraseña para autenticación  
            timeout: Timeout en segundos para conexiones
        """
        self.timeout = timeout
        self.is_scanning = False
        
        # Inicializar coordinador de escaneo
        self.scan_coordinator = ScanCoordinator(username, password, timeout)
        
        # Callbacks
        self.progress_callback: Optional[Callable] = None
        self.result_callback: Optional[Callable] = None
        
        # Configuración de credenciales
        self.test_credentials = bool(username and password)
    
    def set_progress_callback(self, callback: Callable):
        """Establece el callback para reportar progreso."""
        self.progress_callback = callback
        self.scan_coordinator.set_progress_callback(callback)
    
    def set_result_callback(self, callback: Callable):
        """Establece el callback para reportar resultados individuales."""
        self.result_callback = callback
    
    def set_credentials(self, username: str, password: str):
        """
        Configura las credenciales para pruebas de autenticación.
        
        Args:
            username: Usuario para autenticación
            password: Contraseña para autenticación
        """
        self.test_credentials = bool(username and password)
        self.scan_coordinator.set_credentials(username, password)
    
    def set_intensity_level(self, level: str):
        """
        Establece el nivel de intensidad para las pruebas de URL.
        
        Args:
            level: 'basic', 'medium', 'high', 'maximum'
        """
        self.scan_coordinator.set_intensity_level(level)
    
    def scan_port(self, ip: str, port: int) -> PortResult:
        """
        Escanea un puerto específico.
        
        Args:
            ip: Dirección IP del host
            port: Puerto a escanear
            
        Returns:
            Resultado del escaneo del puerto
        """
        start_time = time.time()
        
        try:
            # Crear socket y probar conexión
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            response_time = time.time() - start_time
            
            is_open = result == 0
            banner = None
            
            if is_open:
                banner = self._get_banner(sock, port)
            
            sock.close()
            
            # Crear resultado del puerto
            port_result = PortResult(
                port=port,
                is_open=is_open,
                service_name=self.CAMERA_PORTS.get(port, f"Unknown-{port}"),
                response_time=response_time,
                banner=banner
            )
            
            # Probar credenciales si el puerto está abierto y están configuradas
            if is_open and self.test_credentials:
                self.scan_coordinator.test_port_authentication(ip, port_result)
            
            return port_result
            
        except Exception:
            return PortResult(
                port=port,
                is_open=False,
                service_name=self.CAMERA_PORTS.get(port, f"Unknown-{port}"),
                response_time=time.time() - start_time
            )
    
    def _get_banner(self, sock: socket.socket, port: int) -> Optional[str]:
        """
        Obtiene el banner del servicio en el puerto.
        
        Args:
            sock: Socket conectado
            port: Puerto del servicio
            
        Returns:
            Banner del servicio o None
        """
        try:
            sock.settimeout(1.0)
            
            # Enviar solicitud HTTP para puertos web
            if port in [80, 443, 8000, 8080]:
                sock.send(b"GET / HTTP/1.0\r\n\r\n")
            
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            return banner.split('\n')[0][:100] if banner else None
        except:
            return None
    
    def scan_host(self, ip: str, ports: List[int] = None) -> ScanResult:
        """
        Escanea todos los puertos de un host.
        
        Args:
            ip: Dirección IP del host
            ports: Lista de puertos a escanear (por defecto todos los de cámaras)
            
        Returns:
            Resultado completo del escaneo
        """
        start_time = time.time()
        self.is_scanning = True
        
        if ports is None:
            ports = list(self.CAMERA_PORTS.keys())
        
        open_ports = []
        closed_ports = []
        successful_auths = 0
        
        # Usar ThreadPoolExecutor para escaneo paralelo
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_port = {
                executor.submit(self.scan_port, ip, port): port 
                for port in ports
            }
            completed = 0
            
            for future in as_completed(future_to_port):
                if not self.is_scanning:
                    break
                
                completed += 1
                
                try:
                    result = future.result()
                    
                    if result.is_open:
                        open_ports.append(result)
                        if result.auth_success:
                            successful_auths += 1
                    else:
                        closed_ports.append(result)
                    
                    # Reportar resultado individual
                    if self.result_callback:
                        self.result_callback(result)
                    
                    # Reportar progreso
                    if self.progress_callback:
                        status = f"Escaneando {ip}..."
                        if self.test_credentials:
                            status += f" (Con credenciales)"
                        self.progress_callback(completed, len(ports), status)
                        
                except Exception:
                    # Ignorar errores individuales
                    pass
        
        # Ordenar resultados
        open_ports.sort(key=lambda x: x.port)
        closed_ports.sort(key=lambda x: x.port)
        scan_duration = time.time() - start_time
        
        return ScanResult(
            target_ip=ip,
            total_ports_scanned=len(ports),
            open_ports=open_ports,
            closed_ports=closed_ports,
            scan_duration=scan_duration,
            is_alive=len(open_ports) > 0,
            credentials_tested=self.test_credentials,
            successful_auths=successful_auths
        )
    
    def stop_scan(self):
        """Detiene el escaneo actual."""
        self.is_scanning = False
        self.scan_coordinator.stop_all_testing()
    
    def get_supported_ports(self) -> List[int]:
        """
        Obtiene la lista de puertos soportados.
        
        Returns:
            Lista de puertos de cámaras soportados
        """
        return list(self.CAMERA_PORTS.keys())
    
    def export_results(self) -> dict:
        """
        Exporta configuración básica del escáner.
        
        Returns:
            Diccionario con información del escáner
        """
        return {
            "scanner_type": "PortScanner",
            "supported_ports": self.get_supported_ports(),
            "timeout": self.timeout,
            "credentials_enabled": self.test_credentials
        } 