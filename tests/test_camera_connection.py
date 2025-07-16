"""
Script de prueba interactivo para conexiones de cámaras.

Permite probar conexiones ONVIF y RTSP de forma manual.
"""

import asyncio
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any
import cv2
import numpy as np

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models import ConnectionConfig
from services.protocol_handlers.onvif_handler import ONVIFHandler
from services.protocol_handlers.rtsp_handler import RTSPHandler
from services.protocol_service import StreamingConfig
from onvif import ONVIFCamera

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CameraConnectionTester:
    """Probador de conexiones de cámaras."""
    
    def __init__(self):
        self.config = None
        self.streaming_config = StreamingConfig()
        
    def print_header(self, text: str):
        """Imprime un encabezado formateado."""
        print("\n" + "="*50)
        print(f" {text}")
        print("="*50)
        
    def print_success(self, text: str):
        """Imprime mensaje de éxito."""
        print(f"✓ {text}")
        
    def print_error(self, text: str):
        """Imprime mensaje de error."""
        print(f"✗ {text}")
        
    def print_info(self, text: str):
        """Imprime información."""
        print(f"ℹ {text}")
    
    def _sanitize_url(self, url: str) -> str:
        """Oculta credenciales en la URL para mostrar."""
        if '@' in url:
            # Extraer partes de la URL
            parts = url.split('@')
            if len(parts) == 2:
                # Ocultar credenciales
                protocol_part = parts[0].split('://')
                if len(protocol_part) == 2:
                    return f"{protocol_part[0]}://****:****@{parts[1]}"
        return url
        
    def get_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Obtiene entrada del usuario con valor por defecto opcional."""
        if default:
            value = input(f"{prompt} [{default}]: ").strip()
            return value if value else default
        else:
            return input(f"{prompt}: ").strip()
            
    def collect_connection_info(self) -> ConnectionConfig:
        """Recolecta información de conexión del usuario."""
        self.print_header("CONFIGURACIÓN DE CONEXIÓN")
        
        # IP de la cámara
        ip = self.get_input("IP de la cámara")
        
        # Credenciales
        username = self.get_input("Usuario", "admin")
        password = self.get_input("Contraseña")
        
        # Protocolo
        print("\nProtocolos disponibles:")
        print("1. ONVIF")
        print("2. RTSP")
        protocol_choice = self.get_input("Seleccione protocolo (1-2)", "1")
        protocol = "ONVIF" if protocol_choice == "1" else "RTSP"
        
        # Puertos según protocolo
        if protocol == "ONVIF":
            onvif_port = int(self.get_input("Puerto ONVIF", "80"))
            rtsp_port = int(self.get_input("Puerto RTSP", "554"))
            http_port = int(self.get_input("Puerto HTTP", "80"))
        else:
            rtsp_port = int(self.get_input("Puerto RTSP", "554"))
            onvif_port = 80
            http_port = 80
            
        # Crear configuración
        config = ConnectionConfig(
            ip=ip,
            username=username,
            password=password,
            onvif_port=onvif_port,
            rtsp_port=rtsp_port,
            http_port=http_port
        )
        
        return config, protocol
        
    async def test_onvif_connection(self) -> Optional[Dict[str, Any]]:
        """Prueba conexión ONVIF y obtiene perfiles."""
        self.print_header("PRUEBA DE CONEXIÓN ONVIF")
        
        try:
            # Crear handler ONVIF
            handler = ONVIFHandler(self.config, self.streaming_config)
            
            # Conectar
            self.print_info(f"Conectando a {self.config.ip}:{self.config.onvif_port}...")
            self.print_info(f"Usuario: {self.config.username}")
            self.print_info(f"Password: {'*' * len(self.config.password) if self.config.password else 'Sin password'}")
            
            success = await handler.connect()
            
            if not success:
                self.print_error("No se pudo conectar via ONVIF")
                self.print_info("Tip: Para cámaras Dahua, verifica:")
                self.print_info("  - Puerto ONVIF: usualmente 80, 8000 o 8080")
                self.print_info("  - Credenciales correctas")
                self.print_info("  - ONVIF habilitado en la cámara")
                return None
                
            self.print_success("Conexión ONVIF establecida")
            
            # Obtener información del dispositivo
            try:
                device_info = await handler.get_device_info()
                if isinstance(device_info, dict):
                    if 'success' in device_info and device_info['success']:
                        self.print_info("Información del dispositivo:")
                        for key, value in device_info['data'].items():
                            print(f"  - {key}: {value}")
                    elif 'manufacturer' in device_info:
                        # Formato directo
                        self.print_info("Información del dispositivo:")
                        for key, value in device_info.items():
                            print(f"  - {key}: {value}")
            except Exception as e:
                self.print_error(f"No se pudo obtener información del dispositivo: {e}")
                    
            # Obtener perfiles
            try:
                # get_profiles no es asíncrono
                profiles = handler.get_profiles()
                profiles_data = []
                
                if isinstance(profiles, dict) and 'success' in profiles:
                    if profiles['success']:
                        profiles_data = profiles['data']
                elif isinstance(profiles, list):
                    profiles_data = profiles
                elif isinstance(profiles, dict) and 'data' in profiles:
                    profiles_data = profiles['data']
                else:
                    # Si get_profiles devuelve directamente una lista
                    profiles_data = profiles if profiles else []
                
                self.print_info(f"Perfiles obtenidos: {len(profiles_data)}")
                    
                if profiles_data:
                    self.print_info(f"Se encontraron {len(profiles_data)} perfiles:")
                    
                    profile_urls = []
                    for i, profile in enumerate(profiles_data):
                        print(f"\n  Perfil {i+1}:")
                        
                        # Manejar diferentes formatos de perfil
                        if hasattr(profile, '_token'):
                            # Objeto ONVIF
                            print(f"    - Token: {profile._token}")
                            print(f"    - Nombre: {getattr(profile, 'Name', 'Sin nombre')}")
                            
                            # Obtener URL del stream
                            try:
                                # get_stream_uri retorna diccionario {'success': bool, 'data': str}
                                stream_result = await handler._get_best_stream_url()
                                if stream_result:
                                    profile_urls.append({
                                        'name': getattr(profile, 'Name', f'Perfil {i+1}'),
                                        'url': stream_result,
                                        'token': profile._token
                                    })
                                    print(f"    - URL: {self._sanitize_url(stream_result)}")
                                else:
                                    self.print_error(f"    - No se pudo obtener URL del stream")
                            except Exception as e:
                                self.print_error(f"    - Error obteniendo URL: {e}")
                        elif hasattr(profile, 'Name'):
                            # Objeto ONVIF con atributos en mayúsculas
                            print(f"    - Token: {getattr(profile, '_token', 'N/A')}")
                            print(f"    - Nombre: {getattr(profile, 'Name', 'Sin nombre')}")
                            
                            # Intentar obtener URL directamente
                            if hasattr(handler, '_stream_uri') and handler._stream_uri:
                                url = handler._stream_uri
                                profile_urls.append({
                                    'name': getattr(profile, 'Name', f'Perfil {i+1}'),
                                    'url': url,
                                    'token': getattr(profile, '_token', 'unknown')
                                })
                                print(f"    - URL: {url}")
                        else:
                            # Diccionario
                            print(f"    - Nombre: {profile.get('name', 'Sin nombre')}")
                            print(f"    - Token: {profile.get('token', 'N/A')}")
                            
                            if 'video_encoder' in profile:
                                encoder = profile['video_encoder']
                                resolution = encoder.get('resolution', {})
                                print(f"    - Resolución: {resolution.get('width', 'N/A')}x{resolution.get('height', 'N/A')}")
                                print(f"    - Encoding: {encoder.get('encoding', 'N/A')}")
                                print(f"    - FPS: {encoder.get('framerate', 'N/A')}")
                else:
                    self.print_error("No se encontraron perfiles")
                    
            except Exception as e:
                self.print_error(f"Error obteniendo perfiles: {e}")
                profile_urls = []
            
            # Desconectar
            await handler.disconnect()
            
            # Retornar lo que se pudo obtener
            if 'profile_urls' in locals() and profile_urls:
                return {
                    'profiles': profiles_data if 'profiles_data' in locals() else [],
                    'urls': profile_urls
                }
            else:
                return None
                
        except Exception as e:
            self.print_error(f"Error en prueba ONVIF: {e}")
            logger.exception("Error detallado:")
            return None
            
    async def test_rtsp_stream(self, rtsp_url: Optional[str] = None) -> bool:
        """Prueba streaming RTSP."""
        self.print_header("PRUEBA DE STREAMING RTSP")
        
        # Si no se proporciona URL, pedirla
        if not rtsp_url:
            rtsp_url = self.get_input("URL RTSP completa")
            
        try:
            self.print_info(f"Probando URL: {self._sanitize_url(rtsp_url)}")
            
            # Conectar directamente con OpenCV para prueba rápida
            self.print_info("Intentando conexión directa con OpenCV...")
            cap = cv2.VideoCapture(rtsp_url)
            
            if not cap.isOpened():
                self.print_error("No se pudo abrir el stream con OpenCV")
                return False
                
            # Verificar que podemos leer frames
            ret, frame = cap.read()
            if not ret or frame is None:
                self.print_error("No se pueden leer frames del stream")
                cap.release()
                return False
                
            self.print_success("Conexión RTSP establecida con OpenCV")
            
            # Obtener propiedades del stream
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            self.print_info(f"Resolución: {width}x{height}")
            self.print_info(f"FPS: {fps}")
                
            # Mostrar frames
            print("\nMostrando video en vivo. Presione 'q' para salir...")
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    frame_count += 1
                    
                    # Redimensionar para visualización
                    height, width = frame.shape[:2]
                    if width > 800:
                        scale = 800 / width
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        frame = cv2.resize(frame, (new_width, new_height))
                    else:
                        new_width, new_height = width, height
                    
                    # Agregar información al frame
                    cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Res: {width}x{height}", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, "Presione 'q' para salir", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    # Mostrar frame
                    cv2.imshow("Stream de Camara", frame)
                    
                    # Verificar si se presiona 'q'
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    self.print_error("Error leyendo frame")
                    break
                        
            # Cerrar ventana y liberar recursos
            cv2.destroyAllWindows()
            cap.release()
            
            self.print_success(f"Prueba completada. Se capturaron {frame_count} frames")
            return True
            
        except Exception as e:
            self.print_error(f"Error en prueba RTSP: {e}")
            logger.exception("Error detallado:")
            return False
            
    async def run(self):
        """Ejecuta el probador de conexiones."""
        self.print_header("PROBADOR DE CONEXIONES DE CÁMARAS")
        print("Universal Camera Viewer - Test de Conexión")
        
        # Recolectar información
        self.config, protocol = self.collect_connection_info()
        
        # Modo de prueba
        if protocol == "ONVIF":
            # Primero probar ONVIF para obtener perfiles
            onvif_result = await self.test_onvif_connection()
            
            if onvif_result and onvif_result.get('urls'):
                # Preguntar si quiere probar algún stream
                print("\n¿Desea probar alguno de los streams encontrados?")
                for i, url_info in enumerate(onvif_result['urls']):
                    print(f"{i+1}. {url_info['name']}")
                print("0. No probar ninguno")
                
                choice = self.get_input("Seleccione opción (0-" + str(len(onvif_result['urls'])) + ")", "1")
                
                if choice != "0" and choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(onvif_result['urls']):
                        rtsp_url = onvif_result['urls'][idx]['url']
                        await self.test_rtsp_stream(rtsp_url)
            else:
                # Si ONVIF falla, ofrecer probar RTSP directo
                print("\n¿Desea probar conexión RTSP directa?")
                print("1. Sí, con URL manual")
                print("2. Sí, con URL estándar de Dahua")
                print("0. No")
                
                choice = self.get_input("Seleccione opción (0-2)", "2")
                
                if choice == "1":
                    await self.test_rtsp_stream()
                elif choice == "2":
                    # URLs estándar de Dahua
                    print("\nSeleccione calidad del stream:")
                    print("1. Stream principal (HD)")
                    print("2. Stream secundario (SD)")
                    
                    quality_choice = self.get_input("Seleccione calidad (1-2)", "1")
                    
                    if quality_choice == "1":
                        rtsp_url = f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/cam/realmonitor?channel=1&subtype=0"
                    else:
                        rtsp_url = f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/cam/realmonitor?channel=1&subtype=1"
                    
                    self.print_info(f"Probando con URL Dahua estándar...")
                    await self.test_rtsp_stream(rtsp_url)
        else:
            # Modo RTSP directo
            print("\n¿Cómo desea especificar la URL RTSP?")
            print("1. Ingresar URL completa manualmente")
            print("2. Usar plantilla por marca")
            
            choice = self.get_input("Seleccione opción (1-2)", "1")
            
            if choice == "1":
                await self.test_rtsp_stream()
            else:
                # Plantillas por marca
                print("\nMarcas disponibles:")
                print("1. Dahua")
                print("2. TP-Link")
                print("3. Hikvision")
                print("4. Genérico")
                
                brand_choice = self.get_input("Seleccione marca (1-4)", "1")
                
                rtsp_templates = {
                    "1": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/cam/realmonitor?channel=1&subtype=0",
                    "2": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/stream1",
                    "3": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/Streaming/Channels/101",
                    "4": f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/live"
                }
                
                rtsp_url = rtsp_templates.get(brand_choice, rtsp_templates["1"])
                await self.test_rtsp_stream(rtsp_url)
            
        print("\n" + "="*50)
        print(" Prueba finalizada")
        print("="*50)


async def main():
    """Función principal."""
    tester = CameraConnectionTester()
    try:
        await tester.run()
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        logger.exception("Error completo:")


if __name__ == "__main__":
    # Ejecutar
    asyncio.run(main())