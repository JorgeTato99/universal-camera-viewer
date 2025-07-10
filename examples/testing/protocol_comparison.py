"""
Comparación técnica completa entre protocolos soportados.
Consolida funcionalidades técnicas de testing ONVIF y expande la comparación.

Funcionalidades incluidas:
- Comparación directa ONVIF vs RTSP vs Amcrest
- Tests de descubrimiento y conexión directa
- Análisis de compatibilidad y características
- Métricas técnicas detalladas
- Recomendaciones específicas por protocolo

Basado en: test_onvif_simple.py + test_onvif_direct.py + test_onvif_discovery.py
"""

import sys
import time
import logging
import socket
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from connections import ConnectionFactory, ONVIFConnection, RTSPConnection, AmcrestConnection
from utils.config import get_config


def setup_logging():
    """Configura logging para comparación de protocolos."""
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "protocol_comparison.log"
    
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


def test_network_connectivity(ip: str, port: int, protocol_name: str) -> bool:
    """
    Verifica conectividad básica de red a un puerto específico.
    
    Args:
        ip: Dirección IP a probar
        port: Puerto a probar
        protocol_name: Nombre del protocolo para logging
        
    Returns:
        True si hay conectividad
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ {protocol_name} puerto {port}: Conectividad OK")
            return True
        else:
            print(f"❌ {protocol_name} puerto {port}: Sin conectividad")
            return False
    except Exception as e:
        print(f"❌ {protocol_name} puerto {port}: Error - {str(e)}")
        return False


def analyze_onvif_protocol(config) -> dict:
    """
    Análisis completo del protocolo ONVIF.
    
    Returns:
        Diccionario con resultados del análisis
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("🔍 ANÁLISIS ONVIF COMPLETO")
    print("="*60)
    
    logger.info("=== INICIANDO ANÁLISIS ONVIF COMPLETO ===")
    logger.info(f"Analizando IP: {config.camera_ip}, Usuario: {config.camera_user}")
    
    results = {
        'protocol': 'ONVIF',
        'network_ok': False,
        'connection_ok': False,
        'discovery_ok': False,
        'services': [],
        'capabilities': [],
        'device_info': {},
        'profiles': [],
        'snapshot_ok': False,
        'stream_ok': False,
        'connection_time': 0,
        'errors': []
    }
    
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        # 1. Test de conectividad de red
        print("1. Verificando conectividad de red...")
        logger.info("Verificando conectividad ONVIF puerto 80")
        results['network_ok'] = test_network_connectivity(config.camera_ip, 80, "ONVIF")
        
        if not results['network_ok']:
            results['errors'].append("Puerto 80 no accesible")
            logger.error("Puerto ONVIF 80 no accesible")
            return results
        else:
            logger.info("Conectividad ONVIF puerto 80 confirmada")
        
        # 2. Test de conexión básica
        print("2. Probando conexión ONVIF básica...")
        start_time = time.time()
        
        connection = ONVIFConnection(config.camera_ip, credentials)
        
        if connection.connect():
            results['connection_ok'] = True
            results['connection_time'] = time.time() - start_time
            print(f"✅ Conexión ONVIF exitosa ({results['connection_time']:.2f}s)")
            logger.info(f"Conexión ONVIF exitosa - Tiempo: {results['connection_time']:.2f}s")
            
            # 3. Test de descubrimiento de servicios
            print("3. Descubriendo servicios ONVIF...")
            try:
                services = connection.get_available_services()
                if services:
                    results['discovery_ok'] = True
                    results['services'] = services
                    print(f"✅ Servicios descubiertos: {len(services)}")
                    for service in services[:5]:  # Mostrar solo los primeros 5
                        print(f"   • {service}")
                else:
                    print("⚠️ No se encontraron servicios")
            except Exception as e:
                results['errors'].append(f"Discovery error: {str(e)}")
                print(f"❌ Error en discovery: {str(e)}")
            
            # 4. Test de información del dispositivo
            print("4. Obteniendo información del dispositivo...")
            try:
                device_info = connection.get_device_info()
                if device_info:
                    results['device_info'] = device_info
                    print("✅ Información del dispositivo obtenida:")
                    logger.info("Información del dispositivo ONVIF obtenida:")
                    for key, value in device_info.items():
                        if key.lower() not in ['password', 'pass']:
                            print(f"   {key}: {value}")
                            logger.info(f"Device {key}: {value}")
                else:
                    print("⚠️ No se pudo obtener información del dispositivo")
                    logger.warning("No se pudo obtener información del dispositivo ONVIF")
            except Exception as e:
                results['errors'].append(f"Device info error: {str(e)}")
                print(f"❌ Error obteniendo device info: {str(e)}")
            
            # 5. Test de perfiles de media
            print("5. Analizando perfiles de media...")
            try:
                profiles = connection.get_profiles()
                if profiles:
                    results['profiles'] = profiles
                    print(f"✅ Perfiles encontrados: {len(profiles)}")
                    logger.info(f"ONVIF perfiles encontrados: {len(profiles)}")
                    for i, profile in enumerate(profiles):
                        print(f"   Profile {i+1}: {profile}")
                        # Log solo información básica del perfil, no toda la estructura
                        profile_name = getattr(profile, 'Name', f'Profile_{i+1}')
                        logger.info(f"Profile {i+1}: {profile_name}")
                else:
                    print("⚠️ No se encontraron perfiles")
                    logger.warning("No se encontraron perfiles ONVIF")
            except Exception as e:
                results['errors'].append(f"Profiles error: {str(e)}")
                print(f"❌ Error obteniendo perfiles: {str(e)}")
            
            # 6. Test de snapshot
            print("6. Probando captura de snapshot...")
            try:
                snapshot = connection.get_snapshot()
                if snapshot and len(snapshot) > 0:
                    results['snapshot_ok'] = True
                    print(f"✅ Snapshot capturado: {len(snapshot)} bytes")
                    logger.info(f"ONVIF snapshot capturado: {len(snapshot)} bytes")
                else:
                    print("❌ No se pudo capturar snapshot")
                    logger.error("No se pudo capturar snapshot ONVIF")
            except Exception as e:
                results['errors'].append(f"Snapshot error: {str(e)}")
                print(f"❌ Error en snapshot: {str(e)}")
            
            # 7. Test de streaming
            print("7. Probando capacidad de streaming...")
            try:
                frame = connection.get_frame()
                if frame is not None:
                    results['stream_ok'] = True
                    print("✅ Streaming funcional")
                    logger.info("ONVIF streaming funcional")
                else:
                    print("❌ Streaming no funcional")
                    logger.error("ONVIF streaming no funcional")
            except Exception as e:
                results['errors'].append(f"Streaming error: {str(e)}")
                print(f"❌ Error en streaming: {str(e)}")
            
            connection.disconnect()
            
        else:
            results['errors'].append("Connection failed")
            print("❌ No se pudo conectar con ONVIF")
    
    except Exception as e:
        results['errors'].append(f"General error: {str(e)}")
        print(f"❌ Error general ONVIF: {str(e)}")
    
    return results


