"""
Test del servicio de escaneo de red.
Prueba la funcionalidad del ScanService sin reimplementar lógica.
"""

import asyncio
import pytest
import sys
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from services.scan_service import scan_service
from models.scan_model import ScanMethod, ScanRange


async def test_scan_service_basic():
    """Prueba básica del servicio de escaneo."""
    print("\n" + "="*60)
    print(" TEST: Servicio de Escaneo")
    print("="*60)
    
    # IP de prueba (localhost siempre responde)
    test_ip = "127.0.0.1"
    
    # Configurar escaneo
    scan_range = ScanRange(
        start_ip=test_ip,
        end_ip=test_ip,
        ports=[80, 443, 8080],  # Puertos comunes en localhost
        timeout=2.0
    )
    
    print(f"\n1. Iniciando escaneo de {test_ip}")
    
    # Iniciar escaneo usando el servicio
    scan_id = await scan_service.start_scan_async(
        scan_range=scan_range,
        methods=[ScanMethod.PORT_SCAN],
        use_cache=False
    )
    
    print(f"   Escaneo iniciado con ID: {scan_id}")
    
    # Esperar a que complete
    print("\n2. Esperando resultados...")
    max_wait = 10
    waited = 0
    
    while waited < max_wait:
        status = scan_service.get_scan_status(scan_id)
        
        if status:
            print(f"   Estado: {status['status']}, Progreso: {status['progress']:.1f}%")
            
            if status['status'] in ['completed', 'cancelled', 'error']:
                break
                
        await asyncio.sleep(0.5)
        waited += 0.5
    
    # Obtener resultados usando el nuevo método
    print("\n3. Obteniendo resultados...")
    results = await scan_service.get_scan_results(scan_id)
    
    # Debug: verificar qué hay en completed_scans
    if scan_id in scan_service.completed_scans:
        print(f"   Escaneo encontrado en completed_scans")
        scan_data = scan_service.completed_scans[scan_id]
        print(f"   Tipo de 'results': {type(scan_data['results'])}")
        print(f"   Longitud de results: {len(scan_data['results'])}")
        print(f"   Contenido de results: {scan_data['results']}")
        print(f"   Camera results: {scan_data.get('camera_results', [])}")
        print(f"   Stats: {scan_data.get('stats', {})}")
            
    print(f"   Valor de results: {results}")
    
    if results is not None and len(results) > 0:
        print(f"   Resultados obtenidos: {len(results)} IP(s) escaneadas")
        
        for result in results:
            if result['ip'] == test_ip:
                print(f"\n   Resultados para {test_ip}:")
                print(f"   - Puertos escaneados: {scan_range.ports}")
                print(f"   - Puertos abiertos: {result.get('open_ports', [])}")
                
                # Verificar que el servicio funciona
                assert 'ip' in result
                assert 'open_ports' in result
                print("\n   [OK] Test pasado: El servicio devuelve resultados correctamente")
    else:
        print("   [X] No se obtuvieron resultados")
        
    # Verificar que el historial funciona
    history = scan_service.get_scan_history(limit=5)
    print(f"\n4. Historial de escaneos: {len(history)} entradas")
    
    print("\n" + "="*60)
    print(" Test completado")
    print("="*60)


async def test_scan_real_camera(ip: str = None):
    """
    Test con una cámara real (opcional).
    
    Args:
        ip: IP de la cámara a probar
    """
    if not ip:
        print("\nPara probar con una cámara real, proporcione una IP")
        return
        
    print(f"\n{'='*60}")
    print(f" TEST: Escaneo de Cámara Real")
    print(f"{'='*60}")
    
    # Configurar escaneo para cámara
    scan_range = ScanRange(
        start_ip=ip,
        end_ip=ip,
        ports=[80, 443, 554, 2020, 8000, 8080, 5543],
        timeout=3.0
    )
    
    print(f"\nEscaneando cámara en {ip}...")
    
    # Usar el servicio
    scan_id = await scan_service.start_scan_async(
        scan_range=scan_range,
        methods=[ScanMethod.PORT_SCAN]
    )
    
    # Esperar resultados
    completed = False
    for i in range(20):  # Max 10 segundos
        status = scan_service.get_scan_status(scan_id)
        if status and status['status'] == 'completed':
            completed = True
            break
        await asyncio.sleep(0.5)
    
    if completed:
        results = await scan_service.get_scan_results(scan_id)
        if results:
            for result in results:
                if result['ip'] == ip:
                    print(f"\nResultados:")
                    print(f"  - Puertos abiertos: {result.get('open_ports', [])}")
                    print(f"  - Es cámara: {result.get('has_camera_protocols', False)}")
                    
                    # Análisis de puertos
                    open_ports = result.get('open_ports', [])
                    if 554 in open_ports:
                        print("  - RTSP disponible (puerto 554)")
                    if 2020 in open_ports:
                        print("  - ONVIF TP-Link (puerto 2020)")
                    if 8000 in open_ports:
                        print("  - ONVIF Hikvision/Steren (puerto 8000)")


async def main():
    """Ejecuta los tests."""
    # Test básico siempre
    await test_scan_service_basic()
    
    # Test con cámara real si se proporciona IP
    if len(sys.argv) > 1:
        camera_ip = sys.argv[1]
        await test_scan_real_camera(camera_ip)
    else:
        print("\nTip: Puedes probar con una cámara real:")
        print("  python test_scan_service.py 192.168.1.77")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest cancelado")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Asegurar limpieza
        try:
            asyncio.run(scan_service.cleanup())
        except:
            pass