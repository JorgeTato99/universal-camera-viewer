"""
Detector y diagnóstico completo de cámaras Dahua en red.
Herramienta de diagnóstico para identificar y analizar cámaras disponibles.

Funcionalidades incluidas:
- Escaneo de red para detectar cámaras
- Análisis de puertos comunes (80, 554, 37777)
- Test de protocolos soportados
- Diagnóstico de conectividad
- Reporte de configuración recomendada
- Detección específica de Hero-K51H
"""

import sys
import socket
import threading
import time
import logging
import ipaddress
import asyncio
from typing import Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

# Imports con manejo de errores
try:
    from utils.config import get_config
    from services.protocol_service import ProtocolService
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("💡 Asegúrate de ejecutar desde el directorio raíz del proyecto")
    print("   cd universal-camera-viewer")
    print("   python examples/diagnostics/camera_detector.py")
    sys.exit(1)


def setup_logging():
    """Configura logging para diagnóstico."""
    import logging
    
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "camera_detector.log"
    
    # Limpiar configuración existente
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True
    )
    
    print(f"📝 Logs guardándose en: {log_file}")
    print(f"📊 Nivel de logging: INFO")
    print(f"🔄 Formato: timestamp - módulo - nivel - mensaje")


def scan_port(ip: str, port: int, timeout: float = 2.0) -> bool:
    """
    Escanea un puerto específico en una IP.
    
    Args:
        ip: Dirección IP a escanear
        port: Puerto a verificar
        timeout: Timeout en segundos
        
    Returns:
        True si el puerto está abierto
    """
    logger = logging.getLogger(__name__)
    
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        response_time = (time.time() - start_time) * 1000  # en milisegundos
        is_open = result == 0
        
        logger.debug(f"Puerto {port} en {ip}: {'ABIERTO' if is_open else 'CERRADO'} (response: {response_time:.1f}ms)")
        
        return is_open
    except Exception as e:
        logger.debug(f"Error escaneando puerto {port} en {ip}: {e}")
        return False


def scan_host(ip: str, ports: list) -> dict:
    """
    Escanea todos los puertos especificados en una IP.
    
    Args:
        ip: Dirección IP a escanear
        ports: Lista de puertos a verificar
        
    Returns:
        Diccionario con resultados del escaneo
    """
    logger = logging.getLogger(__name__)
    
    result = {
        'ip': ip,
        'open_ports': [],
        'likely_camera': False,
        'protocols': []
    }
    
    start_time = time.time()
    logger.info(f"🔍 Iniciando escaneo de IP {ip} - Puertos a verificar: {ports}")
    print(f"🔍 Escaneando IP {ip} - Puertos: {ports}")
    
    for port in ports:
        logger.info(f"   Probando puerto {port} en {ip}...")
        if scan_port(ip, port, timeout=1.5):
            result['open_ports'].append(port)
            logger.info(f"   ✅ Puerto {port} ABIERTO en {ip}")
            print(f"   ✅ Puerto {port} ABIERTO")
        else:
            logger.info(f"   ❌ Puerto {port} CERRADO en {ip}")
    
    scan_duration = (time.time() - start_time) * 1000  # en milisegundos
    logger.info(f"Resultado escaneo {ip}: {len(result['open_ports'])} puertos abiertos de {len(ports)} escaneados (duración: {scan_duration:.1f}ms)")
    print(f"📊 Resultado: {len(result['open_ports'])} puertos abiertos de {len(ports)} escaneados")
    logger.info(f"Puertos abiertos en {ip}: {result['open_ports']}")
    logger.info(f"Puertos cerrados en {ip}: {[p for p in ports if p not in result['open_ports']]}")
    
    # Analizar puertos para determinar si es una cámara
    camera_indicators = []
    
    if 80 in result['open_ports']:
        camera_indicators.append('HTTP/ONVIF')
        result['protocols'].append('ONVIF')
        result['protocols'].append('HTTP')
        logger.info(f"Puerto 80 detectado en {ip} - Protocolos: HTTP/ONVIF")
    
    if 554 in result['open_ports']:
        camera_indicators.append('RTSP')
        result['protocols'].append('RTSP')
        logger.info(f"Puerto 554 detectado en {ip} - Protocolo: RTSP")
    
    if 37777 in result['open_ports']:
        camera_indicators.append('Dahua SDK')
        result['protocols'].append('SDK')
        logger.info(f"Puerto 37777 detectado en {ip} - Protocolo: Dahua SDK")
    
    if 8000 in result['open_ports']:
        camera_indicators.append('HTTP Alt')
        logger.info(f"Puerto 8000 detectado en {ip} - Protocolo: HTTP Alt")
    
    if 443 in result['open_ports']:
        logger.info(f"Puerto 443 detectado en {ip} - Protocolo: HTTPS")
    
    # Considerar dispositivo como cámara si tiene múltiples puertos típicos
    if len(result['open_ports']) >= 2 and any(p in result['open_ports'] for p in [80, 554, 37777]):
        result['likely_camera'] = True
        logger.info(f"Dispositivo en {ip} clasificado como CÁMARA - Indicadores: {camera_indicators}")
    else:
        logger.info(f"Dispositivo en {ip} NO clasificado como cámara - Puertos insuficientes")
    
    logger.info(f"Análisis de protocolos para {ip}: {result['protocols']}")
    return result


