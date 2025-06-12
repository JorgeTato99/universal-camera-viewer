import socket
import threading
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import base64
from urllib.parse import urlparse
import hashlib
import re


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


@dataclass  
class ScanResult:
    target_ip: str
    total_ports_scanned: int
    open_ports: List[PortResult]
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
    
    # Rutas comunes para probar HTTP
    HTTP_TEST_PATHS = [
        "/", "/index.html", "/cgi-bin/main.cgi", "/onvif/device_service",
        "/cgi-bin/hi3510/param.cgi", "/web/", "/admin/", "/system/",
        "/ISAPI/System/deviceInfo", "/stw-cgi/system.cgi"
    ]
    
    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self.is_scanning = False
        self.progress_callback = None
        self.result_callback = None
        
        # Configuración para pruebas de credenciales
        self.test_credentials = False
        self.username = ""
        self.password = ""
    
    def set_progress_callback(self, callback: Callable):
        self.progress_callback = callback
    
    def set_result_callback(self, callback: Callable):
        self.result_callback = callback
    
    def set_credentials(self, username: str, password: str):
        """Configura las credenciales para pruebas de autenticación."""
        self.username = username
        self.password = password
        self.test_credentials = bool(username and password)
    
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
        """Prueba autenticación en el puerto especificado."""
        port_result.auth_tested = True
        
        try:
            if port in [80, 443, 8000, 8080, 6667, 9000]:
                # Prueba HTTP/HTTPS
                success, method, error = self._test_http_auth(ip, port)
                port_result.auth_success = success
                port_result.auth_method = method
                port_result.auth_error = error
                
            elif port in [554, 5543, 8554]:
                # Prueba RTSP
                success, method, error = self._test_rtsp_auth(ip, port)
                port_result.auth_success = success
                port_result.auth_method = method
                port_result.auth_error = error
                
            elif port == 37777:
                # Prueba Dahua SDK
                success, method, error = self._test_dahua_auth(ip, port)
                port_result.auth_success = success
                port_result.auth_method = method
                port_result.auth_error = error
                
            elif port == 2020:
                # Prueba ONVIF
                success, method, error = self._test_onvif_auth(ip, port)
                port_result.auth_success = success
                port_result.auth_method = method
                port_result.auth_error = error
                
        except Exception as e:
            port_result.auth_error = f"Error en prueba: {str(e)}"
    
    def _test_http_auth(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """Prueba autenticación HTTP básica y digest."""
        protocol = "https" if port == 443 else "http"
        
        for path in self.HTTP_TEST_PATHS[:3]:  # Probar solo las primeras 3 rutas
            try:
                url = f"{protocol}://{ip}:{port}{path}"
                
                # Primero sin autenticación para ver qué se requiere
                response = requests.get(url, timeout=self.timeout, verify=False)
                
                if response.status_code == 200:
                    return True, "Sin autenticación", None
                
                if response.status_code == 401:
                    auth_header = response.headers.get('WWW-Authenticate', '')
                    
                    if 'Basic' in auth_header:
                        # Probar autenticación básica
                        response = requests.get(
                            url, 
                            auth=(self.username, self.password),
                            timeout=self.timeout,
                            verify=False
                        )
                        if response.status_code == 200:
                            return True, "HTTP Basic", None
                        
                    elif 'Digest' in auth_header:
                        # Probar autenticación digest
                        from requests.auth import HTTPDigestAuth
                        response = requests.get(
                            url,
                            auth=HTTPDigestAuth(self.username, self.password),
                            timeout=self.timeout,
                            verify=False
                        )
                        if response.status_code == 200:
                            return True, "HTTP Digest", None
                
            except Exception as e:
                continue
        
        return False, None, "Credenciales incorrectas o servicio no accesible"
    
    def _test_rtsp_auth(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """Prueba autenticación RTSP."""
        try:
            # Crear socket RTSP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Enviar OPTIONS request
            rtsp_request = f"OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\nCSeq: 1\r\nUser-Agent: PortScanner\r\n\r\n"
            sock.send(rtsp_request.encode())
            
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            
            if "200 OK" in response:
                return True, "RTSP Sin Auth", None
            elif "401 Unauthorized" in response:
                # Aquí se podría implementar autenticación RTSP más compleja
                return False, None, "Requiere autenticación RTSP"
            
        except Exception as e:
            return False, None, f"Error RTSP: {str(e)}"
        
        return False, None, "No se pudo conectar RTSP"
    
    def _test_onvif_auth(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """Prueba autenticación ONVIF."""
        try:
            # ONVIF básico con SOAP
            onvif_url = f"http://{ip}:{port}/onvif/device_service"
            
            # Crear mensaje SOAP básico para GetDeviceInformation
            soap_body = '''<?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
                <soap:Body>
                    <tds:GetDeviceInformation xmlns:tds="http://www.onvif.org/ver10/device/wsdl"/>
                </soap:Body>
            </soap:Envelope>'''
            
            headers = {
                'Content-Type': 'application/soap+xml',
                'SOAPAction': 'http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation'
            }
            
            # Probar sin autenticación primero
            response = requests.post(onvif_url, data=soap_body, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200 and 'GetDeviceInformationResponse' in response.text:
                return True, "ONVIF Sin Auth", None
            
            # Si requiere autenticación, probar con credenciales básicas
            response = requests.post(
                onvif_url, 
                data=soap_body, 
                headers=headers,
                auth=(self.username, self.password),
                timeout=self.timeout
            )
            
            if response.status_code == 200 and 'GetDeviceInformationResponse' in response.text:
                return True, "ONVIF Basic Auth", None
                
        except Exception as e:
            return False, None, f"Error ONVIF: {str(e)}"
        
        return False, None, "ONVIF no accesible o credenciales incorrectas"
    
    def _test_dahua_auth(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """Prueba autenticación Dahua SDK."""
        try:
            # Conexión TCP al puerto SDK de Dahua
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Enviar mensaje de login básico (simplificado)
            # En un escenario real se usaría el protocolo completo de Dahua
            login_data = f"{self.username}:{self.password}".encode()
            sock.send(login_data)
            
            response = sock.recv(1024)
            sock.close()
            
            # Análisis básico de respuesta
            if len(response) > 0:
                return True, "Dahua SDK", None
            
        except Exception as e:
            return False, None, f"Error Dahua: {str(e)}"
        
        return False, None, "Dahua SDK no accesible"
    
    def scan_host(self, ip: str, ports: List[int] = None) -> ScanResult:
        start_time = time.time()
        self.is_scanning = True
        
        if ports is None:
            ports = list(self.CAMERA_PORTS.keys())
        
        open_ports = []
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
        scan_duration = time.time() - start_time
        
        return ScanResult(
            target_ip=ip,
            total_ports_scanned=len(ports),
            open_ports=open_ports,
            scan_duration=scan_duration,
            is_alive=len(open_ports) > 0,
            credentials_tested=self.test_credentials,
            successful_auths=successful_auths
        )
    
    def stop_scan(self):
        self.is_scanning = False
    
    def export_results(self) -> Dict:
        return {"message": "Escaneo completado"} 