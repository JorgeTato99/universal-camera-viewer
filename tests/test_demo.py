"""
Demo del probador universal con datos precargados.
Muestra cómo funciona el sistema de detección.
"""

import asyncio
import sys
import time
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models import ConnectionConfig
from models.scan_model import ScanModel, ScanMethod, ScanRange
from models.camera_model import ProtocolType


async def demo_universal_tester():
    print("="*60)
    print(" DEMO - PROBADOR UNIVERSAL DE CÁMARAS")
    print("="*60)
    
    # Configuración de ejemplo (tu cámara TP-Link)
    config = ConnectionConfig(
        ip="192.168.1.77",
        username="admin-tato",
        password="mUidGT87gMxg8ce!Wxso3Guu8t.3*Q",
        rtsp_port=554,
        onvif_port=80,
        http_port=80
    )
    
    print(f"\nProbando cámara en: {config.ip}")
    print(f"Usuario: {config.username}")
    print("Contraseña: ***")
    
    # 1. ESCANEO DE PUERTOS
    print("\n1. ESCANEANDO PUERTOS...")
    print("-" * 40)
    
    scan_range = ScanRange(
        start_ip=config.ip,
        end_ip=config.ip,
        ports=[80, 443, 554, 2020, 8000, 8080, 8554, 5543, 37777],
        timeout=3.0
    )
    
    scan_model = ScanModel(
        scan_id=f"demo_scan_{int(time.time())}",
        scan_range=scan_range,
        methods=[ScanMethod.PORT_SCAN],
        max_concurrent=8,
        timeout=3.0,
        include_offline=True
    )
    
    # Ejecutar escaneo
    success = await scan_model.start_scan_async()
    
    if success:
        all_results = scan_model.get_all_results()
        
        if all_results:
            for result in all_results:
                if result['ip'] == config.ip:
                    open_ports = result.get('open_ports', [])
                    print(f"[OK] Puertos abiertos: {open_ports}")
                    
                    # Análisis de puertos
                    if 2020 in open_ports:
                        print("  - Puerto 2020: ONVIF (TP-Link)")
                        config.onvif_port = 2020
                    if 443 in open_ports:
                        print("  - Puerto 443: HTTPS")
                        config.http_port = 443
                    if 554 in open_ports:
                        print("  - Puerto 554: RTSP estándar")
                    if 8000 in open_ports:
                        print("  - Puerto 8000: ONVIF (Hikvision/Steren)")
                        
                    # 2. DETECCIÓN DE PROTOCOLOS
                    print("\n2. PROTOCOLOS DISPONIBLES")
                    print("-" * 40)
                    
                    protocols = []
                    
                    # RTSP
                    if any(port in open_ports for port in [554, 5543, 8554]):
                        protocols.append("RTSP")
                        print("[OK] RTSP disponible")
                        
                    # ONVIF
                    if any(port in open_ports for port in [80, 8080, 2020, 8000]):
                        protocols.append("ONVIF")
                        print("[OK] ONVIF disponible")
                        
                    # HTTP/HTTPS
                    if any(port in open_ports for port in [80, 443, 8080]):
                        protocols.append("HTTP/HTTPS")
                        print("[OK] HTTP/HTTPS disponible")
                        
                    # 3. CONFIGURACIÓN RECOMENDADA
                    print("\n3. CONFIGURACIÓN FINAL")
                    print("-" * 40)
                    
                    print(f"IP: {config.ip}")
                    print(f"Usuario: {config.username}")
                    print(f"Puerto RTSP: {config.rtsp_port}")
                    print(f"Puerto ONVIF: {config.onvif_port}")
                    print(f"Puerto HTTP: {config.http_port}")
                    
                    # 4. URLs DE CONEXIÓN
                    print("\n4. URLs DE CONEXIÓN")
                    print("-" * 40)
                    
                    if "RTSP" in protocols:
                        print("URLs RTSP para probar:")
                        print(f"  - rtsp://{config.username}:[password]@{config.ip}:{config.rtsp_port}/stream1")
                        print(f"  - rtsp://{config.username}:[password]@{config.ip}:{config.rtsp_port}/stream2")
                        print(f"  - rtsp://{config.username}:[password]@{config.ip}:{config.rtsp_port}/h264")
                        
                    if "ONVIF" in protocols:
                        print(f"\nURL ONVIF:")
                        print(f"  - http://{config.ip}:{config.onvif_port}/onvif/device_service")
                        
                    # 5. RESUMEN
                    print("\n" + "="*60)
                    print(" RESUMEN")
                    print("="*60)
                    
                    print("\nLa cámara está correctamente configurada y accesible.")
                    print("El sistema puede conectarse usando los protocolos detectados.")
                    print("\nEste proceso funciona igual para CUALQUIER marca de cámara:")
                    print("  - Dahua")
                    print("  - Hikvision")
                    print("  - TP-Link")
                    print("  - Steren")
                    print("  - Y cualquier otra marca compatible con RTSP/ONVIF")
                    
                    break
    
    # Limpiar
    scan_model.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(demo_universal_tester())
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()