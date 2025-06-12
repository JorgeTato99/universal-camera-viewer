#!/usr/bin/env python3
"""
Punto de entrada principal del Visor Universal de Cámaras.
Nueva estructura modular con sistema de menús y múltiples vistas.
"""

import sys
import os
import logging
from pathlib import Path

# Agregar el directorio src al path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Configura el sistema de logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('universal_visor.log', encoding='utf-8')
        ]
    )

def main():
    """Función principal de entrada."""
    try:
        # Configurar logging
        setup_logging()
        logger = logging.getLogger("MainApp")
        
        logger.info("=== Iniciando Visor Universal de Cámaras ===")
        logger.info("Versión: 1.2.0 - Multi-marca con GUI modular")
        
        # Importar la aplicación principal
        from gui.main_application import MainApplication
        
        # Crear y ejecutar aplicación
        app = MainApplication()
        app.run()
        
        logger.info("Aplicación cerrada correctamente")
        
    except ImportError as e:
        print(f"Error de importación: {e}")
        print("Asegúrese de que todas las dependencias estén instaladas")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        logging.exception("Error crítico en aplicación principal")
        sys.exit(1)

if __name__ == "__main__":
    main() 