"""
Ejemplo completo de conexión RTSP para cámaras Dahua.
Demuestra todas las funcionalidades RTSP disponibles en el sistema.

Características incluidas:
- Conexión con context manager
- Conexión manual
- Captura de frames en tiempo real
- Snapshots automáticos
- Propiedades del stream
- Manejo robusto de errores
- Workflow para Hero-K51H (sleep/wake)
"""

import cv2
import time
import logging
from pathlib import Path
import sys

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from connections.rtsp_connection import RTSPConnection
from utils.config import get_config


def setup_logging():
    """
    Configura el sistema de logging para el ejemplo.
    """
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "rtsp_example.log"
    
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


def show_hero_k51h_workflow():
    """
    Muestra el workflow específico para Hero-K51H con modo sleep/wake.
    """
    print("\n" + "="*60)
    print("📱 WORKFLOW HERO-K51H (IMPORTANTE)")
    print("="*60)
    print("La cámara Hero-K51H tiene un comportamiento sleep/wake:")
    print()
    print("1. 🌙 Servicios RTSP dormidos por defecto (ahorro energético)")
    print("2. 📱 Abrir app DMSS y conectar brevemente")
    print("3. ⚡ Los servicios RTSP se 'despiertan'")
    print("4. 📱 Cerrar DMSS")
    print("5. 🚀 Ejecutar este ejemplo (conexión exitosa)")
    print()
    print("Si no sigues este workflow, RTSP puede fallar.")
    print("Recomendación: Usar ONVIF como protocolo principal.")
    print("="*60)


