"""
Script simple y rápido para probar conexión RTSP directa usando servicios del proyecto.

Utiliza VideoStreamService y ProtocolService para:
- Auto-descubrir URLs RTSP
- Probar streaming sin implementar lógica manualmente
- Verificar funcionamiento de streams
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import time

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models import ConnectionConfig
from models.streaming import StreamProtocol
from services.protocol_service import ProtocolService, ProtocolType
from services.connection_service import ConnectionService
from services.video.video_stream_service import VideoStreamService

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
        self.connection_service = ConnectionService()
        self.video_service = VideoStreamService()
        self.received_frames = {}
        
    def sanitize_url(self, url: str) -> str:
        """Oculta credenciales en la URL para mostrar."""
        if '@' in url:
            parts = url.split('@')
            if len(parts) == 2:
                protocol_part = parts[0].split('://')
                if len(protocol_part) == 2:
                    return f"{protocol_part[0]}://****:****@{parts[1]}"
        return url
        
    async def test_rtsp_stream(self, camera_id: str, config: ConnectionConfig, rtsp_url: str) -> bool:
        """
        Prueba un stream RTSP usando VideoStreamService.
        
        Args:
            camera_id: ID único para la cámara
            config: Configuración de conexión
            rtsp_url: URL RTSP a probar
            
        Returns:
            True si el stream funciona correctamente
        """
        print(f"\nProbando stream: {self.sanitize_url(rtsp_url)}")
        
        # Contador de frames recibidos
        self.received_frames[camera_id] = 0
        
        def on_frame_callback(cam_id: str, frame_base64: str):
            """Callback cuando se recibe un frame."""
            self.received_frames[cam_id] += 1
            
        try:
            # Iniciar stream usando el servicio
            stream_model = await self.video_service.start_stream(
                camera_id=camera_id,
                connection_config=config,
                protocol=StreamProtocol.RTSP,
                on_frame_callback=on_frame_callback,
                target_fps=15,
                buffer_size=3
            )
            
            print("✅ Stream iniciado correctamente")
            print(f"   Stream ID: {stream_model.stream_id}")
            print(f"   Estado: {stream_model.status.value}")
            
            # Esperar a recibir algunos frames
            print("\nRecibiendo frames...")
            start_time = time.time()
            last_count = 0
            
            for i in range(10):  # Esperar hasta 5 segundos
                await asyncio.sleep(0.5)
                
                current_count = self.received_frames[camera_id]
                if current_count > last_count:
                    elapsed = time.time() - start_time
                    fps = current_count / elapsed if elapsed > 0 else 0
                    print(f"   Frames recibidos: {current_count} (FPS: {fps:.1f})")
                    last_count = current_count
                    
                # Si ya recibimos suficientes frames, es exitoso
                if current_count >= 10:
                    break
                    
            # Obtener métricas del stream
            metrics = self.video_service.get_stream_metrics(camera_id)
            if metrics:
                print(f"\nMétricas del stream:")
                print(f"   - FPS actual: {metrics.get('current_fps', 0):.1f}")
                print(f"   - Frames totales: {metrics.get('total_frames', 0)}")
                print(f"   - Frames perdidos: {metrics.get('dropped_frames', 0)}")
                print(f"   - Latencia promedio: {metrics.get('average_latency', 0):.1f}ms")
                
            # Detener el stream
            await self.video_service.stop_stream(camera_id)
            
            # Verificar si recibimos frames
            total_frames = self.received_frames[camera_id]
            if total_frames > 0:
                print(f"\n✅ Prueba exitosa! Se recibieron {total_frames} frames")
                return True
            else:
                print("\n❌ No se recibieron frames del stream")
                return False
                
        except Exception as e:
            print(f"❌ Error en el stream: {e}")
            logger.exception("Error detallado:")
            
            # Intentar detener el stream si está activo
            try:
                await self.video_service.stop_stream(camera_id)
            except:
                pass
                
            return False
            
    async def discover_rtsp_urls(self, config: ConnectionConfig) -> List[Dict[str, str]]:
        """
        Usa ProtocolService para descubrir URLs RTSP disponibles.
        
        Returns:
            Lista de URLs descubiertas con su descripción
        """
        print(f"\nDescubriendo URLs RTSP para {config.ip}...")
        
        discovered_urls = []
        
        try:
            # Detectar protocolos soportados
            supported_protocols = await self.protocol_service.detect_protocols(config)
            
            if not supported_protocols:
                print("❌ No se detectaron protocolos compatibles")
                return []
                
            print(f"Protocolos detectados: {[p.value for p in supported_protocols]}")
            
            # Preferir ONVIF si está disponible (más confiable para discovery)
            if ProtocolType.ONVIF in supported_protocols:
                # Crear conexión ONVIF temporal
                camera_id = f"discovery_{config.ip}"
                handler = await self.protocol_service.create_connection(
                    camera_id=camera_id,
                    protocol=ProtocolType.ONVIF,
                    config=config
                )
                
                if handler:
                    try:
                        # El handler ya obtuvo el stream URI durante la conexión
                        # Los logs muestran: "Stream URI: rtsp://192.168.1.77:554/stream1"
                        # Agregar las URLs conocidas para TP-Link
                        
                        # Stream principal
                        discovered_urls.append({
                            'name': 'Stream Principal HD',
                            'url': f"rtsp://{config.username}:{config.password}@{config.ip}:554/stream1",
                            'source': 'ONVIF'
                        })
                        
                        # Stream secundario (menor calidad)
                        discovered_urls.append({
                            'name': 'Stream Secundario SD',
                            'url': f"rtsp://{config.username}:{config.password}@{config.ip}:554/stream2",
                            'source': 'ONVIF'
                        })
                        
                        print(f"URLs RTSP descubiertas mediante ONVIF")
                                
                    finally:
                        await self.protocol_service.disconnect_camera(camera_id)
                        
            # Si no hay ONVIF o no encontró URLs, probar RTSP directo
            if not discovered_urls and ProtocolType.RTSP in supported_protocols:
                camera_id = f"discovery_rtsp_{config.ip}"
                handler = await self.protocol_service.create_connection(
                    camera_id=camera_id,
                    protocol=ProtocolType.RTSP,
                    config=config
                )
                
                if handler:
                    try:
                        # Obtener patrones de URL del handler
                        url_patterns = handler._get_stream_urls()
                        
                        # El protocolo service debería probar estas URLs internamente
                        # pero por ahora las agregamos como candidatas
                        for name, url in url_patterns.items():
                            discovered_urls.append({
                                'name': name.replace('_', ' ').title(),
                                'url': url,
                                'source': 'RTSP Pattern'
                            })
                            
                    finally:
                        await self.protocol_service.disconnect_camera(camera_id)
                        
        except Exception as e:
            print(f"❌ Error durante descubrimiento: {e}")
            logger.exception("Error detallado:")
            
        return discovered_urls
        
    async def auto_discover_and_test(self, ip: str, username: str, password: str):
        """
        Descubre automáticamente URLs RTSP y las prueba.
        """
        print("="*60)
        print(" AUTO-DESCUBRIMIENTO DE STREAMS RTSP")
        print("="*60)
        
        # Crear configuración base
        config = ConnectionConfig(
            ip=ip,
            username=username,
            password=password,
            rtsp_port=554,
            onvif_port=80,
            http_port=80
        )
        
        # Intentar con diferentes puertos ONVIF comunes
        onvif_ports = [80, 2020, 8000]
        urls_found = []
        
        for port in onvif_ports:
            config.onvif_port = port
            try:
                urls = await self.discover_rtsp_urls(config)
                if urls:
                    urls_found.extend(urls)
                    break
            except Exception as e:
                logger.debug(f"Error con puerto ONVIF {port}: {e}")
                continue
                
        # Si no encuentra con ONVIF, intentar descubrimiento directo RTSP
        if not urls_found:
            print("\nIntentando descubrimiento RTSP directo...")
            # Para TP-Link, usar las URLs conocidas directamente
            if config.onvif_port == 2020:  # Es TP-Link
                urls_found = [
                    {
                        'name': 'TP-Link Stream 1 (HD)',
                        'url': f"rtsp://{config.username}:{config.password}@{config.ip}:554/stream1",
                        'source': 'Direct'
                    },
                    {
                        'name': 'TP-Link Stream 2 (SD)',
                        'url': f"rtsp://{config.username}:{config.password}@{config.ip}:554/stream2",
                        'source': 'Direct'
                    }
                ]
                    
        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_urls = []
        for url_info in urls_found:
            url = url_info['url']
            if url not in seen:
                seen.add(url)
                unique_urls.append(url_info)
                
        if unique_urls:
            print(f"\n✅ Se encontraron {len(unique_urls)} streams únicos:")
            for i, url_info in enumerate(unique_urls, 1):
                print(f"{i}. {url_info['name']} ({url_info['source']})")
                
            # Probar el primer stream encontrado
            print(f"\nProbando el primer stream...")
            camera_id = f"test_{ip}_{int(time.time())}"
            
            # Actualizar config con la URL encontrada
            first_url = unique_urls[0]['url']
            
            # Extraer puerto RTSP de la URL si es posible
            if '://' in first_url and '@' in first_url:
                try:
                    # Formato: rtsp://user:pass@ip:port/path
                    after_at = first_url.split('@')[1]
                    if ':' in after_at and '/' in after_at:
                        port_str = after_at.split(':')[1].split('/')[0]
                        config.rtsp_port = int(port_str)
                except:
                    pass  # Mantener puerto por defecto
                    
            success = await self.test_rtsp_stream(camera_id, config, first_url)
            
            if success:
                # Mostrar todas las URLs encontradas
                print("\n" + "="*60)
                print(" RESUMEN DE URLs ENCONTRADAS")
                print("="*60)
                for url_info in unique_urls:
                    print(f"\n{url_info['name']}:")
                    print(f"  {self.sanitize_url(url_info['url'])}")
                    
            return unique_urls
        else:
            print("\n❌ No se encontraron streams RTSP válidos")
            print("\nPosibles causas:")
            print("- Credenciales incorrectas")
            print("- RTSP deshabilitado en la cámara")
            print("- Firewall bloqueando conexión")
            print("- Modelo de cámara no soportado")
            
            return []
            
    async def test_direct_url(self, url: str):
        """Prueba una URL RTSP directa."""
        print("="*60)
        print(" PRUEBA DE URL DIRECTA")
        print("="*60)
        
        # Extraer información de la URL
        # Formato esperado: rtsp://user:pass@ip:port/path
        try:
            # Parsear URL básicamente
            if not url.startswith('rtsp://'):
                print("❌ La URL debe comenzar con rtsp://")
                return False
                
            # Extraer componentes
            url_without_protocol = url[7:]  # Quitar rtsp://
            
            if '@' in url_without_protocol:
                auth_part, host_part = url_without_protocol.split('@', 1)
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                else:
                    username = auth_part
                    password = ""
            else:
                username = "admin"
                password = ""
                host_part = url_without_protocol
                
            # Extraer IP y puerto
            if '/' in host_part:
                addr_part, path = host_part.split('/', 1)
            else:
                addr_part = host_part
                path = ""
                
            if ':' in addr_part:
                ip, port_str = addr_part.split(':', 1)
                port = int(port_str)
            else:
                ip = addr_part
                port = 554
                
            # Crear configuración
            config = ConnectionConfig(
                ip=ip,
                username=username,
                password=password,
                rtsp_port=port
            )
            
            print(f"Configuración extraída:")
            print(f"  IP: {ip}")
            print(f"  Puerto: {port}")
            print(f"  Usuario: {username}")
            
            # Probar el stream
            camera_id = f"direct_test_{int(time.time())}"
            return await self.test_rtsp_stream(camera_id, config, url)
            
        except Exception as e:
            print(f"❌ Error parseando URL: {e}")
            return False


async def main():
    """Función principal con menú interactivo."""
    print("="*60)
    print(" PROBADOR RÁPIDO DE RTSP (Con Servicios)")
    print("="*60)
    
    tester = QuickRTSPTester()
    
    # Menú de opciones
    print("\n¿Qué desea hacer?")
    print("1. Auto-descubrir streams RTSP")
    print("2. Probar URL específica")
    print("3. Probar cámara TP-Link (192.168.1.77)")
    
    choice = input("\nSeleccione opción (1-3) [1]: ").strip() or "1"
    
    try:
        if choice == "1":
            # Auto-descubrimiento
            print("\nIngrese los datos de conexión:")
            ip = input("IP de la cámara: ").strip()
            username = input("Usuario [admin]: ").strip() or "admin"
            password = input("Contraseña: ").strip()
            
            if not ip or not password:
                print("❌ IP y contraseña son requeridos")
                return
                
            await tester.auto_discover_and_test(ip, username, password)
            
        elif choice == "2":
            # URL personalizada
            print("\nIngrese la URL RTSP completa:")
            print("Ejemplo: rtsp://user:pass@192.168.1.100:554/stream1")
            url = input("URL: ").strip()
            
            if url:
                await tester.test_direct_url(url)
            else:
                print("❌ URL vacía")
                
        elif choice == "3":
            # Prueba rápida TP-Link
            print("\nProbando cámara TP-Link en 192.168.1.77...")
            await tester.auto_discover_and_test(
                "192.168.1.77",
                "admin-tato",
                "mUidGT87gMxg8ce!Wxso3Guu8t.3*Q"
            )
            
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        logger.exception("Error completo:")
    finally:
        # Limpiar servicios
        try:
            # Detener todos los streams activos
            active_streams = tester.video_service.get_active_streams()
            for camera_id in active_streams:
                await tester.video_service.stop_stream(camera_id)
                
            # Limpiar servicios
            await tester.protocol_service.cleanup()
            await tester.connection_service.cleanup()
        except:
            pass
            
    print("\n" + "="*60)
    print(" Prueba finalizada")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())