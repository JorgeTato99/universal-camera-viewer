"""
Script de prueba interactivo para conexiones de cámaras usando los servicios del proyecto.

Utiliza los servicios internos del proyecto para:
- Auto-detectar protocolos soportados
- Descubrir URLs RTSP automáticamente
- Probar streaming en vivo
"""

import asyncio
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List
import cv2

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models import ConnectionConfig
from services.protocol_service import ProtocolService, ProtocolType, StreamingConfig
from services.scan_service import ScanService, ScanRange, ScanMethod
from services.camera_manager_service import CameraManagerService
from services.data_service import DataService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CameraConnectionTester:
    """Probador de conexiones de cámaras usando servicios del proyecto."""
    
    def __init__(self):
        self.protocol_service = ProtocolService()
        self.scan_service = ScanService()
        self.camera_manager = CameraManagerService()
        self.data_service = DataService()
        self.config = None
        self.scan_results = []
        
        # Configurar callback para resultados de escaneo
        self.scan_service.on_scan_completed = self._on_scan_completed
        
    def _on_scan_completed(self, scan_id: str, results: List[Dict[str, Any]]):
        """Callback cuando se completa un escaneo."""
        self.scan_results = results
        logger.info(f"Escaneo completado: {len(results)} resultados")
        
    def print_header(self, text: str):
        """Imprime un encabezado formateado."""
        print("\n" + "="*60)
        print(f" {text}")
        print("="*60)
        
    def print_success(self, text: str):
        """Imprime mensaje de éxito."""
        print(f"✓ {text}")
        
    def print_error(self, text: str):
        """Imprime mensaje de error."""
        print(f"✗ {text}")
        
    def print_info(self, text: str):
        """Imprime información."""
        print(f"ℹ {text}")
    
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
        
        # Crear configuración básica
        config = ConnectionConfig(
            ip=ip,
            username=username,
            password=password,
            onvif_port=80,  # Se ajustará durante detección
            rtsp_port=554,  # Se ajustará durante detección
            http_port=80    # Se ajustará durante detección
        )
        
        return config
        
    async def scan_camera_ports(self, ip: str) -> Dict[str, Any]:
        """Escanea puertos comunes de cámaras IP."""
        self.print_header("ESCANEANDO PUERTOS")
        self.print_info(f"Escaneando puertos comunes en {ip}...")
        
        # Crear rango de escaneo para una sola IP
        scan_range = ScanRange(
            start_ip=ip,
            end_ip=ip,
            ports=[80, 443, 554, 2020, 8000, 8080, 8554, 5543]  # Puertos comunes
        )
        
        # Reiniciar resultados
        self.scan_results = []
        
        # Ejecutar escaneo
        scan_id = await self.scan_service.start_scan_async(
            scan_range=scan_range,
            methods=[ScanMethod.PORT_SCAN],
            priority=3,
            use_cache=False
        )
        
        # Esperar a que complete el escaneo
        max_wait = 10  # segundos
        waited = 0
        all_results = None
        
        while waited < max_wait:
            status = self.scan_service.get_scan_status(scan_id)
            
            # Intentar capturar resultados en cada iteración
            if scan_id in self.scan_service.active_scans:
                scan_model = self.scan_service.active_scans[scan_id]
                # Capturar resultados cuando el escaneo esté cerca de completarse
                if status and status.value in ['completed', 'processing']:
                    try:
                        all_results = scan_model.get_all_results()
                    except:
                        pass  # El modelo puede haberse eliminado
                    
            if status and status.value in ['completed', 'error', 'cancelled']:
                # Dar una última oportunidad de capturar resultados
                if not all_results and scan_id in self.scan_service.active_scans:
                    try:
                        all_results = self.scan_service.active_scans[scan_id].get_all_results()
                    except:
                        pass
                await asyncio.sleep(0.1)  # Pequeña pausa antes de salir
                break
                
            await asyncio.sleep(0.5)
            waited += 0.5
            
        # Debug: mostrar qué capturamos
        self.logger.info(f"Escaneo completado: {len(all_results) if all_results else 0} resultados")
        
        # Obtener información de la cámara
        camera_info = {}
        
        if all_results and len(all_results) > 0:
            # El primer resultado debería ser nuestra IP
            result = all_results[0]
            open_ports = result.get('open_ports', [])
            
            self.print_success(f"Puertos abiertos encontrados: {open_ports}")
            
            # Ajustar configuración basada en puertos encontrados
            if 2020 in open_ports:
                self.print_info("Puerto 2020 detectado - Posible cámara TP-Link")
                self.config.onvif_port = 2020
            elif 8000 in open_ports:
                self.print_info("Puerto 8000 detectado - Posible cámara Hikvision/Steren")
                self.config.onvif_port = 8000
                
            if 443 in open_ports:
                self.print_info("Puerto HTTPS 443 detectado")
                self.config.http_port = 443
                
            if 5543 in open_ports:
                self.print_info("Puerto 5543 detectado - RTSP alternativo")
                self.config.rtsp_port = 5543
                
            camera_info = result
        else:
            self.print_error("No se detectaron puertos abiertos")
            self.print_info("Esto puede deberse a:")
            self.print_info("  - Firewall bloqueando los puertos")
            self.print_info("  - La cámara no responde a escaneos de puertos")
            self.print_info("  - Los puertos están en rangos no estándar")
            
        return camera_info
            
    async def auto_detect_protocols(self) -> List[ProtocolType]:
        """Auto-detecta protocolos soportados por la cámara."""
        self.print_header("DETECCIÓN AUTOMÁTICA DE PROTOCOLOS")
        self.print_info("Probando protocolos disponibles...")
        
        # Detectar protocolos soportados
        supported_protocols = await self.protocol_service.detect_protocols(self.config)
        
        if supported_protocols:
            self.print_success(f"Protocolos detectados: {[p.value for p in supported_protocols]}")
        else:
            self.print_error("No se detectaron protocolos compatibles")
            self.print_info("Esto puede deberse a:")
            self.print_info("  - Credenciales incorrectas")
            self.print_info("  - Firewall bloqueando conexiones")
            self.print_info("  - Protocolos deshabilitados en la cámara")
            
        return supported_protocols
        
    async def discover_rtsp_urls(self, protocol: ProtocolType) -> List[Dict[str, str]]:
        """Descubre URLs RTSP disponibles."""
        self.print_header("DESCUBRIMIENTO DE URLs RTSP")
        
        urls = []
        
        # Crear conexión temporal para descubrimiento
        camera_id = f"test_{self.config.ip}"
        handler = await self.protocol_service.create_connection(
            camera_id=camera_id,
            protocol=protocol,
            config=self.config
        )
        
        if not handler:
            self.print_error("No se pudo crear conexión para descubrimiento")
            return urls
            
        try:
            if protocol == ProtocolType.ONVIF:
                # Para ONVIF, obtener perfiles y sus URLs
                profiles = handler.get_profiles()
                
                if isinstance(profiles, dict) and profiles.get('success'):
                    profiles_data = profiles.get('data', [])
                elif isinstance(profiles, list):
                    profiles_data = profiles
                else:
                    profiles_data = []
                    
                self.print_info(f"Perfiles ONVIF encontrados: {len(profiles_data)}")
                
                for i, profile in enumerate(profiles_data):
                    try:
                        # Obtener URL del stream para este perfil
                        if hasattr(profile, '_token'):
                            stream_uri = await handler.get_stream_uri(profile._token)
                            if stream_uri:
                                url_info = {
                                    'name': getattr(profile, 'Name', f'Perfil {i+1}'),
                                    'url': stream_uri,
                                    'token': profile._token
                                }
                                urls.append(url_info)
                                self.print_success(f"URL encontrada: {url_info['name']}")
                    except Exception as e:
                        self.print_error(f"Error obteniendo URL del perfil {i+1}: {e}")
                        
            elif protocol == ProtocolType.RTSP:
                # Para RTSP directo, usar patrones comunes
                rtsp_patterns = handler._get_stream_urls()
                
                for name, url in rtsp_patterns.items():
                    # Probar si la URL funciona
                    cap = cv2.VideoCapture(url)
                    if cap.isOpened():
                        ret, _ = cap.read()
                        if ret:
                            url_info = {
                                'name': name.replace('_', ' ').title(),
                                'url': url,
                                'token': name
                            }
                            urls.append(url_info)
                            self.print_success(f"URL RTSP válida: {name}")
                    cap.release()
                    
        except Exception as e:
            self.print_error(f"Error durante descubrimiento: {e}")
            logger.exception("Error detallado:")
        finally:
            # Desconectar
            await self.protocol_service.disconnect_camera(camera_id)
            
        return urls
        
    async def test_rtsp_stream(self, rtsp_url: str, name: str = "Stream") -> bool:
        """Prueba streaming RTSP con visualización."""
        self.print_header(f"PRUEBA DE STREAMING: {name}")
        
        try:
            self.print_info(f"Conectando a stream...")
            
            cap = cv2.VideoCapture(rtsp_url)
            
            if not cap.isOpened():
                self.print_error("No se pudo abrir el stream")
                return False
                
            # Verificar que podemos leer frames
            ret, frame = cap.read()
            if not ret or frame is None:
                self.print_error("No se pueden leer frames del stream")
                cap.release()
                return False
                
            self.print_success("Conexión RTSP establecida")
            
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
                    if width > 800:
                        scale = 800 / width
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        display_frame = cv2.resize(frame, (new_width, new_height))
                    else:
                        display_frame = frame
                    
                    # Agregar información al frame
                    cv2.putText(display_frame, f"{name} - Frame: {frame_count}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(display_frame, f"Res: {width}x{height} @ {fps}fps", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(display_frame, "Presione 'q' para salir", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    # Mostrar frame
                    cv2.imshow(f"Camera Test - {self.config.ip}", display_frame)
                    
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
            
    async def save_camera_if_desired(self, rtsp_url: str) -> bool:
        """Pregunta si desea guardar la cámara en la base de datos."""
        print("\n¿Desea guardar esta cámara en la base de datos?")
        save = self.get_input("Guardar (s/n)", "n")
        
        if save.lower() != 's':
            return False
            
        # Recolectar información adicional
        display_name = self.get_input("Nombre para mostrar", f"Cámara {self.config.ip}")
        brand = self.get_input("Marca de la cámara", "generic")
        model = self.get_input("Modelo", "Unknown")
        location = self.get_input("Ubicación", "Sin especificar")
        
        try:
            # Crear datos de la cámara
            camera_data = {
                "display_name": display_name,
                "ip_address": self.config.ip,
                "brand": brand.lower(),
                "model": model,
                "location": location,
                "username": self.config.username,
                "password": self.config.password,
                "rtsp_port": self.config.rtsp_port,
                "onvif_port": self.config.onvif_port,
                "http_port": self.config.http_port
            }
            
            # Guardar usando el servicio
            result = await self.camera_manager.create_camera(camera_data)
            
            if result and result.get('success'):
                self.print_success(f"Cámara guardada con ID: {result.get('camera_id')}")
                
                # Guardar el endpoint RTSP descubierto
                await self.camera_manager.save_discovered_endpoint(
                    camera_id=result.get('camera_id'),
                    endpoint_type='rtsp_main',
                    url=rtsp_url,
                    name='Stream Principal'
                )
                
                return True
            else:
                self.print_error("No se pudo guardar la cámara")
                return False
                
        except Exception as e:
            self.print_error(f"Error guardando cámara: {e}")
            return False
            
    async def run(self):
        """Ejecuta el probador de conexiones."""
        self.print_header("PROBADOR UNIVERSAL DE CÁMARAS IP")
        print("Sistema de detección automática y prueba de streaming")
        
        # Recolectar información básica
        self.config = self.collect_connection_info()
        
        # Escanear puertos para ajustar configuración
        camera_info = await self.scan_camera_ports(self.config.ip)
        
        if not camera_info:
            print("\n¿Desea continuar sin escaneo de puertos?")
            cont = self.get_input("Continuar (s/n)", "s")
            if cont.lower() != 's':
                return
        
        # Auto-detectar protocolos
        supported_protocols = await self.auto_detect_protocols()
        
        if not supported_protocols:
            # Ofrecer prueba manual
            print("\n¿Desea intentar conexión RTSP manual?")
            manual = self.get_input("Continuar (s/n)", "s")
            
            if manual.lower() == 's':
                # Construir URLs RTSP comunes
                urls = [
                    {
                        'name': 'RTSP Genérico Stream 1',
                        'url': f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/stream1"
                    },
                    {
                        'name': 'RTSP Genérico Stream 2', 
                        'url': f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/stream2"
                    },
                    {
                        'name': 'Dahua Principal',
                        'url': f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/cam/realmonitor?channel=1&subtype=0"
                    },
                    {
                        'name': 'Hikvision Principal',
                        'url': f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/Streaming/Channels/101"
                    },
                    {
                        'name': 'TP-Link H264 HD',
                        'url': f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/h264_hd.sdp"
                    },
                    {
                        'name': 'TP-Link H264 VGA',
                        'url': f"rtsp://{self.config.username}:{self.config.password}@{self.config.ip}:{self.config.rtsp_port}/h264_vga.sdp"
                    }
                ]
                
                # Probar cada URL
                for url_info in urls:
                    print(f"\nProbando: {url_info['name']}...")
                    if await self.test_rtsp_stream(url_info['url'], url_info['name']):
                        await self.save_camera_if_desired(url_info['url'])
                        break
        else:
            # Usar el primer protocolo detectado
            protocol = supported_protocols[0]
            self.print_info(f"Usando protocolo: {protocol.value}")
            
            # Descubrir URLs RTSP
            rtsp_urls = await self.discover_rtsp_urls(protocol)
            
            if rtsp_urls:
                print(f"\nSe encontraron {len(rtsp_urls)} streams disponibles:")
                for i, url_info in enumerate(rtsp_urls):
                    print(f"{i+1}. {url_info['name']}")
                    
                print("0. Probar todos")
                choice = self.get_input("Seleccione stream para probar", "1")
                
                if choice == "0":
                    # Probar todos
                    for url_info in rtsp_urls:
                        if await self.test_rtsp_stream(url_info['url'], url_info['name']):
                            await self.save_camera_if_desired(url_info['url'])
                            break
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(rtsp_urls):
                        url_info = rtsp_urls[idx]
                        if await self.test_rtsp_stream(url_info['url'], url_info['name']):
                            await self.save_camera_if_desired(url_info['url'])
            else:
                self.print_error("No se encontraron URLs RTSP")
                
        print("\n" + "="*60)
        print(" Prueba finalizada")
        print("="*60)


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
    finally:
        # Limpiar servicios
        await tester.protocol_service.cleanup()


if __name__ == "__main__":
    # Ejecutar
    asyncio.run(main())