def analyze_rtsp_protocol(config) -> dict:
    """
    Análisis completo del protocolo RTSP.
    
    Returns:
        Diccionario con resultados del análisis
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("📹 ANÁLISIS RTSP COMPLETO")
    print("="*60)
    
    logger.info("=== INICIANDO ANÁLISIS RTSP COMPLETO ===")
    logger.info(f"Analizando RTSP - IP: {config.camera_ip}")
    
    results = {
        'protocol': 'RTSP',
        'network_ok': False,
        'connection_ok': False,
        'url_generated': False,
        'stream_ok': False,
        'connection_time': 0,
        'rtsp_url': '',
        'requires_workflow': True,
        'errors': []
    }
    
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        # 1. Test de conectividad de red
        print("1. Verificando conectividad RTSP...")
        results['network_ok'] = test_network_connectivity(config.camera_ip, 554, "RTSP")
        
        # 2. Test de generación de URL
        print("2. Generando URL RTSP...")
        connection = RTSPConnection(config.camera_ip, credentials)
        
        if hasattr(connection, 'rtsp_url') and connection.rtsp_url:
            results['url_generated'] = True
            results['rtsp_url'] = connection.rtsp_url
            print(f"✅ URL RTSP generada: {connection.rtsp_url}")
        else:
            results['errors'].append("URL generation failed")
            print("❌ No se pudo generar URL RTSP")
            return results
        
        # 3. Test de conexión (puede fallar sin workflow DMSS)
        print("3. Probando conexión RTSP...")
        print("ℹ️ NOTA: RTSP puede requerir workflow DMSS previo")
        
        start_time = time.time()
        
        if connection.connect():
            results['connection_ok'] = True
            results['connection_time'] = time.time() - start_time
            print(f"✅ Conexión RTSP exitosa ({results['connection_time']:.2f}s)")
            logger.info(f"Conexión RTSP exitosa - Tiempo: {results['connection_time']:.2f}s")
            
            # 4. Test de streaming
            print("4. Probando streaming RTSP...")
            try:
                frame = connection.get_frame()
                if frame is not None:
                    results['stream_ok'] = True
                    print("✅ Streaming RTSP funcional")
                else:
                    print("❌ No se recibieron frames")
            except Exception as e:
                results['errors'].append(f"Streaming error: {str(e)}")
                print(f"❌ Error en streaming: {str(e)}")
            
            connection.disconnect()
            
        else:
            results['errors'].append("Connection failed - may need DMSS workflow")
            print("❌ Conexión RTSP falló")
            print("💡 Solución: Ejecutar workflow DMSS antes de usar RTSP")
    
    except Exception as e:
        results['errors'].append(f"General error: {str(e)}")
        print(f"❌ Error general RTSP: {str(e)}")
    
    return results


def analyze_amcrest_protocol(config) -> dict:
    """
    Análisis completo del protocolo HTTP/Amcrest.
    
    Returns:
        Diccionario con resultados del análisis
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("🌐 ANÁLISIS HTTP/AMCREST COMPLETO")
    print("="*60)
    
    logger.info("=== INICIANDO ANÁLISIS HTTP/AMCREST COMPLETO ===")
    logger.info(f"Analizando HTTP/Amcrest - IP: {config.camera_ip}")
    
    results = {
        'protocol': 'Amcrest',
        'network_ok': False,
        'connection_ok': False,
        'compatibility': False,
        'snapshot_ok': False,
        'connection_time': 0,
        'expected_failure': True,  # Para Hero-K51H
        'errors': []
    }
    
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        # 1. Test de conectividad HTTP
        print("1. Verificando conectividad HTTP...")
        results['network_ok'] = test_network_connectivity(config.camera_ip, 80, "HTTP")
        
        # 2. Test de conexión Amcrest
        print("2. Probando conexión HTTP/Amcrest...")
        print("ℹ️ NOTA: Hero-K51H puede no ser compatible con CGI HTTP")
        
        start_time = time.time()
        connection = AmcrestConnection(config.camera_ip, credentials)
        
        if connection.connect():
            results['connection_ok'] = True
            results['compatibility'] = True
            results['connection_time'] = time.time() - start_time
            results['expected_failure'] = False
            print(f"✅ Conexión HTTP exitosa ({results['connection_time']:.2f}s)")
            print("🎉 ¡Cámara compatible con HTTP/Amcrest!")
            
            # 3. Test de snapshot HTTP
            print("3. Probando snapshot HTTP...")
            try:
                snapshot = connection.get_snapshot()
                if snapshot and len(snapshot) > 0:
                    results['snapshot_ok'] = True
                    print(f"✅ Snapshot HTTP: {len(snapshot)} bytes")
                else:
                    print("❌ Snapshot HTTP falló")
            except Exception as e:
                results['errors'].append(f"Snapshot error: {str(e)}")
                print(f"❌ Error en snapshot: {str(e)}")
            
            connection.disconnect()
            
        else:
            results['errors'].append("Connection failed - likely incompatible")
            print("❌ Conexión HTTP falló (esperado para Hero-K51H)")
            print("💡 Hero-K51H no es compatible con API HTTP/CGI estándar")
            logger.info("Conexión HTTP/Amcrest falló - Error esperado para Hero-K51H")
    
    except Exception as e:
        results['errors'].append(f"General error: {str(e)}")
        print(f"❌ Error HTTP/Amcrest: {str(e)}")
        if "Hero-K51H" in str(e) or "not compatible" in str(e).lower():
            print("💡 Error esperado - Hero-K51H no soporta HTTP CGI")
    
    return results


