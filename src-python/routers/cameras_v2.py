"""
Router de cámaras v2 - REFACTORIZADO.

Este archivo ahora solo sirve como punto de entrada al router refactorizado.
Todo el código ha sido movido a la carpeta cameras_v2/ para mejor organización.

La funcionalidad se ha dividido en:
- crud.py: Operaciones CRUD básicas (5 endpoints + statistics + endpoints)
- connections.py: Gestión de conexiones (4 endpoints)
- credentials.py: Gestión de credenciales (5 endpoints)  
- protocols.py: Gestión de protocolos (4 endpoints)
- capabilities.py: Información de capacidades (1 endpoint)
- monitoring.py: Eventos, logs y snapshots (3 endpoints)
- shared.py: Funciones compartidas
"""

# Importar el router integrado desde el módulo refactorizado
from .cameras_v2 import router

# Exportar para compatibilidad con imports existentes
__all__ = ["router"]