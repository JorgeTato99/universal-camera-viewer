"""
Scan Service - MVP Architecture
===============================

Servicio de coordinación de escaneos de red para descubrimiento de cámaras IP.
Gestiona múltiples instancias de ScanModel, orchestración de escaneos en paralelo,
cache de resultados y análisis de tendencias de descubrimiento.

Responsabilidades:
- Coordinar múltiples ScanModel instances
- Implementar cache inteligente de resultados
- Gestionar escaneos programados y automáticos
- Analizar patrones de dispositivos en la red
- Proporcionar métricas de descubrimiento
- Optimizar rangos de escaneo basado en historiales
"""

import asyncio
import ipaddress
import json

import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from services.logging_service import get_secure_logger

try:
    from ..models.scan_model import ScanModel, ScanStatus, ScanMethod, ScanRange, ScanResult, ProtocolDetectionResult
    from ..models.camera_model import ProtocolType
    from ..utils.config import ConfigurationManager
except ImportError:
    # Fallback para ejecución directa
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from models.scan_model import ScanModel, ScanStatus, ScanMethod, ScanRange, ScanResult, ProtocolDetectionResult
    from models.camera_model import ProtocolType
    from utils.config import ConfigurationManager


class ScanServiceStatus(Enum):
    """Estados del servicio de escaneo."""
    IDLE = "idle"
    SCANNING = "scanning"
    PROCESSING = "processing"
    ERROR = "error"


