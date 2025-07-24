#!/usr/bin/env python3
"""
BasePresenter - Clase base para todos los presenters del patrón MVP.

Proporciona funcionalidades comunes:
- Gestión de estado del presenter
- Comunicación con servicios
- Manejo de eventos
- Logging estructurado
- Lifecycle management
"""

import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Generic
from weakref import WeakKeyDictionary

# Type variable para el tipo de vista
ViewType = TypeVar('ViewType')


class PresenterState(Enum):
    """Estados del presenter."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DESTROYED = "destroyed"


@dataclass
class PresenterEvent:
    """Evento del presenter."""
    event_type: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class BasePresenter(ABC, Generic[ViewType]):
    """
    Clase base para todos los presenters del patrón MVP.
    
    Proporciona funcionalidades comunes como gestión de estado,
    comunicación con servicios, manejo de eventos y lifecycle management.
    
    Type parameter:
        ViewType: Tipo de la vista asociada
    """
    
    def __init__(self, view: Optional[ViewType] = None):
        """
        Inicializa el presenter base.
        
        Args:
            view: Vista asociada al presenter
        """
        self.view = view
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Estado del presenter
        self._state = PresenterState.INITIALIZING
        self._state_lock = threading.RLock()
        
        # Eventos y callbacks
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._view_callbacks: WeakKeyDictionary = WeakKeyDictionary()
        
        # Tareas asíncronas
        self._background_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        
        # Configuración
        self._config: Dict[str, Any] = {}
        
        # Métricas y estado
        self._metrics = {
            "events_processed": 0,
            "errors_count": 0,
            "last_activity": datetime.now(),
            "initialization_time": datetime.now()
        }
        
        # Flags de control
        self._initialized = False
        self._destroyed = False
        
        self.logger.debug(f"Presenter {self.__class__.__name__} initialized")
    
    # === Propiedades ===
    
    @property
    def state(self) -> PresenterState:
        """Estado actual del presenter."""
        with self._state_lock:
            return self._state
    
    @property
    def is_ready(self) -> bool:
        """Indica si el presenter está listo."""
        return self.state == PresenterState.READY
    
    @property
    def is_busy(self) -> bool:
        """Indica si el presenter está ocupado."""
        return self.state == PresenterState.BUSY
    
    @property
    def is_destroyed(self) -> bool:
        """Indica si el presenter fue destruido."""
        return self._destroyed
    
    # === Lifecycle Management ===
    
    async def initialize(self) -> bool:
        """
        Inicializa el presenter.
        
        Returns:
            True si se inicializó correctamente
        """
        if self._initialized:
            return True
        
        try:
            self.logger.info("Initializing presenter...")
            self._set_state(PresenterState.INITIALIZING)
            
            # Inicialización específica del presenter
            await self._initialize_presenter()
            
            # Configurar vista si está disponible
            if self.view:
                await self._setup_view()
            
            # Inicializar servicios
            await self._initialize_services()
            
            # Iniciar tareas de fondo
            await self._start_background_tasks()
            
            self._initialized = True
            self._set_state(PresenterState.READY)
            
            self.logger.info("Presenter initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing presenter: {e}")
            self._set_state(PresenterState.ERROR)
            return False
    
    async def destroy(self) -> None:
        """Destruye el presenter y libera recursos."""
        if self._destroyed:
            return
        
        try:
            self.logger.info("Destroying presenter...")
            self._set_state(PresenterState.DESTROYED)
            
            # Señalar shutdown
            self._shutdown_event.set()
            
            # Detener tareas de fondo
            await self._stop_background_tasks()
            
            # Cleanup específico del presenter
            await self._cleanup_presenter()
            
            # Cleanup de vista
            if self.view:
                await self._cleanup_view()
            
            # Limpiar eventos
            self._event_handlers.clear()
            self._view_callbacks.clear()
            
            self._destroyed = True
            self.logger.info("Presenter destroyed")
            
        except Exception as e:
            self.logger.error(f"Error destroying presenter: {e}")
    
    # === Métodos abstractos para implementar ===
    
    @abstractmethod
    async def _initialize_presenter(self) -> None:
        """
        Inicialización específica del presenter.
        Debe ser implementado por cada presenter concreto.
        """
        pass
    
    @abstractmethod
    async def _cleanup_presenter(self) -> None:
        """
        Cleanup específico del presenter.
        Debe ser implementado por cada presenter concreto.
        """
        pass
    
    # === Métodos virtuales para sobrescribir ===
    
    async def _setup_view(self) -> None:
        """
        Configura la vista asociada.
        Puede ser sobrescrito por presenters específicos.
        """
        pass
    
    async def _cleanup_view(self) -> None:
        """
        Limpia la vista asociada.
        Puede ser sobrescrito por presenters específicos.
        """
        pass
    
    async def _initialize_services(self) -> None:
        """
        Inicializa servicios requeridos.
        Puede ser sobrescrito por presenters específicos.
        """
        pass
    
    async def _start_background_tasks(self) -> None:
        """
        Inicia tareas de fondo.
        Puede ser sobrescrito por presenters específicos.
        """
        pass
    
    # === Gestión de estado ===
    
    def _set_state(self, new_state: PresenterState) -> None:
        """Establece el estado del presenter."""
        with self._state_lock:
            old_state = self._state
            self._state = new_state
            
            if old_state != new_state:
                self.logger.debug(f"State changed: {old_state.value} → {new_state.value}")
                asyncio.create_task(self._emit_event("state_changed", {
                    "old_state": old_state.value,
                    "new_state": new_state.value
                }))
    
    async def set_busy(self, busy: bool = True) -> None:
        """
        Establece el estado ocupado.
        
        Args:
            busy: True para ocupado, False para listo
        """
        if busy and self.state == PresenterState.READY:
            self._set_state(PresenterState.BUSY)
        elif not busy and self.state == PresenterState.BUSY:
            self._set_state(PresenterState.READY)
    
    # === Gestión de eventos ===
    
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Agrega un manejador de eventos.
        
        Args:
            event_type: Tipo de evento
            handler: Función manejadora
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        self.logger.debug(f"Added event handler for '{event_type}'")
    
    def remove_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Remueve un manejador de eventos.
        
        Args:
            event_type: Tipo de evento
            handler: Función manejadora
        """
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                self.logger.debug(f"Removed event handler for '{event_type}'")
            except ValueError:
                pass
    
    async def _emit_event(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Emite un evento a todos los manejadores registrados.
        
        Args:
            event_type: Tipo de evento
            data: Datos del evento
        """
        # Primero emitir a manejadores locales si existen
        if event_type in self._event_handlers:
            event = PresenterEvent(
                event_type=event_type,
                source=self.__class__.__name__,
                data=data or {}
            )
            
            self._metrics["events_processed"] += 1
            self._metrics["last_activity"] = datetime.now()
            
            # Llamar manejadores de forma asíncrona
            handlers = self._event_handlers[event_type].copy()
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    self.logger.error(f"Error in event handler for '{event_type}': {e}")
                    self._metrics["errors_count"] += 1
        
        # También emitir a través del sistema WebSocket si está disponible
        try:
            from api.websocket_events import emit_event
            await emit_event(event_type, data or {})
        except ImportError:
            # WebSocket events no disponible, continuar sin error
            pass
        except Exception as e:
            self.logger.debug(f"Error emitiendo evento WebSocket '{event_type}': {e}")
    
    # === Gestión de tareas de fondo ===
    
    def _add_background_task(self, coro) -> asyncio.Task:
        """
        Agrega una tarea de fondo.
        
        Args:
            coro: Corrutina a ejecutar
            
        Returns:
            Task creado
        """
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        
        # Cleanup automático cuando termine
        task.add_done_callback(self._background_tasks.discard)
        
        return task
    
    async def _stop_background_tasks(self) -> None:
        """Detiene todas las tareas de fondo."""
        if not self._background_tasks:
            return
        
        self.logger.debug(f"Stopping {len(self._background_tasks)} background tasks")
        
        # Cancelar todas las tareas
        for task in self._background_tasks:
            task.cancel()
        
        # Esperar a que terminen
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()
    
    # === Comunicación con vista ===
    
    def bind_view_callback(self, view_object: Any, callback_name: str, handler: Callable) -> None:
        """
        Vincula un callback de la vista.
        
        Args:
            view_object: Objeto de la vista
            callback_name: Nombre del callback
            handler: Función manejadora
        """
        if view_object not in self._view_callbacks:
            self._view_callbacks[view_object] = {}
        
        self._view_callbacks[view_object][callback_name] = handler
        self.logger.debug(f"Bound view callback '{callback_name}'")
    
    async def notify_view(self, method_name: str, *args, **kwargs) -> Any:
        """
        Notifica a la vista llamando uno de sus métodos.
        
        Args:
            method_name: Nombre del método a llamar
            *args: Argumentos posicionales
            **kwargs: Argumentos de palabra clave
            
        Returns:
            Resultado del método de la vista
        """
        if not self.view:
            return None
        
        try:
            if hasattr(self.view, method_name):
                method = getattr(self.view, method_name)
                if asyncio.iscoroutinefunction(method):
                    return await method(*args, **kwargs)
                else:
                    return method(*args, **kwargs)
            else:
                self.logger.warning(f"View method '{method_name}' not found")
                
        except Exception as e:
            self.logger.error(f"Error calling view method '{method_name}': {e}")
            self._metrics["errors_count"] += 1
        
        return None
    
    # === Configuración ===
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración.
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        self._config[key] = value
        self.logger.debug(f"Config set: {key} = {value}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración
            default: Valor por defecto
            
        Returns:
            Valor de configuración
        """
        return self._config.get(key, default)
    
    # === Métricas ===
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas del presenter.
        
        Returns:
            Diccionario con métricas
        """
        return {
            **self._metrics,
            "state": self.state.value,
            "initialized": self._initialized,
            "destroyed": self._destroyed,
            "active_tasks": len(self._background_tasks),
            "event_handlers": {
                event_type: len(handlers)
                for event_type, handlers in self._event_handlers.items()
            }
        }
    
    # === Utilidades ===
    
    async def execute_safely(self, coro_or_func, *args, **kwargs) -> Any:
        """
        Ejecuta una función o corrutina de forma segura.
        
        Args:
            coro_or_func: Función o corrutina a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos de palabra clave
            
        Returns:
            Resultado de la ejecución o None si hay error
        """
        try:
            if asyncio.iscoroutinefunction(coro_or_func):
                return await coro_or_func(*args, **kwargs)
            else:
                return coro_or_func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error executing {coro_or_func.__name__}: {e}")
            self._metrics["errors_count"] += 1
            return None
    
    def add_metric(self, key: str, value: Any) -> None:
        """
        Agrega o actualiza una métrica.
        
        Args:
            key: Clave de la métrica
            value: Valor de la métrica
        """
        self._metrics[key] = value
        self.logger.debug(f"Metric added: {key} = {value}")
    
    async def set_error(self, error_message: str) -> None:
        """
        Establece un estado de error en el presenter.
        
        Args:
            error_message: Mensaje de error
        """
        self.logger.error(f"Error state set: {error_message}")
        self._set_state(PresenterState.ERROR)
        self._metrics["errors_count"] += 1
        self._metrics["last_error"] = error_message
        self._metrics["last_error_time"] = datetime.now()
        
        # Emitir evento de error
        await self._emit_event("error", {"message": error_message})

    def __repr__(self) -> str:
        """Representación string del presenter."""
        return f"{self.__class__.__name__}(state={self.state.value}, view={self.view is not None})" 