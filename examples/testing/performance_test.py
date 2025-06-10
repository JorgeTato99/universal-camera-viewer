"""
Test de performance completo para todos los protocolos soportados.
Mide y compara FPS, latencia, uso de recursos y estabilidad.

Expansión del test_performance_comparison.py original con:
- ONVIF vs RTSP vs Amcrest comparison
- Métricas detalladas (FPS, latencia, jitter)
- Análisis de estabilidad
- Recomendaciones automáticas
- Benchmarking completo
"""

import sys
import time
import logging
import threading
from pathlib import Path
from statistics import mean, stdev
from collections import deque

# cspell: disable
# Import opcional de psutil para métricas del sistema
try:
    import psutil
    PSUTIL_AVAILABLE = True
    print("✅ psutil disponible - Métricas del sistema habilitadas")
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil no disponible - Métricas del sistema deshabilitadas")
    print("Para instalar: pip install psutil")

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from connections import ConnectionFactory
from utils.config import get_config


def setup_logging():
    """Configura logging para tests de performance."""
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "performance_test.log"
    
    # Limpiar configuración existente
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,  # Capturar toda la información del test
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True
    )
    
    print(f"📝 Logs guardándose en: {log_file}")


class PerformanceMetrics:
    """Clase para recopilar y analizar métricas de performance."""
    
    def __init__(self, protocol_name: str):
        self.protocol_name = protocol_name
        self.fps_samples = deque(maxlen=100)
        self.latency_samples = deque(maxlen=100)
        self.frame_count = 0
        self.start_time = None
        self.last_frame_time = None
        self.errors = 0
        self.memory_usage = []
        self.cpu_usage = []
    
    def start_measurement(self):
        """Inicia la medición de performance."""
        self.start_time = time.time()
        self.last_frame_time = self.start_time
    
    def record_frame(self, frame_received=True):
        """Registra un frame y calcula métricas."""
        current_time = time.time()
        
        if frame_received:
            self.frame_count += 1
            
            # Calcular FPS instantáneo
            if self.last_frame_time and current_time - self.last_frame_time > 0:
                instant_fps = 1.0 / (current_time - self.last_frame_time)
                self.fps_samples.append(instant_fps)
            
            # Calcular latencia (tiempo desde último frame)
            if self.last_frame_time:
                latency = current_time - self.last_frame_time
                self.latency_samples.append(latency * 1000)  # en ms
            
            self.last_frame_time = current_time
        else:
            self.errors += 1
    
    def record_system_metrics(self):
        """Registra métricas del sistema (CPU, memoria)."""
        if not PSUTIL_AVAILABLE:
            return
            
        try:
            self.memory_usage.append(psutil.virtual_memory().percent)
            self.cpu_usage.append(psutil.cpu_percent(interval=None))
        except Exception:
            pass  # Fallar silenciosamente si hay error
    
    def get_summary(self):
        """Obtiene un resumen de todas las métricas."""
        total_time = time.time() - self.start_time if self.start_time else 0
        average_fps = self.frame_count / total_time if total_time > 0 else 0
        
        summary = {
            'protocol': self.protocol_name,
            'frames_total': self.frame_count,
            'duration': total_time,
            'average_fps': average_fps,
            'errors': self.errors,
            'fps_samples': list(self.fps_samples),
            'latency_samples': list(self.latency_samples)
        }
        
        # Estadísticas FPS
        if self.fps_samples:
            summary['fps_mean'] = mean(self.fps_samples)
            summary['fps_stdev'] = stdev(self.fps_samples) if len(self.fps_samples) > 1 else 0
            summary['fps_min'] = min(self.fps_samples)
            summary['fps_max'] = max(self.fps_samples)
        
        # Estadísticas latencia
        if self.latency_samples:
            summary['latency_mean'] = mean(self.latency_samples)
            summary['latency_stdev'] = stdev(self.latency_samples) if len(self.latency_samples) > 1 else 0
            summary['latency_min'] = min(self.latency_samples)
            summary['latency_max'] = max(self.latency_samples)
        
        # Métricas del sistema (solo si psutil está disponible)
        if PSUTIL_AVAILABLE:
            if self.memory_usage:
                summary['memory_avg'] = mean(self.memory_usage)
            if self.cpu_usage:
                summary['cpu_avg'] = mean(self.cpu_usage)
        else:
            summary['system_metrics_note'] = 'Métricas del sistema no disponibles (instalar psutil)'
        
        return summary


