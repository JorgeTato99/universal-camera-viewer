"""
Ejemplo completo de conexión HTTP/Amcrest para cámaras Dahua.
Demuestra todas las funcionalidades HTTP CGI disponibles en el sistema.

IMPORTANTE: Este ejemplo funciona con cámaras Dahua que soporten HTTP CGI.
La cámara Hero-K51H NO es compatible con este protocolo.

Características incluidas:
- Conexión HTTP con autenticación Digest
- Información completa del dispositivo
- Snapshots vía CGI
- Stream MJPEG
- Controles PTZ completos
- Presets PTZ
- Factory Pattern
- Manejo robusto de errores
"""

import time
import logging
from pathlib import Path
import sys

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from connections.amcrest_connection import AmcrestConnection
from connections import ConnectionFactory
from utils.config import get_config


def setup_logging():
    """
    Configura el sistema de logging para el ejemplo.
    """
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "amcrest_example.log"
    
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


def show_compatibility_warning():
    """
    Muestra advertencia sobre compatibilidad del protocolo HTTP CGI.
    """
    print("\n" + "="*60)
    print("⚠️ ADVERTENCIA DE COMPATIBILIDAD")
    print("="*60)
    print("El protocolo HTTP CGI/Amcrest NO es compatible con:")
    print("• Dahua Hero-K51H")
    print("• Algunos modelos específicos de Dahua")
    print()
    print("Si tu cámara es Hero-K51H, usa:")
    print("• ONVIF (protocolo principal recomendado)")
    print("• RTSP (protocolo de backup)")
    print()
    print("Este ejemplo es útil para:")
    print("• Otras cámaras Dahua compatibles con HTTP CGI")
    print("• Testing de funcionalidades HTTP")
    print("• Desarrollo y debugging")
    print("="*60)


def test_amcrest_connection():
    """
    Demuestra la conexión HTTP/Amcrest con context manager.
    
    Returns:
        bool: True si la conexión es exitosa
    """
    print("\n" + "="*60)
    print("🔗 CONEXIÓN HTTP/AMCREST CON CONTEXT MANAGER")
    print("="*60)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Obtener configuración
        config = get_config()
        credentials = config.get_camera_credentials()
        
        print(f"📍 Conectando a: {config.camera_ip}:{config.http_port}")
        print(f"👤 Usuario: {credentials.get('username')}")
        
        # Crear conexión Amcrest
        amcrest_conn = AmcrestConnection(
            camera_ip=config.camera_ip,
            credentials=credentials,
            port=config.http_port,
            timeout=15
        )
        
        # Usar context manager
        with amcrest_conn as conn:
            print("✅ Conexión HTTP establecida exitosamente")
            
            # Mostrar información de la conexión
            conn_info = conn.get_connection_info()
            print(f"📊 Info conexión: {conn_info}")
            
            # Obtener información completa del dispositivo
            print("\n📋 Obteniendo información del dispositivo...")
            device_info = conn.get_device_info()
            if device_info:
                print("✅ Información del dispositivo:")
                for key, value in device_info.items():
                    print(f"   {key}: {value}")
            else:
                print("⚠️ No se pudo obtener información del dispositivo")
            
            # Obtener URL del stream MJPEG
            print("\n🎥 Obteniendo URL de stream MJPEG...")
            mjpeg_url = conn.get_mjpeg_stream_url()
            # Ocultar contraseña en la URL
            safe_url = mjpeg_url.replace(config.camera_password, '***')
            print(f"✅ URL MJPEG: {safe_url}")
            
            # Prueba de snapshots múltiples
            print("\n📸 Pruebas de snapshots...")
            snapshot_count = 3
            snapshots_success = 0
            
            for i in range(snapshot_count):
                timestamp = int(time.time())
                snapshot_filename = f"examples/logs/amcrest_snapshot_{timestamp}_{i+1}.jpg"
                
                print(f"   Capturando snapshot {i+1}/{snapshot_count}...")
                
                if conn.save_snapshot(snapshot_filename):
                    print(f"   ✅ Snapshot {i+1} guardado: {snapshot_filename}")
                    snapshots_success += 1
                else:
                    print(f"   ❌ Error al guardar snapshot {i+1}")
                
                time.sleep(1)  # Pausa entre snapshots
            
            print(f"✅ Snapshots completados: {snapshots_success}/{snapshot_count}")
            
            # Prueba de captura de frame
            print("\n🖼️ Capturando frame directo...")
            frame = conn.get_frame()
            if frame is not None:
                height, width = frame.shape[:2]
                print(f"✅ Frame capturado: {width}x{height}")
            else:
                print("⚠️ No se pudo capturar frame directo")
            
        print("✅ Context manager completado - recursos liberados")
        return True
        
    except Exception as e:
        logger.error(f"Error durante conexión Amcrest: {str(e)}")
        print(f"❌ Error: {str(e)}")
        print("💡 Esto es normal si tu cámara no soporta HTTP CGI")
        return False


