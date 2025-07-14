"""
Emisor de eventos para comunicación con Tauri.

Proporciona una interfaz para emitir eventos que Tauri
puede capturar y enviar al frontend.
"""

import json
import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod


class EventEmitter(ABC):
    """Interfaz base para emisores de eventos."""
    
    @abstractmethod
    async def emit(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Emite un evento con payload."""
        pass


class TauriEventEmitter(EventEmitter):
    """
    Emisor de eventos específico para Tauri.
    
    En producción, esto se conectará con el runtime de Tauri.
    Por ahora, proporciona logging y callbacks para testing.
    """
    
    def __init__(self):
        """Inicializa el emisor de eventos."""
        self.logger = logging.getLogger(__name__)
        
        # Para desarrollo/testing - callbacks locales
        self._event_handlers: Dict[str, list[Callable]] = {}
        
        # Cola de eventos para buffering si es necesario
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Control de rate limiting
        self._last_emit_times: Dict[str, float] = {}
        self._min_emit_interval = 0.033  # ~30 FPS máximo por evento
    
    async def emit(self, event_name: str, payload: Dict[str, Any]) -> None:
        """
        Emite un evento para Tauri.
        
        Args:
            event_name: Nombre del evento
            payload: Datos del evento
        """
        try:
            # Rate limiting por tipo de evento
            if self._should_throttle(event_name):
                return
            
            # Agregar timestamp si no existe
            if 'timestamp' not in payload:
                payload['timestamp'] = datetime.now().isoformat()
            
            # En producción, aquí se llamaría a la API de Tauri
            # Por ejemplo: tauri.emit(event_name, payload)
            
            # Por ahora, log y callbacks locales
            self.logger.debug(f"Tauri event: {event_name} - payload size: {len(str(payload))}")
            
            # Ejecutar handlers locales (para testing)
            await self._execute_handlers(event_name, payload)
            
            # Actualizar tiempo de última emisión
            self._last_emit_times[event_name] = asyncio.get_event_loop().time()
            
        except Exception as e:
            self.logger.error(f"Error emitiendo evento {event_name}: {e}")
    
    async def emit_frame_update(self, camera_id: str, frame_base64: str) -> None:
        """
        Emite una actualización de frame.
        
        Args:
            camera_id: ID de la cámara
            frame_base64: Frame en base64
        """
        await self.emit('frame-update', {
            'cameraId': camera_id,
            'frameData': frame_base64,
            'dataUri': f"data:image/jpeg;base64,{frame_base64}"
        })
    
    async def emit_stream_status(self, camera_id: str, status: str, details: Optional[Dict] = None) -> None:
        """
        Emite un cambio de estado del stream.
        
        Args:
            camera_id: ID de la cámara
            status: Estado del stream
            details: Detalles adicionales
        """
        payload = {
            'cameraId': camera_id,
            'status': status
        }
        
        if details:
            payload.update(details)
        
        await self.emit('stream-status', payload)
    
    async def emit_stream_metrics(self, camera_id: str, metrics: Dict[str, Any]) -> None:
        """
        Emite métricas del stream.
        
        Args:
            camera_id: ID de la cámara
            metrics: Métricas del stream
        """
        await self.emit('stream-metrics', {
            'cameraId': camera_id,
            'metrics': metrics
        })
    
    async def emit_error(self, camera_id: str, error_type: str, message: str) -> None:
        """
        Emite un error del stream.
        
        Args:
            camera_id: ID de la cámara
            error_type: Tipo de error
            message: Mensaje de error
        """
        await self.emit('stream-error', {
            'cameraId': camera_id,
            'errorType': error_type,
            'message': message
        })
    
    def _should_throttle(self, event_name: str) -> bool:
        """
        Determina si un evento debe ser throttled.
        
        Args:
            event_name: Nombre del evento
            
        Returns:
            True si debe ser throttled
        """
        # Solo throttle para eventos de frame
        if not event_name.startswith('frame-'):
            return False
        
        current_time = asyncio.get_event_loop().time()
        last_time = self._last_emit_times.get(event_name, 0)
        
        return (current_time - last_time) < self._min_emit_interval
    
    # Métodos para testing/desarrollo
    
    def on(self, event_name: str, handler: Callable) -> None:
        """
        Registra un handler para testing.
        
        Args:
            event_name: Nombre del evento
            handler: Función a ejecutar
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
    
    def off(self, event_name: str, handler: Callable) -> None:
        """
        Desregistra un handler.
        
        Args:
            event_name: Nombre del evento
            handler: Handler a remover
        """
        if event_name in self._event_handlers:
            handlers = self._event_handlers[event_name]
            if handler in handlers:
                handlers.remove(handler)
    
    async def _execute_handlers(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Ejecuta handlers locales para testing."""
        handlers = self._event_handlers.get(event_name, [])
        handlers.extend(self._event_handlers.get('*', []))  # Handlers globales
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_name, payload)
                else:
                    handler(event_name, payload)
            except Exception as e:
                self.logger.error(f"Error en handler para {event_name}: {e}")


class MockEventEmitter(EventEmitter):
    """
    Emisor mock para testing sin Tauri.
    
    Guarda todos los eventos emitidos para verificación.
    """
    
    def __init__(self):
        """Inicializa el emisor mock."""
        self.events: list[tuple[str, Dict[str, Any]]] = []
        self.logger = logging.getLogger(__name__)
    
    async def emit(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Guarda el evento emitido."""
        self.events.append((event_name, payload))
        self.logger.debug(f"Mock event: {event_name}")
    
    def get_events(self, event_name: Optional[str] = None) -> list[Dict[str, Any]]:
        """Obtiene eventos emitidos, opcionalmente filtrados por nombre."""
        if event_name:
            return [payload for name, payload in self.events if name == event_name]
        return [payload for _, payload in self.events]
    
    def clear(self) -> None:
        """Limpia los eventos guardados."""
        self.events.clear()