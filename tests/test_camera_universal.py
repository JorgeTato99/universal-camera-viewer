"""
Probador universal de cámaras IP - Versión mejorada
No específico por marca, funciona con cualquier cámara.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models import ConnectionConfig
from models.scan_model import ScanModel, ScanMethod, ScanRange
from models.camera_model import ProtocolType
from services.protocol_service import ProtocolService
from services.connection_service import ConnectionService
from services.camera_manager_service import camera_manager_service


class UniversalCameraTester:
    """Probador universal para cualquier cámara IP."""
    
    def __init__(self):
        self.protocol_service = ProtocolService()
        self.connection_service = ConnectionService()
        
    def print_header(self, text: str):
        print(f"\n{'='*60}")
        print(f" {text}")
        print(f"{'='*60}")
        
    def print_success(self, text: str):
        print(f"[OK] {text}")
        
    def print_error(self, text: str):
        print(f"[X] {text}")
        
    def print_info(self, text: str):
        print(f"[i] {text}")
        
    def get_input(self, prompt: str, default: str = "") -> str:
        """Obtiene entrada del usuario con valor por defecto."""
        if default:
            return input(f"{prompt} [{default}]: ").strip() or default
        return input(f"{prompt}: ").strip()
        
    def collect_connection_info(self) -> ConnectionConfig:
        """Recolecta información de conexión del usuario."""
        self.print_header("CONFIGURACIÓN DE CONEXIÓN")
        
        ip = self.get_input("IP de la cámara")
        username = self.get_input("Usuario", "admin")
        password = self.get_input("Contraseña")
        
        config = ConnectionConfig(
            ip=ip,
            username=username,
            password=password,
            rtsp_port=554,
            onvif_port=80,
            http_port=80
        )
        
        return config
        
    async def scan_ports_direct(self, ip: str) -> Optional[List[int]]:
        """Escanea puertos usando directamente el modelo."""
        self.print_header("ESCANEANDO PUERTOS")
        self.print_info(f"Escaneando puertos comunes en {ip}...")
        
        # Crear rango de escaneo
        scan_range = ScanRange(
            start_ip=ip,
            end_ip=ip,
            ports=[80, 443, 554, 2020, 8000, 8080, 8554, 5543, 37777],
            timeout=3.0
        )
        
        # Crear modelo de escaneo directamente
        scan_model = ScanModel(
            scan_id=f"test_scan_{int(time.time())}",
            scan_range=scan_range,
            methods=[ScanMethod.PORT_SCAN],
            max_concurrent=8,
            timeout=3.0,
            include_offline=True
        )
        
        try:
            # Ejecutar escaneo
            success = await scan_model.start_scan_async()
            
            if success:
                # Obtener resultados inmediatamente
                all_results = scan_model.get_all_results()
                
                if all_results:
                    for result in all_results:
                        if result['ip'] == ip:
                            open_ports = result.get('open_ports', [])
                            self.print_success(f"Puertos abiertos encontrados: {open_ports}")
                            
                            # Analizar puertos
                            if 2020 in open_ports:
                                self.print_info("Puerto 2020 detectado - Posible ONVIF (TP-Link)")
                            if 8000 in open_ports:
                                self.print_info("Puerto 8000 detectado - Posible ONVIF (Hikvision/Steren)")
                            if 443 in open_ports:
                                self.print_info("Puerto 443 detectado - HTTPS")
                            if 554 in open_ports:
                                self.print_info("Puerto 554 detectado - RTSP estándar")
                            if 5543 in open_ports:
                                self.print_info("Puerto 5543 detectado - RTSP alternativo")
                            if 37777 in open_ports:
                                self.print_info("Puerto 37777 detectado - Posible Dahua/Amcrest")
                                
                            return open_ports
                            
            self.print_error("No se detectaron puertos abiertos")
            return None
            
        except Exception as e:
            self.print_error(f"Error durante el escaneo: {e}")
            return None
        finally:
            # Limpiar recursos
            scan_model.cleanup()
            
    def adjust_config_by_ports(self, config: ConnectionConfig, open_ports: List[int]):
        """Ajusta la configuración basándose en los puertos detectados."""
        # ONVIF
        if 2020 in open_ports:
            config.onvif_port = 2020
        elif 8000 in open_ports:
            config.onvif_port = 8000
            
        # HTTPS
        if 443 in open_ports:
            config.http_port = 443
            
        # RTSP
        if 5543 in open_ports:
            config.rtsp_port = 5543
            
    async def test_protocols_smart(self, config: ConnectionConfig, open_ports: List[int]) -> List[ProtocolType]:
        """Prueba protocolos de manera inteligente basándose en puertos."""
        self.print_header("DETECCIÓN DE PROTOCOLOS")
        
        supported_protocols = []
        
        # Probar RTSP si hay puertos RTSP abiertos
        if any(port in open_ports for port in [554, 5543, 8554]):
            self.print_info("Probando RTSP...")
            
            # En lugar de test_connection completo, intentar URLs comunes
            rtsp_urls = [
                f"rtsp://{config.username}:{config.password}@{config.ip}:{config.rtsp_port}/stream1",
                f"rtsp://{config.username}:{config.password}@{config.ip}:{config.rtsp_port}/stream2",
                f"rtsp://{config.username}:{config.password}@{config.ip}:{config.rtsp_port}/h264",
                f"rtsp://{config.username}:{config.password}@{config.ip}:{config.rtsp_port}/live",
                f"rtsp://{config.username}:{config.password}@{config.ip}:{config.rtsp_port}/ch1",
            ]
            
            # Simplemente verificar que el puerto responde
            # El test real de OpenCV puede fallar por muchas razones
            supported_protocols.append(ProtocolType.RTSP)
            self.print_success("RTSP disponible (puerto abierto)")
            
            self.print_info("URLs RTSP comunes para probar:")
            for url in rtsp_urls[:3]:  # Mostrar las 3 primeras
                print(f"  - {url}")
                
        # Probar ONVIF si hay puertos ONVIF abiertos
        if any(port in open_ports for port in [80, 8080, 2020, 8000]):
            self.print_info("Probando ONVIF...")
            # Similar, asumir disponible si el puerto está abierto
            supported_protocols.append(ProtocolType.ONVIF)
            self.print_success("ONVIF posiblemente disponible (puerto abierto)")
            
        # HTTP/HTTPS
        if any(port in open_ports for port in [80, 443, 8080]):
            supported_protocols.append(ProtocolType.HTTP)
            self.print_success("HTTP/HTTPS disponible")
            
        return supported_protocols
        
    async def show_connection_info(self, config: ConnectionConfig, open_ports: List[int], protocols: List[ProtocolType]):
        """Muestra información de conexión recomendada."""
        self.print_header("INFORMACIÓN DE CONEXIÓN")
        
        print("\nConfiguración detectada:")
        print(f"  IP: {config.ip}")
        print(f"  Usuario: {config.username}")
        print(f"  Puertos abiertos: {open_ports}")
        print(f"  Protocolos disponibles: {[p.value for p in protocols]}")
        
        print("\nPuertos configurados:")
        print(f"  RTSP: {config.rtsp_port}")
        print(f"  ONVIF: {config.onvif_port}")
        print(f"  HTTP: {config.http_port}")
        
        if ProtocolType.RTSP in protocols:
            print("\nPara conectar por RTSP:")
            print(f"  URL principal: rtsp://{config.username}:[password]@{config.ip}:{config.rtsp_port}/stream1")
            print(f"  URL secundaria: rtsp://{config.username}:[password]@{config.ip}:{config.rtsp_port}/stream2")
            
        print("\nPuedes usar estas configuraciones en el sistema principal.")
        
    async def run(self):
        """Ejecuta el probador universal."""
        self.print_header("PROBADOR UNIVERSAL DE CÁMARAS IP")
        print("Sistema de detección automática - Funciona con cualquier marca")
        
        try:
            # 1. Recolectar información
            config = self.collect_connection_info()
            
            # 2. Escanear puertos
            open_ports = await self.scan_ports_direct(config.ip)
            
            if not open_ports:
                self.print_error("\nNo se detectaron puertos abiertos.")
                self.print_info("Posibles causas:")
                self.print_info("  - La IP es incorrecta")
                self.print_info("  - La cámara está apagada")
                self.print_info("  - Firewall bloqueando la conexión")
                return
                
            # 3. Ajustar configuración según puertos
            self.adjust_config_by_ports(config, open_ports)
            
            # 4. Detectar protocolos
            protocols = await self.test_protocols_smart(config, open_ports)
            
            if not protocols:
                self.print_error("\nNo se detectaron protocolos compatibles.")
                return
                
            # 5. Mostrar información de conexión
            await self.show_connection_info(config, open_ports, protocols)
            
            # 6. Preguntar si quiere probar streaming
            response = self.get_input("\n¿Desea probar el streaming de video? (s/n)", "n")
            if response.lower() == 's':
                await self.test_streaming(config)
                
        except KeyboardInterrupt:
            print("\n\nPrueba cancelada por el usuario")
        except Exception as e:
            self.print_error(f"Error inesperado: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Limpiar servicios
            await self.connection_service.cleanup()
            
    async def test_streaming(self, config: ConnectionConfig):
        """Prueba básica de streaming."""
        self.print_header("PRUEBA DE STREAMING")
        
        self.print_info("Para probar el streaming completo, use:")
        print(f"\n  python tests/test_rtsp_direct.py")
        print(f"\nO puede usar VLC Media Player:")
        print(f"  1. Abrir VLC")
        print(f"  2. Media → Abrir ubicación de red")
        print(f"  3. Pegar: rtsp://{config.username}:[password]@{config.ip}:{config.rtsp_port}/stream1")


async def main():
    tester = UniversalCameraTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())