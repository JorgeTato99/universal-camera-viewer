"""
Configuración de logging para filtrar mensajes no deseados.
"""
import logging


class IgnoreOptionsFilter(logging.Filter):
    """Filtro para ignorar logs de peticiones OPTIONS."""
    
    def filter(self, record):
        # Ignorar logs de peticiones OPTIONS
        if hasattr(record, 'args') and record.args:
            if len(record.args) >= 3 and record.args[1] == "OPTIONS":
                return False
        return True


class ReducePollingLogsFilter(logging.Filter):
    """Filtro para reducir logs de endpoints de polling."""
    
    POLLING_ENDPOINTS = [
        "/api/publishing/status",
        "/api/publishing/health", 
        "/api/mediamtx/remote-publishing/list"
    ]
    
    def filter(self, record):
        # Ignorar completamente logs de polling exitosos (200 OK)
        if hasattr(record, 'args') and record.args:
            message = str(record.args)
            for endpoint in self.POLLING_ENDPOINTS:
                if endpoint in message and "200 OK" in message:
                    return False
        return True


def configure_logging():
    """Configura los filtros de logging."""
    # Obtener el logger de uvicorn.access
    uvicorn_logger = logging.getLogger("uvicorn.access")
    
    # Agregar filtro para ignorar OPTIONS
    uvicorn_logger.addFilter(IgnoreOptionsFilter())
    
    # Agregar filtro para reducir logs de polling
    uvicorn_logger.addFilter(ReducePollingLogsFilter())