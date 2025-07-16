"""
Prueba directa del servicio de escaneo.
Usa el servicio en lugar de acceder directamente al modelo.
"""

import asyncio
import sys
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from services.scan_service import scan_service
from models.scan_model import ScanMethod, ScanRange


async def test_direct_scan():
    """Prueba directa del servicio de escaneo."""
    print("="*60)
    print(" PRUEBA DIRECTA DE ESCANEO DE PUERTOS")
    print("="*60)
    
    # IP de prueba (puedes cambiarla)
    ip = "192.168.1.77"
    
    print(f"\nEscaneando {ip}")
    print("Puertos: 443, 554, 80, 8080, 2020")
    
    # Crear rango de escaneo
    scan_range = ScanRange(
        start_ip=ip,
        end_ip=ip,
        ports=[80, 443, 554, 2020, 8080],
        timeout=3.0
    )
    
    print("\nIniciando escaneo...")
    
    # Iniciar escaneo usando el servicio
    scan_id = await scan_service.start_scan_async(
        scan_range=scan_range,
        methods=[ScanMethod.PORT_SCAN],
        use_cache=False
    )
    
    print(f"Escaneo iniciado con ID: {scan_id}")
    
    # Esperar a que complete
    print("\nEsperando resultados...")
    completed = False
    
    for i in range(20):  # Máximo 10 segundos
        status = scan_service.get_scan_status(scan_id)
        
        if status:
            print(f"  Estado: {status['status']}, Progreso: {status['progress']:.1f}%")
            
            if status['status'] in ['completed', 'cancelled', 'error']:
                completed = True
                print(f"\nEstado final: {status['status']}")
                print(f"Duración: {status.get('elapsed_time', 0):.2f} segundos")
                break
                
        await asyncio.sleep(0.5)
    
    if completed:
        # Obtener resultados usando el servicio
        results = await scan_service.get_scan_results(scan_id)
        
        if results:
            print(f"\nResultados totales: {len(results)}")
            
            # Buscar resultados para nuestra IP
            for result in results:
                if result['ip'] == ip:
                    print(f"\nResultados para {ip}:")
                    print(f"  - Viva: {result.get('is_alive', False)}")
                    print(f"  - Puertos abiertos: {result.get('open_ports', [])}")
                    print(f"  - Tiene protocolos de cámara: {result.get('has_camera_protocols', False)}")
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
                    
                    break
            else:
                print(f"\nX No se encontraron resultados para {ip}")
        else:
            print("\nX No se obtuvieron resultados del servicio")
    else:
        print("\nX El escaneo no se completó en el tiempo esperado")
        
    # Mostrar estadísticas del servicio
    active_scans = scan_service.get_active_scans()
    print(f"\nEscaneos activos: {len(active_scans)}")
    
    history = scan_service.get_scan_history(limit=3)
    print(f"Historial reciente: {len(history)} entradas")
    
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
    finally:
        # Limpiar servicio si es necesario
        try:
            asyncio.run(scan_service.cleanup())
        except:
            pass