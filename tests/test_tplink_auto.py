"""
Script automatizado para probar la cámara TP-Link.
"""

import asyncio
import sys
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models import ConnectionConfig
from models.scan_model import ScanMethod, ScanRange
from services.scan_service import scan_service
from services.protocol_service import ProtocolService
from services.connection_service import ConnectionService
from services.camera_manager_service import camera_manager_service
from models.camera_model import ProtocolType

class TPLinkTester:
    def __init__(self):
        self.scan_service = scan_service
        self.protocol_service = ProtocolService()
        self.connection_service = ConnectionService()
        
        # Configuración de la cámara TP-Link
        self.config = ConnectionConfig(
            ip="192.168.1.77",
            username="admin-tato",
            password="mUidGT87gMxg8ce!Wxso3Guu8t.3*Q",
            rtsp_port=554,
            onvif_port=2020,
            http_port=443
        )
    
    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f" {text}")
        print(f"{'='*60}")
        
    def print_success(self, text):
        print(f"[OK] {text}")
        
    def print_error(self, text):
        print(f"[X] {text}")
        
    def print_info(self, text):
        print(f"[i] {text}")
        
    async def scan_ports(self):
        """Escanea puertos de la cámara."""
        self.print_header("ESCANEANDO PUERTOS")
        
        self.print_info(f"Escaneando {self.config.ip}...")
        
        # Crear rango de escaneo
        scan_range = ScanRange(
            start_ip=self.config.ip,
            end_ip=self.config.ip,
            ports=[80, 443, 554, 2020, 8000, 8080, 8554, 5543]
        )
        
        # Ejecutar escaneo
        scan_id = await self.scan_service.start_scan_async(
            scan_range=scan_range,
            methods=[ScanMethod.PORT_SCAN],
            priority=3,
            use_cache=False
        )
        
        # Esperar y capturar resultados
        max_wait = 10
        waited = 0
        all_results = None
        
        while waited < max_wait:
            status = self.scan_service.get_scan_status(scan_id)
            
            if scan_id in self.scan_service.active_scans and not all_results:
                scan_model = self.scan_service.active_scans[scan_id]
                if status and status.value == 'completed':
                    all_results = scan_model.get_all_results()
                    
            if status and status.value in ['completed', 'error', 'cancelled']:
                # Esperar un poco más para asegurar captura
                await asyncio.sleep(0.2)
                if not all_results and scan_id in self.scan_service.active_scans:
                    all_results = self.scan_service.active_scans[scan_id].get_all_results()
                break
                
            await asyncio.sleep(0.5)
            waited += 0.5
            
        # Procesar resultados
        if all_results and len(all_results) > 0:
            result = all_results[0]
            open_ports = result.get('open_ports', [])
            
            self.print_success(f"Puertos abiertos encontrados: {open_ports}")
            
            # Analizar puertos
            if 2020 in open_ports:
                self.print_info("Puerto 2020 detectado - ONVIF TP-Link")
            if 443 in open_ports:
                self.print_info("Puerto 443 detectado - HTTPS")
            if 554 in open_ports:
                self.print_info("Puerto 554 detectado - RTSP")
                
            return open_ports
        else:
            self.print_error("No se pudieron obtener resultados del escaneo")
            return []
            
    async def test_protocols(self):
        """Prueba los protocolos detectados."""
        self.print_header("PROBANDO PROTOCOLOS")
        
        # Detectar protocolos soportados
        supported_protocols = await self.protocol_service.detect_protocols(self.config)
        
        if supported_protocols:
            self.print_success(f"Protocolos detectados: {[p.value for p in supported_protocols]}")
            
            for protocol in supported_protocols:
                self.print_info(f"\nProbando protocolo {protocol.value}...")
                
                # Crear handler de conexión
                handler = await self.protocol_service.create_connection(
                    camera_id=f"test_{self.config.ip}",
                    protocol=protocol,
                    config=self.config
                )
                
                if handler:
                    self.print_success(f"Conexión {protocol.value} establecida")
                    
                    # Para ONVIF, obtener perfiles
                    if protocol == ProtocolType.ONVIF:
                        profiles = handler.get_profiles()
                        if profiles:
                            self.print_info(f"Perfiles ONVIF: {len(profiles) if isinstance(profiles, list) else 'N/A'}")
                            
                    # Para RTSP, obtener URL
                    elif protocol == ProtocolType.RTSP:
                        url = handler.get_stream_url()
                        if url:
                            self.print_success(f"URL RTSP: {url}")
                else:
                    self.print_error(f"No se pudo establecer conexión {protocol.value}")
        else:
            self.print_error("No se detectaron protocolos compatibles")
            
    async def test_streaming(self):
        """Prueba el streaming de video."""
        self.print_header("PROBANDO STREAMING")
        
        # Configurar conexión para streaming
        camera_id = f"test_{self.config.ip}"
        
        # Intentar conectar
        success = await self.connection_service.connect_camera(
            camera_id=camera_id,
            config=self.config,
            protocol=ProtocolType.RTSP
        )
        
        if success:
            self.print_success("Conexión establecida para streaming")
            
            # Obtener información de conexión
            connection_info = await self.connection_service.get_connection_info(camera_id)
            if connection_info:
                self.print_info(f"Estado: {connection_info.get('status')}")
                self.print_info(f"Protocolo: {connection_info.get('protocol')}")
                
                endpoints = connection_info.get('endpoints', [])
                for endpoint in endpoints:
                    self.print_info(f"Endpoint {endpoint.get('name')}: {endpoint.get('url')}")
        else:
            self.print_error("No se pudo establecer conexión para streaming")
            
    async def run(self):
        """Ejecuta todas las pruebas."""
        self.print_header("PRUEBA AUTOMATIZADA - TP-LINK TAPO C520WS")
        
        self.print_info(f"IP: {self.config.ip}")
        self.print_info(f"Usuario: {self.config.username}")
        self.print_info("Contraseña: ***")
        
        try:
            # 1. Escanear puertos
            open_ports = await self.scan_ports()
            
            if not open_ports:
                self.print_error("\nNo se detectaron puertos abiertos. Abortando pruebas.")
                return
                
            # 2. Probar protocolos
            await self.test_protocols()
            
            # 3. Probar streaming
            await self.test_streaming()
            
            self.print_header("PRUEBA COMPLETADA")
            self.print_success("Todas las pruebas ejecutadas")
            
        except Exception as e:
            self.print_error(f"Error durante las pruebas: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Limpiar servicios
            await self.scan_service.cleanup()
            await self.connection_service.cleanup()


async def main():
    tester = TPLinkTester()
    await tester.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback
        traceback.print_exc()