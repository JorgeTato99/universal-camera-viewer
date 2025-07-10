"""
Testeador de protocolo RTSP para cámaras IP.
Implementa pruebas de autenticación RTSP con timeouts agresivos.
"""

import threading
import time
from typing import Tuple, Optional, List
from .base_protocol_tester import BaseProtocolTester

# cspell:disable
class RTSPProtocolTester(BaseProtocolTester):
    """
    Testeador específico para protocolo RTSP.
    
    Implementa pruebas de autenticación RTSP usando OpenCV
    con timeouts agresivos para evitar bloqueos.
    """
    
    def get_supported_ports(self) -> List[int]:
        """Puertos RTSP soportados."""
        return [554, 5543, 8554]
    
    def test_authentication(self, ip: str, port: int) -> Tuple[bool, Optional[str], Optional[str], List[str], List[str]]:
        """
        Prueba autenticación RTSP con URLs comunes y timeouts agresivos.
        
        Args:
            ip: Dirección IP
            port: Puerto RTSP
            
        Returns:
            Tupla con (éxito, método_auth, error, urls_válidas, urls_probadas)
        """
        if not self._validate_credentials():
            return False, None, "Credenciales no configuradas", [], []
        
        try:
            import cv2
        except ImportError:
            return False, None, "OpenCV no disponible para RTSP", [], []
        
        # URLs RTSP comunes para probar
        rtsp_urls = [
            f"rtsp://{self.username}:{self.password}@{ip}:{port}/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://{self.username}:{self.password}@{ip}:{port}/stream1",
            f"rtsp://{self.username}:{self.password}@{ip}:{port}/live"
        ]
        
        tested_urls = rtsp_urls.copy()
        
        # Probar URLs con timeout total máximo
        start_time = time.time()
        max_total_time = 6.0
        
        for url in rtsp_urls:
            if not self.is_testing:
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
                success, error = self._test_single_rtsp_url(url, timeout_per_url)
                if success:
                    return True, "RTSP", None, [url], tested_urls
            except Exception:
                continue
        
        return False, None, "RTSP no accesible con credenciales (timeout o conexión rechazada)", [], tested_urls
    
    def _test_single_rtsp_url(self, url: str, timeout_seconds: float = 3.0) -> Tuple[bool, Optional[str]]:
        """
        Prueba una URL RTSP con timeout estricto.
        
        Args:
            url: URL RTSP a probar
            timeout_seconds: Timeout en segundos
            
        Returns:
            Tupla con (éxito, error)
        """
        import cv2
        
        result = [False, None]  # [success, error]
        
        def rtsp_worker():
            """Worker que ejecuta la prueba RTSP."""
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