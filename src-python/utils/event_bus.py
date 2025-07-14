#!/usr/bin/env python3
"""
Sistema de Event Bus para comunicación desacoplada.

Implementa un bus de eventos simple pero efectivo para permitir
comunicación entre componentes sin acoplamiento directo, siguiendo
el patrón Observer.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from weakref import WeakSet
import inspect


@dataclass
class Event:
    """
    Representa un evento en el sistema.
    
    Attributes:
        name: Nombre/tipo del evento
        data: Datos asociados al evento
        source: Origen del evento
        timestamp: Momento en que se creó el evento
    """
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        """Representación legible del evento."""
        return f"Event(name='{self.name}', source='{self.source}', timestamp={self.timestamp.isoformat()})"


class EventBus:
    """
    Bus de eventos centralizado para la aplicación.
    
    Permite registro de listeners y emisión de eventos de forma
    desacoplada. Soporta tanto callbacks síncronos como asíncronos.
    """
    
    def __init__(self):
        """Inicializa el bus de eventos."""
        self.logger = logging.getLogger(__name__)
        # Diccionario de event_name -> lista de callbacks
        self._listeners: Dict[str, List[Callable]] = {}
        # Para evitar memory leaks, trackear objetos débilmente
        self._subscriber_refs: WeakSet = WeakSet()
        # Lock para thread safety
        self._lock = asyncio.Lock()
        
    def subscribe(self, event_name: str, callback: Callable) -> None:
        """
        Suscribe un callback a un evento específico.
        
        Args:
            event_name: Nombre del evento a escuchar
            callback: Función a ejecutar cuando ocurra el evento
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
            
        if callback not in self._listeners[event_name]:
            self._listeners[event_name].append(callback)
            self.logger.debug(f"Suscrito callback {callback.__name__} a evento '{event_name}'")
            
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """
        Desuscribe un callback de un evento.
        
        Args:
            event_name: Nombre del evento
            callback: Callback a remover
        """
        if event_name in self._listeners and callback in self._listeners[event_name]:
            self._listeners[event_name].remove(callback)
            self.logger.debug(f"Desuscrito callback {callback.__name__} de evento '{event_name}'")
            
            # Limpiar lista vacía
            if not self._listeners[event_name]:
                del self._listeners[event_name]
                
    def subscribe_all(self, callback: Callable) -> None:
        """
        Suscribe un callback a TODOS los eventos.
        
        Útil para logging o debugging.
        
        Args:
            callback: Función a ejecutar en cualquier evento
        """
        self.subscribe("*", callback)
        
    async def emit_async(self, event: Event) -> None:
        """
        Emite un evento de forma asíncrona.
        
        Args:
            event: Evento a emitir
        """
        async with self._lock:
            # Notificar a listeners específicos
            await self._notify_listeners(event.name, event)
            
            # Notificar a listeners universales
            if "*" in self._listeners:
                await self._notify_listeners("*", event)
                
    def emit(self, event: Event) -> None:
        """
        Emite un evento de forma síncrona.
        
        Crea una tarea async si es necesario.
        
        Args:
            event: Evento a emitir
        """
        try:
            # Si hay un event loop corriendo, usarlo
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.emit_async(event))
            else:
                # Si no hay loop, crear uno temporal
                asyncio.run(self.emit_async(event))
        except RuntimeError:
            # Fallback: ejecutar síncronamente
            self._emit_sync(event)
            
    def _emit_sync(self, event: Event) -> None:
        """
        Emite evento de forma completamente síncrona.
        
        Solo para casos donde no hay event loop disponible.
        
        Args:
            event: Evento a emitir
        """
        # Notificar listeners específicos
        if event.name in self._listeners:
            for callback in self._listeners[event.name].copy():
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error en callback {callback.__name__}: {e}")
                    
        # Notificar listeners universales
        if "*" in self._listeners:
            for callback in self._listeners["*"].copy():
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(f"Error en callback universal {callback.__name__}: {e}")
                    
    async def _notify_listeners(self, event_name: str, event: Event) -> None:
        """
        Notifica a todos los listeners de un evento.
        
        Args:
            event_name: Nombre del evento (puede ser "*")
            event: Evento a pasar a los callbacks
        """
        if event_name not in self._listeners:
            return
            
        # Copiar lista para evitar problemas si se modifica durante iteración
        listeners = self._listeners[event_name].copy()
        
        for callback in listeners:
            try:
                # Verificar si el callback es async
                if inspect.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    # Ejecutar callbacks síncronos en thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, callback, event)
                    
            except Exception as e:
                self.logger.error(
                    f"Error ejecutando callback {callback.__name__} "
                    f"para evento '{event.name}': {e}"
                )
                
    def clear(self, event_name: Optional[str] = None) -> None:
        """
        Limpia listeners.
        
        Args:
            event_name: Si se especifica, limpia solo ese evento.
                       Si no, limpia todos los eventos.
        """
        if event_name:
            if event_name in self._listeners:
                del self._listeners[event_name]
                self.logger.debug(f"Limpiados listeners para evento '{event_name}'")
        else:
            self._listeners.clear()
            self.logger.debug("Limpiados todos los listeners")
            
    def get_listener_count(self, event_name: Optional[str] = None) -> int:
        """
        Obtiene el número de listeners.
        
        Args:
            event_name: Si se especifica, cuenta solo para ese evento.
                       Si no, cuenta todos los listeners.
                       
        Returns:
            Número de listeners registrados
        """
        if event_name:
            return len(self._listeners.get(event_name, []))
        else:
            return sum(len(listeners) for listeners in self._listeners.values())


# Instancia global del event bus
_event_bus = EventBus()


# === API pública simplificada ===

def subscribe(event_name: str, callback: Callable) -> None:
    """Suscribe un callback a un evento."""
    _event_bus.subscribe(event_name, callback)
    

def unsubscribe(event_name: str, callback: Callable) -> None:
    """Desuscribe un callback de un evento."""
    _event_bus.unsubscribe(event_name, callback)
    

def emit(event_name: str, data: Optional[Dict[str, Any]] = None, source: Optional[str] = None) -> None:
    """
    Emite un evento.
    
    Args:
        event_name: Nombre del evento
        data: Datos del evento
        source: Origen del evento
    """
    event = Event(name=event_name, data=data or {}, source=source)
    _event_bus.emit(event)
    

async def emit_async(event_name: str, data: Optional[Dict[str, Any]] = None, source: Optional[str] = None) -> None:
    """
    Emite un evento de forma asíncrona.
    
    Args:
        event_name: Nombre del evento
        data: Datos del evento
        source: Origen del evento
    """
    event = Event(name=event_name, data=data or {}, source=source)
    await _event_bus.emit_async(event)


def get_event_bus() -> EventBus:
    """Obtiene la instancia del event bus."""
    return _event_bus


# === Decoradores útiles ===

def on_event(event_name: str):
    """
    Decorador para registrar automáticamente una función como listener.
    
    Ejemplo:
        @on_event("theme_changed")
        def handle_theme_change(event: Event):
            print(f"Tema cambió a: {event.data['theme']}")
    """
    def decorator(func: Callable) -> Callable:
        subscribe(event_name, func)
        return func
    return decorator


__all__ = [
    'Event',
    'EventBus',
    'subscribe',
    'unsubscribe',
    'emit',
    'emit_async',
    'get_event_bus',
    'on_event',
]