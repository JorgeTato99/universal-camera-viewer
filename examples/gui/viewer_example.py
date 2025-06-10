"""
Ejemplo completo del Visor Universal en Tiempo Real.
Demuestra la aplicación GUI completa con todas sus funcionalidades.

Características incluidas:
- Interfaz gráfica moderna con tkinter
- Panel de control con 3 pestañas
- Soporte para múltiples protocolos (ONVIF, RTSP, Amcrest)
- Múltiples layouts (1x1, 2x2, 3x3, 4x3, etc.)
- Configuración persistente JSON
- Captura de snapshots
- Monitor FPS en tiempo real
- Threading robusto para streaming
"""

import sys
import logging
from pathlib import Path

# Agregar el directorio raíz del proyecto al path (que contiene src)
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.viewer.real_time_viewer import RealTimeViewer


def setup_logging():
    """
    Configura el sistema de logging para el ejemplo GUI.
    """
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "viewer_example.log"
    
    # Limpiar configuración existente y configurar nuevo logging
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ],
        force=True  # Forzar reconfiguración
    )
    
    # Configurar loggers específicos del visor
    logging.getLogger("RealTimeViewer").setLevel(logging.INFO)
    logging.getLogger("CameraWidget").setLevel(logging.INFO)
    logging.getLogger("ControlPanel").setLevel(logging.INFO)
    logging.getLogger("ONVIFConnection").setLevel(logging.INFO)
    logging.getLogger("RTSPConnection").setLevel(logging.INFO)
    
    # Log de confirmación
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configurado - Archivo: {log_file}")
    print(f"📝 Logs guardándose en: {log_file}")


def show_application_info():
    """
    Muestra información detallada sobre la aplicación GUI.
    """
    print("="*60)
    print("🎥 VISOR UNIVERSAL DE CÁMARAS - MÓDULO DAHUA")
    print("="*60)
    print()
    print("🚀 APLICACIÓN GUI COMPLETA")
    print("Este ejemplo ejecuta el visor completo con:")
    print()
    print("📋 Funcionalidades principales:")
    print("• 🖥️ Interfaz gráfica moderna")
    print("• 🎛️ Panel de control integrado (3 pestañas)")
    print("• 🔗 Soporte múltiples protocolos")
    print("• 📹 Streaming en tiempo real")
    print("• 📐 Layouts configurables")
    print("• 📸 Captura de snapshots")
    print("• 💾 Configuración persistente")
    print("• 📊 Monitor FPS")
    print()
    print("🔌 Protocolos soportados:")
    print("• 🥇 ONVIF (Principal - Recomendado)")
    print("• 🥈 RTSP (Backup - Requiere workflow DMSS)")
    print("• 🥉 HTTP/Amcrest (Solo cámaras compatibles)")
    print()
    print("📐 Layouts disponibles:")
    print("• 1x1 (1 cámara)")
    print("• 2x2 (4 cámaras)")
    print("• 3x3 (9 cámaras)")
    print("• 4x3 (12 cámaras)")
    print("• Y más configuraciones...")
    print()


def show_usage_instructions():
    """
    Muestra las instrucciones de uso de la aplicación.
    """
    print("📖 INSTRUCCIONES DE USO:")
    print("="*60)
    print()
    print("🔧 CONFIGURACIÓN INICIAL:")
    print("1. La aplicación abrirá con configuración predeterminada")
    print("2. Ve a la pestaña 'Cámaras' en el panel de control")
    print("3. Configura tu IP de cámara y credenciales")
    print("4. Selecciona ONVIF como protocolo (recomendado)")
    print("5. Presiona 'Conectar' para iniciar el stream")
    print()
    print("🎮 CONTROLES PRINCIPALES:")
    print("• ⚙️ Pestaña 'Configuración': Layouts y configuración general")
    print("• 📹 Pestaña 'Cámaras': Agregar/editar/eliminar cámaras")
    print("• 📊 Pestaña 'Monitor': Estado y estadísticas")
    print("• 📸 Click derecho en cámara: Capturar snapshot")
    print("• 🔄 Cambio de layouts en tiempo real")
    print()
    print("💡 CONFIGURACIÓN PARA HERO-K51H:")
    print("• IP: 192.168.1.172 (ajustar según tu red)")
    print("• Usuario: admin")
    print("• Contraseña: (tu contraseña específica)")
    print("• Protocolo: ONVIF (Puerto 80)")
    print("• Backup: RTSP (requiere workflow DMSS)")
    print()


def show_troubleshooting():
    """
    Muestra información de troubleshooting común.
    """
    print("🔧 SOLUCIÓN DE PROBLEMAS:")
    print("="*60)
    print()
    print("❌ Si ONVIF no conecta:")
    print("• Verificar IP de cámara en la red")
    print("• Confirmar credenciales correctas")
    print("• Verificar puerto 80 abierto")
    print("• Revisar logs en examples/logs/")
    print()
    print("❌ Si RTSP no conecta:")
    print("• Seguir workflow DMSS primero:")
    print("  1. Abrir app DMSS")
    print("  2. Conectar brevemente")
    print("  3. Cerrar DMSS") 
    print("  4. Probar RTSP en el visor")
    print()
    print("❌ Si la GUI no responde:")
    print("• Cerrar y reiniciar aplicación")
    print("• Verificar que no hay múltiples instancias")
    print("• Revisar logs para errores")
    print()
    print("💡 RECOMENDACIONES:")
    print("• Usar ONVIF como protocolo principal")
    print("• Mantener credenciales actualizadas")
    print("• Configurar solo las cámaras necesarias")
    print("• Usar layouts apropiados para tu setup")
    print()


def main():
    """
    Función principal que ejecuta el visor GUI completo.
    """
    # Mostrar información de la aplicación
    show_application_info()
    show_usage_instructions()
    show_troubleshooting()
    
    print("🚀 INICIANDO APLICACIÓN...")
    print("="*60)
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Crear y ejecutar visor
        logger.info("Iniciando Visor Universal de Cámaras")
        
        viewer = RealTimeViewer()
        viewer.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicación interrumpida por el usuario")
        logger.info("Aplicación interrumpida por el usuario")
        
    except Exception as e:
        print(f"\n❌ Error al ejecutar el visor: {str(e)}")
        logger.error(f"Error fatal en el visor: {str(e)}")
        
        # Mostrar información de ayuda en caso de error
        print("\n🔧 AYUDA PARA RESOLVER ERRORES:")
        print("1. Revisar logs en examples/logs/viewer_example.log")
        print("2. Verificar configuración de red y credenciales")
        print("3. Probar conexión con ejemplos individuales de protocolos")
        print("4. Consultar documentación en README.md")
        
    finally:
        print("\n✅ Ejemplo GUI finalizado")
        logger.info("Visor Universal finalizado")
        print("="*60)


if __name__ == "__main__":
    main() 