def measure_protocol_performance(connection, protocol_name: str, duration: int = 30) -> dict:
    """
    Mide la performance completa de un protocolo.
    
    Args:
        connection: Conexión a medir
        protocol_name: Nombre del protocolo
        duration: Duración en segundos
        
    Returns:
        Diccionario con métricas de performance
    """
    print(f"\n📊 Midiendo performance {protocol_name} durante {duration}s...")
    
    metrics = PerformanceMetrics(protocol_name)
    
    try:
        # Intentar conectar
        if not connection.connect():
            print(f"❌ No se pudo conectar {protocol_name}")
            return {'protocol': protocol_name, 'error': 'Connection failed'}
        
        print(f"✅ {protocol_name} conectado, iniciando medición...")
        metrics.start_measurement()
        
        # Thread para monitoreo del sistema (solo si psutil está disponible)
        if PSUTIL_AVAILABLE:
            def system_monitor():
                while metrics.start_time and time.time() - metrics.start_time < duration:
                    metrics.record_system_metrics()
                    time.sleep(1)
            
            monitor_thread = threading.Thread(target=system_monitor, daemon=True)
            monitor_thread.start()
        else:
            print(f"  ⚠️ Métricas del sistema deshabilitadas (psutil no disponible)")
        
        # Loop principal de medición
        while time.time() - metrics.start_time < duration:
            try:
                frame = connection.get_frame()
                metrics.record_frame(frame is not None)
                
                # Mostrar progreso cada 5 segundos
                elapsed = time.time() - metrics.start_time
                if elapsed % 5 < 0.1:  # Aproximadamente cada 5 segundos
                    current_fps = metrics.frame_count / elapsed
                    print(f"  {protocol_name} - {elapsed:.0f}s: {metrics.frame_count} frames, {current_fps:.1f} FPS")
                
                # Pequeña pausa para evitar busy waiting si no hay frame
                if frame is None:
                    time.sleep(0.001)
                    
            except Exception as e:
                metrics.record_frame(False)
                if metrics.errors <= 5:  # Solo mostrar los primeros errores
                    print(f"  ⚠️ Error en frame: {str(e)[:50]}...")
    
    except KeyboardInterrupt:
        print(f"\n⚠️ Medición {protocol_name} interrumpida por usuario")
    except Exception as e:
        print(f"\n❌ Error crítico en {protocol_name}: {e}")
    finally:
        try:
            connection.disconnect()
        except:
            pass
    
    # Obtener resumen final
    summary = metrics.get_summary()
    
    print(f"\n✅ {protocol_name} - Medición completada:")
    print(f"  Frames: {summary['frames_total']}")
    print(f"  FPS promedio: {summary['average_fps']:.2f}")
    print(f"  Errores: {summary['errors']}")
    
    return summary


def test_rtsp_performance(duration: int = 20) -> dict:
    """Test de performance RTSP."""
    print("=" * 60)
    print("🔧 TEST PERFORMANCE RTSP")
    print("=" * 60)
    
    config = get_config()
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        connection = ConnectionFactory.create_connection(
            connection_type="rtsp",
            camera_ip=config.camera_ip,
            credentials=credentials
        )
        
        # Configurar parámetros RTSP
        connection.port = 554
        connection.channel = 1
        connection.subtype = 0
        
        return measure_protocol_performance(connection, "RTSP", duration)
        
    except Exception as e:
        print(f"❌ Error configurando RTSP: {e}")
        return {'protocol': 'RTSP', 'error': str(e)}


def test_onvif_performance(duration: int = 20) -> dict:
    """Test de performance ONVIF."""
    print("=" * 60)
    print("🚀 TEST PERFORMANCE ONVIF OPTIMIZADO")
    print("=" * 60)
    
    config = get_config()
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        connection = ConnectionFactory.create_connection(
            connection_type="onvif",
            camera_ip=config.camera_ip,
            credentials=credentials
        )
        
        return measure_protocol_performance(connection, "ONVIF", duration)
        
    except Exception as e:
        print(f"❌ Error configurando ONVIF: {e}")
        return {'protocol': 'ONVIF', 'error': str(e)}


def test_amcrest_performance(duration: int = 20) -> dict:
    """Test de performance Amcrest (si es compatible)."""
    print("=" * 60)
    print("🌐 TEST PERFORMANCE HTTP/AMCREST")
    print("=" * 60)
    
    config = get_config()
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        connection = ConnectionFactory.create_connection(
            connection_type="amcrest",
            camera_ip=config.camera_ip,
            credentials=credentials
        )
        
        return measure_protocol_performance(connection, "Amcrest", duration)
        
    except Exception as e:
        print(f"⚠️ Amcrest no compatible (esperado para Hero-K51H): {e}")
        return {'protocol': 'Amcrest', 'error': 'Not compatible', 'expected': True}


