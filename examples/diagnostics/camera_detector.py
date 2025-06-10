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
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from utils.config import get_config


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
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True
    )
    
    print(f"📝 Logs guardándose en: {log_file}")


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
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
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
    result = {
        'ip': ip,
        'open_ports': [],
        'likely_camera': False,
        'protocols': []
    }
    
    for port in ports:
        if scan_port(ip, port, timeout=1.5):
            result['open_ports'].append(port)
    
    # Analizar puertos para determinar si es una cámara
    camera_indicators = []
    
    if 80 in result['open_ports']:
        camera_indicators.append('HTTP/ONVIF')
        result['protocols'].append('ONVIF')
        result['protocols'].append('HTTP')
    
    if 554 in result['open_ports']:
        camera_indicators.append('RTSP')
        result['protocols'].append('RTSP')
    
    if 37777 in result['open_ports']:
        camera_indicators.append('Dahua SDK')
        result['protocols'].append('SDK')
    
    if 8000 in result['open_ports']:
        camera_indicators.append('HTTP Alt')
    
    # Considerar dispositivo como cámara si tiene múltiples puertos típicos
    if len(result['open_ports']) >= 2 and any(p in result['open_ports'] for p in [80, 554, 37777]):
        result['likely_camera'] = True
    
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
    
    print(f"🔍 Escaneando red {network}...")
    print(f"   Puertos: {ports}")
    print(f"   Hilos: {max_workers}")
    
    logger.info(f"Iniciando escaneo de red {network} con puertos {ports} usando {max_workers} hilos")
    
    try:
        network_obj = ipaddress.IPv4Network(network, strict=False)
        hosts = list(network_obj.hosts())
        
        if len(hosts) > 254:
            print(f"⚠️ Red muy grande ({len(hosts)} hosts), limitando a /24")
            # Limitar a subnet /24 de la IP actual
            base_ip = str(hosts[0]).rsplit('.', 1)[0]
            network = f"{base_ip}.0/24"
            network_obj = ipaddress.IPv4Network(network, strict=False)
            hosts = list(network_obj.hosts())
        
        print(f"   Escaneando {len(hosts)} hosts...")
        
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
                    logger.info(f"Dispositivo encontrado: {result['ip']} - Puertos: {result['open_ports']}")
        
        logger.info(f"Escaneo de red completado: {len(devices)} dispositivos encontrados de {len(hosts)} hosts escaneados")
        return devices
        
    except Exception as e:
        print(f"❌ Error escaneando red: {e}")
        return []


def test_camera_protocols(ip: str, credentials: dict = None) -> dict:
    """
    Prueba qué protocolos soporta una cámara específica.
    
    Args:
        ip: IP de la cámara a probar
        credentials: Credenciales para autenticación
        
    Returns:
        Diccionario con protocolos soportados
    """
    print(f"\n🧪 Probando protocolos en {ip}...")
    
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
    
    try:
        from connections import ConnectionFactory
        
        # Test ONVIF
        try:
            print("   Probando ONVIF...")
            onvif_conn = ConnectionFactory.create_connection(
                "onvif", ip, credentials
            )
            if onvif_conn.connect():
                result['onvif'] = True
                result['details']['onvif'] = "Funcional"
                print("   ✅ ONVIF: Funcional")
                onvif_conn.disconnect()
            else:
                result['details']['onvif'] = "Conexión falló"
                print("   ❌ ONVIF: Conexión falló")
        except Exception as e:
            result['details']['onvif'] = f"Error: {str(e)[:50]}"
            print(f"   ❌ ONVIF: Error - {str(e)[:50]}")
        
        # Test RTSP
        try:
            print("   Probando RTSP...")
            rtsp_conn = ConnectionFactory.create_connection(
                "rtsp", ip, credentials
            )
            if rtsp_conn.connect():
                result['rtsp'] = True
                result['details']['rtsp'] = "Funcional"
                print("   ✅ RTSP: Funcional")
                rtsp_conn.disconnect()
            else:
                result['details']['rtsp'] = "Conexión falló (puede necesitar DMSS)"
                print("   ⚠️ RTSP: Falló (puede necesitar workflow DMSS)")
        except Exception as e:
            result['details']['rtsp'] = f"Error: {str(e)[:50]}"
            print(f"   ❌ RTSP: Error - {str(e)[:50]}")
        
        # Test HTTP/Amcrest
        try:
            print("   Probando HTTP/Amcrest...")
            http_conn = ConnectionFactory.create_connection(
                "amcrest", ip, credentials
            )
            if http_conn.connect():
                result['http'] = True
                result['details']['http'] = "Funcional"
                print("   ✅ HTTP: Funcional")
                http_conn.disconnect()
            else:
                result['details']['http'] = "No compatible (esperado para Hero-K51H)"
                print("   ⚠️ HTTP: No compatible (esperado)")
        except Exception as e:
            result['details']['http'] = f"No compatible: {str(e)[:50]}"
            print(f"   ❌ HTTP: No compatible - {str(e)[:50]}")
        
    except ImportError:
        print("   ⚠️ Módulos de conexión no disponibles para test completo")
    
    return result


