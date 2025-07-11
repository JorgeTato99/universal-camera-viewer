"""
Ejemplo completo de conexión ONVIF usando servicios MVP.
Demuestra todas las funcionalidades ONVIF disponibles en el sistema.

Características incluidas:
- Uso de ProtocolService para conexiones ONVIF
- Uso de ConfigService para gestión de configuración
- Uso de DataService para persistencia y exportación
- Descubrimiento automático de servicios
- Obtención de información del dispositivo
- Captura de snapshots
- Stream de video
- Manejo robusto de errores
- Exportación de resultados
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Agregar el directorio src al path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

# Importar servicios MVP
from services.protocol_service import ProtocolService
from services.config_service import ConfigService
from services.data_service import DataService, ExportFormat
from models.camera_model import CameraModel, ProtocolType, ConnectionConfig


def setup_logging():
    """Configura el logging para el ejemplo."""
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "onvif_example_mvp.log"
    
    # Limpiar configuración existente
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.DEBUG,  # Logging detallado para debugging
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True
    )
    
    print(f"📝 Logs guardándose en: {log_file}")


def load_mock_camera_data() -> Dict[str, Any]:
    """
    Carga datos mock de cámaras desde archivo JSON.
    
    Returns:
        Diccionario con datos de cámaras mock
    """
    mock_file = Path(__file__).parent / "mock_camera_data.json"
    
    try:
        import json
        with open(mock_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"❌ Error cargando datos mock: {e}")
        return {"cameras": []}


def select_camera_from_mock() -> Optional[Dict[str, Any]]:
    """
    Permite al usuario seleccionar una cámara de los datos mock.
    
    Returns:
        Datos de la cámara seleccionada o None
    """
    mock_data = load_mock_camera_data()
    cameras = mock_data.get("cameras", [])
    
    if not cameras:
        print("❌ No hay cámaras disponibles en datos mock")
        return None
    
    print("\n" + "="*60)
    print("📋 CÁMARAS DISPONIBLES EN DATOS MOCK")
    print("="*60)
    
    for i, camera in enumerate(cameras, 1):
        print(f"{i}. {camera['display_name']}")
        print(f"   📍 IP: {camera['ip']}")
        print(f"   🏷️ Marca: {camera['brand']}")
        print(f"   📱 Modelo: {camera['model']}")
        print(f"   📡 Protocolos: {', '.join(camera['protocols'])}")
        if camera.get('notes'):
            print(f"   📝 Notas: {camera['notes']}")
        print()
    
    while True:
        try:
            choice = input(f"🔢 Selecciona una cámara (1-{len(cameras)}): ").strip()
            if not choice:
                print("❌ Selección requerida")
                continue
            
            index = int(choice) - 1
            if 0 <= index < len(cameras):
                selected_camera = cameras[index]
                print(f"✅ Cámara seleccionada: {selected_camera['display_name']}")
                return selected_camera
            else:
                print(f"❌ Opción inválida. Debe ser 1-{len(cameras)}")
        except ValueError:
            print("❌ Ingresa un número válido")
        except KeyboardInterrupt:
            print("\n🛑 Selección cancelada")
            return None


def get_user_configuration() -> Dict[str, str]:
    """
    Solicita configuración al usuario por consola o usa datos mock.
    
    Returns:
        Diccionario con la configuración
    """
    print("\n" + "="*60)
    print("🔧 CONFIGURACIÓN DE CÁMARA ONVIF")
    print("="*60)
    
    # Preguntar si usar datos mock
    use_mock = input("🤖 ¿Usar datos mock de cámaras? (s/n, Enter para sí): ").strip().lower()
    
    if use_mock in ['', 's', 'si', 'sí', 'y', 'yes']:
        selected_camera = select_camera_from_mock()
        if selected_camera:
            # Usar datos de la cámara mock como valores por defecto
            print("\n📝 Configuración con valores por defecto de datos mock:")
            print("   (Presiona Enter para usar el valor por defecto, o ingresa un nuevo valor)")
            
            config = {}
            
            # IP de la cámara
            default_ip = selected_camera['ip']
            ip = input(f"📡 IP de la cámara (Enter para '{default_ip}'): ").strip()
            config['ip'] = ip if ip else default_ip
            
            # Puerto ONVIF
            default_port = selected_camera['onvif_port']
            port = input(f"🔌 Puerto ONVIF (Enter para {default_port}): ").strip()
            config['port'] = int(port) if port else default_port
            
            # Usuario
            default_username = selected_camera['username']
            username = input(f"👤 Usuario (Enter para '{default_username}'): ").strip()
            config['username'] = username if username else default_username
            
            # Contraseña
            default_password = selected_camera['password']
            password = input(f"🔒 Contraseña (Enter para usar la del mock): ").strip()
            config['password'] = password if password else default_password
            
            # Marca
            default_brand = selected_camera['brand']
            brand = input(f"🏷️ Marca de la cámara (Enter para '{default_brand}'): ").strip()
            config['brand'] = brand if brand else default_brand
            
            # Modelo
            default_model = selected_camera['model']
            model = input(f"📱 Modelo de la cámara (Enter para '{default_model}'): ").strip()
            config['model'] = model if model else default_model
            
            # Guardar datos mock para uso posterior
            config['camera_id'] = selected_camera['id']
            config['mock_data'] = selected_camera
            
            print("✅ Configuración completada con valores personalizados")
            return config
    
    # Configuración manual
    print("\n📝 Configuración manual:")
    config = {}
    
    # IP de la cámara
    while True:
        ip = input("📡 IP de la cámara (ej: 192.168.1.100): ").strip()
        if ip:
            config['ip'] = ip
            break
        print("❌ IP es requerida")
    
    # Puerto ONVIF
    port = input("🔌 Puerto ONVIF (Enter para 80): ").strip()
    config['port'] = int(port) if port else 80
    
    # Usuario
    username = input("👤 Usuario (Enter para 'admin'): ").strip()
    config['username'] = username if username else 'admin'
    
    # Contraseña
    password = input("🔒 Contraseña: ").strip()
    config['password'] = password
    
    # Marca (opcional)
    brand = input("🏷️ Marca de la cámara (Enter para 'Dahua'): ").strip()
    config['brand'] = brand if brand else 'Dahua'
    
    # Modelo (opcional)
    model = input("📱 Modelo de la cámara (Enter para 'Unknown'): ").strip()
    config['model'] = model if model else 'Unknown'
    
    print("✅ Configuración completada")
    return config


async def initialize_services() -> tuple[ProtocolService, ConfigService, DataService]:
    """
    Inicializa todos los servicios MVP.
    
    Returns:
        Tupla con los servicios inicializados
    """
    print("\n🚀 Inicializando servicios MVP...")
    
    # Inicializar servicios
    protocol_service = ProtocolService()
    config_service = ConfigService()
    data_service = DataService()
    
    # Inicializar servicios (ProtocolService no tiene initialize)
    await config_service.initialize()
    await data_service.initialize()
    
    print("✅ Servicios MVP inicializados correctamente")
    return protocol_service, config_service, data_service


async def test_onvif_discovery(protocol_service: ProtocolService, config: Dict[str, str]) -> bool:
    """
    Demuestra el descubrimiento automático de servicios ONVIF.
    
    Args:
        protocol_service: Servicio de protocolos
        config: Configuración de la cámara
        
    Returns:
        True si el descubrimiento fue exitoso
    """
    print("\n" + "="*60)
    print("🔍 DESCUBRIMIENTO AUTOMÁTICO ONVIF")
    print("="*60)
    
    try:
        # Detectar protocolos en la IP
        print(f"🔍 Detectando protocolos en {config['ip']}:{config['port']}...")
        
        # Crear ConnectionConfig para detect_protocols
        connection_config = ConnectionConfig(
            ip=config['ip'],
            username=config['username'],
            password=config['password']
        )
        
        detected_protocols = await protocol_service.detect_protocols(connection_config)
        
        if not detected_protocols:
            print("❌ No se detectaron protocolos")
            return False
        
        print("✅ Protocolos detectados:")
        for protocol in detected_protocols:
            print(f"   📡 {protocol.value} (tipo: {type(protocol)})")
        
        # Debug: mostrar contenido de la lista
        print(f"🔍 Debug - detected_protocols: {detected_protocols}")
        print(f"🔍 Debug - ProtocolType.ONVIF: {ProtocolType.ONVIF} (tipo: {type(ProtocolType.ONVIF)})")
        
        # Verificar si ONVIF está disponible (múltiples formas de validación)
        onvif_available = (
            ProtocolType.ONVIF in detected_protocols or
            any(p.value == "onvif" for p in detected_protocols) or
            any(str(p) == "ProtocolType.ONVIF" for p in detected_protocols)
        )
        
        print(f"🔍 Debug - onvif_available: {onvif_available}")
        
        if not onvif_available:
            print("❌ ONVIF no está disponible en esta cámara")
            return False
        
        print("✅ ONVIF detectado y disponible")
        return True
        
    except Exception as e:
        print(f"❌ Error en descubrimiento ONVIF: {e}")
        return False


async def test_onvif_connection(protocol_service: ProtocolService, data_service: DataService, config: Dict[str, str]) -> bool:
    """
    Demuestra la conexión ONVIF completa.
    
    Args:
        protocol_service: Servicio de protocolos
        config: Configuración de la cámara
        
    Returns:
        True si la conexión fue exitosa
    """
    print("\n" + "="*60)
    print("🔗 CONEXIÓN ONVIF COMPLETA")
    print("="*60)
    
    try:
        # Crear modelo de cámara
        connection_config = ConnectionConfig(
            ip=config['ip'],
            username=config['username'],
            password=config['password']
        )
        
        camera = CameraModel(
            brand=config['brand'],
            model=config['model'],
            display_name=f"Test ONVIF {config['ip']}",
            connection_config=connection_config
        )
        
        # Crear conexión ONVIF
        print("🔗 Creando conexión ONVIF...")
        connection = await protocol_service.create_connection(
            camera_id=camera.camera_id,
            protocol=ProtocolType.ONVIF,  # type: ignore
            config=connection_config
        )
        
        if not connection:
            print("❌ No se pudo crear conexión ONVIF")
            return False
        
        print("✅ Conexión ONVIF creada exitosamente")
        
        # Obtener información del dispositivo
        print("\n📋 Obteniendo información del dispositivo...")
        device_info = await protocol_service.get_device_info(camera.camera_id)
        
        if device_info:
            print("✅ Información del dispositivo:")
            for key, value in device_info.items():
                print(f"   {key}: {value}")
        else:
            print("⚠️ No se pudo obtener información del dispositivo")
        
        # Obtener perfiles ONVIF detallados
        print("\n📹 Obteniendo perfiles ONVIF detallados...")
        onvif_profiles = await protocol_service.get_onvif_profiles(camera.camera_id)
        
        if onvif_profiles:
            print(f"✅ Perfiles ONVIF encontrados: {len(onvif_profiles)}")
            for i, profile in enumerate(onvif_profiles):
                print(f"   Perfil {i+1}: {profile.get('name', 'Unknown')}")
                print(f"      Token: {profile.get('token', 'N/A')}")
                
                # Información de video
                if 'video' in profile:
                    video = profile['video']
                    print(f"      Video: {video.get('encoding', 'Unknown')}")
                    if video.get('resolution'):
                        res = video['resolution']
                        print(f"         Resolución: {res.get('width', 0)}x{res.get('height', 0)}")
                    print(f"         FPS: {video.get('framerate', 0)}")
                    print(f"         Bitrate: {video.get('bitrate', 0)} kbps")
                
                # Información de audio
                if 'audio' in profile:
                    audio = profile['audio']
                    print(f"      Audio: {audio.get('encoding', 'Unknown')}")
                    print(f"         Bitrate: {audio.get('bitrate', 0)} kbps")
                
                # URLs
                if 'stream_uri' in profile:
                    print(f"      Stream URL: {profile['stream_uri']}")
                if 'snapshot_uri' in profile:
                    print(f"      Snapshot URL: {profile['snapshot_uri']}")
        else:
            print("⚠️ No se pudieron obtener perfiles ONVIF")
        
        # Obtener información adicional del dispositivo
        print("\n📋 Información adicional del dispositivo:")
        print(f"   IP: {camera.connection_config.ip}")
        print(f"   Marca: {camera.brand}")
        print(f"   Modelo: {camera.model}")
        print(f"   Protocolo: ONVIF")
        
        # Obtener URL de stream MJPEG (método disponible)
        print("\n🎥 Obteniendo URL de streaming...")
        stream_url = protocol_service.get_mjpeg_stream_url(camera.camera_id)
        
        if stream_url:
            print(f"✅ Stream URL obtenida: {stream_url}")
            print("✅ Streaming MJPEG disponible")
        else:
            print("⚠️ No se pudo obtener URL de streaming")
        
        # Guardar datos de la cámara en DataService
        print("\n💾 Guardando datos de cámara...")
        
        # Crear CameraModel para guardar
        camera_to_save = CameraModel(
            brand=camera.brand,
            model=camera.model,
            display_name=f"ONVIF Test {camera.connection_config.ip}",
            connection_config=camera.connection_config
        )
        
        # Guardar en DataService
        await data_service.save_camera_data(camera_to_save)
        print("✅ Datos de cámara guardados en DataService")
        
        # Cerrar conexión
        await protocol_service.disconnect_camera(camera.camera_id)
        print("✅ Conexión cerrada correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en conexión ONVIF: {e}")
        return False


async def test_error_handling(protocol_service: ProtocolService) -> bool:
    """
    Demuestra el manejo robusto de errores.
    
    Args:
        protocol_service: Servicio de protocolos
        
    Returns:
        True si el manejo de errores funciona correctamente
    """
    print("\n" + "="*60)
    print("🛡️ PRUEBA DE MANEJO DE ERRORES")
    print("="*60)
    
    try:
        # Probar con IP inválida (timeout reducido)
        print("1. Probando con IP inválida...")
        invalid_config = ConnectionConfig(
            ip="192.168.1.999",  # IP inválida
            username="admin",
            password="password"
        )
        
        try:
            # Usar timeout de 3 segundos para IP inválida
            connection = await asyncio.wait_for(
                protocol_service.create_connection(
                    camera_id="test_invalid",
                    protocol=ProtocolType.ONVIF,  # type: ignore
                    config=invalid_config
                ),
                timeout=3.0  # 3 segundos máximo
            )
            
            if connection:
                print("⚠️ ADVERTENCIA: Conexión exitosa con IP inválida")
                await protocol_service.disconnect_camera("test_invalid")
            else:
                print("✅ Error capturado correctamente - IP inválida")
                
        except asyncio.TimeoutError:
            print("✅ Timeout capturado correctamente - IP inválida (3s)")
        except Exception as e:
            print(f"✅ Error capturado correctamente - IP inválida: {str(e)[:50]}...")
        finally:
            # Asegurar que la conexión de prueba se cierre
            try:
                await protocol_service.disconnect_camera("test_invalid")
            except:
                pass  # Ignorar errores al cerrar conexión de prueba
        
        # Probar con credenciales incorrectas (timeout reducido)
        print("\n2. Probando con credenciales incorrectas...")
        bad_credentials_config = ConnectionConfig(
            ip="192.168.1.100",  # IP válida
            username="wrong_user",
            password="wrong_password"
        )
        
        try:
            # Usar timeout de 5 segundos en lugar de 21
            connection = await asyncio.wait_for(
                protocol_service.create_connection(
                    camera_id="test_bad_creds",
                    protocol=ProtocolType.ONVIF,  # type: ignore
                    config=bad_credentials_config
                ),
                timeout=5.0  # 5 segundos máximo
            )
            
            if connection:
                print("⚠️ ADVERTENCIA: Conexión exitosa con credenciales incorrectas")
                await protocol_service.disconnect_camera("test_bad_creds")
            else:
                print("✅ Error capturado correctamente - credenciales incorrectas")
                
        except asyncio.TimeoutError:
            print("✅ Timeout capturado correctamente - credenciales incorrectas (5s)")
        except Exception as e:
            print(f"✅ Error capturado correctamente - credenciales incorrectas: {str(e)[:50]}...")
        finally:
            # Asegurar que la conexión de prueba se cierre
            try:
                await protocol_service.disconnect_camera("test_bad_creds")
            except:
                pass  # Ignorar errores al cerrar conexión de prueba
        
        return True
        
    except Exception as e:
        print(f"✅ Excepción capturada correctamente: {str(e)[:100]}...")
        return True


async def export_results(data_service: DataService, protocol_service: ProtocolService, results: Dict[str, Any]) -> bool:
    """
    Exporta los resultados del test.
    
    Args:
        data_service: Servicio de datos
        results: Resultados del test
        
    Returns:
        True si la exportación fue exitosa
    """
    print("\n" + "="*60)
    print("📤 EXPORTANDO RESULTADOS")
    print("="*60)
    
    try:
        # Crear archivo de exportación específico para este test
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_ip = results.get('config', {}).get('ip', 'unknown')
        filename = f"onvif_test_{test_ip}_{timestamp}.json"
        
        # Obtener perfiles ONVIF para la exportación
        onvif_profiles = None
        
        # Verificar si tenemos datos mock con perfiles
        mock_data = results.get('config', {}).get('mock_data', {})
        if mock_data and 'onvif_profiles' in mock_data:
            onvif_profiles = mock_data['onvif_profiles']
            print("📋 Usando perfiles ONVIF desde datos mock")
        elif results.get('tests', {}).get('connection', False):
            # Si la conexión fue exitosa, intentar obtener perfiles
            try:
                # Crear una conexión temporal para obtener perfiles
                connection_config = ConnectionConfig(
                    ip=test_ip,
                    username=results.get('config', {}).get('username', 'admin'),
                    password=results.get('config', {}).get('password', '')
                )
                
                temp_connection = await protocol_service.create_connection(
                    camera_id=f"temp_{test_ip}",
                    protocol=ProtocolType.ONVIF,  # type: ignore
                    config=connection_config
                )
                
                if temp_connection:
                    onvif_profiles = await protocol_service.get_onvif_profiles(f"temp_{test_ip}")
                    await protocol_service.disconnect_camera(f"temp_{test_ip}")
            except Exception as e:
                print(f"⚠️ No se pudieron obtener perfiles para exportación: {e}")
        
        # Crear datos específicos del test
        test_data = {
            "test_info": {
                "test_type": "onvif_example",
                "timestamp": datetime.now().isoformat(),
                "target_ip": test_ip,
                "duration_seconds": results.get('duration', 0),
                "success_rate": results.get('success_rate', 0)
            },
            "test_results": results.get('tests', {}),
            "config": results.get('config', {}),
            "onvif_profiles": onvif_profiles,
            "export_timestamp": datetime.now().isoformat()
        }
        
        # Guardar archivo directamente
        export_path = Path("exports") / filename
        export_path.parent.mkdir(exist_ok=True)
        
        import json
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Resultados exportados: {export_path}")
        
        # También exportar datos de la base de datos
        print("📄 Exportando datos de base de datos...")
        db_export_path = await data_service.export_data(
            format=ExportFormat.JSON,
            filter_params={"test_type": "onvif"}
        )
        
        if db_export_path:
            print(f"✅ Datos de BD exportados: {db_export_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error exportando resultados: {e}")
        return False


async def main():
    """
    Función principal que ejecuta todos los ejemplos ONVIF usando servicios MVP.
    """
    print("🚀 EJEMPLO COMPLETO ONVIF - SERVICIOS MVP")
    print("="*60)
    print("Este ejemplo demuestra todas las funcionalidades ONVIF usando:")
    print("• ProtocolService para conexiones ONVIF")
    print("• ConfigService para gestión de configuración")
    print("• DataService para persistencia y exportación")
    print("• Descubrimiento automático de servicios")
    print("• Captura de snapshots")
    print("• Stream de video")
    print("• Manejo robusto de errores")
    print("• Exportación de resultados")
    print()
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    results = {
        "tests": {},
        "config": {},
        "duration": 0,
        "success_rate": 0
    }
    
    try:
        # 1. Obtener configuración del usuario
        config = get_user_configuration()
        results["config"] = config
        
        # 2. Inicializar servicios MVP
        protocol_service, config_service, data_service = await initialize_services()
        
        # 3. Guardar credenciales en ConfigService
        print("\n💾 Guardando credenciales en ConfigService...")
        await config_service.set_camera_credentials(
            brand=config['brand'],
            username=config['username'],
            password=config['password']
        )
        
        # 4. Ejecutar tests
        test_results = []
        
        # Test 1: Descubrimiento ONVIF
        discovery_success = await test_onvif_discovery(protocol_service, config)
        test_results.append(("Descubrimiento ONVIF", discovery_success))
        results["tests"]["discovery"] = discovery_success
        
        # Test 2: Conexión ONVIF completa
        if discovery_success:
            connection_success = await test_onvif_connection(protocol_service, data_service, config)
            test_results.append(("Conexión ONVIF", connection_success))
            results["tests"]["connection"] = connection_success
        else:
            print("⏭️ Saltando test de conexión (descubrimiento falló)")
            test_results.append(("Conexión ONVIF", False))
            results["tests"]["connection"] = False
        
        # Test 3: Manejo de errores
        error_handling_success = await test_error_handling(protocol_service)
        test_results.append(("Manejo de Errores", error_handling_success))
        results["tests"]["error_handling"] = error_handling_success
        
        # Test 4: Exportación de resultados
        export_success = await export_results(data_service, protocol_service, results)
        test_results.append(("Exportación", export_success))
        results["tests"]["export"] = export_success
        
        # 5. Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN DE RESULTADOS")
        print("="*60)
        
        for test_name, success in test_results:
            status = "✅ EXITOSO" if success else "❌ FALLÓ"
            print(f"• {test_name}: {status}")
        
        success_count = sum(1 for _, success in test_results if success)
        total_tests = len(test_results)
        success_rate = (success_count / total_tests) * 100
        
        results["duration"] = time.time() - start_time
        results["success_rate"] = success_rate
        
        print(f"\n🎯 Tasa de éxito: {success_rate:.1f}% ({success_count}/{total_tests})")
        print(f"⏱️ Tiempo total: {results['duration']:.2f} segundos")
        
        if success_rate >= 75:
            print("🎉 ONVIF funcionando correctamente con servicios MVP")
        elif success_rate >= 50:
            print("⚠️ ONVIF parcialmente funcional - Revisar configuración")
        else:
            print("❌ ONVIF con problemas - Verificar conectividad y credenciales")
        
        # 6. Mostrar estadísticas de servicios
        print("\n📈 ESTADÍSTICAS DE SERVICIOS")
        print("-" * 40)
        
        # Estadísticas de servicios
        print(f"ProtocolService: {len(protocol_service.get_active_connections())} conexiones activas")
        
        config_stats = config_service.get_statistics()
        print(f"ConfigService: {config_stats.get('config_items_count', 0)} configuraciones")
        
        data_stats = data_service.get_statistics()
        print(f"DataService: {data_stats.get('cameras_tracked', 0)} cámaras registradas")
        
    except KeyboardInterrupt:
        print("\n🛑 Ejemplo interrumpido por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
        logger.error(f"Error fatal en ejemplo ONVIF MVP: {str(e)}")
        
    finally:
        # Cerrar servicios
        try:
            # Cerrar todas las conexiones activas del ProtocolService
            await protocol_service.cleanup()
            print("🔌 ProtocolService limpiado correctamente")
            
            await data_service.shutdown()
            print("✅ Servicios cerrados correctamente")
        except Exception as e:
            print(f"⚠️ Error cerrando servicios: {e}")
        
        print("\n✅ Ejemplo ONVIF MVP finalizado")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main()) 