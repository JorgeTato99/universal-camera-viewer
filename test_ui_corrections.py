#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones de UI:
1. Botones de control en panel de configuración
2. Vista de consola en panel de resultados
3. Funcionalidad completa de la vista refactorizada
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.discovery.port_discovery_view_refactored import PortDiscoveryViewRefactored

def main():
    """Función principal de prueba."""
    print("🧪 Iniciando prueba de correcciones de UI...")
    
    # Crear ventana principal
    root = tk.Tk()
    root.title("Prueba - Correcciones UI Refactorizada")
    root.geometry("1200x800")
    
    try:
        # Crear vista refactorizada
        print("✅ Creando vista refactorizada...")
        view = PortDiscoveryViewRefactored(root)
        
        print("✅ Vista creada exitosamente")
        print("🔍 Verificaciones:")
        print("   - Los botones Escanear, Detener, Limpiar están en Configuración")
        print("   - Hay un botón para alternar Vista Consola/Vista Tabla")
        print("   - El panel de progreso solo muestra barra y estado")
        print("   - El panel de resultados tiene información del escaneo")
        
        # Configurar cierre limpio
        def on_closing():
            print("🧹 Limpiando recursos...")
            view.cleanup()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("🚀 Iniciando interfaz de prueba...")
        print("💡 Prueba las siguientes funciones:")
        print("   1. Cambiar entre modo Simple y Avanzado")
        print("   2. Alternar entre Vista Tabla y Vista Consola")
        print("   3. Usar los botones de control en Configuración")
        print("   4. Verificar que no hay botones duplicados")
        
        # Iniciar loop principal
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✅ Prueba completada exitosamente")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 