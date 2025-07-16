"""
Script simple y rápido para probar conexión RTSP directa usando servicios del proyecto.

Útil para verificar rápidamente URLs RTSP y descubrir automáticamente las correctas.
"""

import asyncio
import cv2
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models import ConnectionConfig
from services.protocol_service import ProtocolService, ProtocolType
from services.protocol_handlers.rtsp_handler import RTSPHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuickRTSPTester:
    """Probador rápido de URLs RTSP usando los servicios del proyecto."""
    
    def __init__(self):
        self.protocol_service = ProtocolService()
        
    def sanitize_url(self, url: str) -> str:
        """Oculta credenciales en la URL para mostrar."""
        if '@' in url:
            parts = url.split('@')
            if len(parts) == 2:
                protocol_part = parts[0].split('://')
                if len(protocol_part) == 2:
                    return f"{protocol_part[0]}://****:****@{parts[1]}"
        return url
        
    def test_rtsp_url(self, url: str, show_video: bool = True) -> bool:
        """
        Prueba una URL RTSP específica.
        
        Args:
            url: URL RTSP completa con credenciales
            show_video: Si True, muestra el video en una ventana
            
        Returns:
            True si la conexión fue exitosa
        """
        print(f"\nProbando: {self.sanitize_url(url)}")
        
        try:
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not cap.isOpened():
                print("❌ No se pudo abrir el stream")
                return False
            
            ret, frame = cap.read()
            if not ret or frame is None:
                print("❌ No se pueden leer frames")
                cap.release()
                return False
            
            # Obtener información del stream
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"✅ Stream funcionando!")
            print(f"   Resolución: {width}x{height}")
            print(f"   FPS: {fps}")
            
            if show_video:
                # Mostrar el frame por unos segundos
                print("\nMostrando preview... (presiona 'q' para cerrar)")
                
                # Redimensionar si es muy grande
                if width > 800:
                    scale = 800 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    display_frame = cv2.resize(frame, (new_width, new_height))
                else:
                    display_frame = frame
                    
                cv2.imshow("RTSP Test", display_frame)
                
                # Mostrar algunos frames más
                start_time = cv2.getTickCount()
                frame_count = 0
                
                while True:
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        frame_count += 1
                        
                        if width > 800:
                            frame = cv2.resize(frame, (new_width, new_height))
                            
                        cv2.imshow("RTSP Test", frame)
                        
                        # Salir con 'q' o después de 5 segundos
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                            
                        elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                        if elapsed > 5:
                            break
                    else:
                        break
                        
                cv2.destroyAllWindows()
                print(f"   Frames mostrados: {frame_count}")
            
            cap.release()
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
            
    async def discover_rtsp_urls(self, ip: str, username: str, password: str, 
                                port: int = 554) -> List[Dict[str, str]]:
        """
        Usa el servicio de protocolos para descubrir URLs RTSP.
        
        Returns:
            Lista de URLs descubiertas con su descripción
        """
        print(f"\nDescubriendo URLs RTSP para {ip}...")
        
        # Crear configuración
        config = ConnectionConfig(
            ip=ip,
            username=username,
            password=password,
            rtsp_port=port
        )
        
        # Crear handler RTSP
        rtsp_handler = RTSPHandler(config)
        
        # Obtener patrones de URLs según marca detectada o genéricos
        url_patterns = rtsp_handler._get_stream_urls()
        
        discovered_urls = []
        
        print(f"Probando {len(url_patterns)} patrones de URL...")
        
        for name, url in url_patterns.items():
            if self.test_rtsp_url(url, show_video=False):
                discovered_urls.append({
                    'name': name.replace('_', ' ').title(),
                    'url': url
                })
                
        return discovered_urls
        
    async def auto_discover_and_test(self, ip: str, username: str, password: str):
        """
        Descubre automáticamente URLs RTSP y las prueba.
        """
        print("="*60)
        print(" AUTO-DESCUBRIMIENTO DE STREAMS RTSP")
        print("="*60)
        
        # Primero intentar con puerto estándar 554
        urls = await self.discover_rtsp_urls(ip, username, password, 554)
        
        # Si no encuentra nada, probar puertos alternativos
        if not urls:
            print("\nProbando puertos alternativos...")
            for port in [8554, 5543]:
                urls = await self.discover_rtsp_urls(ip, username, password, port)
                if urls:
                    break
                    
        if urls:
            print(f"\n✅ Se encontraron {len(urls)} streams válidos:")
            for i, url_info in enumerate(urls, 1):
                print(f"{i}. {url_info['name']}")
                
            # Mostrar el primer stream encontrado
            print(f"\nMostrando: {urls[0]['name']}")
            self.test_rtsp_url(urls[0]['url'], show_video=True)
            
            # Retornar todas las URLs encontradas
            return urls
        else:
            print("\n❌ No se encontraron streams RTSP válidos")
            print("\nPosibles causas:")
            print("- Credenciales incorrectas")
            print("- RTSP deshabilitado en la cámara")
            print("- Firewall bloqueando conexión")
            print("- Modelo de cámara no soportado")
            
            return []
            
    def test_custom_url(self, url: str):
        """Prueba una URL personalizada."""
        print("="*60)
        print(" PRUEBA DE URL PERSONALIZADA")
        print("="*60)
        
        return self.test_rtsp_url(url, show_video=True)


async def main():
    """Función principal con menú interactivo."""
    print("="*60)
    print(" PROBADOR RÁPIDO DE RTSP")
    print("="*60)
    
    tester = QuickRTSPTester()
    
    # Menú de opciones
    print("\n¿Qué desea hacer?")
    print("1. Auto-descubrir streams RTSP")
    print("2. Probar URL específica")
    print("3. Probar cámara TP-Link (192.168.1.77)")
    
    choice = input("\nSeleccione opción (1-3) [1]: ").strip() or "1"
    
    if choice == "1":
        # Auto-descubrimiento
        print("\nIngrese los datos de conexión:")
        ip = input("IP de la cámara: ").strip()
        username = input("Usuario [admin]: ").strip() or "admin"
        password = input("Contraseña: ").strip()
        
        if not ip or not password:
            print("❌ IP y contraseña son requeridos")
            return
            
        urls = await tester.auto_discover_and_test(ip, username, password)
        
        # Mostrar todas las URLs encontradas al final
        if urls:
            print("\n" + "="*60)
            print(" RESUMEN DE URLs ENCONTRADAS")
            print("="*60)
            for url_info in urls:
                print(f"\n{url_info['name']}:")
                print(f"  {url_info['url']}")
                
    elif choice == "2":
        # URL personalizada
        print("\nIngrese la URL RTSP completa:")
        print("Ejemplo: rtsp://user:pass@192.168.1.100:554/stream1")
        url = input("URL: ").strip()
        
        if url:
            tester.test_custom_url(url)
        else:
            print("❌ URL vacía")
            
    elif choice == "3":
        # Prueba rápida TP-Link
        print("\nProbando cámara TP-Link en 192.168.1.77...")
        urls = await tester.auto_discover_and_test(
            "192.168.1.77",
            "admin-tato",
            "mUidGT87gMxg8ce!Wxso3Guu8t.3*Q"
        )
        
    print("\n" + "="*60)
    print(" Prueba finalizada")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        logger.exception("Error completo:")