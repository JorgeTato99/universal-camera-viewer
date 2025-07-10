"""
Analizador de red para diagnóstico de conectividad con cámaras Dahua.
Herramienta especializada en análisis de red y troubleshooting.

Funcionalidades incluidas:
- Análisis de conectividad de red
- Diagnóstico de latencia y performance
- Test de ancho de banda
- Verificación de rutas de red
- Análisis de puertos y protocolos
- Recomendaciones de optimización
"""

import sys
import time
import socket
import subprocess
import platform
import logging
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))


def setup_logging():
    """Configura logging para análisis de red."""
    import logging
    
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "network_analyzer.log"
    
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


def ping_test(target_ip: str, count: int = 4) -> dict:
    """
    Realiza test de ping para medir latencia y pérdida de paquetes.
    
    Args:
        target_ip: IP objetivo
        count: Número de pings a realizar
        
    Returns:
        Diccionario con estadísticas de ping
    """
    logger = logging.getLogger(__name__)
    print(f"📡 Ejecutando ping test a {target_ip}...")
    logger.info(f"Iniciando ping test a {target_ip} con {count} paquetes")
    
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(count), target_ip]
    else:
        cmd = ["ping", "-c", str(count), target_ip]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout
        
        # Parsear resultados (simplificado)
        lines = output.split('\n')
        
        stats = {
            'success': result.returncode == 0,
            'packets_sent': count,
            'packets_received': 0,
            'packet_loss': 100,
            'min_time': 0,
            'max_time': 0,
            'avg_time': 0
        }
        
        if stats['success']:
            # Contar respuestas exitosas
            for line in lines:
                if 'reply' in line.lower() or 'ttl=' in line.lower():
                    stats['packets_received'] += 1
            
            if stats['packets_received'] > 0:
                stats['packet_loss'] = ((count - stats['packets_received']) / count) * 100
                
                # Extraer tiempos (simplificado)
                for line in lines:
                    if 'time=' in line.lower():
                        try:
                            time_part = line.split('time=')[1].split()[0]
                            time_ms = float(time_part.replace('ms', ''))
                            if stats['min_time'] == 0 or time_ms < stats['min_time']:
                                stats['min_time'] = time_ms
                            if time_ms > stats['max_time']:
                                stats['max_time'] = time_ms
                        except:
                            pass
                
                # Calcular promedio aproximado
                if stats['min_time'] > 0 and stats['max_time'] > 0:
                    stats['avg_time'] = (stats['min_time'] + stats['max_time']) / 2
        
        # Mostrar resultados
        if stats['success'] and stats['packet_loss'] < 100:
            print(f"✅ Ping exitoso:")
            print(f"   Paquetes: {stats['packets_received']}/{stats['packets_sent']}")
            print(f"   Pérdida: {stats['packet_loss']:.1f}%")
            if stats['avg_time'] > 0:
                print(f"   Latencia: {stats['avg_time']:.1f}ms")
                
            logger.info(f"Ping exitoso a {target_ip} - Pérdida: {stats['packet_loss']:.1f}%, Latencia: {stats['avg_time']:.1f}ms")
        else:
            print(f"❌ Ping falló - Host no alcanzable")
            logger.warning(f"Ping falló a {target_ip} - Host no alcanzable")
        
        return stats
        
    except subprocess.TimeoutExpired:
        print(f"❌ Ping timeout - Host no responde")
        return {'success': False, 'timeout': True}
    except Exception as e:
        print(f"❌ Error en ping: {e}")
        return {'success': False, 'error': str(e)}


def port_connectivity_test(ip: str, port: int, timeout: float = 5.0) -> dict:
    """
    Prueba conectividad a un puerto específico con análisis detallado.
    
    Args:
        ip: Dirección IP
        port: Puerto a probar
        timeout: Timeout en segundos
        
    Returns:
        Resultado detallado del test
    """
    print(f"🔌 Probando conectividad {ip}:{port}...")
    
    result = {
        'ip': ip,
        'port': port,
        'open': False,
        'response_time': 0,
        'error': None
    }
    
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        connect_result = sock.connect_ex((ip, port))
        response_time = (time.time() - start_time) * 1000  # ms
        
        result['response_time'] = response_time
        
        if connect_result == 0:
            result['open'] = True
            print(f"✅ Puerto {port}: Abierto ({response_time:.1f}ms)")
        else:
            print(f"❌ Puerto {port}: Cerrado o filtrado")
        
        sock.close()
        
    except socket.timeout:
        print(f"⏱️ Puerto {port}: Timeout")
        result['error'] = 'timeout'
    except Exception as e:
        print(f"❌ Puerto {port}: Error - {str(e)}")
        result['error'] = str(e)
    
    return result


