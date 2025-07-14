"""
Connection Model - MVP Architecture
==================================

Modelo que representa y gestiona una conexión individual a una cámara IP.
Encapsula toda la lógica de establecimiento, mantenimiento y monitoreo 
de conexiones utilizando diferentes protocolos.

Responsabilidades:
- Gestionar el ciclo de vida de conexiones
- Implementar retry logic y timeout handling
- Monitorear salud de conexión
- Proporcionar métricas de conexión en tiempo real
- Abstraer diferencias entre protocolos
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Optional, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future

from .camera_model import ProtocolType, ConnectionStatus


class ConnectionType(Enum):
    """Tipos de conexión disponibles."""
    RTSP_STREAM = "rtsp_stream"
    ONVIF_CONTROL = "onvif_control" 
    HTTP_API = "http_api"
    PING_TEST = "ping_test"


@dataclass
class ConnectionAttempt:
    """Información de un intento de conexión."""
    attempt_id: str
    protocol: ProtocolType
    connection_type: ConnectionType
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    response_time_ms: float = 0.0
    
    @property
    def duration_ms(self) -> float:
        """Duración del intento en milisegundos."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0
    
    def mark_completed(self, success: bool, error_message: Optional[str] = None):
        """Marca el intento como completado."""
        self.end_time = datetime.now()
        self.success = success
        self.error_message = error_message
        self.response_time_ms = self.duration_ms


@dataclass
class ConnectionHealth:
    """Métricas de salud de conexión."""
    is_alive: bool = False
    last_successful_check: Optional[datetime] = None
    consecutive_failures: int = 0
    average_response_time: float = 0.0
    packet_loss_percentage: float = 0.0
    uptime_percentage: float = 0.0
    
    def update_health(self, success: bool, response_time: float = 0.0):
        """Actualiza métricas de salud."""
        if success:
            self.is_alive = True
            self.last_successful_check = datetime.now()
            self.consecutive_failures = 0
            # Actualizar promedio de tiempo de respuesta
            if self.average_response_time == 0.0:
                self.average_response_time = response_time
            else:
                self.average_response_time = (self.average_response_time + response_time) / 2
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= 3:  # Considerar muerto después de 3 fallos
                self.is_alive = False


