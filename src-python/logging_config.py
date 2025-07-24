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
        # Solo mostrar cada 10 peticiones de polling
        if hasattr(record, 'args') and record.args:
            for endpoint in self.POLLING_ENDPOINTS:
                if endpoint in str(record.args):
                    # Usar un contador simple (no thread-safe pero suficiente para logging)
                    if not hasattr(self, '_counters'):
                        self._counters = {}
                    
                    key = endpoint
                    self._counters[key] = self._counters.get(key, 0) + 1
                    
                    # Solo mostrar cada 10 peticiones
                    if self._counters[key] % 10 != 0:
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