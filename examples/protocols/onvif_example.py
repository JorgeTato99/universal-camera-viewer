"""
Ejemplo completo de conexión ONVIF para cámaras Dahua.
Demuestra todas las funcionalidades ONVIF disponibles en el sistema.

Características incluidas:
- Verificación de dependencias ONVIF
- Descubrimiento automático de servicios
- Conexión via Factory Pattern
- Conexión directa con ONVIFConnection
- Obtención de información del dispositivo
- Captura de snapshots
- Stream de video
- Context manager
- Manejo robusto de errores
"""

import sys
import logging
import time
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    from onvif import ONVIFCamera
    from onvif.exceptions import ONVIFError
    ONVIF_AVAILABLE = True
    print("✅ Librería ONVIF disponible")
except ImportError:
    ONVIF_AVAILABLE = False
    print("❌ Librería ONVIF no disponible")
    print("Para instalar: pip install onvif-zeep")

from connections import ConnectionFactory, ONVIFConnection
from utils.config import get_config


def setup_logging():
    """Configura el logging para el ejemplo."""
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "onvif_example.log"
    
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


def check_onvif_availability():
    """
    Verifica si ONVIF está disponible y funcional.
    
    Returns:
        bool: True si ONVIF está listo para usar
    """
    if not ONVIF_AVAILABLE:
        print("❌ ONVIF no está disponible")
        print("Instalar con: pip install onvif-zeep")
        return False
    
    print("✅ ONVIF disponible y listo")
    return True


