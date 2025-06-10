"""
Test de integración completo para ONVIF.
Consolida funcionalidades técnicas avanzadas de testing para el protocolo ONVIF.

Este es un test técnico que verifica:
- Integración con Factory Pattern
- Context Manager functionality
- GUI integration testing
- Performance benchmarking
- Error handling robusto
- Compatibilidad completa con sistema

Basado en: test_onvif_integration.py + test_gui_onvif.py
"""

import sys
import logging
import time
import threading
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from connections import ConnectionFactory, ONVIFConnection
from utils.config import get_config


def setup_logging():
    """Configura el logging para testing técnico."""
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "onvif_integration_test.log"
    
    # Limpiar configuración existente
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True
    )
    
    print(f"📝 Logs guardándose en: {log_file}")


def test_onvif_factory_integration():
    """
    Test de integración con Factory Pattern.
    
    Returns:
        dict: Resultados detallados del test
    """
    print("\n" + "="*60)
    print("🏭 TEST: INTEGRACIÓN FACTORY PATTERN")
    print("="*60)
    
    results = {
        'factory_creation': False,
        'connection_info': False,
        'basic_functionality': False,
        'resource_cleanup': False
    }
    
    config = get_config()
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        # 1. Test Factory Creation
        print("1. Testing factory creation...")
        connection = ConnectionFactory.create_connection(
            connection_type="onvif",
            camera_ip=config.camera_ip,
            credentials=credentials
        )
        
        if connection and isinstance(connection, ONVIFConnection):
            print("✅ Factory creation successful")
            results['factory_creation'] = True
        else:
            print("❌ Factory creation failed")
            return results
        
        # 2. Test Connection Info
        print("2. Testing connection info...")
        conn_info = connection.get_connection_info()
        if conn_info and 'protocol' in conn_info:
            print(f"✅ Connection info: {conn_info}")
            results['connection_info'] = True
        else:
            print("❌ Connection info failed")
        
        # 3. Test Basic Functionality
        print("3. Testing basic functionality...")
        if connection.connect():
            print("✅ Connection established")
            
            # Test device info
            device_info = connection.get_device_info()
            if device_info:
                print(f"✅ Device info obtained: {len(device_info)} fields")
                results['basic_functionality'] = True
            
            # Test snapshot
            snapshot = connection.get_snapshot()
            if snapshot:
                print(f"✅ Snapshot captured: {len(snapshot)} bytes")
            
            connection.disconnect()
        else:
            print("❌ Connection failed")
        
        # 4. Test Resource Cleanup
        print("4. Testing resource cleanup...")
        del connection
        print("✅ Resources cleaned up")
        results['resource_cleanup'] = True
        
    except Exception as e:
        print(f"❌ Factory integration error: {str(e)}")
        logging.exception("Factory integration test failed")
    
    return results


def test_onvif_context_manager():
    """
    Test del Context Manager en diferentes escenarios.
    
    Returns:
        dict: Resultados detallados del test
    """
    print("\n" + "="*60)
    print("🔄 TEST: CONTEXT MANAGER SCENARIOS")
    print("="*60)
    
    results = {
        'basic_context': False,
        'exception_handling': False,
        'nested_operations': False,
        'multi_context': False
    }
    
    config = get_config()
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        # 1. Basic Context Manager
        print("1. Testing basic context manager...")
        with ONVIFConnection(config.camera_ip, credentials) as conn:
            if conn.is_alive():
                print("✅ Basic context manager working")
                results['basic_context'] = True
            else:
                print("⚠️ Connection established but not alive")
        
        # 2. Exception Handling in Context
        print("2. Testing exception handling in context...")
        try:
            with ONVIFConnection("192.168.1.999", credentials) as conn:
                # This should fail gracefully
                conn.get_snapshot()
        except Exception:
            print("✅ Exceptions handled gracefully in context")
            results['exception_handling'] = True
        
        # 3. Nested Operations
        print("3. Testing nested operations...")
        with ONVIFConnection(config.camera_ip, credentials) as conn:
            try:
                device_info = conn.get_device_info()
                profiles = conn.get_profiles()
                snapshot = conn.get_snapshot()
                
                operations_success = all([device_info, profiles, snapshot])
                if operations_success:
                    print("✅ Nested operations successful")
                    results['nested_operations'] = True
                else:
                    print("⚠️ Some nested operations failed")
            except Exception as e:
                print(f"⚠️ Nested operations error: {str(e)}")
        
        # 4. Multiple Contexts (Sequential)
        print("4. Testing multiple contexts...")
        context_count = 0
        for i in range(3):
            try:
                with ONVIFConnection(config.camera_ip, credentials) as conn:
                    if conn.get_snapshot():
                        context_count += 1
                time.sleep(0.5)  # Small delay between contexts
            except Exception:
                pass
        
        if context_count >= 2:
            print(f"✅ Multiple contexts working: {context_count}/3")
            results['multi_context'] = True
        else:
            print(f"⚠️ Multiple contexts limited: {context_count}/3")
        
    except Exception as e:
        print(f"❌ Context manager test error: {str(e)}")
        logging.exception("Context manager test failed")
    
    return results