def scan_network_range(network: str, ports: list, max_workers: int = 50) -> list:
    """
    Escanea un rango de red completo buscando cámaras.
    
    Args:
        network: Red en formato CIDR (ej: "192.168.1.0/24")
        ports: Lista de puertos a escanear
        max_workers: Número máximo de hilos concurrentes
        
    Returns:
        Lista de dispositivos encontrados
    """
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    print(f"🔍 Escaneando red {network}...")
    print(f"   Puertos a escanear: {ports}")
    print(f"   Hilos concurrentes: {max_workers}")
    
    logger.info(f"Iniciando escaneo de red {network} con puertos {ports} usando {max_workers} hilos")
    logger.info(f"Puertos específicos a verificar: {ports}")
    logger.info(f"Configuración de escaneo: timeout=1.5s por puerto, max_workers={max_workers}")
    
    try:
        network_obj = ipaddress.IPv4Network(network, strict=False)
        hosts = list(network_obj.hosts())
        
        if len(hosts) > 254:
            print(f"⚠️ Red muy grande ({len(hosts)} hosts), limitando a /24")
            logger.warning(f"Red muy grande ({len(hosts)} hosts), limitando a /24")
            # Limitar a subnet /24 de la IP actual
            base_ip = str(hosts[0]).rsplit('.', 1)[0]
            network = f"{base_ip}.0/24"
            network_obj = ipaddress.IPv4Network(network, strict=False)
            hosts = list(network_obj.hosts())
            logger.info(f"Red limitada a: {network} ({len(hosts)} hosts)")
        
        print(f"   Escaneando {len(hosts)} hosts...")
        logger.info(f"Rango de escaneo: {len(hosts)} hosts en {network}")
        logger.info(f"Primera IP: {hosts[0]}, Última IP: {hosts[-1]}")
        
        devices = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {
                executor.submit(scan_host, str(host), ports): str(host) 
                for host in hosts
            }
            
            for future in as_completed(future_to_ip):
                result = future.result()
                completed += 1
                
                # Mostrar progreso cada 10%
                if completed % max(1, len(hosts) // 10) == 0:
                    progress = (completed / len(hosts)) * 100
                    print(f"   Progreso: {progress:.0f}% ({completed}/{len(hosts)})")
                
                if result['open_ports']:
                    devices.append(result)
                    logger.info(f"Dispositivo encontrado: {result['ip']} - Puertos: {result['open_ports']} - Protocolos: {result.get('protocols', [])}")
        
        scan_duration = (time.time() - start_time) * 1000  # en milisegundos
        logger.info(f"Escaneo de red completado: {len(devices)} dispositivos encontrados de {len(hosts)} hosts escaneados")
        logger.info(f"Duración total del escaneo: {scan_duration:.1f}ms ({scan_duration/1000:.1f}s)")
        logger.info(f"Tiempo promedio por host: {scan_duration/len(hosts):.1f}ms")
        
        if devices:
            logger.info(f"Dispositivos encontrados: {[d['ip'] for d in devices]}")
            cameras = [d for d in devices if d.get('likely_camera', False)]
            logger.info(f"Cámaras detectadas: {len(cameras)} de {len(devices)} dispositivos")
        
        return devices
        
    except Exception as e:
        print(f"❌ Error escaneando red: {e}")
        logger.error(f"Error durante escaneo de red {network}: {e}", exc_info=True)
        return []


def test_camera_protocols(ip: str, credentials: Optional[dict] = None) -> dict:
    """
    Prueba qué protocolos soporta una cámara específica.
    
    Args:
        ip: IP de la cámara a probar
        credentials: Credenciales para autenticación
        
    Returns:
        Diccionario con protocolos soportados
    """
    logger = logging.getLogger(__name__)
    
    print(f"\n🧪 Probando protocolos en {ip}...")
    logger.info(f"Iniciando tests de protocolos para {ip}")
    
    result = {
        'ip': ip,
        'onvif': False,
        'rtsp': False,
        'http': False,
        'sdk': False,
        'details': {}
    }
    
    if not credentials:
        credentials = {'username': 'admin', 'password': 'admin'}
        logger.info(f"Usando credenciales por defecto para {ip}: admin/admin")
    else:
        logger.info(f"Usando credenciales personalizadas para {ip}: {credentials['username']}")
    
    try:
        # Usar nueva API de ProtocolService
        protocol_service = ProtocolService()
        
        # Test ONVIF
        try:
            print("   Probando ONVIF...")
            logger.info(f"Test ONVIF iniciado para {ip}")
            start_time = time.time()
            
            success = asyncio.run(protocol_service.test_connection_async(ip, "onvif", credentials))
            onvif_duration = (time.time() - start_time) * 1000
            
            if success:
                result['onvif'] = True
                result['details']['onvif'] = "Funcional"
                print("   ✅ ONVIF: Funcional")
                logger.info(f"ONVIF exitoso en {ip} (duración: {onvif_duration:.1f}ms)")
                
                # Obtener información del dispositivo
                logger.info(f"Obteniendo información ONVIF de {ip}")
                device_info = asyncio.run(protocol_service.get_device_info_async(ip, "onvif", credentials))
                if device_info:
                    result['details']['onvif_info'] = device_info
                    logger.info(f"Información ONVIF obtenida de {ip}: {len(device_info)} campos")
            else:
                result['details']['onvif'] = "Conexión falló"
                print("   ❌ ONVIF: Conexión falló")
                logger.warning(f"ONVIF falló en {ip} (duración: {onvif_duration:.1f}ms)")
        except Exception as e:
            result['details']['onvif'] = f"Error: {str(e)[:50]}"
            print(f"   ❌ ONVIF: Error - {str(e)[:50]}")
            logger.error(f"Error en test ONVIF para {ip}: {e}")
        
        # Test RTSP
        try:
            print("   Probando RTSP...")
            logger.info(f"Test RTSP iniciado para {ip}")
            start_time = time.time()
            
            success = asyncio.run(protocol_service.test_connection_async(ip, "rtsp", credentials))
            rtsp_duration = (time.time() - start_time) * 1000
            
            if success:
                result['rtsp'] = True
                result['details']['rtsp'] = "Funcional"
                print("   ✅ RTSP: Funcional")
                logger.info(f"RTSP exitoso en {ip} (duración: {rtsp_duration:.1f}ms)")
            else:
                result['details']['rtsp'] = "Conexión falló (puede necesitar DMSS)"
                print("   ⚠️ RTSP: Falló (puede necesitar workflow DMSS)")
                logger.warning(f"RTSP falló en {ip} (duración: {rtsp_duration:.1f}ms) - puede necesitar workflow DMSS")
        except Exception as e:
            result['details']['rtsp'] = f"Error: {str(e)[:50]}"
            print(f"   ❌ RTSP: Error - {str(e)[:50]}")
            logger.error(f"Error en test RTSP para {ip}: {e}")
        
        # Test HTTP/Amcrest
        try:
            print("   Probando HTTP/Amcrest...")
            logger.info(f"Test HTTP/Amcrest iniciado para {ip}")
            start_time = time.time()
            
            success = asyncio.run(protocol_service.test_connection_async(ip, "amcrest", credentials))
            http_duration = (time.time() - start_time) * 1000
            
            if success:
                result['http'] = True
                result['details']['http'] = "Funcional"
                print("   ✅ HTTP: Funcional")
                logger.info(f"HTTP/Amcrest exitoso en {ip} (duración: {http_duration:.1f}ms)")
            else:
                result['details']['http'] = "No compatible (esperado para Hero-K51H)"
                print("   ⚠️ HTTP: No compatible (esperado)")
                logger.info(f"HTTP/Amcrest no compatible en {ip} (duración: {http_duration:.1f}ms) - esperado para Hero-K51H")
        except Exception as e:
            result['details']['http'] = f"No compatible: {str(e)[:50]}"
            print(f"   ❌ HTTP: No compatible - {str(e)[:50]}")
            logger.error(f"Error en test HTTP/Amcrest para {ip}: {e}")
        
    except ImportError:
        print("   ⚠️ Módulos de conexión no disponibles para test completo")
        logger.warning(f"Módulos de conexión no disponibles para tests completos en {ip}")
    
    # Resumen de tests
    successful_protocols = [p for p, v in result.items() if p in ['onvif', 'rtsp', 'http'] and v]
    logger.info(f"Tests de protocolos completados para {ip}: {len(successful_protocols)}/{3} exitosos - {successful_protocols}")
    
    return result


def detect_camera_model(ip: str, credentials: Optional[dict] = None) -> dict:
    """
    Intenta detectar el modelo específico de la cámara.
    
    Args:
        ip: IP de la cámara
        credentials: Credenciales para autenticación
        
    Returns:
        Información del modelo detectado
    """
    logger = logging.getLogger(__name__)
    
    print(f"\n🔎 Detectando modelo de cámara en {ip}...")
    logger.info(f"Iniciando detección de modelo para {ip}")
    
    result = {
        'ip': ip,
        'model': 'Unknown',
        'manufacturer': 'Unknown',
        'firmware': 'Unknown',
        'hero_k51h': False
    }
    
    if not credentials:
        credentials = {'username': 'admin', 'password': 'admin'}
        logger.info(f"Usando credenciales por defecto para detección de modelo en {ip}")
    
    try:
        # Usar nueva API de ProtocolService
        protocol_service = ProtocolService()
        
        # Intentar obtener información vía ONVIF primero
        logger.info(f"Obteniendo información de dispositivo ONVIF de {ip}")
        device_info = asyncio.run(protocol_service.get_device_info_async(ip, "onvif", credentials))
        
        if device_info:
            logger.info(f"Información ONVIF obtenida de {ip}: {len(device_info)} campos")
            logger.debug(f"Campos ONVIF disponibles: {list(device_info.keys())}")
            
            # Extraer información del dispositivo
            for key, value in device_info.items():
                key_lower = key.lower()
                value_str = str(value).lower()
                
                if 'model' in key_lower or 'device' in key_lower:
                    result['model'] = str(value)
                    logger.info(f"Modelo detectado en {ip}: {value}")
                    if 'hero-k51h' in value_str or 'hero_k51h' in value_str:
                        result['hero_k51h'] = True
                        logger.info(f"🎯 Hero-K51H confirmado en {ip}")
                
                elif 'manufacturer' in key_lower or 'vendor' in key_lower:
                    result['manufacturer'] = str(value)
                    logger.info(f"Fabricante detectado en {ip}: {value}")
                
                elif 'firmware' in key_lower or 'version' in key_lower:
                    result['firmware'] = str(value)
                    logger.info(f"Firmware detectado en {ip}: {value}")
            
            print(f"   Modelo: {result['model']}")
            print(f"   Fabricante: {result['manufacturer']}")
            print(f"   Firmware: {result['firmware']}")
            
            if result['hero_k51h']:
                print("   🎯 ¡Dahua Hero-K51H detectado!")
            
            logger.info(f"Detección de modelo completada para {ip}: {result['model']} ({result['manufacturer']})")
        else:
            logger.warning(f"No se pudo obtener información ONVIF de {ip}")
            
    except Exception as e:
        print(f"   ❌ Error detectando modelo: {str(e)}")
        logger.error(f"Error detectando modelo en {ip}: {e}")
    
    return result


def generate_configuration_recommendations(devices: list) -> dict:
    """
    Genera recomendaciones de configuración basadas en los dispositivos encontrados.
    
    Args:
        devices: Lista de dispositivos detectados
        
    Returns:
        Recomendaciones de configuración
    """
    print("\n💡 GENERANDO RECOMENDACIONES DE CONFIGURACIÓN")
    print("="*60)
    
    cameras = [d for d in devices if d.get('likely_camera', False)]
    
    if not cameras:
        print("❌ No se detectaron cámaras en la red")
        return {}
    
    print(f"📹 Se detectaron {len(cameras)} cámaras probables:")
    
    recommendations = {
        'primary_camera': None,
        'protocol_recommendations': {},
        'network_config': {},
        'troubleshooting': []
    }
    
    for i, camera in enumerate(cameras, 1):
        ip = camera['ip']
        protocols = camera.get('protocols', [])
        
        print(f"\n{i}. Cámara en {ip}:")
        print(f"   Puertos abiertos: {camera['open_ports']}")
        print(f"   Protocolos detectados: {protocols}")
        
        # Determinar protocolo recomendado
        if 'ONVIF' in protocols:
            recommended = 'ONVIF'
            reason = 'Estándar universal, conexión inmediata'
        elif 'RTSP' in protocols:
            recommended = 'RTSP'
            reason = 'Funcional pero requiere workflow DMSS'
        elif 'HTTP' in protocols:
            recommended = 'HTTP'
            reason = 'Básico, limitado en funcionalidades'
        else:
            recommended = 'NONE'
            reason = 'No se detectaron protocolos compatibles'
        
        recommendations['protocol_recommendations'][ip] = {
            'primary': recommended,
            'reason': reason,
            'available': protocols
        }
        
        print(f"   Recomendado: {recommended} ({reason})")
        
        # Seleccionar cámara principal (primera con ONVIF o primera disponible)
        if not recommendations['primary_camera']:
            if recommended == 'ONVIF':
                recommendations['primary_camera'] = ip
            elif not recommendations['primary_camera']:
                recommendations['primary_camera'] = ip
    
    # Recomendaciones generales
    print(f"\n🎯 CÁMARA PRINCIPAL RECOMENDADA: {recommendations['primary_camera']}")
    
    if recommendations['primary_camera']:
        primary_protocol = recommendations['protocol_recommendations'][recommendations['primary_camera']]['primary']
        print(f"   Protocolo: {primary_protocol}")
        
        # Configuración de .env recomendada
        print(f"\n📝 CONFIGURACIÓN .env RECOMENDADA:")
        print(f"CAMERA_IP={recommendations['primary_camera']}")
        print(f"CAMERA_USER=admin")
        print(f"CAMERA_PASSWORD=tu_password_aqui")
        
        if primary_protocol == 'ONVIF':
            print(f"ONVIF_PORT=80")
        if 'RTSP' in recommendations['protocol_recommendations'][recommendations['primary_camera']]['available']:
            print(f"RTSP_PORT=554")
        if 'HTTP' in recommendations['protocol_recommendations'][recommendations['primary_camera']]['available']:
            print(f"HTTP_PORT=80")
    
    return recommendations


def main():
    """Función principal del detector de cámaras."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    
    print("🕵️ DETECTOR Y DIAGNÓSTICO DE CÁMARAS DAHUA")
    print("="*60)
    print("Herramienta de diagnóstico para detectar y analizar cámaras en red")
    print()
    
    # Log de inicio
    logger.info("=== INICIANDO DETECTOR DE CÁMARAS DAHUA ===")
    logger.info("Herramienta de diagnóstico para detectar y analizar cámaras en red")
    logger.info(f"Versión del detector: 2.0 - Logging mejorado")
    logger.info(f"Directorio de trabajo: {Path.cwd()}")
    logger.info(f"Python version: {sys.version}")
    
    # Obtener configuración actual
    try:
        config = get_config()
        cameras_config = config.get_cameras_config()
        
        if cameras_config:
            # Usar la primera cámara configurada
            first_camera = cameras_config[0]
            current_ip = first_camera['ip']
            credentials = {
                'username': first_camera['username'],
                'password': first_camera['password']
            }
            print(f"📍 Configuración actual:")
            print(f"   IP configurada: {current_ip}")
            print(f"   Usuario: {first_camera['username']}")
            print(f"   Marca: {first_camera['brand']}")
            
            # Log configuración
            logger.info(f"Configuración cargada - IP: {current_ip}, Usuario: {first_camera['username']}")
        else:
            current_ip = None
            credentials = {'username': 'admin', 'password': 'admin'}
            print("⚠️ No hay cámaras configuradas, usando credenciales por defecto")
            logger.warning("No hay cámaras configuradas, usando credenciales por defecto")
    except Exception as e:
        current_ip = None
        credentials = {'username': 'admin', 'password': 'admin'}
        print(f"⚠️ Error cargando configuración: {e}, usando credenciales por defecto")
        logger.warning(f"Error cargando configuración: {e}, usando credenciales por defecto")
    
    # Opciones de escaneo
    print(f"\n🔍 OPCIONES DE DIAGNÓSTICO:")
    print(f"1. Escanear red local completa")
    print(f"2. Probar IP específica")
    if current_ip:
        print(f"3. Analizar IP configurada ({current_ip})")
    
    try:
        choice = input("\nSelecciona opción (1-3): ").strip()
        
        if choice == "1":
            # Escaneo completo de red
            network = input("Red a escanear (ej: 192.168.1.0/24) [auto]: ").strip()
            if not network:
                # Detectar red local automáticamente
                import subprocess
                try:
                    result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
                    # Simplificado: usar red común
                    network = "192.168.1.0/24"
                except:
                    network = "192.168.1.0/24"
            
            logger.info(f"Iniciando escaneo completo de red: {network}")
            ports = [80, 554, 37777, 8000, 443]
            devices = scan_network_range(network, ports)
            
            if devices:
                logger.info(f"Escaneo completado: {len(devices)} dispositivos encontrados")
                for device in devices:
                    if device.get('likely_camera', False):
                        logger.info(f"Cámara detectada en {device['ip']} - Puertos: {device['open_ports']} - Protocolos: {device['protocols']}")
                        
                recommendations = generate_configuration_recommendations(devices)
                logger.info("Recomendaciones de configuración generadas")
            else:
                print("❌ No se encontraron dispositivos en la red")
                logger.warning("Escaneo de red completado sin encontrar dispositivos")
        
        elif choice == "2":
            # IP específica
            ip = input("IP a analizar: ").strip()
            if ip:
                logger.info(f"Analizando IP específica: {ip}")
                # Escaneo de puertos
                ports = [80, 554, 37777, 8000, 443]
                logger.info(f"Puertos a escanear en {ip}: {ports}")
                print(f"\n🔍 ESCANEO DE PUERTOS EN {ip}")
                print(f"Puertos a verificar: {ports}")
                print(f"Puertos típicos de cámaras: 80 (HTTP/ONVIF), 554 (RTSP), 37777 (Dahua SDK), 8000 (HTTP Alt), 443 (HTTPS)")
                
                device = scan_host(ip, ports)
                
                if device['open_ports']:
                    print(f"\n✅ Dispositivo encontrado en {ip}")
                    print(f"   Puertos abiertos: {device['open_ports']}")
                    print(f"   Protocolos detectados: {device['protocols']}")
                    
                    logger.info(f"Dispositivo encontrado en {ip} - Puertos: {device['open_ports']} - Protocolos: {device['protocols']}")
                    
                    # Tests detallados
                    protocol_test = test_camera_protocols(ip, credentials)
                    model_info = detect_camera_model(ip, credentials)
                    
                    logger.info(f"Tests de protocolos completados para {ip}: ONVIF={protocol_test['onvif']}, RTSP={protocol_test['rtsp']}, HTTP={protocol_test['http']}")
                else:
                    print(f"❌ No hay puertos abiertos en {ip}")
                    logger.warning(f"No hay puertos abiertos en {ip}")
                    logger.info(f"Todos los puertos escaneados en {ip} están cerrados: {ports}")
        
        elif choice == "3" and current_ip:
            # Analizar IP configurada
            print(f"\n🔎 Analizando IP configurada: {current_ip}")
            
            # Escaneo de puertos
            ports = [80, 554, 37777, 8000, 443]
            logger.info(f"Analizando IP configurada {current_ip} - Puertos a escanear: {ports}")
            print(f"Puertos a verificar: {ports}")
            print(f"Puertos típicos de cámaras: 80 (HTTP/ONVIF), 554 (RTSP), 37777 (Dahua SDK), 8000 (HTTP Alt), 443 (HTTPS)")
            
            device = scan_host(current_ip, ports)
            
            if device['open_ports']:
                print(f"\n✅ Cámara accesible en {current_ip}")
                
                # Tests completos
                protocol_test = test_camera_protocols(current_ip, credentials)
                model_info = detect_camera_model(current_ip, credentials)
                
                # Resumen
                print(f"\n📊 RESUMEN DE DIAGNÓSTICO:")
                print(f"   IP: {current_ip}")
                print(f"   ONVIF: {'✅' if protocol_test['onvif'] else '❌'}")
                print(f"   RTSP: {'✅' if protocol_test['rtsp'] else '⚠️'}")
                print(f"   HTTP: {'✅' if protocol_test['http'] else '❌'}")
                
                if model_info['hero_k51h']:
                    print(f"   🎯 Hero-K51H: ✅ Confirmado")
                    print(f"\n💡 Para Hero-K51H recomendamos:")
                    print(f"   • Usar ONVIF como protocolo principal")
                    print(f"   • RTSP como backup (requiere workflow DMSS)")
                    print(f"   • HTTP no es compatible")
            else:
                print(f"❌ No se puede acceder a {current_ip}")
                print(f"💡 Verificar:")
                print(f"   • IP correcta")
                print(f"   • Conectividad de red")
                print(f"   • Firewall/puertos bloqueados")
        
        else:
            print("❌ Opción inválida")
    
    except KeyboardInterrupt:
        print("\n🛑 Diagnóstico interrumpido por usuario")
        logger.info("Diagnóstico interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error durante diagnóstico: {e}")
        logger.error(f"Error durante diagnóstico: {e}")
    
    total_duration = time.time() - start_time
    
    print("\n✅ Diagnóstico completado")
    print(f"⏱️ Duración total: {total_duration:.1f} segundos")
    print("📝 Logs guardados en: examples/logs/camera_detector.log")
    print("="*60)
    
    logger.info("=== DIAGNÓSTICO COMPLETADO ===")
    logger.info(f"Duración total del diagnóstico: {total_duration:.1f}s")
    logger.info("Logs guardados en: examples/logs/camera_detector.log")
    logger.info("=== FIN DEL DETECTOR ===")


if __name__ == "__main__":
    main() 