def compare_protocols(results: list) -> dict:
    """
    Compara los resultados de todos los protocolos y genera análisis.
    
    Args:
        results: Lista de resultados de cada protocolo
        
    Returns:
        Diccionario con comparación completa
    """
    print("\n" + "="*60)
    print("⚖️ COMPARACIÓN COMPLETA DE PROTOCOLOS")
    print("="*60)
    
    comparison = {
        'working_protocols': [],
        'failed_protocols': [],
        'recommended': None,
        'compatibility_score': {},
        'feature_matrix': {}
    }
    
    # Analizar cada protocolo
    for result in results:
        protocol = result['protocol']
        
        # Calcular score de compatibilidad
        score = 0
        max_score = 0
        
        # Criterios de evaluación
        criteria = [
            ('network_ok', 2),
            ('connection_ok', 3),
            ('snapshot_ok', 2),
            ('stream_ok', 3)
        ]
        
        for criterion, weight in criteria:
            max_score += weight
            if result.get(criterion, False):
                score += weight
        
        # Criterios específicos por protocolo
        if protocol == 'ONVIF':
            if result.get('discovery_ok', False):
                score += 2
                max_score += 2
            if result.get('device_info'):
                score += 1
                max_score += 1
        
        compatibility_score = (score / max_score * 100) if max_score > 0 else 0
        comparison['compatibility_score'][protocol] = compatibility_score
        
        # Clasificar protocolo
        if compatibility_score >= 70:
            comparison['working_protocols'].append(protocol)
        else:
            comparison['failed_protocols'].append(protocol)
        
        # Matriz de características
        comparison['feature_matrix'][protocol] = {
            'connectivity': result.get('network_ok', False),
            'connection': result.get('connection_ok', False),
            'snapshot': result.get('snapshot_ok', False),
            'streaming': result.get('stream_ok', False),
            'discovery': result.get('discovery_ok', False),
            'immediate_ready': not result.get('requires_workflow', False),
            'compatibility_score': compatibility_score
        }
    
    # Determinar protocolo recomendado
    if comparison['working_protocols']:
        # Ordenar por score de compatibilidad
        sorted_protocols = sorted(comparison['working_protocols'], 
                                key=lambda p: comparison['compatibility_score'][p], 
                                reverse=True)
        comparison['recommended'] = sorted_protocols[0]
    
    # Mostrar comparación
    print("\n🏆 RANKING DE PROTOCOLOS:")
    all_protocols = sorted(comparison['compatibility_score'].items(), 
                          key=lambda x: x[1], reverse=True)
    
    for i, (protocol, score) in enumerate(all_protocols, 1):
        status = "✅ FUNCIONAL" if protocol in comparison['working_protocols'] else "❌ NO FUNCIONAL"
        print(f"{i}. {protocol:10} - {score:5.1f}% - {status}")
    
    print(f"\n🎯 PROTOCOLO RECOMENDADO: {comparison['recommended'] or 'NINGUNO'}")
    
    return comparison