class ConnectionModel:
    """
    Modelo de conexión para arquitectura MVP.
    
    Gestiona conexiones individuales a cámaras IP con soporte para múltiples
    protocolos, retry logic, health monitoring y métricas en tiempo real.
    """
    
    def __init__(self, 
                 camera_id: str,
                 ip: str,
                 protocol: ProtocolType,
                 connection_type: ConnectionType,
                 username: str = "",
                 password: str = "",
                 port: Optional[int] = None,
                 timeout: float = 10.0,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Inicializa el modelo de conexión.
        
        Args:
            camera_id: ID único de la cámara
            ip: Dirección IP de la cámara
            protocol: Protocolo de conexión
            connection_type: Tipo de conexión
            username: Usuario para autenticación
            password: Contraseña para autenticación
            port: Puerto personalizado (opcional)
            timeout: Timeout en segundos
            max_retries: Máximo número de reintentos
            retry_delay: Delay entre reintentos en segundos
        """
        self.logger = logging.getLogger(f"{__name__}.{camera_id}")
        
        # Identificación
        self.connection_id = f"{camera_id}_{protocol.value}_{connection_type.value}"
        self.camera_id = camera_id
        self.ip = ip
        self.protocol = protocol
        self.connection_type = connection_type
        
        # Configuración de conexión
        self.username = username
        self.password = password
        self.port = port or self._get_default_port()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Estado de conexión
        self._status = ConnectionStatus.DISCONNECTED
        self._status_lock = threading.Lock()
        self._connection_handle: Optional[Any] = None
        
        # Métricas y monitoring
        self.health = ConnectionHealth()
        self.attempts_history: List[ConnectionAttempt] = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"conn_{camera_id}")
        self._monitoring_task: Optional[Future] = None
        self._stop_monitoring = threading.Event()
        
        # Callbacks
        self.on_status_changed: Optional[Callable[[ConnectionStatus, ConnectionStatus], None]] = None
        self.on_connection_lost: Optional[Callable[[str], None]] = None
        self.on_connection_restored: Optional[Callable[[], None]] = None
        
        self.logger.info(f"Connection model initialized: {self.connection_id}")
    
    def _get_default_port(self) -> int:
        """Obtiene puerto por defecto según protocolo."""
        port_mapping = {
            ProtocolType.RTSP: 554,
            ProtocolType.ONVIF: 80,
            ProtocolType.HTTP: 80,
            ProtocolType.AMCREST: 37777,
            ProtocolType.GENERIC: 80
        }
        return port_mapping.get(self.protocol, 80)
    
    @property
    def status(self) -> ConnectionStatus:
        """Estado actual de conexión (thread-safe)."""
        with self._status_lock:
            return self._status
    
    @status.setter 
    def status(self, new_status: ConnectionStatus):
        """Establece nuevo estado de conexión (thread-safe)."""
        with self._status_lock:
            old_status = self._status
            self._status = new_status
            self.last_activity = datetime.now()
            
            # Trigger callback si hay cambio
            if old_status != new_status:
                self.logger.info(f"Connection status changed: {old_status.value} → {new_status.value}")
                if self.on_status_changed:
                    try:
                        self.on_status_changed(old_status, new_status)
                    except Exception as e:
                        self.logger.error(f"Error in status change callback: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Indica si la conexión está activa."""
        return self.status in [ConnectionStatus.CONNECTED, ConnectionStatus.STREAMING]
    
    @property
    def connection_url(self) -> str:
        """Construye URL de conexión según protocolo."""
        auth_part = f"{self.username}:{self.password}@" if self.username and self.password else ""
        
        if self.protocol == ProtocolType.RTSP:
            return f"rtsp://{auth_part}{self.ip}:{self.port}/stream1"
        elif self.protocol == ProtocolType.ONVIF:
            return f"http://{self.ip}:{self.port}/onvif/device_service"
        elif self.protocol == ProtocolType.HTTP:
            return f"http://{auth_part}{self.ip}:{self.port}/"
        else:
            return f"http://{auth_part}{self.ip}:{self.port}/"
    
    # === Gestión de Conexión ===
    
    async def connect_async(self) -> bool:
        """
        Establece conexión de forma asíncrona.
        
        Returns:
            True si la conexión fue exitosa
        """
        attempt = ConnectionAttempt(
            attempt_id=f"{len(self.attempts_history)}",
            protocol=self.protocol,
            connection_type=self.connection_type,
            start_time=datetime.now()
        )
        
        self.status = ConnectionStatus.CONNECTING
        
        try:
            for retry in range(self.max_retries + 1):
                try:
                    self.logger.debug(f"Connection attempt {retry + 1}/{self.max_retries + 1}")
                    
                    # Simular conexión según protocolo
                    success = await self._attempt_connection()
                    
                    if success:
                        attempt.mark_completed(True)
                        self.attempts_history.append(attempt)
                        self.status = ConnectionStatus.CONNECTED
                        self.health.update_health(True, attempt.response_time_ms)
                        
                        # Iniciar monitoring si no está activo
                        self._start_health_monitoring()
                        
                        self.logger.info(f"Connection established successfully")
                        return True
                    
                    # Si falló y hay más reintentos
                    if retry < self.max_retries:
                        self.logger.warning(f"Connection attempt {retry + 1} failed, retrying in {self.retry_delay}s")
                        await asyncio.sleep(self.retry_delay)
                    
                except Exception as e:
                    self.logger.error(f"Connection attempt {retry + 1} error: {e}")
                    if retry < self.max_retries:
                        await asyncio.sleep(self.retry_delay)
            
            # Todos los intentos fallaron
            attempt.mark_completed(False, "Max retries exceeded")
            self.attempts_history.append(attempt)
            self.status = ConnectionStatus.ERROR
            self.health.update_health(False)
            
            return False
            
        except Exception as e:
            attempt.mark_completed(False, str(e))
            self.attempts_history.append(attempt)
            self.status = ConnectionStatus.ERROR
            self.health.update_health(False)
            self.logger.error(f"Connection failed with exception: {e}")
            return False
    
    def connect(self) -> bool:
        """
        Establece conexión de forma síncrona.
        
        Returns:
            True si la conexión fue exitosa
        """
        try:
            # Ejecutar conexión asíncrona en thread pool
            future = self.executor.submit(self._run_async_connect)
            return future.result(timeout=self.timeout * (self.max_retries + 1))
        except Exception as e:
            self.logger.error(f"Synchronous connection failed: {e}")
            self.status = ConnectionStatus.ERROR
            return False
    
    def _run_async_connect(self) -> bool:
        """Helper para ejecutar conexión asíncrona."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.connect_async())
        finally:
            loop.close()
    
    async def _attempt_connection(self) -> bool:
        """
        Intenta establecer conexión según protocolo.
        
        Returns:
            True si la conexión fue exitosa
        """
        start_time = time.time()
        
        try:
            if self.protocol == ProtocolType.RTSP:
                return await self._test_rtsp_connection()
            elif self.protocol == ProtocolType.ONVIF:
                return await self._test_onvif_connection()
            elif self.protocol == ProtocolType.HTTP:
                return await self._test_http_connection()
            else:
                return await self._test_generic_connection()
                
        except asyncio.TimeoutError:
            self.logger.warning(f"Connection timeout after {self.timeout}s")
            return False
        except Exception as e:
            self.logger.error(f"Connection attempt failed: {e}")
            return False
    
    async def _test_rtsp_connection(self) -> bool:
        """Prueba conexión RTSP."""
        # Simular prueba RTSP (en implementación real usaría opencv/ffmpeg)
        await asyncio.sleep(0.5)  # Simular delay de conexión
        import random
        return random.random() > 0.2  # 80% éxito para demo
    
    async def _test_onvif_connection(self) -> bool:
        """Prueba conexión ONVIF."""
        # Simular prueba ONVIF (en implementación real usaría onvif-zeep)
        await asyncio.sleep(0.3)  # Simular delay
        import random
        return random.random() > 0.1  # 90% éxito para demo
    
    async def _test_http_connection(self) -> bool:
        """Prueba conexión HTTP."""
        # Simular prueba HTTP (en implementación real usaría aiohttp)
        await asyncio.sleep(0.2)  # Simular delay
        import random
        return random.random() > 0.15  # 85% éxito para demo
    
    async def _test_generic_connection(self) -> bool:
        """Prueba conexión genérica."""
        await asyncio.sleep(0.4)  # Simular delay
        import random
        return random.random() > 0.3  # 70% éxito para demo
    
    def disconnect(self):
        """Desconecta y limpia recursos."""
        self.logger.info("Disconnecting...")
        
        # Detener monitoring
        self._stop_health_monitoring()
        
        # Limpiar handle de conexión
        if self._connection_handle:
            try:
                # Aquí iría lógica específica de limpieza según protocolo
                self._connection_handle = None
            except Exception as e:
                self.logger.error(f"Error cleaning up connection handle: {e}")
        
        self.status = ConnectionStatus.DISCONNECTED
        self.health.is_alive = False
        
        self.logger.info("Disconnected successfully")
    
    # === Health Monitoring ===
    
    def _start_health_monitoring(self):
        """Inicia monitoring de salud de conexión."""
        if self._monitoring_task and not self._monitoring_task.done():
            return  # Ya está corriendo
        
        self._stop_monitoring.clear()
        self._monitoring_task = self.executor.submit(self._health_monitoring_loop)
        self.logger.debug("Health monitoring started")
    
    def _stop_health_monitoring(self):
        """Detiene monitoring de salud."""
        self._stop_monitoring.set()
        if self._monitoring_task:
            try:
                self._monitoring_task.result(timeout=2)
            except Exception as e:
                self.logger.warning(f"Error stopping health monitoring: {e}")
        self.logger.debug("Health monitoring stopped")
    
    def _health_monitoring_loop(self):
        """Loop principal de monitoring de salud."""
        while not self._stop_monitoring.wait(30):  # Check cada 30 segundos
            try:
                if self.is_connected:
                    # Realizar health check
                    health_ok = self._perform_health_check()
                    self.health.update_health(health_ok)
                    
                    if not health_ok and self.health.consecutive_failures >= 3:
                        self.logger.warning("Connection health check failed multiple times")
                        if self.on_connection_lost:
                            self.on_connection_lost("Health check failures")
                        self.status = ConnectionStatus.ERROR
                        
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
    
    def _perform_health_check(self) -> bool:
        """Realiza check de salud de conexión."""
        try:
            # Simular health check (en implementación real haría ping/request específico)
            import random
            return random.random() > 0.1  # 90% éxito
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    # === Métricas y Estadísticas ===
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de conexión."""
        total_attempts = len(self.attempts_history)
        successful_attempts = sum(1 for attempt in self.attempts_history if attempt.success)
        
        return {
            'connection_id': self.connection_id,
            'camera_id': self.camera_id,
            'protocol': self.protocol.value,
            'connection_type': self.connection_type.value,
            'current_status': self.status.value,
            'is_connected': self.is_connected,
            'health': {
                'is_alive': self.health.is_alive,
                'consecutive_failures': self.health.consecutive_failures,
                'average_response_time': self.health.average_response_time,
                'last_successful_check': self.health.last_successful_check.isoformat() if self.health.last_successful_check else None
            },
            'statistics': {
                'total_attempts': total_attempts,
                'successful_attempts': successful_attempts,
                'success_rate': (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
                'average_response_time': sum(a.response_time_ms for a in self.attempts_history) / total_attempts if total_attempts > 0 else 0,
                'uptime_hours': (datetime.now() - self.created_at).total_seconds() / 3600
            },
            'configuration': {
                'ip': self.ip,
                'port': self.port,
                'timeout': self.timeout,
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay
            }
        }
    
    def get_recent_attempts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene intentos de conexión recientes."""
        recent = self.attempts_history[-limit:] if self.attempts_history else []
        return [
            {
                'attempt_id': attempt.attempt_id,
                'start_time': attempt.start_time.isoformat(),
                'success': attempt.success,
                'response_time_ms': attempt.response_time_ms,
                'error_message': attempt.error_message
            }
            for attempt in recent
        ]
    
    # === Cleanup ===
    
    def cleanup(self):
        """Limpia recursos del modelo."""
        self.logger.info("Cleaning up connection model...")
        
        # Desconectar si está conectado
        if self.is_connected:
            self.disconnect()
        
        # Detener monitoring
        self._stop_health_monitoring()
        
        # Cerrar thread pool
        self.executor.shutdown(wait=True)
        
        self.logger.info("Connection model cleanup completed")
    
    def __str__(self) -> str:
        """Representación string del modelo."""
        return f"ConnectionModel({self.camera_id}, {self.protocol.value}, {self.status.value})"
    
    def __repr__(self) -> str:
        """Representación detallada del modelo."""
        return f"ConnectionModel(camera_id='{self.camera_id}', protocol='{self.protocol.value}', ip='{self.ip}', status='{self.status.value}')" 