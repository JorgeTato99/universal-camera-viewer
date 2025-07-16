"""
Script de prueba para verificar el escaneo real de puertos.
Prueba específicamente con la cámara TP-Link en 192.168.1.77
"""

import asyncio
import sys
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

from services.scan_service import scan_service
from models.scan_model import ScanMethod, ScanRange

async def test_real_scan():
    """Prueba el escaneo real de puertos."""
    print("="*60)
    print(" PRUEBA DE ESCANEO REAL DE PUERTOS")
    print("="*60)
    
    # IP de la cámara TP-Link
    ip = "192.168.1.77"
    
    print(f"\nEscaneando cámara TP-Link en {ip}")
    print("Puertos a escanear: 443, 554")
    
    try:
        # Crear rango de escaneo
        scan_range = ScanRange(
            start_ip=ip,
            end_ip=ip,
            ports=[443, 554, 80, 8080, 2020],  # Incluir más puertos para ver diferencia
            timeout=5.0
        )
        
        # Iniciar escaneo
        print("\nIniciando escaneo...")
        scan_id = await scan_service.start_scan_async(
            scan_range=scan_range,
            methods=[ScanMethod.PORT_SCAN]
        )
        
        print(f"Escaneo iniciado con ID: {scan_id}")
        
        # Monitorear progreso
        print("\nProgreso:")
        last_progress = -1
        final_results = None
        
        while True:
            # No usar await, get_scan_status es síncrono
            status = scan_service.get_scan_status(scan_id)
            if not status:
                break
                
            # Obtener progreso del modelo
            if scan_id in scan_service.active_scans:
                model = scan_service.active_scans[scan_id]
                progress = model.progress.overall_progress_percentage
                
                # Mostrar progreso solo si cambió
                if int(progress) > last_progress:
                    last_progress = int(progress)
                    print(f"  {int(progress)}% - Escaneando puerto {model.progress.scanned_ports}/{model.progress.total_ports}")
                
                # Si está por completarse, capturar resultados
                if status.value == "completed" and not final_results:
                    final_results = model.get_all_results()
            
            # Verificar si terminó (status es un enum)
            if status.value in ["completed", "cancelled", "error"]:
                print(f"\nEstado final: {status.value}")
                break
                
            await asyncio.sleep(0.5)
        
        # Obtener resultados
        print("\nObteniendo resultados...")
        
        # Usar los resultados capturados antes de que se eliminara el modelo
        if final_results:
            # Buscar resultados para nuestra IP
            scan_result = None
            for result in final_results:
                if result['ip'] == ip:
                    scan_result = result
                    break
            
            if scan_result:
                print(f"\nResultados para {ip}:")
                print(f"  - Puertos abiertos: {scan_result.get('open_ports', [])}")
                print(f"  - Viva: {scan_result.get('is_alive', False)}")
                
                # Comparar con lo esperado
                expected_ports = [443, 554]
                found_ports = scan_result.get('open_ports', [])
            
                print("\nVerificación:")
                for port in expected_ports:
                    if port in found_ports:
                        print(f"  OK Puerto {port} detectado correctamente")
                    else:
                        print(f"  X Puerto {port} NO detectado (esperado abierto)")
                        
                for port in found_ports:
                    if port not in expected_ports:
                        print(f"  ? Puerto {port} detectado (no esperado)")
            else:
                print(f"\nX No se obtuvieron resultados para {ip}")
        else:
            print(f"\nX No se pudieron capturar los resultados del escaneo")
            
    except Exception as e:
        print(f"\nError durante el escaneo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpiar
        # No necesita cleanup, scan_service maneja su propio ciclo de vida
        pass


if __name__ == "__main__":
    try:
        asyncio.run(test_real_scan())
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback
        traceback.print_exc()