def analyze_camera_ports(ip: str) -> dict:
    """
    Análisis completo de puertos de cámara con diagnóstico específico.
    
    Args:
        ip: IP de la cámara
        
    Returns:
        Análisis completo de puertos
    """
    logger = logging.getLogger(__name__)
    print(f"\n🎯 Analizando puertos de cámara en {ip}...")
    logger.info(f"Iniciando análisis de puertos de cámara en {ip}")
    
    camera_ports = {
        80: {'name': 'HTTP/ONVIF', 'critical': True},
        554: {'name': 'RTSP', 'critical': True},
        37777: {'name': 'Dahua SDK', 'critical': False},
        8000: {'name': 'HTTP Alt', 'critical': False},
        443: {'name': 'HTTPS', 'critical': False},
        8080: {'name': 'HTTP Alt 2', 'critical': False}
    }
    
    analysis = {
        'ip': ip,
        'total_open': 0,
        'critical_open': 0,
        'ports': {},
        'recommendations': []
    }
    
    for port, info in camera_ports.items():
        result = port_connectivity_test(ip, port, timeout=3.0)
        analysis['ports'][port] = {
            **result,
            'name': info['name'],
            'critical': info['critical']
        }
        
        if result['open']:
            analysis['total_open'] += 1
            if info['critical']:
                analysis['critical_open'] += 1
            logger.info(f"Puerto {port} ({info['name']}) - ABIERTO - Tiempo: {result.get('response_time', 0):.1f}ms")
        else:
            logger.info(f"Puerto {port} ({info['name']}) - CERRADO")
    
    # Generar recomendaciones
    if analysis['critical_open'] == 0:
        analysis['recommendations'].append(
            "❌ CRÍTICO: Ningún puerto crítico abierto - Verificar conectividad"
        )
        logger.warning(f"CRÍTICO: Ningún puerto crítico abierto en {ip}")
    elif analysis['ports'][80]['open'] and analysis['ports'][554]['open']:
        analysis['recommendations'].append(
            "✅ EXCELENTE: ONVIF y RTSP disponibles - Configuración óptima"
        )
        logger.info(f"Configuración óptima en {ip}: ONVIF y RTSP disponibles")
    elif analysis['ports'][80]['open']:
        analysis['recommendations'].append(
            "✅ BUENO: ONVIF disponible - Protocolo principal funcional"
        )
        logger.info(f"ONVIF disponible en {ip} - Protocolo principal funcional")
    elif analysis['ports'][554]['open']:
        analysis['recommendations'].append(
            "⚠️ LIMITADO: Solo RTSP - Requiere workflow DMSS"
        )
        logger.warning(f"Solo RTSP disponible en {ip} - Requiere workflow DMSS")
    
    if not analysis['ports'][37777]['open']:
        analysis['recommendations'].append(
            "ℹ️ SDK Dahua no disponible - Funcionalidades avanzadas limitadas"
        )
    
    logger.info(f"Análisis de puertos completado para {ip} - Total abiertos: {analysis['total_open']}, Críticos: {analysis['critical_open']}")
    
    return analysis


