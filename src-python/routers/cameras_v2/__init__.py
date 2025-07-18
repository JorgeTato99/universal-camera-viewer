"""
Router principal de cámaras v2 - Integración de subrouters.

Este módulo integra todos los subrouters específicos de cámaras:
- CRUD: Operaciones básicas de cámaras
- Connections: Gestión de conexiones
- Credentials: Gestión de credenciales
- Protocols: Gestión de protocolos
- Capabilities: Información de capacidades
- Monitoring: Eventos y logs

La separación en subrouters mejora la organización y mantenibilidad del código.
"""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Importar subrouters
from .crud import router as crud_router
from .connections import router as connections_router  
from .credentials import router as credentials_router
from .protocols import router as protocols_router
from .capabilities import router as capabilities_router
from .monitoring import router as monitoring_router

# Crear router principal
router = APIRouter(
    tags=["cameras-v2"],
    responses={404: {"description": "Cámara no encontrada"}}
)

# Incluir subrouters
# Nota: No añadimos prefix aquí porque cada subrouter ya tiene prefix="/cameras"
logger.info("Registrando subrouters de cameras_v2")

try:
    router.include_router(crud_router)
    logger.debug("Subrouter CRUD registrado con éxito")
    
    router.include_router(connections_router)
    logger.debug("Subrouter Connections registrado con éxito")
    
    router.include_router(credentials_router)
    logger.debug("Subrouter Credentials registrado con éxito")
    
    router.include_router(protocols_router)
    logger.debug("Subrouter Protocols registrado con éxito")
    
    router.include_router(capabilities_router)
    logger.debug("Subrouter Capabilities registrado con éxito")
    
    router.include_router(monitoring_router)
    logger.debug("Subrouter Monitoring registrado con éxito")
    
    logger.info("Todos los subrouters de cameras_v2 registrados exitosamente")
    
except Exception as e:
    logger.error(f"Error registrando subrouters: {e}", exc_info=True)
    raise

# Exportar router principal
__all__ = ["router"]