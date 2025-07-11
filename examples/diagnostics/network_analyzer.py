"""
Analizador de red para diagnóstico de conectividad con cámaras IP.
Herramienta especializada en análisis de red y troubleshooting.

Funcionalidades incluidas:
- Análisis de conectividad de red usando servicios MVP
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
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

# Imports de servicios MVP
try:
    from src.services import (
        ProtocolService, 
        ScanService, 
        DataService, 
        ConfigService,
        get_scan_service,
        get_data_service,
        get_config_service
    )
    from src.models.scan_model import ScanRange, ScanMethod
    from src.models.camera_model import ProtocolType
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Algunos servicios MVP no disponibles: {e}")
    print("💡 Usando funcionalidad básica del analizador")
    SERVICES_AVAILABLE = False


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
    
    # Configuración mejorada de logging
    logging.basicConfig(
        level=logging.DEBUG,  # Nivel más detallado
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True
    )
    
    # Configurar logger específico para el analizador
    logger = logging.getLogger("NetworkAnalyzer")
    logger.setLevel(logging.DEBUG)
    
    print(f"📝 Logs guardándose en: {log_file}")
    print(f"🔧 Nivel de logging: DEBUG (máximo detalle)")
    
    # Log de configuración del sistema
    logger.info("=== CONFIGURACIÓN DEL SISTEMA ===")
    logger.info(f"Directorio de trabajo: {Path.cwd()}")
    logger.info(f"Archivo de logs: {log_file}")
    logger.info(f"Servicios MVP disponibles: {SERVICES_AVAILABLE}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    
    return logger


def ping_test(target_ip: str, count: int = 4) -> dict:
    """
    Realiza test de ping para medir latencia y pérdida de paquetes.
    
    Args:
        target_ip: IP objetivo
        count: Número de pings a realizar
        
    Returns:
        Diccionario con estadísticas de ping
    """
    logger = logging.getLogger("NetworkAnalyzer")
    start_time = time.time()
    
    print(f"📡 Ejecutando ping test a {target_ip}...")
    logger.info(f"=== INICIANDO PING TEST ===")
    logger.info(f"Target IP: {target_ip}")
    logger.info(f"Paquetes a enviar: {count}")
    logger.info(f"Timeout configurado: 30 segundos")
    logger.debug(f"Timestamp de inicio: {start_time}")
    
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
        
        # Calcular duración del test
        test_duration = time.time() - start_time
        
        # Mostrar resultados
        if stats['success'] and stats['packet_loss'] < 100:
            print(f"✅ Ping exitoso:")
            print(f"   Paquetes: {stats['packets_received']}/{stats['packets_sent']}")
            print(f"   Pérdida: {stats['packet_loss']:.1f}%")
            if stats['avg_time'] > 0:
                print(f"   Latencia: {stats['avg_time']:.1f}ms")
            print(f"   Duración del test: {test_duration:.1f}s")
                
            logger.info(f"=== PING TEST EXITOSO ===")
            logger.info(f"Target IP: {target_ip}")
            logger.info(f"Paquetes enviados/recibidos: {stats['packets_sent']}/{stats['packets_received']}")
            logger.info(f"Pérdida de paquetes: {stats['packet_loss']:.1f}%")
            logger.info(f"Latencia promedio: {stats['avg_time']:.1f}ms")
            logger.info(f"Latencia mínima: {stats['min_time']:.1f}ms")
            logger.info(f"Latencia máxima: {stats['max_time']:.1f}ms")
            logger.info(f"Duración del test: {test_duration:.1f}s")
            logger.debug(f"Comando ejecutado: {'ping -n' if system == 'windows' else 'ping -c'} {count} {target_ip}")
        else:
            print(f"❌ Ping falló - Host no alcanzable")
            print(f"   Duración del test: {test_duration:.1f}s")
            
            logger.warning(f"=== PING TEST FALLÓ ===")
            logger.warning(f"Target IP: {target_ip}")
            logger.warning(f"Paquetes enviados: {stats['packets_sent']}")
            logger.warning(f"Paquetes recibidos: {stats['packets_received']}")
            logger.warning(f"Pérdida de paquetes: {stats['packet_loss']:.1f}%")
            logger.warning(f"Duración del test: {test_duration:.1f}s")
            logger.warning(f"Return code: {result.returncode}")
        
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
    logger = logging.getLogger("NetworkAnalyzer")
    start_time = time.time()
    
    print(f"🔌 Probando conectividad {ip}:{port}...")
    logger.debug(f"=== INICIANDO TEST DE PUERTO ===")
    logger.debug(f"Target: {ip}:{port}")
    logger.debug(f"Timeout configurado: {timeout}s")
    logger.debug(f"Timestamp de inicio: {start_time}")
    
    result = {
        'ip': ip,
        'port': port,
        'open': False,
        'response_time': 0,
        'error': None,
        'test_duration': 0
    }
    
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        connect_result = sock.connect_ex((ip, port))
        response_time = (time.time() - start_time) * 1000  # ms
        
        result['response_time'] = response_time
        
        test_duration = time.time() - start_time
        result['test_duration'] = test_duration
        
        if connect_result == 0:
            result['open'] = True
            print(f"✅ Puerto {port}: Abierto ({response_time:.1f}ms)")
            logger.debug(f"=== PUERTO ABIERTO ===")
            logger.debug(f"Target: {ip}:{port}")
            logger.debug(f"Response time: {response_time:.1f}ms")
            logger.debug(f"Test duration: {test_duration:.1f}s")
            logger.debug(f"Socket family: AF_INET")
            logger.debug(f"Socket type: SOCK_STREAM")
        else:
            print(f"❌ Puerto {port}: Cerrado o filtrado")
            logger.debug(f"=== PUERTO CERRADO ===")
            logger.debug(f"Target: {ip}:{port}")
            logger.debug(f"Connect result: {connect_result}")
            logger.debug(f"Test duration: {test_duration:.1f}s")
            logger.debug(f"Error code: {connect_result}")
        
        sock.close()
        logger.debug(f"Socket cerrado para {ip}:{port}")
        
    except socket.timeout:
        test_duration = time.time() - start_time
        result['test_duration'] = test_duration
        print(f"⏱️ Puerto {port}: Timeout")
        result['error'] = 'timeout'
        logger.warning(f"=== PUERTO TIMEOUT ===")
        logger.warning(f"Target: {ip}:{port}")
        logger.warning(f"Timeout configurado: {timeout}s")
        logger.warning(f"Test duration: {test_duration:.1f}s")
    except Exception as e:
        test_duration = time.time() - start_time
        result['test_duration'] = test_duration
        print(f"❌ Puerto {port}: Error - {str(e)}")
        result['error'] = str(e)
        logger.error(f"=== ERROR EN TEST DE PUERTO ===")
        logger.error(f"Target: {ip}:{port}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Test duration: {test_duration:.1f}s")
        logger.error(f"Exception type: {type(e).__name__}")
    
    return result


async def analyze_camera_ports_with_services(ip: str) -> dict:
    """
    Análisis completo de puertos de cámara usando servicios MVP.
    
    Args:
        ip: IP de la cámara
        
    Returns:
        Análisis completo de puertos
    """
    logger = logging.getLogger("NetworkAnalyzer")
    start_time = time.time()
    
    print(f"\n🎯 Analizando puertos de cámara en {ip} usando servicios MVP...")
    logger.info(f"=== INICIANDO ANÁLISIS DE PUERTOS CON SERVICIOS MVP ===")
    logger.info(f"Target IP: {ip}")
    logger.info(f"Método: ScanService + ProtocolService")
    logger.info(f"Puertos a escanear: [80, 554, 37777, 8000, 443, 8080]")
    logger.debug(f"Timestamp de inicio: {start_time}")
    logger.debug(f"Servicios disponibles: {SERVICES_AVAILABLE}")
    
    analysis = {
        'ip': ip,
        'total_open': 0,
        'critical_open': 0,
        'ports': {},
        'protocols_detected': [],
        'recommendations': [],
        'service_used': 'MVP Services'
    }
    
    if SERVICES_AVAILABLE:
        try:
            # Usar ScanService para escaneo de puertos
            scan_service = get_scan_service()
            
            # Crear rango de escaneo para IP específica
            scan_range = ScanRange(
                start_ip=ip,
                end_ip=ip,
                ports=[80, 554, 37777, 8000, 443, 8080]
            )
            
            # Iniciar escaneo
            scan_id = await scan_service.start_scan_async(
                scan_range=scan_range,
                methods=[ScanMethod.PORT_SCAN, ScanMethod.PROTOCOL_DETECTION],
                use_cache=True
            )
            
            # Esperar resultados
            while scan_service.get_scan_status(scan_id) == 'running':
                await asyncio.sleep(0.5)
            
            # Obtener resultados
            scan_results = scan_service.get_scan_history(limit=1)
            if scan_results:
                latest_scan = scan_results[0]
                camera_results = latest_scan.get('camera_results', [])
                
                if camera_results:
                    camera_data = camera_results[0]  # Primera cámara encontrada
                    open_ports = camera_data.get('open_ports', [])
                    detected_protocols = camera_data.get('all_protocols', [])
                    
                    # Mapear puertos a información
                    camera_ports = {
                        80: {'name': 'HTTP/ONVIF', 'critical': True},
                        554: {'name': 'RTSP', 'critical': True},
                        37777: {'name': 'Dahua SDK', 'critical': False},
                        8000: {'name': 'HTTP Alt', 'critical': False},
                        443: {'name': 'HTTPS', 'critical': False},
                        8080: {'name': 'HTTP Alt 2', 'critical': False}
                    }
                    
                    for port, info in camera_ports.items():
                        is_open = port in open_ports
                        analysis['ports'][port] = {
                            'ip': ip,
                            'port': port,
                            'open': is_open,
                            'name': info['name'],
                            'critical': info['critical'],
                            'response_time': 0  # No disponible en ScanService
                        }
                        
                        if is_open:
                            analysis['total_open'] += 1
                            if info['critical']:
                                analysis['critical_open'] += 1
                            logger.info(f"Puerto {port} ({info['name']}) - ABIERTO")
                        else:
                            logger.info(f"Puerto {port} ({info['name']}) - CERRADO")
                    
                    # Protocolos detectados
                    analysis['protocols_detected'] = detected_protocols
                    logger.info(f"Protocolos detectados: {detected_protocols}")
                    
                    # Usar ProtocolService para tests adicionales
                    await _test_protocols_with_service(ip, analysis)
                    
                else:
                    logger.warning(f"No se encontraron cámaras en {ip} usando ScanService")
                    # Fallback a método manual
                    return await analyze_camera_ports_manual(ip)
            else:
                logger.warning("No se obtuvieron resultados del ScanService")
                return await analyze_camera_ports_manual(ip)
                
        except Exception as e:
            logger.error(f"Error usando servicios MVP: {e}")
            return await analyze_camera_ports_manual(ip)
    else:
        return await analyze_camera_ports_manual(ip)
    
    # Calcular duración del análisis
    analysis_duration = time.time() - start_time
    
    # Generar recomendaciones
    _generate_port_recommendations(analysis, logger)
    
    logger.info(f"=== ANÁLISIS DE PUERTOS COMPLETADO ===")
    logger.info(f"Target IP: {ip}")
    logger.info(f"Total puertos abiertos: {analysis['total_open']}")
    logger.info(f"Puertos críticos abiertos: {analysis['critical_open']}")
    logger.info(f"Protocolos detectados: {analysis['protocols_detected']}")
    logger.info(f"Método usado: {analysis['service_used']}")
    logger.info(f"Duración del análisis: {analysis_duration:.1f}s")
    logger.debug(f"Detalles por puerto: {analysis['ports']}")
    
    return analysis


async def analyze_camera_ports_manual(ip: str) -> dict:
    """
    Análisis manual de puertos de cámara (fallback).
    
    Args:
        ip: IP de la cámara
        
    Returns:
        Análisis completo de puertos
    """
    logger = logging.getLogger("NetworkAnalyzer")
    start_time = time.time()
    
    print(f"\n🎯 Analizando puertos de cámara en {ip} (método manual)...")
    logger.info(f"=== INICIANDO ANÁLISIS MANUAL DE PUERTOS ===")
    logger.info(f"Target IP: {ip}")
    logger.info(f"Método: Socket connectivity test")
    logger.info(f"Puertos a escanear: [80, 554, 37777, 8000, 443, 8080]")
    logger.debug(f"Timestamp de inicio: {start_time}")
    logger.debug(f"Timeout por puerto: 3.0s")
    
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
        'protocols_detected': [],
        'recommendations': [],
        'service_used': 'Manual'
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
    
    # Calcular duración del análisis
    analysis_duration = time.time() - start_time
    
    # Generar recomendaciones
    _generate_port_recommendations(analysis, logger)
    
    logger.info(f"=== ANÁLISIS MANUAL DE PUERTOS COMPLETADO ===")
    logger.info(f"Target IP: {ip}")
    logger.info(f"Total puertos abiertos: {analysis['total_open']}")
    logger.info(f"Puertos críticos abiertos: {analysis['critical_open']}")
    logger.info(f"Protocolos detectados: {analysis['protocols_detected']}")
    logger.info(f"Método usado: {analysis['service_used']}")
    logger.info(f"Duración del análisis: {analysis_duration:.1f}s")
    logger.debug(f"Detalles por puerto: {analysis['ports']}")
    
    return analysis


async def _test_protocols_with_service(ip: str, analysis: dict):
    """
    Prueba protocolos usando ProtocolService.
    
    Args:
        ip: IP de la cámara
        analysis: Diccionario de análisis a actualizar
    """
    if not SERVICES_AVAILABLE:
        return
    
    logger = logging.getLogger("NetworkAnalyzer")
    start_time = time.time()
    
    logger.info(f"=== INICIANDO TEST DE PROTOCOLOS CON PROTOCOLSERVICE ===")
    logger.info(f"Target IP: {ip}")
    logger.info(f"Credenciales: admin/admin")
    logger.debug(f"Timestamp de inicio: {start_time}")
    
    try:
        protocol_service = ProtocolService()
        credentials = {'username': 'admin', 'password': 'admin'}
        
        # Test ONVIF
        if 80 in analysis['ports'] and analysis['ports'][80]['open']:
            logger.debug(f"Probando protocolo ONVIF en {ip}")
            onvif_start = time.time()
            onvif_success = await protocol_service.test_connection_async(ip, "onvif", credentials)
            onvif_duration = time.time() - onvif_start
            
            if onvif_success:
                analysis['protocols_detected'].append('ONVIF')
                logger.info(f"✅ ONVIF confirmado en {ip} ({onvif_duration:.1f}s)")
                print(f"   ✅ ONVIF confirmado en {ip}")
            else:
                logger.warning(f"❌ ONVIF falló en {ip} ({onvif_duration:.1f}s)")
        
        # Test RTSP
        if 554 in analysis['ports'] and analysis['ports'][554]['open']:
            logger.debug(f"Probando protocolo RTSP en {ip}")
            rtsp_start = time.time()
            rtsp_success = await protocol_service.test_connection_async(ip, "rtsp", credentials)
            rtsp_duration = time.time() - rtsp_start
            
            if rtsp_success:
                analysis['protocols_detected'].append('RTSP')
                logger.info(f"✅ RTSP confirmado en {ip} ({rtsp_duration:.1f}s)")
                print(f"   ✅ RTSP confirmado en {ip}")
            else:
                logger.warning(f"❌ RTSP falló en {ip} ({rtsp_duration:.1f}s)")
        
        # Test HTTP/Amcrest
        if 80 in analysis['ports'] and analysis['ports'][80]['open']:
            logger.debug(f"Probando protocolo HTTP/Amcrest en {ip}")
            http_start = time.time()
            http_success = await protocol_service.test_connection_async(ip, "amcrest", credentials)
            http_duration = time.time() - http_start
            
            if http_success:
                analysis['protocols_detected'].append('HTTP')
                logger.info(f"✅ HTTP/Amcrest confirmado en {ip} ({http_duration:.1f}s)")
                print(f"   ✅ HTTP/Amcrest confirmado en {ip}")
            else:
                logger.warning(f"❌ HTTP/Amcrest falló en {ip} ({http_duration:.1f}s)")
        
        total_duration = time.time() - start_time
        logger.info(f"=== TEST DE PROTOCOLOS COMPLETADO ===")
        logger.info(f"Target IP: {ip}")
        logger.info(f"Protocolos detectados: {analysis['protocols_detected']}")
        logger.info(f"Duración total: {total_duration:.1f}s")
                
    except Exception as e:
        total_duration = time.time() - start_time
        logger.error(f"=== ERROR EN TEST DE PROTOCOLOS ===")
        logger.error(f"Target IP: {ip}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Duración hasta error: {total_duration:.1f}s")
        logger.error(f"Exception type: {type(e).__name__}")
        print(f"   ❌ Error probando protocolos: {e}")


def _generate_port_recommendations(analysis: dict, logger):
    """
    Genera recomendaciones basadas en análisis de puertos.
    
    Args:
        analysis: Diccionario de análisis
        logger: Logger para mensajes
    """
    ip = analysis['ip']
    
    logger.info(f"=== GENERANDO RECOMENDACIONES ===")
    logger.info(f"Target IP: {ip}")
    logger.info(f"Puertos críticos abiertos: {analysis['critical_open']}")
    logger.info(f"Total puertos abiertos: {analysis['total_open']}")
    
    if analysis['critical_open'] == 0:
        analysis['recommendations'].append(
            "❌ CRÍTICO: Ningún puerto crítico abierto - Verificar conectividad"
        )
        logger.warning(f"CRÍTICO: Ningún puerto crítico abierto en {ip}")
        logger.warning(f"Recomendación: Verificar firewall y configuración de red")
    elif analysis['ports'][80]['open'] and analysis['ports'][554]['open']:
        analysis['recommendations'].append(
            "✅ EXCELENTE: ONVIF y RTSP disponibles - Configuración óptima"
        )
        logger.info(f"Configuración óptima en {ip}: ONVIF y RTSP disponibles")
        logger.info(f"Recomendación: Usar ONVIF como protocolo principal, RTSP como backup")
    elif analysis['ports'][80]['open']:
        analysis['recommendations'].append(
            "✅ BUENO: ONVIF disponible - Protocolo principal funcional"
        )
        logger.info(f"ONVIF disponible en {ip} - Protocolo principal funcional")
        logger.info(f"Recomendación: Configurar aplicación para usar ONVIF")
    elif analysis['ports'][554]['open']:
        analysis['recommendations'].append(
            "⚠️ LIMITADO: Solo RTSP - Requiere workflow DMSS"
        )
        logger.warning(f"Solo RTSP disponible en {ip} - Requiere workflow DMSS")
        logger.warning(f"Recomendación: Verificar configuración ONVIF o usar DMSS")
    
    if not analysis['ports'][37777]['open']:
        analysis['recommendations'].append(
            "ℹ️ SDK Dahua no disponible - Funcionalidades avanzadas limitadas"
        )
        logger.info(f"SDK Dahua no disponible en {ip} - Funcionalidades avanzadas limitadas")
    
    logger.info(f"Total recomendaciones generadas: {len(analysis['recommendations'])}")
    logger.debug(f"Recomendaciones: {analysis['recommendations']}")


def analyze_camera_ports(ip: str) -> dict:
    """
    Análisis completo de puertos de cámara (compatibilidad síncrona).
    
    Args:
        ip: IP de la cámara
        
    Returns:
        Análisis completo de puertos
    """
    # Ejecutar versión async de forma síncrona
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(analyze_camera_ports_with_services(ip))
    except RuntimeError:
        # Si no hay loop, crear uno temporal
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(analyze_camera_ports_with_services(ip))
        finally:
            loop.close()


def bandwidth_test(ip: str, duration: int = 10) -> dict:
    """
    Test básico de ancho de banda hacia la cámara.
    
    Args:
        ip: IP de la cámara
        duration: Duración del test en segundos
        
    Returns:
        Estadísticas de ancho de banda
    """
    logger = logging.getLogger("NetworkAnalyzer")
    start_time = time.time()
    
    print(f"\n📊 Iniciando test de ancho de banda a {ip}...")
    print(f"   Duración: {duration} segundos")
    
    logger.info(f"=== INICIANDO TEST DE ANCHO DE BANDA ===")
    logger.info(f"Target IP: {ip}")
    logger.info(f"Duración configurada: {duration} segundos")
    logger.info(f"Puerto de test: 80 (HTTP/ONVIF)")
    logger.info(f"Timeout por conexión: 2.0s")
    logger.debug(f"Timestamp de inicio: {start_time}")
    
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
        
        test_duration = time.time() - start_time
        
        print(f"✅ Test completado:")
        print(f"   Conexiones: {successful_connections}/{result['connections_made']}")
        print(f"   Tiempo promedio: {result['avg_connection_time']:.1f}ms")
        print(f"   Performance: {result['estimated_bandwidth']}")
        print(f"   Duración del test: {test_duration:.1f}s")
        
        logger.info(f"=== TEST DE ANCHO DE BANDA COMPLETADO ===")
        logger.info(f"Target IP: {ip}")
        logger.info(f"Conexiones exitosas/total: {successful_connections}/{result['connections_made']}")
        logger.info(f"Tiempo promedio de conexión: {result['avg_connection_time']:.1f}ms")
        logger.info(f"Performance estimada: {result['estimated_bandwidth']}")
        logger.info(f"Duración del test: {test_duration:.1f}s")
        logger.info(f"Tasa de éxito: {result['successful_rate']:.1f}%")
        logger.debug(f"Tiempos de conexión: {connection_times[:5]}...")  # Primeros 5 tiempos
        
    except Exception as e:
        test_duration = time.time() - start_time
        print(f"❌ Error en test de ancho de banda: {e}")
        result['error'] = str(e)
        
        logger.error(f"=== ERROR EN TEST DE ANCHO DE BANDA ===")
        logger.error(f"Target IP: {ip}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Duración hasta error: {test_duration:.1f}s")
        logger.error(f"Exception type: {type(e).__name__}")
    
    return result


def network_route_analysis(target_ip: str) -> dict:
    """
    Análisis básico de ruta de red (traceroute simplificado).
    
    Args:
        target_ip: IP objetivo
        
    Returns:
        Información de ruta de red
    """
    logger = logging.getLogger("NetworkAnalyzer")
    start_time = time.time()
    
    print(f"\n🗺️ Analizando ruta de red a {target_ip}...")
    
    logger.info(f"=== INICIANDO ANÁLISIS DE RUTA DE RED ===")
    logger.info(f"Target IP: {target_ip}")
    logger.info(f"Método: Análisis de subnet + traceroute básico")
    logger.debug(f"Timestamp de inicio: {start_time}")
    logger.debug(f"Platform: {platform.system()}")
    
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
        logger.info(f"IP local detectada: {local_ip}")
        logger.debug(f"Método de detección: Socket UDP a 8.8.8.8:80")
        
        # Análisis básico de subnet
        local_parts = local_ip.split('.')
        target_parts = target_ip.split('.')
        
        # Verificar si están en la misma subnet /24
        if local_parts[:3] == target_parts[:3]:
            result['same_subnet'] = True
            result['gateway_required'] = False
            result['hops_estimated'] = 1
            print(f"   ✅ Misma subnet - Comunicación directa")
            logger.info(f"Análisis de subnet: Misma red /24")
            logger.info(f"Local subnet: {'.'.join(local_parts[:3])}.0/24")
            logger.info(f"Target subnet: {'.'.join(target_parts[:3])}.0/24")
            logger.info(f"Comunicación: Directa (1 salto)")
        else:
            result['hops_estimated'] = 2
            print(f"   ⚠️ Diferente subnet - Requiere gateway")
            logger.info(f"Análisis de subnet: Diferentes redes")
            logger.info(f"Local subnet: {'.'.join(local_parts[:3])}.0/24")
            logger.info(f"Target subnet: {'.'.join(target_parts[:3])}.0/24")
            logger.info(f"Comunicación: Via gateway (2+ saltos)")
        
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
                        logger.info(f"Traceroute completado: {hop_count} saltos detectados")
                        logger.debug(f"Comando ejecutado: tracert -h 5 {target_ip}")
                
            except subprocess.TimeoutExpired:
                print(f"   ⏱️ Traceroute timeout")
                logger.warning(f"Traceroute timeout después de 15s")
            except Exception as e:
                print(f"   ❌ Traceroute error: {str(e)}")
                logger.error(f"Error en traceroute: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error en análisis de ruta: {e}")
        result['error'] = str(e)
        logger.error(f"Error general en análisis de ruta: {str(e)}")
    
    analysis_duration = time.time() - start_time
    logger.info(f"=== ANÁLISIS DE RUTA COMPLETADO ===")
    logger.info(f"Target IP: {target_ip}")
    logger.info(f"IP local: {result.get('local_ip', 'Unknown')}")
    logger.info(f"Misma subnet: {result.get('same_subnet', False)}")
    logger.info(f"Saltos estimados: {result.get('hops_estimated', 0)}")
    logger.info(f"Duración del análisis: {analysis_duration:.1f}s")
    
    return result


async def main_async():
    """Función principal async del analizador de red."""
    logger = setup_logging()
    start_time = time.time()
    
    print("🌐 ANALIZADOR DE RED PARA CÁMARAS IP")
    print("="*60)
    print("Herramienta especializada en diagnóstico de conectividad")
    print(f"🔧 Servicios MVP: {'✅ Disponibles' if SERVICES_AVAILABLE else '❌ No disponibles'}")
    print()
    
    # Log de inicio
    logger.info("=== INICIANDO ANALIZADOR DE RED PARA CÁMARAS IP ===")
    logger.info("Herramienta especializada en diagnóstico de conectividad")
    logger.info(f"Servicios MVP disponibles: {SERVICES_AVAILABLE}")
    logger.info(f"Timestamp de inicio: {start_time}")
    logger.info(f"Directorio de trabajo: {Path.cwd()}")
    
    # Solicitar IP a analizar
    default_ip = "192.168.1.172"
    print(f"📍 IP por defecto: {default_ip}")
    
    # Intentar obtener IP configurada si los servicios están disponibles
    if SERVICES_AVAILABLE:
        try:
            # Usar ConfigService de forma síncrona
            config_service = get_config_service()
            # Por ahora usar IP por defecto, se puede mejorar después
            print(f"💡 ConfigService disponible - usando IP por defecto")
        except Exception as e:
            print(f"⚠️ ConfigService no disponible: {e}")
    else:
        print(f"💡 Usando funcionalidad básica del analizador")
    
    target_ip = input(f"\nIP a analizar [{default_ip}]: ").strip() or default_ip
    
    print(f"\n🚀 Iniciando análisis completo de {target_ip}...")
    print("="*60)
    
    logger.info(f"Iniciando análisis completo para IP: {target_ip}")
    
    # 1. Test de ping básico
    logger.info("Ejecutando test de ping")
    ping_results = ping_test(target_ip, count=4)
    logger.info(f"Ping completado - Éxito: {ping_results.get('success', False)}, Pérdida: {ping_results.get('packet_loss', 'N/A')}%")
    
    # 2. Análisis de puertos de cámara usando servicios MVP
    logger.info("Iniciando análisis de puertos de cámara")
    if SERVICES_AVAILABLE:
        print(f"🔧 Usando servicios MVP para análisis de puertos...")
        port_analysis = await analyze_camera_ports_with_services(target_ip)
    else:
        print(f"🔧 Usando análisis manual de puertos...")
        port_analysis = await analyze_camera_ports_manual(target_ip)
    logger.info(f"Puertos analizados - Críticos abiertos: {port_analysis['critical_open']}")
    logger.info(f"Método usado: {port_analysis.get('service_used', 'Manual')}")
    
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
    
    # Mostrar todos los puertos abiertos
    open_ports = [port for port, info in port_analysis['ports'].items() if info['open']]
    if open_ports:
        print(f"🔓 Puertos abiertos detectados: {len(open_ports)}")
        for port in open_ports:
            port_info = port_analysis['ports'][port]
            port_name = port_info.get('name', f'Puerto {port}')
            response_time = port_info.get('response_time', 0)
            if response_time > 0:
                print(f"   {port_name} ({port}): ✅ - {response_time:.1f}ms")
            else:
                print(f"   {port_name} ({port}): ✅")
    else:
        print(f"🔓 Puertos abiertos: Ninguno detectado")
    
    # Performance de red
    print(f"⚡ Performance: {bandwidth_results.get('estimated_bandwidth', 'N/A')}")
    
    # Topología
    if route_analysis.get('same_subnet', False):
        print(f"🗺️ Topología: Misma subnet (directo)")
    else:
        print(f"🗺️ Topología: Via gateway ({route_analysis.get('hops_estimated', '?')} saltos)")
    
    # Recomendaciones finales
    print(f"\n💡 RECOMENDACIONES:")
    
    if ping_results.get('success', False):
        if critical_ports > 0:
            print(f"✅ Red configurada correctamente")
            if port_analysis['ports'][80]['open']:
                print(f"   • Usar ONVIF como protocolo principal")
            if port_analysis['ports'][554]['open']:
                print(f"   • RTSP disponible como backup")
        elif len(open_ports) > 0:
            print(f"⚠️ Conectividad parcial detectada")
            print(f"   • Puertos críticos (80, 554) cerrados")
            print(f"   • Puertos alternativos disponibles: {', '.join(map(str, open_ports))}")
            print(f"   • Verificar configuración de puertos en la cámara")
            print(f"   • Algunas cámaras usan puertos no estándar")
        else:
            print(f"❌ Problemas de conectividad detectados:")
            print(f"   • Ningún puerto de cámara está abierto")
            print(f"   • Verificar puertos 80 y 554")
            print(f"   • Revisar firewall de cámara")
            print(f"   • Verificar que la cámara esté encendida")
    else:
        print(f"❌ Problemas de conectividad detectados:")
        print(f"   • Verificar IP y conectividad básica")
        print(f"   • Verificar que el dispositivo esté en la red")
    
    # Optimizaciones
    if bandwidth_results.get('avg_connection_time', 0) > 100:
        print(f"⚠️ Latencia alta detectada:")
        print(f"   • Considerar conexión ethernet")
        print(f"   • Verificar interferencias Wi-Fi")
        print(f"   • Revisar carga de red")
    
    print(f"\n✅ Análisis de red completado")
    print(f"📝 Logs guardados en: examples/logs/network_analyzer.log")
    print("="*60)
    
    # Calcular duración total
    total_duration = time.time() - start_time
    
    # Log de finalización con resumen
    logger.info("=== RESUMEN FINAL DEL ANÁLISIS ===")
    logger.info(f"IP analizada: {target_ip}")
    logger.info(f"Conectividad básica: {'OK' if ping_results.get('success', False) else 'FALLO'}")
    # Obtener información de puertos abiertos para logging
    open_ports = [port for port, info in port_analysis['ports'].items() if info['open']]
    open_ports_info = []
    for port in open_ports:
        port_info = port_analysis['ports'][port]
        port_name = port_info.get('name', f'Puerto {port}')
        response_time = port_info.get('response_time', 0)
        if response_time > 0:
            open_ports_info.append(f"{port_name}({port}):{response_time:.1f}ms")
        else:
            open_ports_info.append(f"{port_name}({port})")
    
    logger.info(f"Puertos críticos: {critical_ports}/{total_critical}")
    logger.info(f"Puertos abiertos totales: {len(open_ports)}")
    if open_ports_info:
        logger.info(f"Puertos abiertos: {', '.join(open_ports_info)}")
    else:
        logger.info(f"Puertos abiertos: Ninguno")
    logger.info(f"Performance: {bandwidth_results.get('estimated_bandwidth', 'N/A')}")
    logger.info(f"Misma subnet: {route_analysis.get('same_subnet', False)}")
    logger.info(f"Duración total del análisis: {total_duration:.1f}s")
    logger.info(f"Servicios MVP utilizados: {SERVICES_AVAILABLE}")
    logger.info("=== ANÁLISIS DE RED COMPLETADO ===")
    logger.info("Logs guardados en: examples/logs/network_analyzer.log")
    logger.info(f"Timestamp de finalización: {time.time()}")


def main():
    """Función principal del analizador de red (wrapper síncrono)."""
    try:
        # Ejecutar versión async
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n⚠️ Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en el análisis: {e}")


if __name__ == "__main__":
    main() 