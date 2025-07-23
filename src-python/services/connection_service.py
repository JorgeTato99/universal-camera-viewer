"""
Connection Service - MVP Architecture
=====================================

Servicio de orquestación de conexiones para múltiples cámaras IP.
Gestiona el ciclo de vida de conexiones, coordinación de protocolos,
load balancing y métricas agregadas del sistema.

Responsabilidades:
- Orquestar múltiples ConnectionModel instances
- Gestionar pools de conexiones por protocolo
- Implementar connection pooling y load balancing
- Proporcionar métricas agregadas del sistema
- Manejar failover y recovery automático
- Coordinar operaciones batch (conectar/desconectar múltiples cámaras)
"""

import asyncio

import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from services.logging_service import get_secure_logger

try:
    from ..models.camera_model import CameraModel, ProtocolType, ConnectionStatus
    from ..models.connection_model import ConnectionModel, ConnectionType, ConnectionHealth
    from ..utils.config import ConfigurationManager
except ImportError:
    # Fallback para ejecución directa
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from models.camera_model import CameraModel, ProtocolType, ConnectionStatus
    from models.connection_model import ConnectionModel, ConnectionType, ConnectionHealth
    from utils.config import ConfigurationManager


class ServiceStatus(Enum):
    """Estados del servicio de conexión."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ConnectionPool(Enum):
    """Tipos de pools de conexión."""
    RTSP_STREAMING = "rtsp_streaming"
    ONVIF_CONTROL = "onvif_control"
    HTTP_API = "http_api"
    AMCREST_SDK = "amcrest_sdk"


@dataclass
class ConnectionServiceConfig:
    """Configuración del servicio de conexión."""
    max_concurrent_connections: int = 50
    max_connections_per_camera: int = 3
    connection_timeout: float = 10.0
    health_check_interval: float = 30.0
    retry_failed_connections: bool = True
    retry_interval: float = 60.0
    enable_connection_pooling: bool = True
    pool_size_per_protocol: int = 10
    auto_reconnect: bool = True
    connection_metrics_enabled: bool = True
    
    def validate(self):
        """Valida la configuración."""
        if self.max_concurrent_connections <= 0:
            raise ValueError("max_concurrent_connections debe ser mayor a 0")
        if self.connection_timeout <= 0:
            raise ValueError("connection_timeout debe ser mayor a 0")
        if self.health_check_interval <= 0:
            raise ValueError("health_check_interval debe ser mayor a 0")


@dataclass
class ConnectionMetrics:
    """Métricas agregadas de conexiones."""
    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0
    average_response_time: float = 0.0
    total_bytes_transferred: int = 0
    connections_per_protocol: Dict[str, int] = field(default_factory=dict)
    uptime_percentage: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_protocol_count(self, protocol: ProtocolType, delta: int):
        """Actualiza contador por protocolo."""
        protocol_name = protocol.value
        current = self.connections_per_protocol.get(protocol_name, 0)
        self.connections_per_protocol[protocol_name] = max(0, current + delta)


@dataclass
class BatchOperation:
    """Operación en lote sobre múltiples cámaras."""
    operation_id: str
    operation_type: str  # 'connect', 'disconnect', 'health_check'
    camera_ids: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    results: Dict[str, bool] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_completed(self) -> bool:
        """Indica si la operación está completa."""
        return self.end_time is not None
    
    @property
    def success_rate(self) -> float:
        """Porcentaje de éxito de la operación."""
        if not self.results:
            return 0.0
        successful = sum(1 for success in self.results.values() if success)
        return (successful / len(self.results)) * 100


class ConnectionService:
    """
    Servicio de orquestación de conexiones para arquitectura MVP.
    
    Gestiona múltiples conexiones de cámaras, implementa connection pooling,
    métricas agregadas y operaciones en lote.
    """
    
    def __init__(self, config: Optional[ConnectionServiceConfig] = None):
        """
        Inicializa el servicio de conexión.
        
        Args:
            config: Configuración del servicio (opcional)
        """
        self.logger = get_secure_logger("services.connection_service")
        
        # Configuración
        self.config = config or ConnectionServiceConfig()
        self.config.validate()
        
        # Estado del servicio
        self._status = ServiceStatus.STOPPED
        self._status_lock = threading.Lock()
        self._shutdown_event = threading.Event()
        
        # Gestión de conexiones
        self.connections: Dict[str, ConnectionModel] = {}  # camera_id -> connection
        self.connection_pools: Dict[ConnectionPool, List[ConnectionModel]] = {
            pool: [] for pool in ConnectionPool
        }
        
        # Métricas y monitoring
        self.metrics = ConnectionMetrics()
        self.batch_operations: Dict[str, BatchOperation] = {}
        
        # Threading
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_connections,
            thread_name_prefix="conn_service"
        )
        self._health_check_task: Optional[asyncio.Task] = None
        self._retry_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_connection_established: Optional[Callable[[str, ProtocolType], None]] = None
        self.on_connection_lost: Optional[Callable[[str, str], None]] = None
        self.on_batch_completed: Optional[Callable[[BatchOperation], None]] = None
        
        # Configuration manager
        self.config_manager = ConfigurationManager()
        
        self.logger.info("Connection service initialized")
    
    @property
    def status(self) -> ServiceStatus:
        """Estado actual del servicio (thread-safe)."""
        with self._status_lock:
            return self._status
    
    @status.setter
    def status(self, new_status: ServiceStatus):
        """Establece nuevo estado del servicio (thread-safe)."""
        with self._status_lock:
            old_status = self._status
            self._status = new_status
            
            if old_status != new_status:
                self.logger.info(f"Service status changed: {old_status.value} → {new_status.value}")
    
    @property
    def is_running(self) -> bool:
        """Indica si el servicio está corriendo."""
        return self.status == ServiceStatus.RUNNING
    
    # === Gestión del Servicio ===
    
    async def start_async(self) -> bool:
        """
        Inicia el servicio de forma asíncrona.
        
        Returns:
            True si el servicio se inició correctamente
        """
        if self.is_running:
            self.logger.warning("Service is already running")
            return True
        
        self.logger.info("Starting connection service...")
        self.status = ServiceStatus.STARTING
        
        try:
            # Limpiar estado previo
            self._shutdown_event.clear()
            
            # Inicializar pools de conexión
            self._initialize_connection_pools()
            
            # Iniciar tareas de background
            await self._start_background_tasks()
            
            self.status = ServiceStatus.RUNNING
            self.logger.info("Connection service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            self.status = ServiceStatus.ERROR
            return False
    
    def start(self) -> bool:
        """
        Inicia el servicio de forma síncrona.
        
        Returns:
            True si el servicio se inició correctamente
        """
        try:
            future = self.executor.submit(self._run_async_start)
            return future.result(timeout=30)
        except Exception as e:
            self.logger.error(f"Synchronous service start failed: {e}")
            self.status = ServiceStatus.ERROR
            return False
    
    def _run_async_start(self) -> bool:
        """Helper para ejecutar inicio asíncrono."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.start_async())
        finally:
            loop.close()
    
    async def stop_async(self):
        """Detiene el servicio de forma asíncrona."""
        if not self.is_running:
            self.logger.warning("Service is not running")
            return
        
        self.logger.info("Stopping connection service...")
        self.status = ServiceStatus.STOPPING
        
        try:
            # Señalar shutdown
            self._shutdown_event.set()
            
            # Desconectar todas las cámaras
            await self.disconnect_all_cameras()
            
            # Detener tareas de background
            await self._stop_background_tasks()
            
            # Limpiar pools
            self._cleanup_connection_pools()
            
            self.status = ServiceStatus.STOPPED
            self.logger.info("Connection service stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
            self.status = ServiceStatus.ERROR
    
    def stop(self):
        """Detiene el servicio de forma síncrona."""
        try:
            future = self.executor.submit(self._run_async_stop)
            future.result(timeout=30)
        except Exception as e:
            self.logger.error(f"Synchronous service stop failed: {e}")
    
    def _run_async_stop(self):
        """Helper para ejecutar stop asíncrono."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.stop_async())
        finally:
            loop.close()
    
    def _initialize_connection_pools(self):
        """Inicializa pools de conexión."""
        self.logger.debug("Initializing connection pools")
        
        for pool in ConnectionPool:
            self.connection_pools[pool] = []
        
        self.logger.debug(f"Initialized {len(ConnectionPool)} connection pools")
    
    def _cleanup_connection_pools(self):
        """Limpia pools de conexión."""
        self.logger.debug("Cleaning up connection pools")
        
        for pool_name, pool in self.connection_pools.items():
            for connection in pool:
                try:
                    connection.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up connection in pool {pool_name}: {e}")
            pool.clear()
    
    async def _start_background_tasks(self):
        """Inicia tareas de background."""
        self.logger.debug("Starting background tasks")
        
        # Health check task
        if self.config.health_check_interval > 0:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Retry task
        if self.config.retry_failed_connections:
            self._retry_task = asyncio.create_task(self._retry_loop())
    
    async def _stop_background_tasks(self):
        """Detiene tareas de background."""
        self.logger.debug("Stopping background tasks")
        
        # Cancelar health check
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cancelar retry task
        if self._retry_task and not self._retry_task.done():
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass
    
    # === Gestión de Conexiones Individuales ===
    
    async def connect_camera_async(self, camera: CameraModel, 
                                 connection_type: ConnectionType = ConnectionType.RTSP_STREAM) -> bool:
        """
        Conecta una cámara de forma asíncrona.
        
        Args:
            camera: Modelo de cámara a conectar
            connection_type: Tipo de conexión a establecer
            
        Returns:
            True si la conexión fue exitosa
        """
        self.logger.info(f"[CONNECTION] Recibiendo solicitud de conexión para cámara {camera.camera_id}")
        self.logger.info(f"[CONNECTION] Datos recibidos:")
        self.logger.info(f"  - IP: {camera.connection_config.ip}")
        self.logger.info(f"  - Protocolo: {camera.protocol}")
        self.logger.info(f"  - Marca: {camera.brand}")
        self.logger.info(f"  - Puerto ONVIF: {camera.connection_config.onvif_port}")
        self.logger.info(f"  - Puerto RTSP: {camera.connection_config.rtsp_port}")
        
        if not self.is_running:
            self.logger.error("Service is not running")
            return False
        
        camera_id = camera.camera_id
        
        # Verificar si ya está conectada
        if camera_id in self.connections:
            existing_conn = self.connections[camera_id]
            if existing_conn.is_connected:
                self.logger.warning(f"Camera {camera_id} is already connected")
                return True
        
        # Verificar que el protocolo esté definido
        if not camera.protocol:
            self.logger.error(f"Camera {camera_id} has no protocol defined")
            camera.connection_status = ConnectionStatus.ERROR
            return False
        
        # Usar variable local para evitar problemas de tipo
        protocol = camera.protocol
        
        self.logger.info(f"Connecting camera {camera_id} with protocol {protocol.value}")
        
        try:
            # Crear nueva conexión
            connection = ConnectionModel(
                camera_id=camera_id,
                ip=camera.ip,
                protocol=protocol,
                connection_type=connection_type,
                username=camera.username,
                password=camera.password,
                timeout=self.config.connection_timeout
            )
            
            # Configurar callbacks
            connection.on_status_changed = self._on_connection_status_changed
            connection.on_connection_lost = self._on_connection_lost
            
            # Intentar conexión
            success = await connection.connect_async()
            
            if success:
                # Registrar conexión
                self.connections[camera_id] = connection
                
                # Actualizar métricas
                self._update_metrics_on_connect(protocol)
                
                # Actualizar estado de cámara
                camera.connection_status = ConnectionStatus.CONNECTED
                camera.last_connection_attempt = datetime.now()
                
                # Callback de éxito
                if self.on_connection_established:
                    self.on_connection_established(camera_id, protocol)
                
                self.logger.info(f"Camera {camera_id} connected successfully")
                return True
            else:
                # Limpiar en caso de fallo
                connection.cleanup()
                camera.connection_status = ConnectionStatus.ERROR
                
                self.logger.warning(f"Failed to connect camera {camera_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting camera {camera_id}: {e}")
            camera.connection_status = ConnectionStatus.ERROR
            return False
    
    def connect_camera(self, camera: CameraModel, 
                      connection_type: ConnectionType = ConnectionType.RTSP_STREAM) -> bool:
        """
        Conecta una cámara de forma síncrona.
        
        Args:
            camera: Modelo de cámara a conectar
            connection_type: Tipo de conexión a establecer
            
        Returns:
            True si la conexión fue exitosa
        """
        try:
            future = self.executor.submit(self._run_async_connect, camera, connection_type)
            return future.result(timeout=self.config.connection_timeout * 2)
        except Exception as e:
            self.logger.error(f"Synchronous camera connection failed: {e}")
            return False
    
    def _run_async_connect(self, camera: CameraModel, connection_type: ConnectionType) -> bool:
        """Helper para ejecutar conexión asíncrona."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.connect_camera_async(camera, connection_type))
        finally:
            loop.close()
    
    async def disconnect_camera_async(self, camera_id: str) -> bool:
        """
        Desconecta una cámara de forma asíncrona.
        
        Args:
            camera_id: ID de la cámara a desconectar
            
        Returns:
            True si la desconexión fue exitosa
        """
        if camera_id not in self.connections:
            self.logger.warning(f"Camera {camera_id} is not connected")
            return True
        
        self.logger.info(f"Disconnecting camera {camera_id}")
        
        try:
            connection = self.connections[camera_id]
            protocol = connection.protocol
            
            # Desconectar
            connection.disconnect()
            connection.cleanup()
            
            # Remover de registro
            del self.connections[camera_id]
            
            # Actualizar métricas
            self._update_metrics_on_disconnect(protocol)
            
            self.logger.info(f"Camera {camera_id} disconnected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting camera {camera_id}: {e}")
            return False
    
    def disconnect_camera(self, camera_id: str) -> bool:
        """
        Desconecta una cámara de forma síncrona.
        
        Args:
            camera_id: ID de la cámara a desconectar
            
        Returns:
            True si la desconexión fue exitosa
        """
        try:
            future = self.executor.submit(self._run_async_disconnect, camera_id)
            return future.result(timeout=self.config.connection_timeout)
        except Exception as e:
            self.logger.error(f"Synchronous camera disconnection failed: {e}")
            return False
    
    def _run_async_disconnect(self, camera_id: str) -> bool:
        """Helper para ejecutar desconexión asíncrona."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.disconnect_camera_async(camera_id))
        finally:
            loop.close()
    
    # === Operaciones en Lote ===
    
    async def connect_multiple_cameras_async(self, cameras: List[CameraModel]) -> BatchOperation:
        """
        Conecta múltiples cámaras de forma asíncrona.
        
        Args:
            cameras: Lista de cámaras a conectar
            
        Returns:
            Objeto BatchOperation con resultados
        """
        operation_id = f"connect_batch_{int(time.time())}"
        camera_ids = [camera.camera_id for camera in cameras]
        
        batch_op = BatchOperation(
            operation_id=operation_id,
            operation_type="connect",
            camera_ids=camera_ids,
            start_time=datetime.now()
        )
        
        self.batch_operations[operation_id] = batch_op
        
        self.logger.info(f"Starting batch connect operation for {len(cameras)} cameras")
        
        # Ejecutar conexiones concurrentemente
        tasks = []
        semaphore = asyncio.Semaphore(self.config.max_concurrent_connections)
        
        for camera in cameras:
            task = self._connect_camera_with_semaphore(semaphore, camera, batch_op)
            tasks.append(task)
        
        # Esperar todas las tareas
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Finalizar operación
        batch_op.end_time = datetime.now()
        
        # Callback
        if self.on_batch_completed:
            self.on_batch_completed(batch_op)
        
        self.logger.info(f"Batch connect completed: {batch_op.success_rate:.1f}% success rate")
        return batch_op
    
    async def _connect_camera_with_semaphore(self, semaphore: asyncio.Semaphore, 
                                           camera: CameraModel, batch_op: BatchOperation):
        """Conecta cámara con semáforo para control de concurrencia."""
        async with semaphore:
            try:
                success = await self.connect_camera_async(camera)
                batch_op.results[camera.camera_id] = success
                
                if not success:
                    batch_op.errors[camera.camera_id] = "Connection failed"
                    
            except Exception as e:
                batch_op.results[camera.camera_id] = False
                batch_op.errors[camera.camera_id] = str(e)
                self.logger.error(f"Error in batch connect for {camera.camera_id}: {e}")
    
    async def disconnect_all_cameras(self) -> BatchOperation:
        """
        Desconecta todas las cámaras conectadas.
        
        Returns:
            Objeto BatchOperation con resultados
        """
        camera_ids = list(self.connections.keys())
        
        operation_id = f"disconnect_all_{int(time.time())}"
        batch_op = BatchOperation(
            operation_id=operation_id,
            operation_type="disconnect_all",
            camera_ids=camera_ids,
            start_time=datetime.now()
        )
        
        self.batch_operations[operation_id] = batch_op
        
        if not camera_ids:
            batch_op.end_time = datetime.now()
            return batch_op
        
        self.logger.info(f"Disconnecting all {len(camera_ids)} cameras")
        
        # Ejecutar desconexiones concurrentemente
        tasks = []
        for camera_id in camera_ids:
            task = self._disconnect_camera_for_batch(camera_id, batch_op)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        batch_op.end_time = datetime.now()
        
        self.logger.info(f"All cameras disconnected: {batch_op.success_rate:.1f}% success rate")
        return batch_op
    
    async def _disconnect_camera_for_batch(self, camera_id: str, batch_op: BatchOperation):
        """Desconecta cámara para operación en lote."""
        try:
            success = await self.disconnect_camera_async(camera_id)
            batch_op.results[camera_id] = success
            
            if not success:
                batch_op.errors[camera_id] = "Disconnection failed"
                
        except Exception as e:
            batch_op.results[camera_id] = False
            batch_op.errors[camera_id] = str(e)
            self.logger.error(f"Error in batch disconnect for {camera_id}: {e}")
    
    # === Monitoreo y Métricas ===
    
    async def _health_check_loop(self):
        """Loop de health check para conexiones activas."""
        self.logger.debug("Starting health check loop")
        
        while not self._shutdown_event.is_set():
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)  # Backoff en caso de error
        
        self.logger.debug("Health check loop stopped")
    
    async def _perform_health_checks(self):
        """Realiza health checks en todas las conexiones activas."""
        if not self.connections:
            return
        
        self.logger.debug(f"Performing health checks on {len(self.connections)} connections")
        
        failed_connections = []
        
        for camera_id, connection in self.connections.items():
            try:
                if connection.is_connected:
                    # El health check se maneja internamente en ConnectionModel
                    if not connection.health.is_alive:
                        failed_connections.append(camera_id)
            except Exception as e:
                self.logger.error(f"Health check error for {camera_id}: {e}")
                failed_connections.append(camera_id)
        
        # Manejar conexiones fallidas
        for camera_id in failed_connections:
            await self._handle_failed_connection(camera_id)
        
        # Actualizar métricas
        self._update_aggregate_metrics()
    
    async def _handle_failed_connection(self, camera_id: str):
        """Maneja una conexión fallida."""
        self.logger.warning(f"Handling failed connection for camera {camera_id}")
        
        if self.config.auto_reconnect:
            # Intentar reconexión automática se manejará en retry loop
            pass
        
        # Callback de conexión perdida
        if self.on_connection_lost:
            self.on_connection_lost(camera_id, "Health check failed")
    
    async def _retry_loop(self):
        """Loop de reintentos para conexiones fallidas."""
        self.logger.debug("Starting retry loop")
        
        while not self._shutdown_event.is_set():
            try:
                await self._retry_failed_connections()
                await asyncio.sleep(self.config.retry_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in retry loop: {e}")
                await asyncio.sleep(10)  # Backoff
        
        self.logger.debug("Retry loop stopped")
    
    async def _retry_failed_connections(self):
        """Reintenta conexiones fallidas."""
        failed_connections = [
            (camera_id, conn) for camera_id, conn in self.connections.items()
            if not conn.is_connected
        ]
        
        if not failed_connections:
            return
        
        self.logger.info(f"Retrying {len(failed_connections)} failed connections")
        
        for camera_id, connection in failed_connections:
            try:
                success = await connection.connect_async()
                if success:
                    self.logger.info(f"Reconnected camera {camera_id}")
                    self._update_metrics_on_connect(connection.protocol)
            except Exception as e:
                self.logger.error(f"Retry failed for {camera_id}: {e}")
    
    def _update_metrics_on_connect(self, protocol: ProtocolType):
        """Actualiza métricas al conectar."""
        self.metrics.total_connections += 1
        self.metrics.active_connections += 1
        self.metrics.update_protocol_count(protocol, 1)
        self.metrics.last_updated = datetime.now()
    
    def _update_metrics_on_disconnect(self, protocol: ProtocolType):
        """Actualiza métricas al desconectar."""
        self.metrics.active_connections = max(0, self.metrics.active_connections - 1)
        self.metrics.update_protocol_count(protocol, -1)
        self.metrics.last_updated = datetime.now()
    
    def _update_aggregate_metrics(self):
        """Actualiza métricas agregadas."""
        if not self.connections:
            return
        
        # Calcular tiempo promedio de respuesta
        response_times = []
        for connection in self.connections.values():
            if connection.health.average_response_time > 0:
                response_times.append(connection.health.average_response_time)
        
        if response_times:
            self.metrics.average_response_time = sum(response_times) / len(response_times)
        
        # Calcular uptime
        healthy_connections = sum(1 for conn in self.connections.values() if conn.health.is_alive)
        total_connections = len(self.connections)
        
        if total_connections > 0:
            self.metrics.uptime_percentage = (healthy_connections / total_connections) * 100
        
        self.metrics.last_updated = datetime.now()
    
    # === Callbacks ===
    
    def _on_connection_status_changed(self, old_status: ConnectionStatus, new_status: ConnectionStatus):
        """Callback para cambios de estado de conexión."""
        self.logger.debug(f"Connection status changed: {old_status.value} → {new_status.value}")
        
        if new_status == ConnectionStatus.ERROR:
            self.metrics.failed_connections += 1
    
    def _on_connection_lost(self, reason: str):
        """Callback para conexión perdida."""
        self.logger.warning(f"Connection lost: {reason}")
    
    # === API Pública ===
    
    def get_connection_status(self, camera_id: str) -> Optional[ConnectionStatus]:
        """Obtiene estado de conexión de una cámara."""
        if camera_id in self.connections:
            return self.connections[camera_id].status
        return None
    
    def get_active_connections(self) -> Dict[str, ConnectionModel]:
        """Obtiene todas las conexiones activas."""
        return {
            camera_id: conn for camera_id, conn in self.connections.items()
            if conn.is_connected
        }
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del servicio."""
        return {
            'service_status': self.status.value,
            'total_connections': len(self.connections),
            'active_connections': len(self.get_active_connections()),
            'metrics': {
                'total_connections': self.metrics.total_connections,
                'active_connections': self.metrics.active_connections,
                'failed_connections': self.metrics.failed_connections,
                'average_response_time': self.metrics.average_response_time,
                'uptime_percentage': self.metrics.uptime_percentage,
                'connections_per_protocol': self.metrics.connections_per_protocol,
                'last_updated': self.metrics.last_updated.isoformat()
            },
            'configuration': {
                'max_concurrent_connections': self.config.max_concurrent_connections,
                'connection_timeout': self.config.connection_timeout,
                'health_check_interval': self.config.health_check_interval,
                'auto_reconnect': self.config.auto_reconnect
            },
            'batch_operations': len(self.batch_operations)
        }
    
    def get_batch_operation(self, operation_id: str) -> Optional[BatchOperation]:
        """Obtiene información de una operación en lote."""
        return self.batch_operations.get(operation_id)
    
    # === Cleanup ===
    
    def cleanup(self):
        """Limpia recursos del servicio."""
        self.logger.info("Cleaning up connection service...")
        
        # Detener servicio
        if self.is_running:
            self.stop()
        
        # Limpiar conexiones
        for connection in self.connections.values():
            try:
                connection.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up connection: {e}")
        
        self.connections.clear()
        
        # Cerrar thread pool
        self.executor.shutdown(wait=True)
        
        self.logger.info("Connection service cleanup completed")
    
    def __del__(self):
        """Destructor para cleanup automático."""
        try:
            self.cleanup()
        except Exception:
            pass  # Evitar errores en destructor


# Función global para obtener instancia del servicio
_connection_service_instance: Optional[ConnectionService] = None


def get_connection_service(config: Optional[ConnectionServiceConfig] = None) -> ConnectionService:
    """
    Obtiene la instancia global del ConnectionService.
    
    Args:
        config: Configuración opcional
        
    Returns:
        Instancia del ConnectionService
    """
    global _connection_service_instance
    
    if _connection_service_instance is None:
        _connection_service_instance = ConnectionService(config)
    
    return _connection_service_instance 