def generate_technical_report(results: list, comparison: dict):
    """Genera un reporte técnico detallado."""
    print("\n" + "="*60)
    print("📋 REPORTE TÉCNICO DETALLADO")
    print("="*60)
    
    print("\n📊 MATRIZ DE COMPATIBILIDAD:")
    print(f"{'Protocolo':<12} {'Conectiv':<8} {'Conexión':<8} {'Snapshot':<8} {'Stream':<8} {'Score':<6}")
    print("-" * 60)
    
    for protocol, features in comparison['feature_matrix'].items():
        conn = "✅" if features['connectivity'] else "❌"
        connection = "✅" if features['connection'] else "❌"
        snapshot = "✅" if features['snapshot'] else "❌"
        streaming = "✅" if features['streaming'] else "❌"
        score = f"{features['compatibility_score']:.1f}%"
        
        print(f"{protocol:<12} {conn:<8} {connection:<8} {snapshot:<8} {streaming:<8} {score:<6}")
    
    print("\n💡 RECOMENDACIONES TÉCNICAS:")
    
    if comparison['recommended'] == 'ONVIF':
        print("🥇 ONVIF es el protocolo óptimo:")
        print("   ✅ Estándar universal para cámaras IP")
        print("   ✅ Conexión inmediata sin prerequisitos")
        print("   ✅ Descubrimiento automático de servicios")
        print("   ✅ Soporte completo de funcionalidades")
        
    elif comparison['recommended'] == 'RTSP':
        print("🥈 RTSP es funcional pero requiere setup:")
        print("   ⚠️ Requiere workflow DMSS previo")
        print("   ✅ Buena performance de streaming")
        print("   ⚠️ Puede perder conexión periódicamente")
        
    elif comparison['recommended'] == 'Amcrest':
        print("🥉 HTTP/Amcrest funcional (inesperado):")
        print("   🎉 Cámara compatible con CGI HTTP")
        print("   ✅ Acceso directo a snapshots")
        print("   ⚠️ Limitado en funcionalidades avanzadas")
    
    else:
        print("❌ NINGÚN PROTOCOLO FUNCIONAL:")
        print("   🔧 Verificar configuración de red")
        print("   🔧 Confirmar credenciales de cámara")
        print("   🔧 Revisar firewall y conectividad")
    
    print("\n🛠️ PARA DESARROLLO:")
    print("   • Implementar ONVIF como protocolo principal")
    print("   • Mantener RTSP como backup con workflow")
    print("   • Agregar reconexión automática")
    print("   • Implementar fallback entre protocolos")