def test_ptz_controls():
    """
    Demuestra los controles PTZ completos (si la cámara los soporta).
    
    Returns:
        bool: True si PTZ funciona
    """
    print("\n" + "="*60)
    print("🎮 CONTROLES PTZ COMPLETOS")
    print("="*60)
    
    logger = logging.getLogger(__name__)
    config = get_config()
    credentials = config.get_camera_credentials()
    
    amcrest_conn = AmcrestConnection(
        camera_ip=config.camera_ip,
        credentials=credentials,
        port=config.http_port
    )
    
    try:
        if amcrest_conn.connect():
            print("✅ Conexión PTZ establecida")
            
            # Secuencia de comandos PTZ de prueba
            ptz_sequence = [
                ("up", 2, "🔼 Mover hacia arriba"),
                ("stop", 0, "⏹️ Detener movimiento"),
                ("down", 2, "🔽 Mover hacia abajo"),
                ("stop", 0, "⏹️ Detener movimiento"),
                ("left", 2, "◀️ Mover hacia la izquierda"),
                ("stop", 0, "⏹️ Detener movimiento"),
                ("right", 2, "▶️ Mover hacia la derecha"),
                ("stop", 0, "⏹️ Detener movimiento"),
                ("zoom_in", 1, "🔍 Zoom in"),
                ("stop", 0, "⏹️ Detener zoom"),
                ("zoom_out", 1, "🔍 Zoom out"),
                ("stop", 0, "⏹️ Detener zoom")
            ]
            
            print("🎬 Ejecutando secuencia de comandos PTZ...")
            success_count = 0
            
            for action, speed, description in ptz_sequence:
                print(f"   {description}")
                
                if amcrest_conn.ptz_control(action, speed):
                    print(f"   ✅ Comando '{action}' ejecutado")
                    success_count += 1
                else:
                    print(f"   ⚠️ Comando '{action}' falló o no soportado")
                
                time.sleep(1.5)  # Pausa entre comandos
            
            print(f"\n✅ Comandos PTZ completados: {success_count}/{len(ptz_sequence)}")
            
            # Prueba de presets
            print("\n📍 Prueba de presets PTZ...")
            preset_id = 1
            preset_name = "Preset de Prueba"
            
            if amcrest_conn.set_preset(preset_id, preset_name):
                print(f"✅ Preset {preset_id} '{preset_name}' establecido")
                
                # Mover la cámara
                print("   📐 Moviendo cámara para probar preset...")
                amcrest_conn.ptz_control("right", 2)
                time.sleep(2)
                amcrest_conn.ptz_control("stop")
                
                # Volver al preset
                if amcrest_conn.goto_preset(preset_id):
                    print(f"✅ Regreso a preset {preset_id} exitoso")
                else:
                    print(f"⚠️ No se pudo ir al preset {preset_id}")
            else:
                print("ℹ️ Presets PTZ no soportados en este dispositivo")
            
            amcrest_conn.disconnect()
            return success_count > 0
            
        else:
            print("❌ No se pudo establecer conexión para PTZ")
            return False
            
    except Exception as e:
        logger.error(f"Error en pruebas PTZ: {str(e)}")
        print(f"❌ Error PTZ: {str(e)}")
        return False


def test_factory_integration():
    """
    Demuestra el uso del Factory Pattern para crear conexiones Amcrest.
    
    Returns:
        bool: True si factory funciona
    """
    print("\n" + "="*60)
    print("🏭 FACTORY PATTERN - CREACIÓN AMCREST")
    print("="*60)
    
    config = get_config()
    credentials = config.get_camera_credentials()
    
    try:
        # Crear conexión via factory
        connection = ConnectionFactory.create_connection(
            connection_type="amcrest",
            camera_ip=config.camera_ip,
            credentials=credentials
        )
        
        print(f"✅ Conexión Amcrest creada: {type(connection).__name__}")
        print(f"📊 Info: {connection.get_connection_info()}")
        
        # Probar funcionalidad básica
        if connection.connect():
            print("✅ Factory connection establecida")
            
            # Snapshot rápido via factory
            snapshot_data = connection.get_snapshot()
            if snapshot_data:
                print(f"✅ Snapshot via factory: {len(snapshot_data)} bytes")
            
            connection.disconnect()
            return True
        else:
            print("❌ Factory connection falló")
            return False
            
    except Exception as e:
        print(f"❌ Error creando conexión Amcrest: {str(e)}")
        return False