def test_rtsp_context_manager():
    """
    Demuestra el uso de RTSP con context manager (método recomendado).
    
    Returns:
        bool: True si la prueba es exitosa
    """
    print("\n" + "="*60)
    print("🔗 CONEXIÓN RTSP CON CONTEXT MANAGER")
    print("="*60)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Obtener configuración
        config = get_config()
        credentials = config.get_camera_credentials()
        
        print(f"📍 Conectando a: {config.camera_ip}:{config.rtsp_port}")
        print(f"👤 Usuario: {credentials.get('username')}")
        
        # Crear conexión RTSP
        rtsp_conn = RTSPConnection(
            camera_ip=config.camera_ip,
            credentials=credentials,
            port=config.rtsp_port,
            channel=config.rtsp_channel,
            subtype=config.rtsp_subtype
        )
        
        # Usar context manager
        with rtsp_conn as conn:
            print("✅ Conexión RTSP establecida exitosamente")
            
            # Mostrar información de la conexión
            conn_info = conn.get_connection_info()
            print(f"📊 Info conexión: {conn_info}")
            
            # Obtener propiedades del stream
            properties = conn.get_frame_properties()
            if properties:
                print("📹 Propiedades del stream:")
                for key, value in properties.items():
                    print(f"   {key}: {value}")
            
            # Capturar frames
            print("\n🎥 Capturando frames...")
            frames_captured = 0
            max_frames = 10
            start_time = time.time()
            
            while frames_captured < max_frames:
                frame = conn.get_frame()
                if frame is not None:
                    frames_captured += 1
                    height, width = frame.shape[:2]
                    print(f"   Frame {frames_captured}: {width}x{height}")
                    
                    # Mostrar primer frame por 2 segundos
                    if frames_captured == 1:
                        print("   📺 Mostrando primer frame...")
                        cv2.imshow("Dahua RTSP - Frame", frame)
                        cv2.waitKey(2000)
                        cv2.destroyAllWindows()
                        
                        # Guardar snapshot
                        snapshot_path = f"examples/logs/rtsp_snapshot_{int(time.time())}.jpg"
                        if conn.save_snapshot(snapshot_path):
                            print(f"   📸 Snapshot guardado: {snapshot_path}")
                    
                    time.sleep(0.1)  # Pausa entre frames
                else:
                    print("   ⚠️ No se pudo obtener frame")
                    break
            
            elapsed = time.time() - start_time
            fps = frames_captured / elapsed if elapsed > 0 else 0
            
            print(f"\n✅ Captura completada:")
            print(f"   Frames: {frames_captured}/{max_frames}")
            print(f"   Tiempo: {elapsed:.2f}s")
            print(f"   FPS: {fps:.2f}")
            
        print("✅ Context manager completado - recursos liberados")
        return True
        
    except Exception as e:
        logger.error(f"Error durante conexión RTSP: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False


def test_rtsp_manual_connection():
    """
    Demuestra la conexión RTSP manual (sin context manager).
    
    Returns:
        bool: True si la prueba es exitosa
    """
    print("\n" + "="*60)
    print("🔧 CONEXIÓN RTSP MANUAL")
    print("="*60)
    
    logger = logging.getLogger(__name__)
    config = get_config()
    credentials = config.get_camera_credentials()
    
    # Crear conexión
    rtsp_conn = RTSPConnection(
        camera_ip=config.camera_ip,
        credentials=credentials
    )
    
    try:
        # Conectar manualmente
        print("1. Estableciendo conexión...")
        if rtsp_conn.connect():
            print("✅ Conexión manual establecida")
            
            # Verificar estado
            print("2. Verificando estado...")
            if rtsp_conn.is_alive():
                print("✅ Conexión activa y funcionando")
                
                # Capturar frame
                print("3. Capturando frame de prueba...")
                frame = rtsp_conn.get_frame()
                if frame is not None:
                    height, width = frame.shape[:2]
                    print(f"✅ Frame capturado: {width}x{height}")
                else:
                    print("⚠️ No se pudo capturar frame")
            else:
                print("❌ Conexión no responde")
                return False
        else:
            print("❌ Falló la conexión manual")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error en conexión manual: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False
        
    finally:
        # Asegurar desconexión
        print("4. Desconectando...")
        if rtsp_conn.disconnect():
            print("✅ Desconexión exitosa")
        else:
            print("⚠️ Problemas en desconexión")


def test_rtsp_error_handling():
    """
    Demuestra el manejo robusto de errores con credenciales/IP incorrectas.
    """
    print("\n" + "="*60)
    print("🛡️ PRUEBA DE MANEJO DE ERRORES")
    print("="*60)
    
    logger = logging.getLogger(__name__)
    
    # Credenciales incorrectas intencionalmente
    bad_credentials = {
        "username": "wrong_user",
        "password": "wrong_password"
    }
    
    print("1. Probando con IP inválida...")
    rtsp_conn = RTSPConnection(
        camera_ip="192.168.1.999",  # IP inválida
        credentials=bad_credentials
    )
    
    try:
        if rtsp_conn.connect():
            print("⚠️ ADVERTENCIA: Conexión exitosa con IP inválida")
            rtsp_conn.disconnect()
        else:
            print("✅ Error capturado correctamente - IP inválida")
    except Exception as e:
        print(f"✅ Excepción capturada: {str(e)[:50]}...")
    
    print("\n2. Probando con credenciales incorrectas...")
    config = get_config()
    rtsp_conn2 = RTSPConnection(
        camera_ip=config.camera_ip,  # IP correcta
        credentials=bad_credentials  # Credenciales incorrectas
    )
    
    try:
        if rtsp_conn2.connect():
            print("⚠️ ADVERTENCIA: Conexión exitosa con credenciales incorrectas")
            rtsp_conn2.disconnect()
        else:
            print("✅ Error capturado correctamente - credenciales incorrectas")
    except Exception as e:
        print(f"✅ Excepción capturada: {str(e)[:50]}...")


def main():
    """
    Función principal que ejecuta todos los ejemplos RTSP.
    """
    print("🚀 EJEMPLO COMPLETO RTSP - CÁMARAS DAHUA")
    print("="*60)
    print("Este ejemplo demuestra todas las funcionalidades RTSP:")
    print("• Conexión con context manager (recomendado)")
    print("• Conexión manual")
    print("• Captura de frames en tiempo real")
    print("• Snapshots automáticos")
    print("• Propiedades del stream")
    print("• Manejo robusto de errores")
    print("• Workflow específico Hero-K51H")
    print()
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Verificar configuración
        config = get_config()
        if not config.validate_configuration():
            print("❌ Configuración inválida. Verifica tu archivo .env")
            return
        
        # Mostrar workflow Hero-K51H
        show_hero_k51h_workflow()
        
        # Preguntar si continuar
        print("\n¿Has seguido el workflow DMSS? (Enter para continuar, Ctrl+C para salir)")
        input()
        
        # Ejecutar pruebas
        results = []
        
        # 1. Context manager
        print("\n🔄 Ejecutando pruebas...")
        context_success = test_rtsp_context_manager()
        results.append(context_success)
        
        time.sleep(2)
        
        # 2. Conexión manual
        manual_success = test_rtsp_manual_connection()
        results.append(manual_success)
        
        time.sleep(2)
        
        # 3. Manejo de errores
        test_rtsp_error_handling()
        
        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN DE RESULTADOS")
        print("="*60)
        
        tests = ["Context Manager", "Conexión Manual"]
        for i, (test, result) in enumerate(zip(tests, results)):
            status = "✅ EXITOSO" if result else "❌ FALLÓ"
            print(f"{i+1}. {test}: {status}")
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n🎯 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 50:
            print("🎉 RTSP funcionando - Listo para usar")
            print("💡 Consejo: Considera ONVIF como protocolo principal")
        else:
            print("⚠️ RTSP con problemas - Usar ONVIF como alternativa")
        
    except KeyboardInterrupt:
        print("\n🛑 Ejemplo interrumpido por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
        logger.error(f"Error fatal en ejemplo RTSP: {str(e)}")
        
    finally:
        print("\n✅ Ejemplo RTSP finalizado")
        print("="*60)


if __name__ == "__main__":
    main() 