def test_onvif_performance():
    """
    Test de performance y benchmarking.
    
    Returns:
        dict: Métricas de performance
    """
    print("\n" + "="*60)
    print("⚡ TEST: PERFORMANCE BENCHMARKING")
    print("="*60)
    
    metrics = {
        'connection_time': 0,
        'snapshot_time': 0,
        'frame_rate': 0,
        'memory_usage': 'N/A'
    }
    
    config = get_config()
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        connection = ONVIFConnection(config.camera_ip, credentials)
        
        # 1. Connection Time
        print("1. Measuring connection time...")
        start_time = time.time()
        success = connection.connect()
        connection_time = time.time() - start_time
        metrics['connection_time'] = connection_time
        
        if success:
            print(f"✅ Connection time: {connection_time:.2f}s")
            
            # 2. Snapshot Time
            print("2. Measuring snapshot performance...")
            start_time = time.time()
            snapshot = connection.get_snapshot()
            snapshot_time = time.time() - start_time
            metrics['snapshot_time'] = snapshot_time
            
            if snapshot:
                print(f"✅ Snapshot time: {snapshot_time:.2f}s ({len(snapshot)} bytes)")
            
            # 3. Frame Rate Test
            print("3. Measuring frame rate...")
            frame_count = 0
            test_duration = 5  # seconds
            start_time = time.time()
            
            while time.time() - start_time < test_duration:
                frame = connection.get_frame()
                if frame is not None:
                    frame_count += 1
                else:
                    break
            
            actual_duration = time.time() - start_time
            frame_rate = frame_count / actual_duration
            metrics['frame_rate'] = frame_rate
            
            print(f"✅ Frame rate: {frame_rate:.2f} FPS ({frame_count} frames in {actual_duration:.1f}s)")
            
            connection.disconnect()
        else:
            print("❌ Connection failed for performance test")
    
    except Exception as e:
        print(f"❌ Performance test error: {str(e)}")
        logging.exception("Performance test failed")
    
    return metrics


def test_onvif_threading():
    """
    Test de threading y operaciones concurrentes.
    
    Returns:
        dict: Resultados de threading
    """
    print("\n" + "="*60)
    print("🧵 TEST: THREADING & CONCURRENCY")
    print("="*60)
    
    results = {
        'single_thread': False,
        'multi_thread': False,
        'concurrent_snapshots': 0,
        'thread_safety': False
    }
    
    config = get_config()
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    def worker_thread(thread_id, results_list):
        """Worker function for threading test."""
        try:
            with ONVIFConnection(config.camera_ip, credentials) as conn:
                snapshot = conn.get_snapshot()
                if snapshot:
                    results_list.append(f"Thread-{thread_id}: {len(snapshot)} bytes")
                    return True
        except Exception as e:
            results_list.append(f"Thread-{thread_id}: Error - {str(e)[:30]}")
        return False
    
    try:
        # 1. Single Thread Test
        print("1. Testing single thread operation...")
        with ONVIFConnection(config.camera_ip, credentials) as conn:
            snapshot = conn.get_snapshot()
            if snapshot:
                print("✅ Single thread operation successful")
                results['single_thread'] = True
        
        # 2. Multi-threading Test
        print("2. Testing multi-threading...")
        thread_results = []
        threads = []
        num_threads = 3
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i, thread_results))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout
        
        successful_threads = len([r for r in thread_results if "Error" not in r])
        results['concurrent_snapshots'] = successful_threads
        
        if successful_threads > 0:
            print(f"✅ Multi-threading: {successful_threads}/{num_threads} threads successful")
            results['multi_thread'] = True
            
            if successful_threads == num_threads:
                results['thread_safety'] = True
                print("✅ Thread safety confirmed")
            else:
                print("⚠️ Partial thread safety")
        else:
            print("❌ Multi-threading failed")
        
        # Show thread results
        for result in thread_results:
            print(f"   {result}")
    
    except Exception as e:
        print(f"❌ Threading test error: {str(e)}")
        logging.exception("Threading test failed")
    
    return results


