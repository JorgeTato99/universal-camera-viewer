"""
Test específico para ONVIF: obtener perfiles y URLs RTSP.

Este test usa directamente el ONVIFHandler para:
- Conectar a una cámara ONVIF
- Obtener todos los perfiles disponibles
- Extraer las URLs RTSP de cada perfil
- Mostrar información detallada del dispositivo
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models import ConnectionConfig
from services.protocol_handlers.onvif_handler import ONVIFHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Silenciar logs de zeep
logging.getLogger('zeep').setLevel(logging.WARNING)


class ONVIFProfileTester:
    """Test directo de ONVIF para obtener perfiles y URLs."""
    
    def __init__(self):
        self.handler = None
        
    def print_header(self, text: str):
        """Imprime un encabezado formateado."""
        print("\n" + "="*60)
        print(f" {text}")
        print("="*60)
        
    def print_success(self, text: str):
        """Imprime mensaje de éxito."""
        print(f"✅ {text}")
        
    def print_error(self, text: str):
        """Imprime mensaje de error."""
        print(f"❌ {text}")
        
    def print_info(self, text: str):
        """Imprime información."""
        print(f"ℹ️  {text}")
        
    def sanitize_url(self, url: str) -> str:
        """Oculta credenciales en la URL."""
        if '@' in url:
            parts = url.split('@')
            if len(parts) == 2:
                protocol_part = parts[0].split('://')
                if len(protocol_part) == 2:
                    return f"{protocol_part[0]}://****:****@{parts[1]}"
        return url
        
    async def test_onvif_connection(self, ip: str, username: str, password: str, port: int = 80):
        """
        Prueba conexión ONVIF y obtiene perfiles.
        
        Args:
            ip: IP de la cámara
            username: Usuario ONVIF
            password: Contraseña ONVIF
            port: Puerto ONVIF (80, 2020, 8000, etc.)
        """
        self.print_header("PRUEBA DE CONEXIÓN ONVIF")
        
        # Crear configuración
        config = ConnectionConfig(
            ip=ip,
            username=username,
            password=password,
            onvif_port=port
        )
        
        # Crear handler ONVIF
        self.handler = ONVIFHandler(config)
        
        try:
            # Conectar
            self.print_info(f"Conectando a {ip}:{port}...")
            success = await self.handler.connect()
            
            if not success:
                self.print_error("No se pudo conectar via ONVIF")
                
                # Dar sugerencias basadas en el puerto
                if port == 554:
                    self.print_info("💡 Puerto 554 es para RTSP, no ONVIF")
                    self.print_info("   Intente con estos puertos ONVIF:")
                    self.print_info("   - 2020 (TP-Link)")
                    self.print_info("   - 80 (Estándar)")
                    self.print_info("   - 8000 (Hikvision)")
                elif port == 80:
                    self.print_info("💡 Puerto 80 no respondió")
                    self.print_info("   Para TP-Link use puerto 2020")
                    self.print_info("   Para Hikvision use puerto 8000")
                else:
                    self.print_info("💡 Verifique:")
                    self.print_info("   - La IP es correcta")
                    self.print_info("   - El puerto ONVIF es correcto")
                    self.print_info("   - Las credenciales son correctas")
                    self.print_info("   - ONVIF está habilitado en la cámara")
                return
                
            self.print_success("Conexión ONVIF establecida")
            
            # Obtener información del dispositivo
            self.print_header("INFORMACIÓN DEL DISPOSITIVO")
            device_info = await self.handler.get_device_info()
            
            if device_info:
                print(f"Fabricante: {device_info.get('manufacturer', 'Desconocido')}")
                print(f"Modelo: {device_info.get('model', 'Desconocido')}")
                print(f"Firmware: {device_info.get('firmware_version', 'Desconocido')}")
                print(f"Serial: {device_info.get('serial_number', 'Desconocido')}")
                print(f"Hardware: {device_info.get('hardware_id', 'Desconocido')}")
            
            # Obtener capacidades
            self.print_header("CAPACIDADES DEL DISPOSITIVO")
            capabilities = self.handler.get_capabilities()
            
            if capabilities:
                print(f"Streaming soportado: {'Sí' if capabilities.supports_streaming else 'No'}")
                print(f"Snapshots soportados: {'Sí' if capabilities.supports_snapshots else 'No'}")
                print(f"PTZ soportado: {'Sí' if capabilities.supports_ptz else 'No'}")
                print(f"Audio soportado: {'Sí' if capabilities.supports_audio else 'No'}")
                print(f"Resolución máxima: {capabilities.max_resolution}")
                print(f"Códecs soportados: {', '.join(capabilities.supported_codecs) if capabilities.supported_codecs else 'N/A'}")
            
            # Obtener perfiles
            self.print_header("PERFILES ONVIF DISPONIBLES")
            profiles = self.handler.get_profiles()
            
            if not profiles:
                self.print_error("No se pudieron obtener perfiles")
                return
                
            # Si es un dict con success/data, extraer data
            if isinstance(profiles, dict):
                if profiles.get('success') and 'data' in profiles:
                    profiles_list = profiles['data']
                    print(f"[DEBUG] Respuesta exitosa con {len(profiles_list)} perfiles")
                else:
                    self.print_error(f"Error obteniendo perfiles: {profiles.get('error', 'Desconocido')}")
                    return
            elif isinstance(profiles, list):
                profiles_list = profiles
                print(f"[DEBUG] Lista directa con {len(profiles_list)} perfiles")
            else:
                self.print_error(f"Formato de perfiles inesperado: {type(profiles)}")
                return
                
            print(f"\nSe encontraron {len(profiles_list)} perfiles:")
            
            # URLs encontradas
            urls_found = []
            
            # Procesar cada perfil
            for i, profile in enumerate(profiles_list):
                print(f"\n--- Perfil {i+1} ---")
                
                # Los perfiles vienen como diccionarios del handler
                if isinstance(profile, dict):
                    profile_name = profile.get('name', f'Perfil_{i+1}')
                    profile_token = profile.get('token')
                    
                    print(f"Nombre: {profile_name}")
                    print(f"Token: {profile_token}")
                    
                    # Información de video si está disponible
                    if 'video_encoder' in profile:
                        video_enc = profile['video_encoder']
                        print(f"Codificación: {video_enc.get('encoding', 'N/A')}")
                        if 'resolution' in video_enc:
                            res = video_enc['resolution']
                            print(f"Resolución: {res.get('width', '?')}x{res.get('height', '?')}")
                else:
                    # Formato antiguo con objetos
                    print(f"[DEBUG] Tipo de perfil: {type(profile)}")
                    profile_name = getattr(profile, 'Name', f'Perfil_{i+1}')
                    profile_token = getattr(profile, 'token', getattr(profile, '_token', None))
                    
                    print(f"Nombre: {profile_name}")
                    print(f"Token: {profile_token}")
                
                # Obtener URL del stream
                if profile_token:
                    try:
                        print(f"\nObteniendo URL RTSP para token: {profile_token}")
                        stream_uri_response = await self.handler.get_stream_uri(profile_token)
                        
                        if stream_uri_response:
                            # El handler devuelve un dict con success/data
                            if isinstance(stream_uri_response, dict):
                                if stream_uri_response.get('success'):
                                    url = stream_uri_response.get('data')
                                    if url:
                                        self.print_success(f"URL RTSP: {self.sanitize_url(url)}")
                                        urls_found.append({
                                            'name': profile_name,
                                            'token': profile_token,
                                            'url': url,
                                            'profile_index': i
                                        })
                                    else:
                                        self.print_error("Respuesta exitosa pero sin URL")
                                else:
                                    self.print_error(f"Error: {stream_uri_response.get('error', 'Desconocido')}")
                            else:
                                # Respuesta directa como string
                                url = str(stream_uri_response)
                                self.print_success(f"URL RTSP: {self.sanitize_url(url)}")
                                urls_found.append({
                                    'name': profile_name,
                                    'token': profile_token,
                                    'url': url,
                                    'profile_index': i
                                })
                        else:
                            self.print_error("No se obtuvo respuesta del handler")
                            
                    except Exception as e:
                        self.print_error(f"Error obteniendo stream URI: {e}")
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.exception("Error detallado:")
                else:
                    self.print_info("Sin token para este perfil, no se puede obtener URL")
                
            # Resumen de URLs encontradas
            self.print_header("RESUMEN DE URLs RTSP ENCONTRADAS")
            
            if urls_found:
                print(f"\nSe encontraron {len(urls_found)} URLs RTSP:\n")
                
                for url_info in urls_found:
                    print(f"📹 {url_info['name']}:")
                    print(f"   URL completa: {url_info['url']}")
                    print(f"   URL sanitizada: {self.sanitize_url(url_info['url'])}")
                    print()
                    
                # Guardar para uso posterior
                self.discovered_urls = urls_found
            else:
                self.print_error("No se pudieron obtener URLs RTSP desde los perfiles")
                print("\n💡 Posibles causas:")
                print("   - Los perfiles no tienen tokens accesibles")
                print("   - El formato de perfiles es diferente al esperado")
                print("   - Se requiere un método diferente para esta cámara")
                
                # Sugerir verificar el handler
                if hasattr(self.handler, '_stream_uri') and self.handler._stream_uri:
                    print(f"\n📌 Nota: El handler detectó una URL durante la conexión")
                    print(f"   Puede intentar usar el protocolo RTSP directamente")
                
        except Exception as e:
            self.print_error(f"Error durante la prueba: {e}")
            logger.exception("Error detallado:")
            
        finally:
            # Desconectar
            if self.handler and self.handler.is_connected:
                await self.handler.disconnect()
                self.print_info("Desconectado de ONVIF")


async def main():
    """Función principal interactiva."""
    print("="*60)
    print(" TEST DE PERFILES ONVIF")
    print("="*60)
    print("\nEste test obtiene los perfiles ONVIF y sus URLs RTSP")
    
    tester = ONVIFProfileTester()
    
    # Solicitar datos
    print("\nIngrese los datos de conexión ONVIF:")
    
    ip = input("IP de la cámara: ").strip()
    if not ip:
        print("❌ IP es requerida")
        return
        
    username = input("Usuario [admin]: ").strip() or "admin"
    password = input("Contraseña: ").strip()
    if not password:
        print("❌ Contraseña es requerida")
        return
        
    port_str = input("Puerto ONVIF [80]: ").strip() or "80"
    try:
        port = int(port_str)
    except ValueError:
        print("❌ Puerto debe ser un número")
        return
        
    # Opciones comunes de puertos
    print("\nPuertos ONVIF comunes:")
    print("  80   - Puerto estándar")
    print("  2020 - TP-Link")
    print("  8000 - Hikvision/Steren")
    print("  8080 - Alternativo")
    
    # Ejecutar test
    await tester.test_onvif_connection(ip, username, password, port)
    
    # Si encontró URLs, preguntar si quiere probar alguna
    if hasattr(tester, 'discovered_urls') and tester.discovered_urls:
        print("\n¿Desea probar alguna URL RTSP? (s/n) [n]: ", end='')
        test_rtsp = input().strip().lower()
        
        if test_rtsp == 's':
            print("\nSeleccione URL para probar:")
            for i, url_info in enumerate(tester.discovered_urls, 1):
                print(f"{i}. {url_info['name']}")
                
            choice = input("\nNúmero [1]: ").strip() or "1"
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(tester.discovered_urls):
                    selected = tester.discovered_urls[idx]
                    print(f"\nURL seleccionada: {selected['url']}")
                    print("\nPuede probar esta URL con:")
                    print("- VLC: Media → Open Network Stream")
                    print("- ffplay: ffplay \"<URL>\"")
                    print("- OpenCV: cv2.VideoCapture(\"<URL>\")")
            except:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        logger.exception("Error completo:")