def analyze_results(results: list) -> dict:
    """Analiza los resultados y genera recomendaciones."""
    logger = logging.getLogger(__name__)
    
    print("\n" + "=" * 60)
    print("📈 ANÁLISIS DETALLADO DE RESULTADOS")
    print("=" * 60)
    
    valid_results = [r for r in results if 'error' not in r]
    
    if not valid_results:
        print("❌ No hay resultados válidos para analizar")
        logger.warning("No hay resultados válidos para analizar")
        return {}
    
    # Ordenar por FPS promedio
    valid_results.sort(key=lambda x: x.get('average_fps', 0), reverse=True)
    
    print("\n🏆 RANKING POR PERFORMANCE:")
    logger.info("Ranking por performance:")
    for i, result in enumerate(valid_results, 1):
        fps = result.get('average_fps', 0)
        errors = result.get('errors', 0)
        stability = "Alta" if errors < 5 else "Media" if errors < 20 else "Baja"
        print(f"{i}. {result['protocol']:10} - {fps:6.2f} FPS (Estabilidad: {stability})")
        logger.info(f"{i}. {result['protocol']} - {fps:.2f} FPS - Estabilidad: {stability} - Errores: {errors}")
    
    # Análisis detallado del mejor protocolo
    best = valid_results[0]
    print(f"\n🥇 MEJOR PROTOCOLO: {best['protocol']}")
    print(f"   FPS promedio: {best.get('average_fps', 0):.2f}")
    if 'fps_stdev' in best:
        print(f"   Estabilidad FPS: ±{best['fps_stdev']:.2f}")
    if 'latency_mean' in best:
        print(f"   Latencia promedio: {best['latency_mean']:.1f}ms")
    
    # Log del mejor protocolo
    logger.info(f"Mejor protocolo: {best['protocol']} - FPS: {best.get('average_fps', 0):.2f}")
    if 'fps_stdev' in best:
        logger.info(f"Estabilidad FPS: ±{best['fps_stdev']:.2f}")
    if 'latency_mean' in best:
        logger.info(f"Latencia promedio: {best['latency_mean']:.1f}ms")
    
    # Comparaciones
    if len(valid_results) > 1:
        print(f"\n📊 COMPARACIONES:")
        logger.info("Comparaciones entre protocolos:")
        baseline = valid_results[0]
        baseline_fps = baseline.get('average_fps', 0)
        
        for result in valid_results[1:]:
            fps = result.get('average_fps', 0)
            if baseline_fps > 0:
                diff_pct = ((baseline_fps - fps) / baseline_fps) * 100
                print(f"   {result['protocol']} vs {baseline['protocol']}: -{diff_pct:.1f}% FPS")
                logger.info(f"{result['protocol']} vs {baseline['protocol']}: -{diff_pct:.1f}% FPS")
    
    return {
        'best_protocol': best['protocol'],
        'best_fps': best.get('average_fps', 0),
        'ranking': [r['protocol'] for r in valid_results]
    }


def generate_recommendations(analysis: dict, results: list):
    """Genera recomendaciones basadas en el análisis."""
    logger = logging.getLogger(__name__)
    
    print("\n" + "=" * 60)
    print("💡 RECOMENDACIONES")
    print("=" * 60)
    
    best_protocol = analysis.get('best_protocol')
    best_fps = analysis.get('best_fps', 0)
    
    if best_protocol:
        print(f"🎯 PROTOCOLO RECOMENDADO: {best_protocol}")
        print(f"   FPS esperado: {best_fps:.1f}")
        
        logger.info(f"Protocolo recomendado: {best_protocol} - FPS esperado: {best_fps:.1f}")
        
        if best_protocol == "ONVIF":
            print("   ✅ Excelente elección - Sin limitaciones sleep/wake")
            print("   ✅ Conexión inmediata")
            print("   ✅ Protocolo estándar universal")
            logger.info("ONVIF recomendado - Excelente elección sin limitaciones")
        elif best_protocol == "RTSP":
            print("   ✅ Buena performance cuando está activo")
            logger.info("RTSP recomendado - Buena performance")
        elif best_protocol == "Amcrest":
            print("   ⚠️ Solo para cámaras compatibles con HTTP CGI")
            logger.info("Amcrest recomendado - Solo para cámaras compatibles HTTP CGI")
    
    # Recomendaciones generales
    print("\n🔧 OPTIMIZACIONES GENERALES:")
    
    if best_fps < 10:
        print("   ⚠️ FPS bajo detectado:")
        print("     • Verificar ancho de banda de red")
        print("     • Usar conexión ethernet en lugar de Wi-Fi")
        print("     • Cerrar otras aplicaciones que usen la cámara")
        logger.warning(f"FPS bajo detectado: {best_fps:.1f} - Recomendaciones de optimización aplicables")
    elif best_fps >= 15:
        print("   ✅ Performance excelente")
        logger.info(f"Performance excelente detectada: {best_fps:.1f} FPS")
    
    print("\n📋 TIPS DE CONFIGURACIÓN:")
    print("   • Para fluidez máxima: Usar ONVIF como principal")
    print("   • Para compatibilidad: Tener RTSP como backup")
    print("   • Para desarrolladores: Revisar buffer sizes en OpenCV")
    print("   • Para producción: Implementar reconexión automática")
    
    logger.info("Tips de configuración generados - Ver logs para detalles completos")


