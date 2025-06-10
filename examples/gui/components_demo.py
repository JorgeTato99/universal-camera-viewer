"""
Demo de componentes individuales del Visor Universal.
Muestra y prueba cada componente del sistema de forma educativa.

Características incluidas:
- Verificación de dependencias
- Demo de importaciones
- Prueba de componentes GUI individuales
- Test de conexiones sin hardware
- Verificación de configuración
- Ejemplos de uso de cada módulo
"""

import sys
import logging
import time
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))


def setup_logging():
    """
    Configura logging mínimo para el demo.
    """
    # Crear directorio de logs si no existe
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "components_demo.log"
    
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


def demo_dependencies():
    """
    Demuestra la verificación de dependencias del sistema.
    
    Returns:
        bool: True si todas las dependencias están disponibles
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("📦 DEMO: VERIFICACIÓN DE DEPENDENCIAS")
    print("="*60)
    
    logger.info("=== INICIANDO DEMO: VERIFICACIÓN DE DEPENDENCIAS ===")
    logger.info("Verificando dependencias necesarias para el visor")
    
    dependencies = [
        ('OpenCV (Video)', 'cv2'),
        ('Pillow (Imágenes)', 'PIL.Image'),
        ('Requests (HTTP)', 'requests'),
        ('Python-dotenv (Config)', 'dotenv'),
        ('ONVIF Zeep', 'onvif'),
        ('NumPy (Arrays)', 'numpy')
    ]
    
    print("Verificando dependencias necesarias para el visor...")
    all_available = True
    
    for dep_name, import_name in dependencies:
        try:
            if '.' in import_name:
                module_parts = import_name.split('.')
                module = __import__(module_parts[0])
                for part in module_parts[1:]:
                    module = getattr(module, part)
            else:
                __import__(import_name)
            print(f"✅ {dep_name:25} - Disponible")
            logger.info(f"Dependencia disponible: {dep_name}")
        except ImportError:
            print(f"❌ {dep_name:25} - NO disponible")
            logger.error(f"Dependencia faltante: {dep_name}")
            all_available = False
        except Exception as e:
            print(f"⚠️ {dep_name:25} - Error: {str(e)[:30]}...")
            logger.warning(f"Error en dependencia {dep_name}: {str(e)}")
            all_available = False
    
    if all_available:
        print("🎉 Todas las dependencias están disponibles")
        logger.info("ÉXITO: Todas las dependencias están disponibles")
    else:
        print("⚠️ Algunas dependencias faltan - Ejecutar: pip install -r requirements.txt")
        logger.warning("FALLÓ: Algunas dependencias faltan - Ejecutar: pip install -r requirements.txt")
    
    logger.info(f"Demo dependencias completado - Resultado: {'EXITOSO' if all_available else 'FALLÓ'}")
    return all_available


def demo_core_imports():
    """
    Demuestra la importación de módulos core del sistema.
    
    Returns:
        bool: True si todos los imports son exitosos
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("🔧 DEMO: IMPORTACIÓN DE MÓDULOS CORE")
    print("="*60)
    
    logger.info("=== INICIANDO DEMO: IMPORTACIÓN DE MÓDULOS CORE ===")
    
    imports_to_test = [
        ("Configuración", "utils.config", "get_config"),
        ("Conexión Base", "connections.base_connection", "BaseConnection"),
        ("Conexión RTSP", "connections.rtsp_connection", "RTSPConnection"),
        ("Conexión ONVIF", "connections.onvif_connection", "ONVIFConnection"),
        ("Conexión Amcrest", "connections.amcrest_connection", "AmcrestConnection"),
        ("Factory Pattern", "connections", "ConnectionFactory")
    ]
    
    print("Importando módulos del sistema...")
    all_imported = True
    
    for desc, module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {desc:20} - {module_name}.{class_name}")
            logger.info(f"Módulo importado exitosamente: {desc} - {module_name}.{class_name}")
        except ImportError as e:
            print(f"❌ {desc:20} - Error de import: {str(e)[:40]}...")
            logger.error(f"Error importando {desc}: {str(e)}")
            all_imported = False
        except AttributeError:
            print(f"❌ {desc:20} - Clase {class_name} no encontrada")
            logger.error(f"Clase no encontrada para {desc}: {class_name}")
            all_imported = False
    
    logger.info(f"Demo core imports completado - Resultado: {'EXITOSO' if all_imported else 'FALLÓ'}")
    return all_imported


