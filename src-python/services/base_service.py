"""
Clase base para todos los servicios.
"""

import logging
from typing import Dict, List, Any, Callable
from abc import ABC


class BaseService(ABC):
    """
    Clase base abstracta para servicios.
    
    Proporciona funcionalidad común como logging y gestión de eventos.
    """
    
    def __init__(self):
        """Inicializar servicio base."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._listeners: Dict[str, List[Callable]] = {}
        self._is_initialized = False
        
    def _emit_event(self, event_name: str, *args, **kwargs) -> None:
        """
        Emitir un evento a todos los listeners registrados.
        
        Args:
            event_name: Nombre del evento
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
        """
        if event_name in self._listeners:
            for listener in self._listeners[event_name]:
                try:
                    listener(*args, **kwargs)
                except Exception as e:
                    self.logger.error(
                        f"Error en listener para evento {event_name}: {e}"
                    )
    
    def add_listener(self, event_name: str, callback: Callable) -> None:
        """
        Registrar un listener para un evento.
        
        Args:
            event_name: Nombre del evento
            callback: Función a ejecutar cuando se emita el evento
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)
        
    def remove_listener(self, event_name: str, callback: Callable) -> None:
        """
        Eliminar un listener de un evento.
        
        Args:
            event_name: Nombre del evento
            callback: Función a eliminar
        """
        if event_name in self._listeners:
            self._listeners[event_name].remove(callback)
            if not self._listeners[event_name]:
                del self._listeners[event_name]
                
    async def cleanup(self) -> None:
        """
        Limpiar recursos del servicio.
        
        Este método debe ser sobrescrito por las subclases
        para implementar limpieza específica.
        """
        self.logger.info(f"Limpiando servicio {self.__class__.__name__}")
        self._listeners.clear()
        self._is_initialized = False