def test_onvif_discovery():
    """
    Demuestra el descubrimiento automático de servicios ONVIF.
    
    Returns:
        ONVIFCamera: Cámara ONVIF conectada o None
    """
    print("\n" + "="*60)
    print("🔍 DESCUBRIMIENTO AUTOMÁTICO ONVIF")
    print("="*60)
    
    if not ONVIF_AVAILABLE:
        return None
    
    config = get_config()
    
    try:
        # Crear conexión ONVIF básica
        camera = ONVIFCamera(
            config.camera_ip,
            config.onvif_port,
            config.camera_user,
            config.camera_password
        )
        
        # Obtener información del dispositivo
        print("1. Obteniendo información del dispositivo...")
        device_service = camera.create_devicemgmt_service()
        device_info = device_service.GetDeviceInformation()
        
        print("✅ Información del dispositivo:")
        print(f"   Fabricante: {device_info.Manufacturer}")
        print(f"   Modelo: {device_info.Model}")
        print(f"   Firmware: {device_info.FirmwareVersion}")
        print(f"   Serial: {device_info.SerialNumber}")
        
        # Obtener servicios disponibles
        print("\n2. Descubriendo servicios...")
        try:
            capabilities = device_service.GetCapabilities()
            print("✅ Servicios disponibles:")
            
            if hasattr(capabilities, 'Media') and capabilities.Media:
                print("   📹 Media Service - Disponible")
            if hasattr(capabilities, 'PTZ') and capabilities.PTZ:
                print("   🎮 PTZ Service - Disponible")
            if hasattr(capabilities, 'Imaging') and capabilities.Imaging:
                print("   🖼️ Imaging Service - Disponible")
                
        except Exception as e:
            print(f"⚠️ No se pudieron obtener capacidades: {str(e)}")
        
        # Obtener perfiles de media
        print("\n3. Explorando perfiles de media...")
        try:
            media_service = camera.create_media_service()
            profiles = media_service.GetProfiles()
            
            print(f"✅ Perfiles encontrados: {len(profiles)}")
            for i, profile in enumerate(profiles):
                print(f"   Perfil {i+1}: {profile.Name}")
                if hasattr(profile, '_token'):
                    print(f"      Token: {profile._token}")
                    
                    # Obtener URI de snapshot para el primer perfil
                    if i == 0:
                        try:
                            snapshot_uri = media_service.GetSnapshotUri({'ProfileToken': profile._token})
                            print(f"      Snapshot URI: {snapshot_uri.Uri}")
                        except Exception as e:
                            print(f"      Snapshot URI: Error - {str(e)}")
            
        except Exception as e:
            print(f"❌ Error en media service: {str(e)}")
        
        return camera
        
    except ONVIFError as e:
        print(f"❌ Error ONVIF: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return None


def test_factory_pattern():
    """
    Demuestra el uso del Factory Pattern para crear conexiones ONVIF.
    
    Returns:
        ONVIFConnection: Conexión creada via factory o None
    """
    print("\n" + "="*60)
    print("🏭 FACTORY PATTERN - CREACIÓN DE CONEXIÓN")
    print("="*60)
    
    config = get_config()
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        # Crear conexión via factory
        connection = ConnectionFactory.create_connection(
            connection_type="onvif",
            camera_ip=config.camera_ip,
            credentials=credentials
        )
        
        print(f"✅ Conexión ONVIF creada: {type(connection).__name__}")
        print(f"📊 Info: {connection.get_connection_info()}")
        
        return connection
        
    except Exception as e:
        print(f"❌ Error creando conexión ONVIF: {str(e)}")
        return None


def test_direct_connection():
    """
    Demuestra el uso directo de ONVIFConnection con todas sus funcionalidades.
    
    Returns:
        bool: True si todas las pruebas son exitosas
    """
    print("\n" + "="*60)
    print("🔗 CONEXIÓN DIRECTA ONVIF - FUNCIONALIDADES COMPLETAS")
    print("="*60)
    
    config = get_config()
    credentials = {
        'username': config.camera_user,
        'password': config.camera_password
    }
    
    try:
        # Crear conexión directa
        connection = ONVIFConnection(config.camera_ip, credentials)
        
        # Usar context manager
        with connection:
            print("✅ Conexión establecida via context manager")
            
            # 1. Verificar estado
            if connection.is_alive():
                print("✅ Conexión activa y funcionando")
            else:
                print("⚠️ Conexión establecida pero no responde")
                return False
            
            # 2. Obtener información del dispositivo
            print("\n📋 Obteniendo información del dispositivo...")
            device_info = connection.get_device_info()
            if device_info:
                for key, value in device_info.items():
                    print(f"   {key}: {value}")
            else:
                print("⚠️ No se pudo obtener información del dispositivo")
            
            # 3. Obtener perfiles
            print("\n📹 Obteniendo perfiles de media...")
            profiles = connection.get_profiles()
            print(f"✅ Perfiles encontrados: {len(profiles)}")
            
            # 4. Capturar snapshot
            print("\n📸 Capturando snapshot...")
            snapshot_path = "examples/logs/onvif_example_snapshot.jpg"
            snapshot_data = connection.get_snapshot(save_path=snapshot_path)
            if snapshot_data:
                print(f"✅ Snapshot capturado: {len(snapshot_data)} bytes")
                print(f"   Guardado en: {snapshot_path}")
            else:
                print("⚠️ No se pudo capturar snapshot")
            
            # 5. Probar stream de video (breve)
            print("\n🎥 Probando stream de video...")
            frame = connection.get_frame()
            if frame is not None:
                height, width = frame.shape[:2]
                print(f"✅ Frame capturado: {width}x{height}")
                
                # Capturar algunos frames adicionales
                frames_captured = 1
                for i in range(4):  # 4 frames adicionales
                    frame = connection.get_frame()
                    if frame is not None:
                        frames_captured += 1
                        time.sleep(0.1)  # Pequeña pausa
                    else:
                        break
                
                print(f"✅ Total frames capturados: {frames_captured}")
            else:
                print("⚠️ No se pudo obtener frame de video")
            
        print("✅ Context manager completado - recursos liberados")
        return True
        
    except Exception as e:
        logging.exception("Error durante testing directo ONVIF")
        print(f"❌ Error durante testing: {str(e)}")
        return False


def test_error_handling():
    """
    Demuestra el manejo robusto de errores con credenciales incorrectas.
    """
    print("\n" + "="*60)
    print("🛡️ PRUEBA DE MANEJO DE ERRORES")
    print("="*60)
    
    # Credenciales incorrectas intencionalmente
    bad_credentials = {
        "username": "wrong_user",
        "password": "wrong_password"
    }
    
    try:
        connection = ONVIFConnection("192.168.1.999", bad_credentials)
        
        if connection.connect():
            print("⚠️ ADVERTENCIA: Conexión exitosa con credenciales incorrectas")
            connection.disconnect()
        else:
            print("✅ Manejo de errores funcionando - conexión falló como esperado")
            
    except Exception as e:
        print(f"✅ Error capturado correctamente: {str(e)[:100]}...")


def main():
    """
    Función principal que ejecuta todos los ejemplos ONVIF.
    """
    print("🚀 EJEMPLO COMPLETO ONVIF - CÁMARAS DAHUA")
    print("="*60)
    print("Este ejemplo demuestra todas las funcionalidades ONVIF:")
    print("• Descubrimiento automático de servicios")
    print("• Factory Pattern para crear conexiones")
    print("• Conexión directa con ONVIFConnection")
    print("• Captura de snapshots")
    print("• Stream de video")
    print("• Context manager")
    print("• Manejo de errores")
    print()
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 1. Verificar disponibilidad
        if not check_onvif_availability():
            return
        
        # 2. Verificar configuración
        config = get_config()
        if not config.validate_configuration():
            print("❌ Configuración inválida. Verifica tu archivo .env")
            return
        
        print(f"\n📍 Configuración:")
        print(f"   IP: {config.camera_ip}")
        print(f"   Puerto ONVIF: {config.onvif_port}")
        print(f"   Usuario: {config.camera_user}")
        
        # 3. Ejecutar ejemplos
        results = []
        
        # Descubrimiento automático
        camera = test_onvif_discovery()
        results.append(camera is not None)
        
        # Factory Pattern
        factory_connection = test_factory_pattern()
        results.append(factory_connection is not None)
        
        # Conexión directa completa
        direct_success = test_direct_connection()
        results.append(direct_success)
        
        # Manejo de errores
        test_error_handling()
        
        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN DE RESULTADOS")
        print("="*60)
        
        tests = ["Descubrimiento ONVIF", "Factory Pattern", "Conexión Directa"]
        for i, (test, result) in enumerate(zip(tests, results)):
            status = "✅ EXITOSO" if result else "❌ FALLÓ"
            print(f"{i+1}. {test}: {status}")
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n🎯 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 75:
            print("🎉 ONVIF funcionando correctamente - Listo para usar")
        else:
            print("⚠️ Algunos problemas detectados - Revisar configuración")
        
    except KeyboardInterrupt:
        print("\n🛑 Ejemplo interrumpido por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
        logger.error(f"Error fatal en ejemplo ONVIF: {str(e)}")
        
    finally:
        print("\n✅ Ejemplo ONVIF finalizado")
        print("="*60)


if __name__ == "__main__":
    main() 