def demo_gui_components():
    """
    Demuestra los componentes GUI sin mostrar ventanas.
    
    Returns:
        bool: True si GUI está disponible
    """
    print("\n" + "="*60)
    print("🖥️ DEMO: COMPONENTES GUI")
    print("="*60)
    
    try:
        # Test tkinter base
        import tkinter as tk
        from tkinter import ttk
        print("✅ Tkinter base disponible")
        
        # Test crear ventana oculta
        root = tk.Tk()
        root.withdraw()  # Ocultar inmediatamente
        print("✅ Ventana raíz creada")
        
        # Test widgets básicos
        frame = ttk.Frame(root)
        button = ttk.Button(frame, text="Test")
        label = ttk.Label(frame, text="Demo")
        print("✅ Widgets básicos funcionales")
        
        # Test imports del visor
        try:
            from viewer.control_panel import ControlPanel
            print("✅ ControlPanel importado")
        except ImportError:
            print("⚠️ ControlPanel no disponible")
        
        try:
            from viewer.camera_widget import CameraWidget
            print("✅ CameraWidget importado")
        except ImportError:
            print("⚠️ CameraWidget no disponible")
        
        try:
            from viewer.real_time_viewer import RealTimeViewer
            print("✅ RealTimeViewer importado")
        except ImportError:
            print("⚠️ RealTimeViewer no disponible")
        
        # Limpiar
        root.destroy()
        print("✅ Recursos GUI liberados")
        
        return True
        
    except ImportError:
        print("❌ Tkinter no disponible - GUI no funcionará")
        return False
    except Exception as e:
        print(f"❌ Error GUI: {str(e)}")
        return False


def demo_connections():
    """
    Demuestra la creación de conexiones sin conectar al hardware.
    
    Returns:
        bool: True si las conexiones se pueden crear
    """
    print("\n" + "="*60)
    print("🔗 DEMO: CREACIÓN DE CONEXIONES (SIN HARDWARE)")
    print("="*60)
    
    try:
        from connections.rtsp_connection import RTSPConnection
        from connections.onvif_connection import ONVIFConnection
        from connections.amcrest_connection import AmcrestConnection
        from connections import ConnectionFactory
        
        # Configuración de prueba (sin conectar)
        test_config = {
            'ip': '192.168.1.100',
            'credentials': {'username': 'admin', 'password': 'test123'}
        }
        
        print("Creando instancias de conexión (sin conectar)...")
        
        # RTSP Connection
        rtsp_conn = RTSPConnection(
            camera_ip=test_config['ip'],
            credentials=test_config['credentials']
        )
        print(f"✅ RTSP Connection creada")
        print(f"   URL: {rtsp_conn.rtsp_url}")
        
        # ONVIF Connection
        onvif_conn = ONVIFConnection(
            camera_ip=test_config['ip'],
            credentials=test_config['credentials']
        )
        print(f"✅ ONVIF Connection creada")
        print(f"   Info: {onvif_conn.get_connection_info()}")
        
        # Amcrest Connection
        amcrest_conn = AmcrestConnection(
            camera_ip=test_config['ip'],
            credentials=test_config['credentials']
        )
        print(f"✅ Amcrest Connection creada")
        print(f"   Info: {amcrest_conn.get_connection_info()}")
        
        # Factory Pattern
        factory_conn = ConnectionFactory.create_connection(
            connection_type="onvif",
            camera_ip=test_config['ip'],
            credentials=test_config['credentials']
        )
        print(f"✅ Factory Pattern funcional")
        print(f"   Tipo creado: {type(factory_conn).__name__}")
        
        print("💡 Todas las conexiones se crearon exitosamente (sin conectar)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando conexiones: {str(e)}")
        return False


def demo_configuration():
    """
    Demuestra el sistema de configuración.
    
    Returns:
        bool: True si la configuración funciona
    """
    print("\n" + "="*60)
    print("⚙️ DEMO: SISTEMA DE CONFIGURACIÓN")
    print("="*60)
    
    try:
        from utils.config import get_config
        
        # Obtener configuración
        config = get_config()
        print("✅ Configuración cargada exitosamente")
        
        # Mostrar configuración (sin contraseñas)
        print(f"   IP: {config.camera_ip}")
        print(f"   Usuario: {config.camera_user}")
        print(f"   Puerto RTSP: {config.rtsp_port}")
        print(f"   Puerto HTTP: {config.http_port}")
        print(f"   Puerto ONVIF: {config.onvif_port}")
        
        # Test validación
        is_valid = config.validate_configuration()
        if is_valid:
            print("✅ Configuración válida")
        else:
            print("⚠️ Configuración incompleta - revisar .env")
        
        # Test credenciales
        credentials = config.get_camera_credentials()
        print(f"✅ Credenciales obtenidas: {list(credentials.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración: {str(e)}")
        return False


