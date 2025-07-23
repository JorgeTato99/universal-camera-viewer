#!/usr/bin/env python
"""
Script para ejecutar el servidor FastAPI.

Este script es un wrapper conveniente que ejecuta el main.py
ubicado en src-python, evitando problemas con rutas relativas.
"""

import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    # Ruta al main.py en src-python
    main_path = Path(__file__).parent / "src-python" / "main.py"
    
    # Ejecutar main.py usando el mismo intérprete de Python
    subprocess.run([sys.executable, str(main_path)])