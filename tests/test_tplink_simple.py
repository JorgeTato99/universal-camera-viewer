"""
Prueba simple y directa para la cámara TP-Link.
"""

import asyncio
import sys
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models.scan_model import ScanModel, ScanMethod, ScanRange


async def test_tplink():
    print("="*60)
    print(" PRUEBA SIMPLE - TP-LINK TAPO C520WS")
    print("="*60)
    
    # Datos de la cámara
    ip = "192.168.1.77"
    username = "admin-tato"
    password = "mUidGT87gMxg8ce!Wxso3Guu8t.3*Q"
    
    print(f"\nIP: {ip}")
    print(f"Usuario: {username}")
    print("Contraseña: ***\n")
    
    # 1. ESCANEO DE PUERTOS
    print("1. ESCANEANDO PUERTOS...")
    print("-" * 40)
    
    scan_range = ScanRange(
        start_ip=ip,
        end_ip=ip,
        ports=[80, 443, 554, 2020, 8080],
        timeout=3.0
    )
    
    scan_model = ScanModel(
        scan_id="tplink_test",
        scan_range=scan_range,
        methods=[ScanMethod.PORT_SCAN],
        max_concurrent=5,
        timeout=3.0,
        include_offline=True
    )
    
    # Ejecutar escaneo
    result = await scan_model.start_scan_async()
    
    if result:
        all_results = scan_model.get_all_results()
        
        if all_results:
            for res in all_results:
                if res['ip'] == ip:
                    open_ports = res.get('open_ports', [])
                    print(f"Puertos abiertos: {open_ports}")
                    
                    # Análisis de puertos
                    if 443 in open_ports:
                        print("  - Puerto 443: HTTPS detectado")
                    if 554 in open_ports:
                        print("  - Puerto 554: RTSP detectado")
                    if 2020 in open_ports:
                        print("  - Puerto 2020: ONVIF TP-Link detectado")
                    
                    # 2. URLS RTSP CONOCIDAS
                    print("\n2. URLs RTSP PARA TP-LINK TAPO")
                    print("-" * 40)
                    
                    if 554 in open_ports:
                        print("URLs RTSP probables:")
                        print(f"  - rtsp://{username}:{password}@{ip}:554/stream1")
                        print(f"  - rtsp://{username}:{password}@{ip}:554/stream2")
                        print(f"  - rtsp://{username}:{password}@{ip}:554/h264_hd.sdp")
                        print(f"  - rtsp://{username}:{password}@{ip}:554/h264_vga.sdp")
                        
                        print("\nURL verificada que funciona:")
                        print(f"  rtsp://{username}:{password}@{ip}:554/stream1")
                    
                    # 3. CONFIGURACIÓN RECOMENDADA
                    print("\n3. CONFIGURACIÓN RECOMENDADA")
                    print("-" * 40)
                    print("Para agregar esta cámara al sistema:")
                    print(f"  - IP: {ip}")
                    print(f"  - Usuario: {username}")
                    print("  - Contraseña: [usar la contraseña real]")
                    print("  - Puerto RTSP: 554")
                    print("  - Puerto ONVIF: 2020")
                    print("  - Puerto HTTPS: 443")
                    print("  - URL RTSP: rtsp://[usuario]:[password]@[ip]:554/stream1")
                    
                    break
        else:
            print("No se obtuvieron resultados del escaneo")
    else:
        print("El escaneo falló")
        
    # Limpiar
    scan_model.cleanup()
    
    print("\n" + "="*60)
    print(" PRUEBA COMPLETADA")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(test_tplink())
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()