def bandwidth_test(ip: str, duration: int = 10) -> dict:
    """
    Test básico de ancho de banda hacia la cámara.
    
    Args:
        ip: IP de la cámara
        duration: Duración del test en segundos
        
    Returns:
        Estadísticas de ancho de banda
    """
    print(f"\n📊 Iniciando test de ancho de banda a {ip}...")
    print(f"   Duración: {duration} segundos")
    
    result = {
        'ip': ip,
        'duration': duration,
        'connections_made': 0,
        'avg_connection_time': 0,
        'successful_rate': 0,
        'estimated_bandwidth': 'N/A'
    }
    
    connection_times = []
    successful_connections = 0
    
    try:
        # Test repetido de conexiones para medir performance
        test_port = 80  # Puerto HTTP/ONVIF
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                conn_start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                
                connect_result = sock.connect_ex((ip, test_port))
                conn_time = (time.time() - conn_start) * 1000
                
                result['connections_made'] += 1
                
                if connect_result == 0:
                    successful_connections += 1
                    connection_times.append(conn_time)
                
                sock.close()
                time.sleep(0.1)  # Pausa entre conexiones
                
            except Exception:
                result['connections_made'] += 1
        
        # Calcular estadísticas
        if connection_times:
            result['avg_connection_time'] = sum(connection_times) / len(connection_times)
            result['successful_rate'] = (successful_connections / result['connections_made']) * 100
            
            # Estimar "ancho de banda" basado en tiempo de conexión
            if result['avg_connection_time'] < 10:
                result['estimated_bandwidth'] = 'Excelente (< 10ms)'
            elif result['avg_connection_time'] < 50:
                result['estimated_bandwidth'] = 'Bueno (< 50ms)'
            elif result['avg_connection_time'] < 100:
                result['estimated_bandwidth'] = 'Aceptable (< 100ms)'
            else:
                result['estimated_bandwidth'] = 'Lento (> 100ms)'
        
        print(f"✅ Test completado:")
        print(f"   Conexiones: {successful_connections}/{result['connections_made']}")
        print(f"   Tiempo promedio: {result['avg_connection_time']:.1f}ms")
        print(f"   Performance: {result['estimated_bandwidth']}")
        
    except Exception as e:
        print(f"❌ Error en test de ancho de banda: {e}")
        result['error'] = str(e)
    
    return result


def network_route_analysis(target_ip: str) -> dict:
    """
    Análisis básico de ruta de red (traceroute simplificado).
    
    Args:
        target_ip: IP objetivo
        
    Returns:
        Información de ruta de red
    """
    print(f"\n🗺️ Analizando ruta de red a {target_ip}...")
    
    result = {
        'target': target_ip,
        'local_ip': 'Unknown',
        'same_subnet': False,
        'gateway_required': True,
        'hops_estimated': 0
    }
    
    try:
        # Obtener IP local
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            result['local_ip'] = local_ip
        
        print(f"   IP local: {local_ip}")
        
        # Análisis básico de subnet
        local_parts = local_ip.split('.')
        target_parts = target_ip.split('.')
        
        # Verificar si están en la misma subnet /24
        if local_parts[:3] == target_parts[:3]:
            result['same_subnet'] = True
            result['gateway_required'] = False
            result['hops_estimated'] = 1
            print(f"   ✅ Misma subnet - Comunicación directa")
        else:
            result['hops_estimated'] = 2
            print(f"   ⚠️ Diferente subnet - Requiere gateway")
        
        # Traceroute básico en Windows
        if platform.system().lower() == "windows":
            try:
                trace_result = subprocess.run(
                    ["tracert", "-h", "5", target_ip], 
                    capture_output=True, text=True, timeout=15
                )
                
                if trace_result.returncode == 0:
                    lines = trace_result.stdout.split('\n')
                    hop_count = 0
                    for line in lines:
                        if target_ip in line:
                            hop_count = len([l for l in lines if 'ms' in l])
                            break
                    
                    if hop_count > 0:
                        result['hops_estimated'] = hop_count
                        print(f"   Saltos detectados: {hop_count}")
                
            except subprocess.TimeoutExpired:
                print(f"   ⏱️ Traceroute timeout")
            except Exception as e:
                print(f"   ❌ Traceroute error: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error en análisis de ruta: {e}")
        result['error'] = str(e)
    
    return result


