import socket
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import base64
from urllib.parse import urlparse
import hashlib
import re
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

# cspell:disable
@dataclass
class PortResult:
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
    target_ip: str
    total_ports_scanned: int
    open_ports: List[PortResult]
    closed_ports: List[PortResult]  # Agregar puertos cerrados
    scan_duration: float
    is_alive: bool
    credentials_tested: bool = False
    successful_auths: int = 0


class PortScanner:
    CAMERA_PORTS = {
        80: "HTTP", 443: "HTTPS", 554: "RTSP", 2020: "ONVIF-TP-Link",
        5543: "RTSP-Alt", 8000: "HTTP-Alt", 8080: "HTTP-Proxy", 
        37777: "Dahua-SDK", 6667: "HTTP-Alt", 9000: "HTTP-Alt"
    }
    
    # Rutas comunes para probar HTTP - Expandidas por marca
    HTTP_TEST_PATHS = [
        # Rutas básicas
        "/", "/index.html", "/index.htm", "/main.html",
        
        # Rutas de administración genéricas
        "/web/", "/admin/", "/system/", "/config/", "/setup/",
        "/cgi-bin/", "/cgi-bin/main.cgi", "/cgi-bin/index.cgi",
        
        # ONVIF estándar
        "/onvif/device_service", "/onvif/", "/onvif/device",
        
        # Dahua específico
        "/ISAPI/System/deviceInfo", "/ISAPI/", "/ISAPI/System/",
        "/cgi-bin/hi3510/param.cgi", "/cgi-bin/hi3510/",
        "/RPC2", "/RPC2_Login", "/cgi-bin/snapshot.cgi",
        "/cgi-bin/configManager.cgi", "/cgi-bin/magicBox.cgi",
        
        # TP-Link / Tapo específico
        "/stw-cgi/system.cgi", "/stw-cgi/", "/cgi/", 
        "/cgi-bin/luci", "/luci/", "/cgi-bin/luci/",
        "/app/", "/app/main", "/stream/", "/video/",
        
        # Steren / Genéricas chinas
        "/cgi-bin/viewer/video.jpg", "/cgi-bin/snapshot.cgi",
        "/videostream.cgi", "/video.cgi", "/image.cgi",
        "/cgi-bin/video.cgi", "/cgi-bin/image.cgi",
        "/webcapture.jpg", "/snapshot.jpg", "/image.jpg",
        
        # Hikvision (común en genéricas)
        "/ISAPI/Streaming/channels/", "/ISAPI/Security/",
        "/SDK/", "/doc/", "/PSIA/", 
        
        # Axis (menos común pero útil)
        "/axis-cgi/", "/axis-cgi/mjpg/video.cgi",
        
        # Foscam y similares
        "/cgi-bin/CGIProxy.fcgi", "/cgi-bin/hi3510/snap.cgi",
        "/tmpfs/auto.jpg", "/cgi/jpg/image.cgi",
        
        # Rutas de streaming
        "/mjpeg/", "/mjpg/", "/video/", "/stream/",
        "/live/", "/live.htm", "/viewer/", "/view/",
        
        # Rutas de configuración avanzada
        "/form/", "/forms/", "/scripts/", "/js/",
        "/css/", "/images/", "/img/", "/static/",
        
        # APIs REST comunes
        "/api/", "/api/v1/", "/api/v2/", "/rest/",
        "/json/", "/xml/", "/soap/"
    ]
    
    def __init__(self, username: str = "", password: str = "", timeout: int = 3):
        """
        Inicializa el escáner de puertos.
        
        Args:
            username: Usuario para autenticación
            password: Contraseña para autenticación  
            timeout: Timeout en segundos para conexiones
        """
        self.username = username
        self.password = password
        self.timeout = timeout
        self.is_scanning = False
        self.progress_callback: Optional[Callable] = None
        
        # Niveles de intensidad para URLs
        self.intensity_levels = {
            'basic': 10,      # URLs más comunes
            'medium': 20,     # URLs comunes + algunas específicas
            'high': 30,       # URLs comunes + específicas + variantes
            'maximum': 999    # Todas las URLs disponibles
        }
        self.current_intensity = 'basic'  # Por defecto básico
    
    def set_progress_callback(self, callback: Callable):
        self.progress_callback = callback
    
    def set_result_callback(self, callback: Callable):
        self.result_callback = callback
    
    def set_credentials(self, username: str, password: str):
        """Configura las credenciales para pruebas de autenticación."""
        self.username = username
        self.password = password
        self.test_credentials = bool(username and password)
    
    def set_intensity_level(self, level: str):
        """
        Establece el nivel de intensidad para las pruebas de URL.
        
        Args:
            level: 'basic', 'medium', 'high', 'maximum'
        """
        if level in self.intensity_levels:
            self.current_intensity = level
        else:
            raise ValueError(f"Nivel de intensidad inválido: {level}. Usar: {list(self.intensity_levels.keys())}")
    
    def scan_port(self, ip: str, port: int) -> PortResult:
        start_time = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            response_time = time.time() - start_time
            
            is_open = result == 0
            if is_open:
                banner = self._get_banner(sock, port)
            else:
                banner = None
                
            sock.close()
            
            port_result = PortResult(
                port=port,
                is_open=is_open,
                service_name=self.CAMERA_PORTS.get(port, f"Unknown-{port}"),
                response_time=response_time,
                banner=banner
            )
            
            # Probar credenciales si el puerto está abierto y están configuradas
            if is_open and self.test_credentials:
                self._test_authentication(ip, port, port_result)
            
            return port_result
            
        except Exception:
            return PortResult(
                port=port,
                is_open=False,
                service_name=self.CAMERA_PORTS.get(port, f"Unknown-{port}"),
                response_time=time.time() - start_time
            )
    
    def _get_banner(self, sock: socket.socket, port: int) -> Optional[str]:
        try:
            sock.settimeout(1.0)
            if port in [80, 443, 8000, 8080]:
                sock.send(b"GET / HTTP/1.0\r\n\r\n")
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            return banner.split('\n')[0][:100] if banner else None
        except:
            return None
    
    def _test_authentication(self, ip: str, port: int, port_result: PortResult):
        """Prueba autenticación en el puerto especificado con timeout general."""
        port_result.auth_tested = True
        
        import threading
        import time
        
        def auth_worker():
            """Worker que ejecuta la autenticación."""
            try:
                if port in [80, 443, 8000, 8080, 6667, 9000]:
                    # Prueba HTTP/HTTPS
                    if self.progress_callback:
                        self.progress_callback(0, 1, f"Probando autenticación HTTP en puerto {port}...")
                    
                    success, method, error, valid_urls, tested_urls = self._test_http_auth(ip, port)
                    port_result.auth_success = success
                    port_result.auth_method = method
                    port_result.auth_error = error
                    port_result.valid_urls = valid_urls or []
                    port_result.tested_urls = tested_urls or []
                    
                elif port in [554, 5543, 8554]:
                    # Prueba RTSP
                    if self.progress_callback:
                        self.progress_callback(0, 1, f"Probando autenticación RTSP en puerto {port}...")
                    success, method, error = self._test_rtsp_auth(ip, port)
                    port_result.auth_success = success
                    port_result.auth_method = method
                    port_result.auth_error = error
                    
                elif port == 37777:
                    # Prueba Dahua SDK
                    if self.progress_callback:
                        self.progress_callback(0, 1, f"Probando autenticación Dahua SDK en puerto {port}...")
                    success, method, error = self._test_dahua_auth(ip, port)
                    port_result.auth_success = success
                    port_result.auth_method = method
                    port_result.auth_error = error
                    
                elif port == 2020:
                    # Prueba ONVIF
                    if self.progress_callback:
                        self.progress_callback(0, 1, f"Probando autenticación ONVIF en puerto {port}...")
                    success, method, error = self._test_onvif_auth(ip, port)
                    port_result.auth_success = success
                    port_result.auth_method = method
                    port_result.auth_error = error
                    
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
    
    def _test_http_auth(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str], List[str], List[str]]:
        """
        Prueba autenticación HTTP replicando exactamente la lógica del viewer exitoso.
        Usa HTTPDigestAuth como AmcrestConnection y prueba URLs específicas.
        """
        valid_urls = []
        tested_urls = []
        
        try:
            # Obtener rutas según intensidad
            paths = self._get_priority_paths_for_port(port)
            
            # Crear sesión HTTP como en AmcrestConnection
            session = requests.Session()
            session.timeout = min(self.timeout, 2.0)  # Timeout corto
            
            # Configurar autenticación Digest (como en el viewer)
            digest_auth = HTTPDigestAuth(self.username, self.password)
            basic_auth = HTTPBasicAuth(self.username, self.password)
            
            base_url = f"http://{ip}:{port}"
            
            for path in paths:
                if not self.is_scanning:
                    break
                    
                url = f"{base_url}{path}"
                tested_urls.append(url)
                
                try:
                    # Probar primero con Digest Auth (como AmcrestConnection)
                    session.auth = digest_auth
                    response = session.get(url, timeout=2.0, allow_redirects=False)
                    
                    if response.status_code == 200:
                        valid_urls.append(url)
                        if len(valid_urls) >= 3:  # Terminar temprano si encontramos suficientes
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
                    
                    # Probar sin autenticación (para detectar servicios)
                    session.auth = None
                    response = session.get(url, timeout=2.0, allow_redirects=False)
                    
                    # Considerar válido si hay contenido relevante aunque sea 404
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
                # Determinar método de autenticación exitoso
                auth_method = "HTTP Digest/Basic"
                if len(valid_urls) > 1:
                    auth_method += f" ({len(valid_urls)} URLs válidas)"
                return True, auth_method, None, valid_urls, tested_urls
            else:
                return False, None, "No se encontraron URLs válidas", [], tested_urls
                
        except Exception as e:
            return False, None, f"Error HTTP: {str(e)}", [], tested_urls
    
    def _get_priority_paths_for_port(self, port: int) -> List[str]:
        """
        Obtiene rutas priorizadas según el puerto y nivel de intensidad.
        Replica exactamente la lógica del viewer exitoso.
        
        Args:
            port: Puerto a probar
            
        Returns:
            Lista de rutas priorizadas según intensidad
        """
        max_urls = self.intensity_levels[self.current_intensity]
        
        if port == 80:
            # URLs específicas para Dahua HTTP (replicando AmcrestConnection)
            all_paths = [
                # URLs principales del viewer exitoso (PRIORIDAD MÁXIMA)
                "/cgi-bin/magicBox.cgi?action=getMachineName",
                "/cgi-bin/magicBox.cgi?action=getDeviceType", 
                "/cgi-bin/snapshot.cgi?channel=0",
                "/cgi-bin/mjpg/video.cgi?channel=0&subtype=0",
                
                # URLs Dahua comunes
                "/cgi-bin/magicBox.cgi?action=getSystemInfo",
                "/cgi-bin/magicBox.cgi?action=getSerialNo",
                "/cgi-bin/magicBox.cgi?action=getSoftwareVersion",
                "/cgi-bin/magicBox.cgi?action=getHardwareVersion",
                "/cgi-bin/configManager.cgi?action=getConfig&name=General",
                "/cgi-bin/deviceManager.cgi?action=getDeviceInfo",
                
                # URLs ISAPI Dahua
                "/ISAPI/System/deviceInfo",
                "/ISAPI/System/status",
                "/ISAPI/Streaming/channels",
                "/ISAPI/Security/users",
                "/ISAPI/System/capabilities",
                
                # URLs adicionales Dahua
                "/RPC2",
                "/cgi-bin/hi3510/",
                "/cgi-bin/net_sdk.cgi",
                "/cgi-bin/snapshot.cgi",
                "/cgi-bin/mjpg/video.cgi",
                
                # URLs genéricas HTTP
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
                # URLs web alternativas
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
                # Puerto alternativo común en cámaras
                "/",
                "/cgi-bin/snapshot.cgi",
                "/snapshot.jpg",
                "/image.jpg",
                "/video.cgi",
                "/mjpg/video.cgi"
            ]
        elif port == 9000:
            all_paths = [
                # Puerto de gestión
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
        
        # Retornar según nivel de intensidad
        return all_paths[:max_urls]
    
    def _test_rtsp_auth(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """Prueba autenticación RTSP con URLs comunes y timeouts agresivos."""
        try:
            import cv2
            import threading
            import time
            
            # URLs RTSP comunes para probar (solo las más importantes para evitar bloqueos)
            rtsp_urls = [
                f"rtsp://{self.username}:{self.password}@{ip}:{port}/cam/realmonitor?channel=1&subtype=0",
                f"rtsp://{self.username}:{self.password}@{ip}:{port}/stream1",
                f"rtsp://{self.username}:{self.password}@{ip}:{port}/live"
            ]
            
            def test_single_rtsp_url(url, timeout_seconds=3):
                """Prueba una URL RTSP con timeout estricto."""
                result = [False, None]  # [success, error]
                
                def rtsp_worker():
                    try:
                        cap = cv2.VideoCapture(url)
                        # Configurar timeouts muy agresivos
                        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)  # 2 segundos para abrir
                        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 1000)   # 1 segundo para leer
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)             # Buffer mínimo
                        
                        if cap.isOpened():
                            # Intentar leer un frame con timeout
                            ret, _ = cap.read()
                            if ret:
                                result[0] = True
                        cap.release()
                    except Exception as e:
                        result[1] = str(e)
                
                # Ejecutar en hilo con timeout
                thread = threading.Thread(target=rtsp_worker, daemon=True)
                thread.start()
                thread.join(timeout=timeout_seconds)
                
                # Si el hilo sigue vivo, significa que se colgó
                if thread.is_alive():
                    result[1] = f"Timeout después de {timeout_seconds}s"
                
                return result[0], result[1]
            
            # Probar URLs con timeout total máximo de 6 segundos
            start_time = time.time()
            max_total_time = 6.0
            
            for url in rtsp_urls:
                if not self.is_scanning:
                    break
                
                # Verificar timeout total
                elapsed = time.time() - start_time
                if elapsed >= max_total_time:
                    break
                
                remaining_time = max_total_time - elapsed
                timeout_per_url = min(2.0, remaining_time)
                
                if timeout_per_url <= 0:
                    break
                
                try:
                    success, error = test_single_rtsp_url(url, timeout_per_url)
                    if success:
                        return True, "RTSP", None
                except Exception:
                    continue
            
            return False, None, "RTSP no accesible con credenciales (timeout o conexión rechazada)"
            
        except ImportError:
            return False, None, "OpenCV no disponible para RTSP"
        except Exception as e:
            return False, None, f"Error RTSP: {str(e)}"

    def _test_onvif_auth(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """Prueba autenticación ONVIF."""
        try:
            # Probar endpoints ONVIF comunes
            onvif_paths = [
                "/onvif/device_service",
                "/onvif/device",
                "/onvif/Device",
                "/Device",
                "/onvif/"
            ]
            
            for path in onvif_paths:
                if not self.is_scanning:
                    break
                    
                try:
                    url = f"http://{ip}:{port}{path}"
                    
                    # Probar con autenticación Digest
                    response = requests.get(
                        url,
                        auth=HTTPDigestAuth(self.username, self.password),
                        timeout=min(self.timeout, 2.0),
                        allow_redirects=False
                    )
                    
                    if response.status_code in [200, 400, 500]:  # 400/500 pueden indicar ONVIF válido
                        if 'soap' in response.text.lower() or 'onvif' in response.text.lower():
                            return True, "ONVIF", None
                    
                    # Probar con Basic Auth
                    response = requests.get(
                        url,
                        auth=HTTPBasicAuth(self.username, self.password),
                        timeout=min(self.timeout, 2.0),
                        allow_redirects=False
                    )
                    
                    if response.status_code in [200, 400, 500]:
                        if 'soap' in response.text.lower() or 'onvif' in response.text.lower():
                            return True, "ONVIF", None
                            
                except requests.exceptions.Timeout:
                    continue
                except Exception:
                    continue
                
        except requests.exceptions.Timeout:
            return False, None, "Timeout en ONVIF"
        except Exception as e:
            return False, None, f"Error ONVIF: {str(e)}"
        
        return False, None, "ONVIF no accesible"

    def _test_dahua_auth(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """Prueba autenticación Dahua SDK con timeout corto."""
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
                return True, "Dahua SDK", None
            
        except socket.timeout:
            return False, None, "Timeout en Dahua SDK"
        except Exception as e:
            return False, None, f"Error Dahua: {str(e)}"
        
        return False, None, "Dahua SDK no accesible"
    
    def scan_host(self, ip: str, ports: List[int] = None) -> ScanResult:
        start_time = time.time()
        self.is_scanning = True
        
        if ports is None:
            ports = list(self.CAMERA_PORTS.keys())
        
        open_ports = []
        closed_ports = []  # Lista para puertos cerrados
        successful_auths = 0
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_port = {executor.submit(self.scan_port, ip, port): port for port in ports}
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
                        closed_ports.append(result)  # Agregar puertos cerrados
                    
                    # Reportar todos los resultados (abiertos y cerrados)
                    if self.result_callback:
                        self.result_callback(result)
                    
                    if self.progress_callback:
                        status = f"Escaneando {ip}..."
                        if self.test_credentials:
                            status += f" (Con credenciales)"
                        self.progress_callback(completed, len(ports), status)
                except:
                    pass
        
        open_ports.sort(key=lambda x: x.port)
        closed_ports.sort(key=lambda x: x.port)  # Ordenar puertos cerrados también
        scan_duration = time.time() - start_time
        
        return ScanResult(
            target_ip=ip,
            total_ports_scanned=len(ports),
            open_ports=open_ports,
            closed_ports=closed_ports,  # Incluir puertos cerrados
            scan_duration=scan_duration,
            is_alive=len(open_ports) > 0,
            credentials_tested=self.test_credentials,
            successful_auths=successful_auths
        )
    
    def stop_scan(self):
        self.is_scanning = False
    
    def export_results(self) -> Dict:
        return {"message": "Escaneo completado"} 