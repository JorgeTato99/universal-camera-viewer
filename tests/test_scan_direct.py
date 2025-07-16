"""
Prueba directa del modelo de escaneo real.
"""

import asyncio
import sys
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from models.scan_model import ScanModel, ScanMethod, ScanRange

async def test_direct_scan():
    """Prueba directa del modelo de escaneo."""
    print("="*60)
    print(" PRUEBA DIRECTA DE ESCANEO DE PUERTOS")
    print("="*60)
    
    # IP de la cámara TP-Link
    ip = "192.168.1.77"
    
    print(f"\nEscaneando cámara TP-Link en {ip}")
    print("Puertos: 443, 554, 80, 8080, 2020")
    
    # Crear rango de escaneo
    scan_range = ScanRange(
        start_ip=ip,
        end_ip=ip,
        ports=[443, 554, 80, 8080, 2020],
        timeout=3.0
    )
    
    # Crear modelo de escaneo
    scan_model = ScanModel(
        scan_id="test_scan_001",
        scan_range=scan_range,
        methods=[ScanMethod.PORT_SCAN],
        max_concurrent=5,
        timeout=3.0,
        include_offline=True
    )
    
    print("\nIniciando escaneo...")
    
    # Ejecutar escaneo de forma asíncrona
    result = await scan_model.start_scan_async()
    
    if result:
        print(f"\nEscaneo completado exitosamente")
        print(f"Estado: {scan_model.status.value}")
        print(f"Duración: {scan_model.duration_seconds:.2f} segundos")
        
        # Obtener todos los resultados
        all_results = scan_model.get_all_results()
        
        print(f"\nResultados totales: {len(all_results)}")
        
        # Buscar resultados para nuestra IP
        for result in all_results:
            if result['ip'] == ip:
                print(f"\nResultados para {ip}:")
                print(f"  - Viva: {result.get('is_alive', False)}")
                print(f"  - Puertos abiertos: {result.get('open_ports', [])}")
                print(f"  - Protocolos de cámara: {result.get('has_camera_protocols', False)}")
                print(f"  - Duración escaneo: {result.get('scan_duration_ms', 0):.2f} ms")
                
                # Verificar puertos esperados
                expected_ports = [443, 554]
                found_ports = result.get('open_ports', [])
                
                print("\nVerificación:")
                for port in expected_ports:
                    if port in found_ports:
                        print(f"  OK Puerto {port} detectado correctamente")
                    else:
                        print(f"  X Puerto {port} NO detectado")
                        
                for port in found_ports:
                    if port not in expected_ports:
                        print(f"  ? Puerto {port} detectado (adicional)")
                        
                # Mostrar estadísticas
                stats = scan_model.get_scan_stats()
                print(f"\nEstadísticas:")
                print(f"  - IPs escaneadas: {stats['results']['total_ips_scanned']}")
                print(f"  - Puertos abiertos totales: {stats['results']['total_open_ports']}")
                print(f"  - Progreso final: {stats['progress']['overall_progress']:.1f}%")
                
                break
        else:
            print(f"\nX No se encontraron resultados para {ip}")
    else:
        print("\nX El escaneo falló")
        
    # Limpiar recursos
    scan_model.cleanup()
    print("\nPrueba completada")


if __name__ == "__main__":
    try:
        asyncio.run(test_direct_scan())
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback
        traceback.print_exc()