def detect_camera_model(ip: str, credentials: dict = None) -> dict:
    """
    Intenta detectar el modelo específico de la cámara.
    
    Args:
        ip: IP de la cámara
        credentials: Credenciales para autenticación
        
    Returns:
        Información del modelo detectado
    """
    print(f"\n🔎 Detectando modelo de cámara en {ip}...")
    
    result = {
        'ip': ip,
        'model': 'Unknown',
        'manufacturer': 'Unknown',
        'firmware': 'Unknown',
        'hero_k51h': False
    }
    
    if not credentials:
        credentials = {'username': 'admin', 'password': 'admin'}
    
    try:
        from connections import ONVIFConnection
        
        conn = ONVIFConnection(ip, credentials)
        if conn.connect():
            device_info = conn.get_device_info()
            
            if device_info:
                # Extraer información del dispositivo
                for key, value in device_info.items():
                    key_lower = key.lower()
                    value_str = str(value).lower()
                    
                    if 'model' in key_lower or 'device' in key_lower:
                        result['model'] = str(value)
                        if 'hero-k51h' in value_str or 'hero_k51h' in value_str:
                            result['hero_k51h'] = True
                    
                    elif 'manufacturer' in key_lower or 'vendor' in key_lower:
                        result['manufacturer'] = str(value)
                    
                    elif 'firmware' in key_lower or 'version' in key_lower:
                        result['firmware'] = str(value)
                
                print(f"   Modelo: {result['model']}")
                print(f"   Fabricante: {result['manufacturer']}")
                print(f"   Firmware: {result['firmware']}")
                
                if result['hero_k51h']:
                    print("   🎯 ¡Dahua Hero-K51H detectado!")
                
            conn.disconnect()
            
    except Exception as e:
        print(f"   ❌ Error detectando modelo: {str(e)}")
    
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
    
    print("🕵️ DETECTOR Y DIAGNÓSTICO DE CÁMARAS DAHUA")
    print("="*60)
    print("Herramienta de diagnóstico para detectar y analizar cámaras en red")
    print()
    
    # Log de inicio
    logger.info("=== INICIANDO DETECTOR DE CÁMARAS DAHUA ===")
    logger.info("Herramienta de diagnóstico para detectar y analizar cámaras en red")
    
    # Obtener configuración actual
    try:
        config = get_config()
        current_ip = config.camera_ip
        credentials = {
            'username': config.camera_user,
            'password': config.camera_password
        }
        print(f"📍 Configuración actual:")
        print(f"   IP configurada: {current_ip}")
        print(f"   Usuario: {config.camera_user}")
        
        # Log configuración
        logger.info(f"Configuración cargada - IP: {current_ip}, Usuario: {config.camera_user}")
    except:
        current_ip = None
        credentials = {'username': 'admin', 'password': 'admin'}
        print("⚠️ No hay configuración válida, usando credenciales por defecto")
        logger.warning("No hay configuración válida, usando credenciales por defecto")
    
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
        
        elif choice == "3" and current_ip:
            # Analizar IP configurada
            print(f"\n🔎 Analizando IP configurada: {current_ip}")
            
            # Escaneo de puertos
            ports = [80, 554, 37777, 8000, 443]
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
    
    print("\n✅ Diagnóstico completado")
    print("📝 Logs guardados en: examples/logs/camera_detector.log")
    print("="*60)
    
    logger.info("=== DIAGNÓSTICO COMPLETADO ===")
    logger.info("Logs guardados en: examples/logs/camera_detector.log")


if __name__ == "__main__":
    main() 