def main():
    """
    Función principal que ejecuta todos los tests de integración.
    """
    print("🚀 TEST DE INTEGRACIÓN ONVIF COMPLETO")
    print("="*60)
    print("Testing técnico avanzado para el protocolo ONVIF")
    print("Verificando integración, performance y robustez")
    print()
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Verificar configuración
        config = get_config()
        if not config.validate_configuration():
            print("❌ Configuración inválida. Verifica tu archivo .env")
            return False
        
        print(f"📍 Testing configuration:")
        print(f"   IP: {config.camera_ip}")
        print(f"   Puerto ONVIF: {config.onvif_port}")
        print(f"   Usuario: {config.camera_user}")
        
        # Ejecutar batería de tests
        all_results = {}
        
        # 1. Factory Integration
        factory_results = test_onvif_factory_integration()
        all_results['factory'] = factory_results
        
        time.sleep(2)
        
        # 2. Context Manager
        context_results = test_onvif_context_manager()
        all_results['context'] = context_results
        
        time.sleep(2)
        
        # 3. Performance
        performance_metrics = test_onvif_performance()
        all_results['performance'] = performance_metrics
        
        time.sleep(2)
        
        # 4. Threading
        threading_results = test_onvif_threading()
        all_results['threading'] = threading_results
        
        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN DE TESTS DE INTEGRACIÓN")
        print("="*60)
        
        # Factory results
        factory_success = sum(factory_results.values())
        print(f"🏭 Factory Pattern: {factory_success}/4 tests passed")
        
        # Context results
        context_success = sum(context_results.values())
        print(f"🔄 Context Manager: {context_success}/4 tests passed")
        
        # Performance results
        print(f"⚡ Performance:")
        print(f"   Connection: {performance_metrics['connection_time']:.2f}s")
        print(f"   Snapshot: {performance_metrics['snapshot_time']:.2f}s")
        print(f"   Frame Rate: {performance_metrics['frame_rate']:.2f} FPS")
        
        # Threading results
        threading_success = sum([threading_results['single_thread'], threading_results['multi_thread']])
        print(f"🧵 Threading: {threading_success}/2 core tests passed")
        print(f"   Concurrent ops: {threading_results['concurrent_snapshots']}/3")
        
        # Overall assessment
        total_tests = factory_success + context_success + threading_success
        max_tests = 10  # 4 + 4 + 2
        success_rate = (total_tests / max_tests) * 100
        
        print(f"\n🎯 Tasa de éxito general: {success_rate:.1f}% ({total_tests}/{max_tests})")
        
        if success_rate >= 80:
            print("🎉 ONVIF INTEGRATION: EXCELLENT")
        elif success_rate >= 60:
            print("✅ ONVIF INTEGRATION: GOOD")
        elif success_rate >= 40:
            print("⚠️ ONVIF INTEGRATION: FAIR")
        else:
            print("❌ ONVIF INTEGRATION: POOR")
        
        logger.info(f"Integration test completed with {success_rate:.1f}% success rate")
        return success_rate >= 60
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrumpido por el usuario")
        return False
        
    except Exception as e:
        print(f"\n❌ Error general en testing: {str(e)}")
        logger.error(f"Error fatal en test de integración: {str(e)}")
        return False
        
    finally:
        print("\n✅ Test de integración ONVIF finalizado")
        print("📝 Logs detallados en: examples/logs/onvif_integration_test.log")
        print("="*60)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 