def main():
    """Función principal del analizador de red."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🌐 ANALIZADOR DE RED PARA CÁMARAS DAHUA")
    print("="*60)
    print("Herramienta especializada en diagnóstico de conectividad")
    print()
    
    # Log de inicio
    logger.info("=== INICIANDO ANALIZADOR DE RED PARA CÁMARAS DAHUA ===")
    logger.info("Herramienta especializada en diagnóstico de conectividad")
    
    # Solicitar IP a analizar
    try:
        from utils.config import get_config
        config = get_config()
        default_ip = config.camera_ip
        print(f"📍 IP configurada actual: {default_ip}")
    except:
        default_ip = "192.168.1.172"
        print(f"⚠️ Sin configuración, usando IP por defecto: {default_ip}")
    
    target_ip = input(f"\nIP a analizar [{default_ip}]: ").strip() or default_ip
    
    print(f"\n🚀 Iniciando análisis completo de {target_ip}...")
    print("="*60)
    
    logger.info(f"Iniciando análisis completo para IP: {target_ip}")
    
    # 1. Test de ping básico
    logger.info("Ejecutando test de ping")
    ping_results = ping_test(target_ip, count=4)
    logger.info(f"Ping completado - Éxito: {ping_results.get('success', False)}, Pérdida: {ping_results.get('packet_loss', 'N/A')}%")
    
    # 2. Análisis de puertos de cámara
    logger.info("Iniciando análisis de puertos de cámara")
    port_analysis = analyze_camera_ports(target_ip)
    logger.info(f"Puertos analizados - Críticos abiertos: {port_analysis['critical_open']}")
    
    # 3. Análisis de ruta de red
    logger.info("Analizando ruta de red")
    route_analysis = network_route_analysis(target_ip)
    logger.info(f"Análisis de ruta completado - Misma subnet: {route_analysis.get('same_subnet', False)}")
    
    # 4. Test de ancho de banda
    logger.info("Ejecutando test de ancho de banda")
    bandwidth_results = bandwidth_test(target_ip, duration=5)
    logger.info(f"Test de bandwidth completado - Performance: {bandwidth_results.get('estimated_bandwidth', 'N/A')}")
    
    # Resumen final
    print(f"\n📋 RESUMEN DE ANÁLISIS DE RED")
    print("="*60)
    
    print(f"🎯 Objetivo: {target_ip}")
    
    # Conectividad básica
    if ping_results.get('success', False):
        print(f"📡 Conectividad: ✅ OK")
        if 'avg_time' in ping_results and ping_results['avg_time'] > 0:
            print(f"   Latencia: {ping_results['avg_time']:.1f}ms")
        if 'packet_loss' in ping_results:
            print(f"   Pérdida de paquetes: {ping_results['packet_loss']:.1f}%")
    else:
        print(f"📡 Conectividad: ❌ FALLO")
    
    # Puertos críticos
    critical_ports = port_analysis['critical_open']
    total_critical = sum(1 for p in port_analysis['ports'].values() if p['critical'])
    print(f"🔌 Puertos críticos: {critical_ports}/{total_critical}")
    
    if port_analysis['ports'][80]['open']:
        print(f"   ONVIF (80): ✅")
    else:
        print(f"   ONVIF (80): ❌")
    
    if port_analysis['ports'][554]['open']:
        print(f"   RTSP (554): ✅")
    else:
        print(f"   RTSP (554): ❌")
    
    # Performance de red
    print(f"⚡ Performance: {bandwidth_results.get('estimated_bandwidth', 'N/A')}")
    
    # Topología
    if route_analysis.get('same_subnet', False):
        print(f"🗺️ Topología: Misma subnet (directo)")
    else:
        print(f"🗺️ Topología: Via gateway ({route_analysis.get('hops_estimated', '?')} saltos)")
    
    # Recomendaciones finales
    print(f"\n💡 RECOMENDACIONES:")
    
    if ping_results.get('success', False) and critical_ports > 0:
        print(f"✅ Red configurada correctamente")
        if port_analysis['ports'][80]['open']:
            print(f"   • Usar ONVIF como protocolo principal")
        if port_analysis['ports'][554]['open']:
            print(f"   • RTSP disponible como backup")
    else:
        print(f"❌ Problemas de conectividad detectados:")
        if not ping_results.get('success', False):
            print(f"   • Verificar IP y conectividad básica")
        if critical_ports == 0:
            print(f"   • Verificar puertos 80 y 554")
            print(f"   • Revisar firewall de cámara")
    
    # Optimizaciones
    if bandwidth_results.get('avg_connection_time', 0) > 100:
        print(f"⚠️ Latencia alta detectada:")
        print(f"   • Considerar conexión ethernet")
        print(f"   • Verificar interferencias Wi-Fi")
        print(f"   • Revisar carga de red")
    
    print(f"\n✅ Análisis de red completado")
    print(f"📝 Logs guardados en: examples/logs/network_analyzer.log")
    print("="*60)
    
    # Log de finalización con resumen
    logger.info("=== RESUMEN FINAL DEL ANÁLISIS ===")
    logger.info(f"IP analizada: {target_ip}")
    logger.info(f"Conectividad básica: {'OK' if ping_results.get('success', False) else 'FALLO'}")
    logger.info(f"Puertos críticos: {critical_ports}/{total_critical}")
    logger.info(f"Performance: {bandwidth_results.get('estimated_bandwidth', 'N/A')}")
    logger.info(f"Misma subnet: {route_analysis.get('same_subnet', False)}")
    logger.info("=== ANÁLISIS DE RED COMPLETADO ===")
    logger.info("Logs guardados en: examples/logs/network_analyzer.log")


if __name__ == "__main__":
    main() 