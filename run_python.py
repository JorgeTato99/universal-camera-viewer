#!/usr/bin/env python3
"""
Script auxiliar para ejecutar el backend Python desde la nueva ubicación.
Este archivo está en la raíz para facilitar la ejecución.
"""

import sys
import os
from pathlib import Path

# Agregar src-python al path
src_python_path = Path(__file__).parent / "src-python"
sys.path.insert(0, str(src_python_path))

# Importar y ejecutar el main
from main import main

if __name__ == "__main__":
    main()