class ScanPriority(Enum):
    """Prioridades de escaneo."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ScanServiceConfig:
    """Configuración del servicio de escaneo."""
    max_concurrent_scans: int = 3
    default_timeout: float = 5.0
    cache_expiry_hours: int = 24
    enable_scan_cache: bool = True
    auto_optimize_ranges: bool = True
    scheduled_scan_interval: int = 3600  # segundos
    max_cache_entries: int = 1000
    scan_history_retention_days: int = 30
    enable_network_analysis: bool = True
    discovery_methods: List[ScanMethod] = field(
        default_factory=lambda: [
            ScanMethod.PING_SWEEP,
            ScanMethod.PORT_SCAN,
            ScanMethod.PROTOCOL_DETECTION,
            ScanMethod.ONVIF_DISCOVERY
        ]
    )
    
    def validate(self):
        """Valida la configuración."""
        if self.max_concurrent_scans <= 0:
            raise ValueError("max_concurrent_scans debe ser mayor a 0")
        if self.default_timeout <= 0:
            raise ValueError("default_timeout debe ser mayor a 0")
        if self.cache_expiry_hours <= 0:
            raise ValueError("cache_expiry_hours debe ser mayor a 0")


@dataclass
class CachedScanResult:
    """Resultado de escaneo en cache."""
    scan_id: str
    timestamp: datetime
    scan_range: ScanRange
    results: List[Dict[str, Any]]
    cameras_found: int
    scan_duration: float
    
    @property
    def is_expired(self) -> bool:
        """Indica si el resultado está expirado."""
        expiry_time = self.timestamp + timedelta(hours=24)  # Default 24h
        return datetime.now() > expiry_time
    
    @property
    def age_hours(self) -> float:
        """Edad del resultado en horas."""
        return (datetime.now() - self.timestamp).total_seconds() / 3600


@dataclass
class NetworkAnalysis:
    """Análisis de red basado en historiales de escaneo."""
    common_ip_ranges: List[str] = field(default_factory=list)
    frequent_ports: List[int] = field(default_factory=list)
    protocol_distribution: Dict[str, float] = field(default_factory=dict)
    peak_discovery_hours: List[int] = field(default_factory=list)
    device_stability: Dict[str, float] = field(default_factory=dict)  # IP -> stability score
    recommended_scan_ranges: List[ScanRange] = field(default_factory=list)
    last_analysis: datetime = field(default_factory=datetime.now)
    
    def get_optimal_scan_range(self, base_ip: str) -> Optional[ScanRange]:
        """Obtiene rango de escaneo óptimo basado en análisis."""
        if not self.common_ip_ranges:
            return None
        
        # Encontrar rango más común que incluya la IP base
        try:
            base_network = ipaddress.ip_network(f"{base_ip}/24", strict=False)
            
            for range_str in self.common_ip_ranges:
                if base_network.overlaps(ipaddress.ip_network(range_str)):
                    network = ipaddress.ip_network(range_str)
                    return ScanRange(
                        start_ip=str(network.network_address),
                        end_ip=str(network.broadcast_address),
                        ports=self.frequent_ports[:5] if self.frequent_ports else [80, 554, 8080]
                    )
        except Exception:
            pass
        
        return None


@dataclass
class ScanJob:
    """Trabajo de escaneo programado."""
    job_id: str
    scan_range: ScanRange
    methods: List[ScanMethod]
    priority: ScanPriority
    scheduled_time: datetime
    created_time: datetime = field(default_factory=datetime.now)
    started_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    scan_model: Optional[ScanModel] = None
    result_cache_key: Optional[str] = None
    
    @property
    def is_ready(self) -> bool:
        """Indica si el trabajo está listo para ejecutar."""
        return datetime.now() >= self.scheduled_time
    
    @property
    def is_running(self) -> bool:
        """Indica si el trabajo está ejecutándose."""
        return self.scan_model is not None and self.scan_model.is_running
    
    @property
    def is_completed(self) -> bool:
        """Indica si el trabajo está completo."""
        return self.completed_time is not None


class ScanService:
    """
    Servicio de coordinación de escaneos para arquitectura MVP.
    
    Gestiona múltiples escaneos concurrentes, cache de resultados,
    análisis de red y escaneos programados.
    """
    
    def __init__(self, config: Optional[ScanServiceConfig] = None):
        """
        Inicializa el servicio de escaneo.
        
        Args:
            config: Configuración del servicio (opcional)
        """
        self.logger = get_secure_logger("services.scan_service")
        
        # Configuración
        self.config = config or ScanServiceConfig()
        self.config.validate()
        
        # Estado del servicio
        self._status = ScanServiceStatus.IDLE
        self._status_lock = threading.Lock()
        self._shutdown_event = threading.Event()
        
        # Gestión de escaneos
        self.active_scans: Dict[str, ScanModel] = {}  # scan_id -> ScanModel
        self.scan_queue: List[ScanJob] = []
        self.scan_history: List[Dict[str, Any]] = []
        
        # Resultados completados recientes (para evitar race conditions)
        self.completed_scans: Dict[str, Dict[str, Any]] = {}
        self.max_completed_scans = 20
        
        # Cache de resultados
        self.result_cache: Dict[str, CachedScanResult] = {}  # cache_key -> result
        self.cache_lock = threading.Lock()
        
        # Análisis de red
        self.network_analysis = NetworkAnalysis()
        self.analysis_lock = threading.Lock()
        
        # Threading
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_scans,
            thread_name_prefix="scan_service"
        )
        self._scheduler_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_scan_completed: Optional[Callable[[str, List[Dict[str, Any]]], None]] = None
        self.on_camera_discovered: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self.on_scan_progress: Optional[Callable[[str, float], None]] = None
        
        # Configuración manager
        self.config_manager = ConfigurationManager()
        
        # Archivos de persistencia - usar rutas absolutas basadas en src-python
        data_dir = Path(__file__).parent.parent / "data"
        self.cache_file = data_dir / "scan_cache.json"
        self.history_file = data_dir / "scan_history.json"
        self.analysis_file = data_dir / "network_analysis.json"
        
        # Crear directorio de datos
        data_dir.mkdir(exist_ok=True)
        
        # Cargar datos persistentes
        self._load_persistent_data()
        
        self.logger.info("Scan service initialized")
    
    @property
    def status(self) -> ScanServiceStatus:
        """Estado actual del servicio (thread-safe)."""
        with self._status_lock:
            return self._status
    
    @status.setter
    def status(self, new_status: ScanServiceStatus):
        """Establece nuevo estado del servicio (thread-safe)."""
        with self._status_lock:
            old_status = self._status
            self._status = new_status
            
            if old_status != new_status:
                self.logger.info(f"Scan service status changed: {old_status.value} → {new_status.value}")
    
    @property
    def is_scanning(self) -> bool:
        """Indica si hay escaneos activos."""
        return len(self.active_scans) > 0 or self.status == ScanServiceStatus.SCANNING
    
    # === Gestión del Servicio ===
    
    async def start_async(self) -> bool:
        """
        Inicia el servicio de forma asíncrona.
        
        Returns:
            True si el servicio se inició correctamente
        """
        self.logger.info("Starting scan service...")
        
        try:
            # Limpiar estado previo
            self._shutdown_event.clear()
            
            # Iniciar tareas de background
            await self._start_background_tasks()
            
            # Procesar trabajos pendientes en la cola
            await self._process_pending_jobs()
            
            self.logger.info("Scan service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scan service: {e}")
            self.status = ScanServiceStatus.ERROR
            return False
    
    def start(self) -> bool:
        """Inicia el servicio de forma síncrona."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.start_async())
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Synchronous scan service start failed: {e}")
            return False
    
    async def stop_async(self):
        """Detiene el servicio de forma asíncrona."""
        self.logger.info("Stopping scan service...")
        
        try:
            # Señalar shutdown
            self._shutdown_event.set()
            
            # Cancelar escaneos activos
            await self._cancel_active_scans()
            
            # Detener tareas de background
            await self._stop_background_tasks()
            
            # Guardar datos persistentes
            self._save_persistent_data()
            
            self.logger.info("Scan service stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping scan service: {e}")
            self.status = ScanServiceStatus.ERROR
    
    def stop(self):
        """Detiene el servicio de forma síncrona."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.stop_async())
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Synchronous scan service stop failed: {e}")
    
    async def _start_background_tasks(self):
        """Inicia tareas de background."""
        self.logger.debug("Starting background tasks")
        
        # Scheduler task
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # Cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _stop_background_tasks(self):
        """Detiene tareas de background."""
        self.logger.debug("Stopping background tasks")
        
        # Cancelar scheduler
        if self._scheduler_task and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancelar cleanup
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    # === Gestión de Escaneos ===
    
    async def start_scan_async(self, scan_range: ScanRange, 
                             methods: Optional[List[ScanMethod]] = None,
                             priority: ScanPriority = ScanPriority.NORMAL,
                             use_cache: bool = True) -> str:
        """
        Inicia un escaneo de forma asíncrona.
        
        Args:
            scan_range: Rango de escaneo
            methods: Métodos de escaneo (opcional)
            priority: Prioridad del escaneo
            use_cache: Usar cache si está disponible
            
        Returns:
            ID del escaneo iniciado
        """
        # Verificar cache si está habilitado
        if use_cache and self.config.enable_scan_cache:
            cached_result = self._get_cached_result(scan_range)
            if cached_result:
                self.logger.info(f"Using cached result for scan range {scan_range.start_ip}-{scan_range.end_ip}")
                # Simular callback con resultado de cache
                if self.on_scan_completed:
                    self.on_scan_completed(cached_result.scan_id, cached_result.results)
                return cached_result.scan_id
        
        # Verificar límite de escaneos concurrentes
        if len(self.active_scans) >= self.config.max_concurrent_scans:
            # Agregar a cola
            job_id = f"scan_job_{int(time.time())}_{len(self.scan_queue)}"
            job = ScanJob(
                job_id=job_id,
                scan_range=scan_range,
                methods=methods or self.config.discovery_methods,
                priority=priority,
                scheduled_time=datetime.now()
            )
            
            # Insertar según prioridad
            self._insert_job_by_priority(job)
            
            self.logger.info(f"Scan queued: {job_id} (queue size: {len(self.scan_queue)})")
            return job_id
        
        # Crear y ejecutar escaneo inmediatamente
        scan_id = f"scan_{int(time.time())}_{len(self.active_scans)}"
        scan_model = ScanModel(
            scan_id=scan_id,
            scan_range=scan_range,
            methods=methods or self.config.discovery_methods,
            timeout=self.config.default_timeout
        )
        
        # Configurar callbacks
        scan_model.add_progress_callback(lambda progress: self._on_scan_progress(scan_id, progress))
        
        # Registrar escaneo activo
        self.active_scans[scan_id] = scan_model
        self.status = ScanServiceStatus.SCANNING
        
        # Iniciar escaneo
        self.logger.info(f"Starting scan {scan_id} for range {scan_range.start_ip}-{scan_range.end_ip}")
        
        # Ejecutar en background
        asyncio.create_task(self._execute_scan(scan_id, scan_model))
        
        return scan_id
    
    def start_scan(self, scan_range: ScanRange, 
                  methods: Optional[List[ScanMethod]] = None,
                  priority: ScanPriority = ScanPriority.NORMAL,
                  use_cache: bool = True) -> str:
        """Inicia un escaneo de forma síncrona."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.start_scan_async(scan_range, methods, priority, use_cache)
                )
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Synchronous scan start failed: {e}")
            return ""
    
    async def _execute_scan(self, scan_id: str, scan_model: ScanModel):
        """Ejecuta un escaneo y procesa resultados."""
        try:
            # Ejecutar escaneo
            success = await scan_model.start_scan_async()
            
            if success:
                # Procesar resultados
                camera_results = scan_model.get_camera_results()
                all_results = scan_model.get_all_results()
                
                # Actualizar cache
                if self.config.enable_scan_cache:
                    self._cache_scan_result(scan_id, scan_model, all_results)
                
                # Actualizar historial
                self._add_to_history(scan_id, scan_model, camera_results)
                
                # Actualizar análisis de red
                if self.config.enable_network_analysis:
                    await self._update_network_analysis(camera_results)
                
                # Callback de finalización
                if self.on_scan_completed:
                    self.on_scan_completed(scan_id, camera_results)
                
                # Callbacks por cámaras descubiertas
                if self.on_camera_discovered:
                    for camera in camera_results:
                        self.on_camera_discovered(scan_id, camera)
                
                self.logger.info(f"Scan {scan_id} completed successfully. Found {len(camera_results)} cameras")
            else:
                self.logger.warning(f"Scan {scan_id} failed")
                
        except Exception as e:
            self.logger.error(f"Error executing scan {scan_id}: {e}")
        finally:
            # Guardar resultados antes de eliminar el modelo
            if scan_id in self.active_scans:
                scan_model = self.active_scans[scan_id]
                
                # Guardar resultados completos
                self.completed_scans[scan_id] = {
                    'scan_id': scan_id,
                    'status': scan_model.status.value,
                    'results': scan_model.get_all_results(),
                    'camera_results': scan_model.get_camera_results(),
                    'stats': scan_model.get_scan_stats(),
                    'completed_at': datetime.now()
                }
                
                # Limpiar escaneos antiguos si excede el límite
                if len(self.completed_scans) > self.max_completed_scans:
                    oldest_id = min(self.completed_scans.keys(), 
                                  key=lambda k: self.completed_scans[k]['completed_at'])
                    del self.completed_scans[oldest_id]
                
                # Ahora sí eliminar el modelo activo
                del self.active_scans[scan_id]
            
            # Actualizar estado
            if not self.active_scans:
                self.status = ScanServiceStatus.IDLE
            
            # Procesar siguiente trabajo en cola
            await self._process_next_queued_job()
    
    async def cancel_scan(self, scan_id: str) -> bool:
        """
        Cancela un escaneo activo.
        
        Args:
            scan_id: ID del escaneo a cancelar
            
        Returns:
            True si se canceló exitosamente
        """
        if scan_id in self.active_scans:
            try:
                self.active_scans[scan_id].cancel_scan()
                del self.active_scans[scan_id]
                
                if not self.active_scans:
                    self.status = ScanServiceStatus.IDLE
                
                self.logger.info(f"Scan {scan_id} cancelled")
                return True
            except Exception as e:
                self.logger.error(f"Error cancelling scan {scan_id}: {e}")
                return False
        else:
            # Buscar en cola
            for i, job in enumerate(self.scan_queue):
                if job.job_id == scan_id:
                    del self.scan_queue[i]
                    self.logger.info(f"Queued scan {scan_id} cancelled")
                    return True
            
            self.logger.warning(f"Scan {scan_id} not found")
            return False
    
    async def _cancel_active_scans(self):
        """Cancela todos los escaneos activos."""
        scan_ids = list(self.active_scans.keys())
        
        for scan_id in scan_ids:
            await self.cancel_scan(scan_id)
        
        # Limpiar cola
        self.scan_queue.clear()
    
    # === Gestión de Cola y Programación ===
    
    def _insert_job_by_priority(self, job: ScanJob):
        """Inserta trabajo en cola según prioridad."""
        priority_order = {
            ScanPriority.URGENT: 0,
            ScanPriority.HIGH: 1,
            ScanPriority.NORMAL: 2,
            ScanPriority.LOW: 3
        }
        
        job_priority = priority_order[job.priority]
        
        # Encontrar posición de inserción
        insert_pos = 0
        for i, existing_job in enumerate(self.scan_queue):
            existing_priority = priority_order[existing_job.priority]
            if job_priority <= existing_priority:
                insert_pos = i
                break
            insert_pos = i + 1
        
        self.scan_queue.insert(insert_pos, job)
    
    async def _process_pending_jobs(self):
        """Procesa trabajos pendientes en la cola."""
        while self.scan_queue and len(self.active_scans) < self.config.max_concurrent_scans:
            await self._process_next_queued_job()
    
    async def _process_next_queued_job(self):
        """Procesa el siguiente trabajo en cola."""
        if not self.scan_queue or len(self.active_scans) >= self.config.max_concurrent_scans:
            return
        
        # Obtener siguiente trabajo listo
        ready_job = None
        for i, job in enumerate(self.scan_queue):
            if job.is_ready:
                ready_job = self.scan_queue.pop(i)
                break
        
        if not ready_job:
            return
        
        # Ejecutar trabajo
        try:
            scan_id = await self.start_scan_async(
                ready_job.scan_range,
                ready_job.methods,
                ready_job.priority,
                use_cache=True
            )
            
            ready_job.started_time = datetime.now()
            self.logger.info(f"Started queued job {ready_job.job_id} as scan {scan_id}")
            
        except Exception as e:
            self.logger.error(f"Error starting queued job {ready_job.job_id}: {e}")
    
    async def _scheduler_loop(self):
        """Loop principal del scheduler."""
        self.logger.debug("Starting scheduler loop")
        
        while not self._shutdown_event.is_set():
            try:
                # Procesar trabajos pendientes
                await self._process_pending_jobs()
                
                # Escaneos automáticos si está configurado
                if self.config.scheduled_scan_interval > 0:
                    await self._check_scheduled_scans()
                
                await asyncio.sleep(30)  # Check cada 30 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(5)
        
        self.logger.debug("Scheduler loop stopped")
    
    async def _check_scheduled_scans(self):
        """Verifica si es tiempo de escaneos programados."""
        # Por ahora no implementamos escaneos automáticos
        # En implementación real podríamos tener escaneos periódicos
        pass
    
    # === Cache de Resultados ===
    
    def _get_cache_key(self, scan_range: ScanRange) -> str:
        """Genera clave de cache para un rango de escaneo."""
        return f"{scan_range.start_ip}_{scan_range.end_ip}_{sorted(scan_range.ports)}"
    
    def _get_cached_result(self, scan_range: ScanRange) -> Optional[CachedScanResult]:
        """Obtiene resultado de cache si está disponible y válido."""
        cache_key = self._get_cache_key(scan_range)
        
        with self.cache_lock:
            if cache_key in self.result_cache:
                cached = self.result_cache[cache_key]
                if not cached.is_expired:
                    return cached
                else:
                    # Limpiar cache expirado
                    del self.result_cache[cache_key]
        
        return None
    
    def _cache_scan_result(self, scan_id: str, scan_model: ScanModel, results: List[Dict[str, Any]]):
        """Almacena resultado en cache."""
        cache_key = self._get_cache_key(scan_model.scan_range)
        
        cached_result = CachedScanResult(
            scan_id=scan_id,
            timestamp=datetime.now(),
            scan_range=scan_model.scan_range,
            results=results,
            cameras_found=len(scan_model.get_camera_results()),
            scan_duration=scan_model.duration_seconds
        )
        
        with self.cache_lock:
            self.result_cache[cache_key] = cached_result
            
            # Limpiar cache si excede límite
            if len(self.result_cache) > self.config.max_cache_entries:
                self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Limpia entradas expiradas del cache."""
        expired_keys = [
            key for key, cached in self.result_cache.items()
            if cached.is_expired
        ]
        
        for key in expired_keys:
            del self.result_cache[key]
        
        # Si aún excede límite, remover más antiguos
        if len(self.result_cache) > self.config.max_cache_entries:
            sorted_entries = sorted(
                self.result_cache.items(),
                key=lambda x: x[1].timestamp
            )
            
            entries_to_remove = len(self.result_cache) - self.config.max_cache_entries
            for i in range(entries_to_remove):
                key = sorted_entries[i][0]
                del self.result_cache[key]
    
    async def _cleanup_loop(self):
        """Loop de limpieza periódica."""
        self.logger.debug("Starting cleanup loop")
        
        while not self._shutdown_event.is_set():
            try:
                # Limpiar cache
                with self.cache_lock:
                    self._cleanup_cache()
                
                # Limpiar historial antiguo
                self._cleanup_history()
                
                await asyncio.sleep(3600)  # Cleanup cada hora
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)  # Backoff 5 min
        
        self.logger.debug("Cleanup loop stopped")
    
    # === Historial y Análisis ===
    
    def _add_to_history(self, scan_id: str, scan_model: ScanModel, camera_results: List[Dict[str, Any]]):
        """Añade escaneo al historial."""
        history_entry = {
            'scan_id': scan_id,
            'timestamp': datetime.now().isoformat(),
            'scan_range': {
                'start_ip': scan_model.scan_range.start_ip,
                'end_ip': scan_model.scan_range.end_ip,
                'ports': scan_model.scan_range.ports
            },
            'methods': [method.value for method in scan_model.methods],
            'duration_seconds': scan_model.duration_seconds,
            'cameras_found': len(camera_results),
            'total_ips_scanned': len(scan_model.results),
            'camera_results': camera_results
        }
        
        self.scan_history.append(history_entry)
        
        # Limitar tamaño del historial en memoria
        if len(self.scan_history) > 100:  # Mantener últimos 100 en memoria
            self.scan_history = self.scan_history[-100:]
    
    def _cleanup_history(self):
        """Limpia historial antiguo."""
        if not self.config.scan_history_retention_days:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.config.scan_history_retention_days)
        
        self.scan_history = [
            entry for entry in self.scan_history
            if datetime.fromisoformat(entry['timestamp']) > cutoff_date
        ]
    
    async def _update_network_analysis(self, camera_results: List[Dict[str, Any]]):
        """Actualiza análisis de red basado en resultados."""
        if not camera_results:
            return
        
        with self.analysis_lock:
            # Analizar rangos IP comunes
            ip_networks = set()
            for camera in camera_results:
                try:
                    ip = camera['ip']
                    network = ipaddress.ip_network(f"{ip}/24", strict=False)
                    ip_networks.add(str(network))
                except Exception:
                    continue
            
            # Actualizar rangos comunes
            for network in ip_networks:
                if network not in self.network_analysis.common_ip_ranges:
                    self.network_analysis.common_ip_ranges.append(network)
            
            # Analizar puertos frecuentes
            port_counts = defaultdict(int)
            for camera in camera_results:
                for port in camera.get('open_ports', []):
                    port_counts[port] += 1
            
            # Actualizar puertos frecuentes
            frequent_ports = sorted(port_counts.keys(), key=lambda p: port_counts[p], reverse=True)
            self.network_analysis.frequent_ports = frequent_ports[:10]  # Top 10
            
            # Analizar distribución de protocolos
            protocol_counts = defaultdict(int)
            for camera in camera_results:
                for protocol in camera.get('all_protocols', []):
                    protocol_counts[protocol] += 1
            
            total_protocols = sum(protocol_counts.values())
            if total_protocols > 0:
                self.network_analysis.protocol_distribution = {
                    protocol: (count / total_protocols) * 100
                    for protocol, count in protocol_counts.items()
                }
            
            self.network_analysis.last_analysis = datetime.now()
    
    # === Callbacks ===
    
    def _on_scan_progress(self, scan_id: str, progress):
        """Callback para progreso de escaneo."""
        if self.on_scan_progress:
            try:
                self.on_scan_progress(scan_id, progress.overall_progress_percentage)
            except Exception as e:
                self.logger.error(f"Error in scan progress callback: {e}")
    
    # === Persistencia ===
    
    def _load_persistent_data(self):
        """Carga datos persistentes desde archivos."""
        try:
            # Cargar cache
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                    for key, data in cache_data.items():
                        try:
                            cached_result = CachedScanResult(
                                scan_id=data['scan_id'],
                                timestamp=datetime.fromisoformat(data['timestamp']),
                                scan_range=ScanRange(**data['scan_range']),
                                results=data['results'],
                                cameras_found=data['cameras_found'],
                                scan_duration=data['scan_duration']
                            )
                            
                            if not cached_result.is_expired:
                                self.result_cache[key] = cached_result
                        except Exception as e:
                            self.logger.warning(f"Error loading cache entry: {e}")
            
            # Cargar historial
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    self.scan_history = json.load(f)
            
            # Cargar análisis
            if self.analysis_file.exists():
                with open(self.analysis_file, 'r') as f:
                    analysis_data = json.load(f)
                    self.network_analysis = NetworkAnalysis(**analysis_data)
                    
        except Exception as e:
            self.logger.error(f"Error loading persistent data: {e}")
    
    def _save_persistent_data(self):
        """Guarda datos persistentes a archivos."""
        try:
            # Guardar cache
            cache_data = {}
            with self.cache_lock:
                for key, cached in self.result_cache.items():
                    if not cached.is_expired:
                        cache_data[key] = {
                            'scan_id': cached.scan_id,
                            'timestamp': cached.timestamp.isoformat(),
                            'scan_range': asdict(cached.scan_range),
                            'results': cached.results,
                            'cameras_found': cached.cameras_found,
                            'scan_duration': cached.scan_duration
                        }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            # Guardar historial
            with open(self.history_file, 'w') as f:
                json.dump(self.scan_history, f, indent=2)
            
            # Guardar análisis
            with self.analysis_lock:
                analysis_data = asdict(self.network_analysis)
                analysis_data['last_analysis'] = self.network_analysis.last_analysis.isoformat()
                
                with open(self.analysis_file, 'w') as f:
                    json.dump(analysis_data, f, indent=2)
                    
        except Exception as e:
            self.logger.error(f"Error saving persistent data: {e}")
    
    # === API Pública ===
    
    def get_scan_status(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene estado de un escaneo.
        
        Returns:
            Diccionario con información del estado o None
        """
        # Buscar en activos
        if scan_id in self.active_scans:
            scan_model = self.active_scans[scan_id]
            return {
                'status': scan_model.status.value,
                'progress': scan_model.progress.overall_progress_percentage,
                'cameras_found': scan_model.progress.cameras_found,
                'elapsed_time': scan_model.duration_seconds
            }
            
        # Buscar en completados
        if scan_id in self.completed_scans:
            completed = self.completed_scans[scan_id]
            return {
                'status': completed['status'],
                'progress': 100.0,
                'cameras_found': len(completed.get('camera_results', [])),
                'elapsed_time': completed['stats'].get('duration_seconds', 0)
            }
            
        return None
    
    def get_scan_progress(self, scan_id: str) -> Optional[float]:
        """Obtiene progreso de un escaneo."""
        if scan_id in self.active_scans:
            return self.active_scans[scan_id].progress.overall_progress_percentage
        return None
    
    def get_active_scans(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene información de escaneos activos."""
        return {
            scan_id: {
                'status': scan.status.value,
                'progress': scan.progress.overall_progress_percentage,
                'scan_range': {
                    'start_ip': scan.scan_range.start_ip,
                    'end_ip': scan.scan_range.end_ip,
                    'ports': scan.scan_range.ports
                },
                'duration': scan.duration_seconds,
                'cameras_found': scan.progress.cameras_found
            }
            for scan_id, scan in self.active_scans.items()
        }
    
    def get_scan_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene historial de escaneos."""
        return self.scan_history[-limit:] if self.scan_history else []
    
    async def get_scan_results(self, scan_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene los resultados de un escaneo.
        
        Args:
            scan_id: ID del escaneo
            
        Returns:
            Lista de resultados del escaneo o None si no existe
        """
        # Primero buscar en escaneos completados
        if scan_id in self.completed_scans:
            return self.completed_scans[scan_id]['results']
            
        # Si está activo, obtener del modelo
        if scan_id in self.active_scans:
            scan_model = self.active_scans[scan_id]
            return scan_model.get_all_results()
            
        # No encontrado
        return None
    
    def get_network_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis de red."""
        with self.analysis_lock:
            return {
                'common_ip_ranges': self.network_analysis.common_ip_ranges,
                'frequent_ports': self.network_analysis.frequent_ports,
                'protocol_distribution': self.network_analysis.protocol_distribution,
                'last_analysis': self.network_analysis.last_analysis.isoformat(),
                'total_ranges_discovered': len(self.network_analysis.common_ip_ranges)
            }
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del servicio."""
        return {
            'service_status': self.status.value,
            'active_scans': len(self.active_scans),
            'queued_scans': len(self.scan_queue),
            'cache_entries': len(self.result_cache),
            'history_entries': len(self.scan_history),
            'total_cameras_discovered': sum(
                entry.get('cameras_found', 0) for entry in self.scan_history
            ),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'configuration': {
                'max_concurrent_scans': self.config.max_concurrent_scans,
                'cache_enabled': self.config.enable_scan_cache,
                'network_analysis_enabled': self.config.enable_network_analysis
            }
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calcula tasa de aciertos de cache."""
        # Implementación simplificada
        return 0.0  # En implementación real trackearíamos hits/misses
    
    def get_optimal_scan_range(self, base_ip: str) -> Optional[ScanRange]:
        """Obtiene rango de escaneo óptimo basado en análisis."""
        with self.analysis_lock:
            return self.network_analysis.get_optimal_scan_range(base_ip)
    
    # === Cleanup ===
    
    def cleanup(self):
        """Limpia recursos del servicio."""
        self.logger.info("Cleaning up scan service...")
        
        # Detener servicio
        self.stop()
        
        # Limpiar escaneos activos
        for scan in self.active_scans.values():
            try:
                scan.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up scan: {e}")
        
        self.active_scans.clear()
        self.scan_queue.clear()
        
        self.logger.info("Scan service cleanup completed")
    
    def __del__(self):
        """Destructor para cleanup automático."""
        try:
            self.cleanup()
        except Exception:
            pass  # Evitar errores en destructor


# Función global para obtener instancia del servicio
_scan_service_instance: Optional[ScanService] = None


def get_scan_service(config: Optional[ScanServiceConfig] = None) -> ScanService:
    """
    Obtiene la instancia global del ScanService.
    
    Args:
        config: Configuración opcional
        
    Returns:
        Instancia del ScanService
    """
    global _scan_service_instance
    
    if _scan_service_instance is None:
        _scan_service_instance = ScanService(config)
    
    return _scan_service_instance


# NO crear instancia singleton durante la importación
# Usar get_scan_service() cuando se necesite
# scan_service = get_scan_service() 