def main():
    """Función principal del test de performance."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🏁 TEST DE PERFORMANCE COMPLETO - TODOS LOS PROTOCOLOS")
    print("Midiendo FPS, latencia y estabilidad de cada protocolo")
    print()
    
    # Log de inicio
    logger.info("=== INICIANDO TEST DE PERFORMANCE COMPLETO ===")
    logger.info("Midiendo FPS, latencia y estabilidad de cada protocolo")
    
    # Verificar configuración
    config = get_config()
    if not config.validate_configuration():
        print("❌ Configuración inválida. Verifica tu archivo .env")
        logger.error("Configuración inválida - Test abortado")
        return
    
    print(f"📍 Configuración de test:")
    print(f"   IP: {config.camera_ip}")
    print(f"   Usuario: {config.camera_user}")
    print()
    
    # Log de configuración
    logger.info(f"Configuración de test - IP: {config.camera_ip}, Usuario: {config.camera_user}")
    logger.info(f"psutil disponible: {PSUTIL_AVAILABLE}")
    
    # Ejecutar tests de performance
    results = []
    test_duration = 15  # segundos por protocolo
    
    logger.info(f"Iniciando tests de performance - Duración por protocolo: {test_duration}s")
    
    # Test ONVIF (principal)
    logger.info("Iniciando test de performance ONVIF")
    onvif_result = test_onvif_performance(test_duration)
    results.append(onvif_result)
    
    if 'error' not in onvif_result:
        logger.info(f"ONVIF completado - FPS: {onvif_result.get('average_fps', 0):.2f}, Frames: {onvif_result.get('frames_total', 0)}, Errores: {onvif_result.get('errors', 0)}")
    else:
        logger.error(f"ONVIF falló - Error: {onvif_result.get('error', 'Unknown')}")
    
    print("\n⏳ Pausa entre tests...")
    time.sleep(3)
    
    # Test RTSP (backup)
    logger.info("Iniciando test de performance RTSP")
    rtsp_result = test_rtsp_performance(test_duration)
    results.append(rtsp_result)
    
    if 'error' not in rtsp_result:
        logger.info(f"RTSP completado - FPS: {rtsp_result.get('average_fps', 0):.2f}, Frames: {rtsp_result.get('frames_total', 0)}, Errores: {rtsp_result.get('errors', 0)}")
    else:
        logger.error(f"RTSP falló - Error: {rtsp_result.get('error', 'Unknown')}")
    
    print("\n⏳ Pausa entre tests...")
    time.sleep(3)
    
    # Test Amcrest (opcional, puede fallar)
    logger.info("Iniciando test de performance Amcrest")
    amcrest_result = test_amcrest_performance(test_duration)
    results.append(amcrest_result)
    
    if 'error' not in amcrest_result:
        logger.info(f"Amcrest completado - FPS: {amcrest_result.get('average_fps', 0):.2f}, Frames: {amcrest_result.get('frames_total', 0)}, Errores: {amcrest_result.get('errors', 0)}")
    else:
        if amcrest_result.get('expected', False):
            logger.info("Amcrest falló como se esperaba (no compatible con Hero-K51H)")
        else:
            logger.error(f"Amcrest falló - Error: {amcrest_result.get('error', 'Unknown')}")
    
    # Análisis de resultados
    logger.info("Iniciando análisis de resultados")
    analysis = analyze_results(results)
    
    # Log del análisis
    if analysis:
        logger.info(f"Análisis completado - Mejor protocolo: {analysis.get('best_protocol', 'None')}, FPS: {analysis.get('best_fps', 0):.2f}")
        logger.info(f"Ranking de protocolos: {', '.join(analysis.get('ranking', []))}")
    
    # Generar recomendaciones
    logger.info("Generando recomendaciones")
    generate_recommendations(analysis, results)
    
    print("\n✅ Test de performance completado")
    print("📝 Logs detallados guardados en: examples/logs/performance_test.log")
    print("=" * 60)
    
    # Log de finalización
    logger.info("=== TEST DE PERFORMANCE COMPLETADO ===")
    valid_results = [r for r in results if 'error' not in r]
    logger.info(f"Protocolos probados: {len(results)}, Exitosos: {len(valid_results)}")
    if analysis and 'best_protocol' in analysis:
        logger.info(f"Recomendación final: {analysis['best_protocol']} con {analysis['best_fps']:.2f} FPS")
    logger.info("Logs detallados guardados en: examples/logs/performance_test.log")


if __name__ == "__main__":
    main() 