def main():
    """Función principal de comparación de protocolos."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🔬 COMPARACIÓN TÉCNICA DE PROTOCOLOS")
    print("="*60)
    print("Análisis completo de ONVIF, RTSP y HTTP/Amcrest")
    print("Midiendo compatibilidad, funcionalidad y performance")
    print()
    
    # Log de inicio
    logger.info("=== INICIANDO COMPARACIÓN TÉCNICA DE PROTOCOLOS ===")
    logger.info("Análisis completo de ONVIF, RTSP y HTTP/Amcrest")
    
    # Verificar configuración
    config = get_config()
    if not config.validate_configuration():
        print("❌ Configuración inválida. Verifica tu archivo .env")
        logger.error("Configuración inválida - Comparación abortada")
        return False
    
    print(f"📍 Configuración de prueba:")
    print(f"   IP: {config.camera_ip}")
    print(f"   Usuario: {config.camera_user}")
    print(f"   Modelo esperado: Dahua Hero-K51H")
    print()
    
    # Log de configuración
    logger.info(f"Configuración - IP: {config.camera_ip}, Usuario: {config.camera_user}, Modelo: Dahua Hero-K51H")
    
    # Ejecutar análisis de cada protocolo
    all_results = []
    
    # Análisis ONVIF
    logger.info("Iniciando análisis completo de protocolo ONVIF")
    onvif_results = analyze_onvif_protocol(config)
    all_results.append(onvif_results)
    logger.info(f"ONVIF análisis completado - Funcional: {onvif_results.get('connection_ok', False)}")
    
    time.sleep(2)
    
    # Análisis RTSP
    logger.info("Iniciando análisis completo de protocolo RTSP")
    rtsp_results = analyze_rtsp_protocol(config)
    all_results.append(rtsp_results)
    logger.info(f"RTSP análisis completado - Funcional: {rtsp_results.get('connection_ok', False)}")
    
    time.sleep(2)
    
    # Análisis Amcrest
    logger.info("Iniciando análisis completo de protocolo Amcrest")
    amcrest_results = analyze_amcrest_protocol(config)
    all_results.append(amcrest_results)
    logger.info(f"Amcrest análisis completado - Funcional: {amcrest_results.get('connection_ok', False)}")
    
    # Comparación completa
    logger.info("Iniciando comparación completa de protocolos")
    comparison = compare_protocols(all_results)
    
    # Log de resultados de comparación
    logger.info(f"Protocolos funcionales: {', '.join(comparison['working_protocols'])}")
    logger.info(f"Protocolos no funcionales: {', '.join(comparison['failed_protocols'])}")
    logger.info(f"Protocolo recomendado: {comparison['recommended'] or 'NINGUNO'}")
    
    # Reporte técnico
    logger.info("Generando reporte técnico detallado")
    generate_technical_report(all_results, comparison)
    
    print("\n✅ Comparación de protocolos completada")
    print("📝 Logs detallados en: examples/logs/protocol_comparison.log")
    print("="*60)
    
    # Log final con estadísticas
    logger.info("=== COMPARACIÓN DE PROTOCOLOS COMPLETADA ===")
    for protocol, score in comparison['compatibility_score'].items():
        logger.info(f"{protocol} - Compatibilidad: {score:.1f}%")
    logger.info(f"Protocolos funcionales encontrados: {len(comparison['working_protocols'])}")
    logger.info("Logs detallados guardados en: examples/logs/protocol_comparison.log")
    
    return len(comparison['working_protocols']) > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 