def test_error_handling():
    """
    Demuestra el manejo robusto de errores con credenciales/IP incorrectas.
    """
    print("\n" + "="*60)
    print("🛡️ PRUEBA DE MANEJO DE ERRORES")
    print("="*60)
    
    # Credenciales incorrectas intencionalmente
    bad_credentials = {
        "username": "wrong_user",
        "password": "wrong_password"
    }
    
    print("1. Probando con IP inválida...")
    amcrest_conn = AmcrestConnection(
        camera_ip="192.168.1.999",  # IP inválida
        credentials=bad_credentials,
        timeout=5  # Timeout corto para test
    )
    
    try:
        if amcrest_conn.connect():
            print("⚠️ ADVERTENCIA: Conexión exitosa con IP inválida")
            amcrest_conn.disconnect()
        else:
            print("✅ Error capturado correctamente - IP inválida")
    except Exception as e:
        print(f"✅ Excepción capturada: {str(e)[:50]}...")
    
    print("\n2. Probando con credenciales incorrectas...")
    config = get_config()
    amcrest_conn2 = AmcrestConnection(
        camera_ip=config.camera_ip,  # IP correcta
        credentials=bad_credentials,  # Credenciales incorrectas
        timeout=5
    )
    
    try:
        if amcrest_conn2.connect():
            print("⚠️ ADVERTENCIA: Conexión exitosa con credenciales incorrectas")
            amcrest_conn2.disconnect()
        else:
            print("✅ Error capturado correctamente - credenciales incorrectas")
    except Exception as e:
        print(f"✅ Excepción capturada: {str(e)[:50]}...")


def main():
    """
    Función principal que ejecuta todos los ejemplos Amcrest/HTTP.
    """
    print("🚀 EJEMPLO COMPLETO HTTP/AMCREST - CÁMARAS DAHUA")
    print("="*60)
    print("Este ejemplo demuestra todas las funcionalidades HTTP CGI:")
    print("• Conexión HTTP con autenticación Digest")
    print("• Información completa del dispositivo")
    print("• Snapshots vía CGI")
    print("• Stream MJPEG")
    print("• Controles PTZ completos")
    print("• Presets PTZ")
    print("• Factory Pattern")
    print("• Manejo robusto de errores")
    print()
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Mostrar advertencia de compatibilidad
        show_compatibility_warning()
        
        # Preguntar si continuar
        print("\n¿Tu cámara soporta HTTP CGI? (Enter para continuar, Ctrl+C para salir)")
        input()
        
        # Verificar configuración
        config = get_config()
        if not config.validate_configuration():
            print("❌ Configuración inválida. Verifica tu archivo .env")
            return
        
        print(f"\n📍 Configuración:")
        print(f"   IP: {config.camera_ip}")
        print(f"   Puerto HTTP: {config.http_port}")
        print(f"   Usuario: {config.camera_user}")
        
        # Ejecutar pruebas
        results = []
        
        print("\n🔄 Ejecutando pruebas...")
        
        # 1. Conexión básica
        connection_success = test_amcrest_connection()
        results.append(connection_success)
        
        time.sleep(2)
        
        # 2. Factory Pattern
        factory_success = test_factory_integration()
        results.append(factory_success)
        
        time.sleep(2)
        
        # 3. Controles PTZ (solo si conexión básica funcionó)
        if connection_success:
            ptz_success = test_ptz_controls()
            results.append(ptz_success)
        else:
            print("⏭️ Saltando pruebas PTZ (conexión básica falló)")
            results.append(False)
        
        time.sleep(2)
        
        # 4. Manejo de errores
        test_error_handling()
        
        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN DE RESULTADOS")
        print("="*60)
        
        tests = ["Conexión HTTP", "Factory Pattern", "Controles PTZ"]
        for i, (test, result) in enumerate(zip(tests, results)):
            status = "✅ EXITOSO" if result else "❌ FALLÓ"
            print(f"{i+1}. {test}: {status}")
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n🎯 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 33:
            print("🎉 HTTP CGI funcionando - Tu cámara es compatible")
        else:
            print("⚠️ HTTP CGI no funciona - Usa ONVIF o RTSP")
            print("💡 Esto es normal para Hero-K51H y modelos similares")
        
    except KeyboardInterrupt:
        print("\n🛑 Ejemplo interrumpido por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
        logger.error(f"Error fatal en ejemplo Amcrest: {str(e)}")
        
    finally:
        print("\n✅ Ejemplo Amcrest/HTTP finalizado")
        print("="*60)


if __name__ == "__main__":
    main() 