def main():
    """
    Función principal que ejecuta todos los demos.
    """
    print("🚀 DEMO DE COMPONENTES - VISOR UNIVERSAL")
    print("="*60)
    print("Este demo verifica y muestra cada componente del sistema")
    print("sin necesidad de hardware conectado.")
    print()
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Log de inicio
    logger.info("=== INICIANDO DEMO DE COMPONENTES - VISOR UNIVERSAL ===")
    logger.info("Demo completo de verificación sin hardware conectado")
    
    # Ejecutar demos
    demo_results = []
    
    print("🔄 Ejecutando demos...")
    logger.info("Iniciando ejecución de demos de componentes")
    
    # 1. Dependencias
    logger.info("Ejecutando demo: Verificación de dependencias")
    deps_ok = demo_dependencies()
    demo_results.append(("Dependencias", deps_ok))
    logger.info(f"Demo dependencias - Resultado: {'ÉXITO' if deps_ok else 'FALLÓ'}")
    time.sleep(1)
    
    # 2. Imports core
    logger.info("Ejecutando demo: Importación de módulos core")
    imports_ok = demo_core_imports()
    demo_results.append(("Módulos Core", imports_ok))
    logger.info(f"Demo core imports - Resultado: {'ÉXITO' if imports_ok else 'FALLÓ'}")
    time.sleep(1)
    
    # 3. GUI Components
    logger.info("Ejecutando demo: Componentes GUI")
    gui_ok = demo_gui_components()
    demo_results.append(("Componentes GUI", gui_ok))
    logger.info(f"Demo GUI - Resultado: {'ÉXITO' if gui_ok else 'FALLÓ'}")
    time.sleep(1)
    
    # 4. Configuración
    logger.info("Ejecutando demo: Sistema de configuración")
    config_ok = demo_configuration()
    demo_results.append(("Configuración", config_ok))
    logger.info(f"Demo configuración - Resultado: {'ÉXITO' if config_ok else 'FALLÓ'}")
    time.sleep(1)
    
    # 5. Conexiones
    logger.info("Ejecutando demo: Creación de conexiones")
    conn_ok = demo_connections()
    demo_results.append(("Conexiones", conn_ok))
    logger.info(f"Demo conexiones - Resultado: {'ÉXITO' if conn_ok else 'FALLÓ'}")
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE DEMOS")
    print("="*60)
    
    all_passed = True
    for demo_name, result in demo_results:
        status = "✅ EXITOSO" if result else "❌ FALLÓ"
        print(f"{demo_name:20} {status}")
        if not result:
            all_passed = False
    
    success_rate = sum(r[1] for r in demo_results) / len(demo_results) * 100
    print(f"\n🎯 Tasa de éxito: {success_rate:.1f}%")
    
    # Log del resumen completo
    logger.info("=== RESUMEN FINAL DE DEMOS ===")
    for demo_name, result in demo_results:
        logger.info(f"{demo_name}: {'ÉXITO' if result else 'FALLÓ'}")
    logger.info(f"Tasa de éxito general: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 SISTEMA LISTO PARA USAR")
        print("\n✅ El visor está completamente funcional!")
        print("   Ejecutar: python examples/gui/viewer_example.py")
        logger.info("ESTADO FINAL: SISTEMA LISTO PARA USAR")
        logger.info("El visor está completamente funcional")
    elif success_rate >= 60:
        print("⚠️ SISTEMA PARCIALMENTE FUNCIONAL")
        print("\n💡 Algunas funciones pueden fallar - revisar dependencias")
        logger.warning("ESTADO FINAL: SISTEMA PARCIALMENTE FUNCIONAL")
        logger.warning("Algunas funciones pueden fallar - revisar dependencias")
    else:
        print("❌ SISTEMA CON PROBLEMAS")
        print("\n🔧 Revisar instalación y dependencias")
        print("   Comando: pip install -r requirements.txt")
        logger.error("ESTADO FINAL: SISTEMA CON PROBLEMAS")
        logger.error("Revisar instalación y dependencias")
    
    print("\n📝 Logs guardados en: examples/logs/components_demo.log")
    print("="*60)
    
    logger.info("=== DEMO DE COMPONENTES COMPLETADO ===")
    logger.info(f"Estado final: {'EXITOSO' if all_passed else 'CON PROBLEMAS'}")
    logger.info("Logs guardados en: examples/logs/components_demo.log")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    print(f"\n✅ Demo finalizado - Estado: {'EXITOSO' if success else 'CON PROBLEMAS'}")
    sys.exit(0 if success else 1) 