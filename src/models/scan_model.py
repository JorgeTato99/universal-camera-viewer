"""
Scan Model - MVP Architecture
============================

Modelo que representa y gestiona el proceso de escaneo y descubrimiento
de cámaras IP en la red. Encapsula la lógica de scanning de puertos,
detección de protocolos y construcción de resultados de descubrimiento.

Responsabilidades:
- Configurar y gestionar parámetros de escaneo
- Coordinar escaneo de múltiples IPs y puertos
- Detectar protocolos disponibles por IP
- Consolidar y filtrar resultados de descubrimiento
- Proporcionar métricas en tiempo real del progreso
- Gestionar timeouts y reintentos
"""

import asyncio
import ipaddress
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Callable

from .camera_model import ProtocolType


class ScanStatus(Enum):
    """Estados del proceso de escaneo."""
    IDLE = "idle"
    PREPARING = "preparing"
    SCANNING = "scanning"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class ScanMethod(Enum):
    """Métodos de escaneo disponibles."""
    PING_SWEEP = "ping_sweep"
    PORT_SCAN = "port_scan"
    PROTOCOL_DETECTION = "protocol_detection"
    ONVIF_DISCOVERY = "onvif_discovery"
    UPNP_DISCOVERY = "upnp_discovery"


@dataclass
class ScanConfig:
    """Configuración de escaneo de red."""
    network_ranges: List[str] = field(default_factory=lambda: ["192.168.1.0/24"])
    ports: List[int] = field(default_factory=lambda: [80, 8080, 554, 8554])
    timeout: float = 5.0
    max_threads: int = 50
    include_onvif: bool = True
    include_rtsp: bool = True
    include_http: bool = True
    include_amcrest: bool = True
    test_authentication: bool = True
    auto_detect_protocols: bool = True
    
    def __post_init__(self):
        """Validación post-inicialización."""
        if self.timeout <= 0:
            raise ValueError("Timeout debe ser mayor que 0")
        if self.max_threads <= 0:
            raise ValueError("max_threads debe ser mayor que 0")
        if not self.network_ranges:
            raise ValueError("Debe especificar al menos un rango de red")
        if not self.ports:
            raise ValueError("Debe especificar al menos un puerto")


@dataclass
class ScanRange:
    """Configuración de rango de escaneo."""
    start_ip: str
    end_ip: str
    ports: List[int]
    protocols: List[ProtocolType] = field(default_factory=list)
    timeout: float = 5.0
    
    def __post_init__(self):
        """Validación post-inicialización."""
        # Validar IPs
        try:
            start = ipaddress.ip_address(self.start_ip)
            end = ipaddress.ip_address(self.end_ip)
            if start > end:
                raise ValueError("start_ip debe ser menor o igual que end_ip")
        except ipaddress.AddressValueError as e:
            raise ValueError(f"IP inválida: {e}")
    
    @property
    def ip_count(self) -> int:
        """Número total de IPs en el rango."""
        start = int(ipaddress.ip_address(self.start_ip))
        end = int(ipaddress.ip_address(self.end_ip))
        return end - start + 1
    
    @property
    def total_combinations(self) -> int:
        """Total de combinaciones IP:Puerto a escanear."""
        return self.ip_count * len(self.ports)
    
    def get_ip_list(self) -> List[str]:
        """Genera lista de IPs en el rango."""
        start = int(ipaddress.ip_address(self.start_ip))
        end = int(ipaddress.ip_address(self.end_ip))
        return [str(ipaddress.ip_address(ip)) for ip in range(start, end + 1)]


@dataclass
class ProtocolDetectionResult:
    """Resultado de detección de protocolo en una IP:Puerto."""
    ip: str
    port: int
    protocol: ProtocolType
    detected: bool
    response_time_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    @property
    def is_successful(self) -> bool:
        """Indica si la detección fue exitosa."""
        return self.detected and self.error_message is None


@dataclass 
class ScanResult:
    """Resultado de escaneo de una IP específica."""
    ip: str
    hostname: Optional[str] = None
    is_alive: bool = False
    open_ports: List[int] = field(default_factory=list)
    detected_protocols: List[ProtocolDetectionResult] = field(default_factory=list)
    scan_duration_ms: float = 0.0
    scan_timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def has_camera_protocols(self) -> bool:
        """Indica si se detectaron protocolos de cámara."""
        return any(result.detected for result in self.detected_protocols)
    
    @property
    def camera_protocols(self) -> List[ProtocolType]:
        """Lista de protocolos de cámara detectados."""
        return [result.protocol for result in self.detected_protocols if result.detected]
    
    @property
    def best_protocol(self) -> Optional[ProtocolType]:
        """Mejor protocolo detectado (por prioridad)."""
        if not self.has_camera_protocols:
            return None
        
        # Prioridad: ONVIF > RTSP > HTTP > AMCREST > GENERIC
        priority_order = [
            ProtocolType.ONVIF,
            ProtocolType.RTSP, 
            ProtocolType.HTTP,
            ProtocolType.AMCREST,
            ProtocolType.GENERIC
        ]
        
        for protocol in priority_order:
            if protocol in self.camera_protocols:
                return protocol
        
        return self.camera_protocols[0] if self.camera_protocols else None


@dataclass
class ScanProgress:
    """Información de progreso del escaneo."""
    total_ips: int = 0
    scanned_ips: int = 0
    total_ports: int = 0
    scanned_ports: int = 0
    cameras_found: int = 0
    current_ip: Optional[str] = None
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    
    @property
    def ip_progress_percentage(self) -> float:
        """Porcentaje de progreso por IPs."""
        if self.total_ips == 0:
            return 0.0
        return (self.scanned_ips / self.total_ips) * 100
    
    @property
    def port_progress_percentage(self) -> float:
        """Porcentaje de progreso por puertos."""
        if self.total_ports == 0:
            return 0.0
        return (self.scanned_ports / self.total_ports) * 100
    
    @property
    def overall_progress_percentage(self) -> float:
        """Porcentaje de progreso general."""
        total_combinations = self.total_ips * len(getattr(self, 'ports', [80, 554, 8080]))
        if total_combinations == 0:
            return 0.0
        scanned_combinations = (self.scanned_ips - 1) * len(getattr(self, 'ports', [80, 554, 8080])) + self.scanned_ports
        return max(0, (scanned_combinations / total_combinations) * 100)


class ScanModel:
    """
    Modelo de escaneo para arquitectura MVP.
    
    Gestiona el proceso completo de descubrimiento de cámaras IP en la red,
    incluyendo ping sweep, port scanning, y detección de protocolos.
    """
    
    def __init__(self, 
                 scan_id: str,
                 scan_range: ScanRange,
                 methods: List[ScanMethod] = None,
                 max_concurrent: int = 50,
                 timeout: float = 5.0,
                 include_offline: bool = False):
        """
        Inicializa el modelo de escaneo.
        
        Args:
            scan_id: ID único del escaneo
            scan_range: Configuración de rango de escaneo
            methods: Métodos de escaneo a utilizar
            max_concurrent: Máximo de tareas concurrentes
            timeout: Timeout por operación
            include_offline: Incluir IPs offline en resultados
        """
        self.logger = logging.getLogger(f"{__name__}.{scan_id}")
        
        # Configuración básica
        self.scan_id = scan_id
        self.scan_range = scan_range
        self.methods = methods or [ScanMethod.PING_SWEEP, ScanMethod.PORT_SCAN, ScanMethod.PROTOCOL_DETECTION]
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.include_offline = include_offline
        
        # Estado del escaneo
        self._status = ScanStatus.IDLE
        self._status_lock = threading.Lock()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Resultados y progreso
        self.results: Dict[str, ScanResult] = {}
        self.progress = ScanProgress()
        self.errors: List[Dict[str, Any]] = []
        
        # Threading y control
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent, thread_name_prefix=f"scan_{scan_id}")
        self._cancel_event = threading.Event()
        self._progress_callbacks: List[Callable[[ScanProgress], None]] = []
        
        # Configuración de protocolos por puerto
        self.port_protocol_mapping = {
            80: [ProtocolType.HTTP, ProtocolType.ONVIF],
            554: [ProtocolType.RTSP],
            8080: [ProtocolType.HTTP],
            37777: [ProtocolType.AMCREST],
            8000: [ProtocolType.HTTP],
            443: [ProtocolType.HTTP],
        }
        
        self.logger.info(f"Scan model initialized: {scan_id} for range {scan_range.start_ip}-{scan_range.end_ip}")
    
    @property
    def status(self) -> ScanStatus:
        """Estado actual del escaneo (thread-safe)."""
        with self._status_lock:
            return self._status
    
    @status.setter
    def status(self, new_status: ScanStatus):
        """Establece nuevo estado del escaneo (thread-safe)."""
        with self._status_lock:
            old_status = self._status
            self._status = new_status
            
            if old_status != new_status:
                self.logger.info(f"Scan status changed: {old_status.value} → {new_status.value}")
    
    @property
    def is_running(self) -> bool:
        """Indica si el escaneo está en progreso."""
        return self.status in [ScanStatus.PREPARING, ScanStatus.SCANNING, ScanStatus.PROCESSING]
    
    @property
    def is_completed(self) -> bool:
        """Indica si el escaneo terminó."""
        return self.status in [ScanStatus.COMPLETED, ScanStatus.CANCELLED, ScanStatus.ERROR]
    
    @property
    def duration_seconds(self) -> float:
        """Duración del escaneo en segundos."""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    # === Configuración de Callbacks ===
    
    def add_progress_callback(self, callback: Callable[[ScanProgress], None]):
        """Añade callback para actualizaciones de progreso."""
        self._progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[ScanProgress], None]):
        """Remueve callback de progreso."""
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)
    
    def _notify_progress(self):
        """Notifica progreso a todos los callbacks."""
        for callback in self._progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")
    
    # === Gestión de Escaneo ===
    
    async def start_scan_async(self) -> bool:
        """
        Inicia el escaneo de forma asíncrona.
        
        Returns:
            True si el escaneo se completó exitosamente
        """
        if self.is_running:
            self.logger.warning("Scan is already running")
            return False
        
        self.logger.info(f"Starting scan with methods: {[m.value for m in self.methods]}")
        
        # Inicializar estado
        self.status = ScanStatus.PREPARING
        self.start_time = datetime.now()
        self._cancel_event.clear()
        self.results.clear()
        self.errors.clear()
        
        # Configurar progreso
        ip_list = self.scan_range.get_ip_list()
        self.progress = ScanProgress(
            total_ips=len(ip_list),
            total_ports=len(self.scan_range.ports)
        )
        
        try:
            # Ejecutar métodos de escaneo en orden
            for method in self.methods:
                if self._cancel_event.is_set():
                    self.status = ScanStatus.CANCELLED
                    return False
                
                self.logger.info(f"Executing scan method: {method.value}")
                success = await self._execute_scan_method(method, ip_list)
                
                if not success:
                    self.logger.error(f"Scan method {method.value} failed")
                    # Continuar con otros métodos
            
            # Procesar resultados finales
            self.status = ScanStatus.PROCESSING
            self._process_final_results()
            
            self.status = ScanStatus.COMPLETED
            self.end_time = datetime.now()
            
            self.logger.info(f"Scan completed successfully. Found {len([r for r in self.results.values() if r.has_camera_protocols])} cameras")
            return True
            
        except Exception as e:
            self.logger.error(f"Scan failed with exception: {e}")
            self.status = ScanStatus.ERROR
            self.end_time = datetime.now()
            self.errors.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'method': 'general'
            })
            return False
    
    def start_scan(self) -> bool:
        """
        Inicia el escaneo de forma síncrona.
        
        Returns:
            True si el escaneo se completó exitosamente
        """
        try:
            future = self.executor.submit(self._run_async_scan)
            return future.result()
        except Exception as e:
            self.logger.error(f"Synchronous scan failed: {e}")
            self.status = ScanStatus.ERROR
            return False
    
    def _run_async_scan(self) -> bool:
        """Helper para ejecutar escaneo asíncrono."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.start_scan_async())
        finally:
            loop.close()
    
    async def _execute_scan_method(self, method: ScanMethod, ip_list: List[str]) -> bool:
        """Ejecuta un método de escaneo específico."""
        try:
            if method == ScanMethod.PING_SWEEP:
                return await self._ping_sweep(ip_list)
            elif method == ScanMethod.PORT_SCAN:
                return await self._port_scan(ip_list)
            elif method == ScanMethod.PROTOCOL_DETECTION:
                return await self._protocol_detection(ip_list)
            elif method == ScanMethod.ONVIF_DISCOVERY:
                return await self._onvif_discovery(ip_list)
            elif method == ScanMethod.UPNP_DISCOVERY:
                return await self._upnp_discovery(ip_list)
            else:
                self.logger.warning(f"Unknown scan method: {method}")
                return False
        except Exception as e:
            self.logger.error(f"Error executing {method.value}: {e}")
            return False
    
    # === Métodos de Escaneo Específicos ===
    
    async def _ping_sweep(self, ip_list: List[str]) -> bool:
        """Ejecuta ping sweep para identificar hosts activos."""
        self.logger.debug(f"Starting ping sweep for {len(ip_list)} IPs")
        self.status = ScanStatus.SCANNING
        
        tasks = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        for ip in ip_list:
            if self._cancel_event.is_set():
                break
            task = self._ping_host(semaphore, ip)
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        alive_count = len([r for r in self.results.values() if r.is_alive])
        self.logger.info(f"Ping sweep completed. {alive_count}/{len(ip_list)} hosts alive")
        return True
    
    async def _ping_host(self, semaphore: asyncio.Semaphore, ip: str):
        """Ejecuta ping a un host específico."""
        async with semaphore:
            if self._cancel_event.is_set():
                return
            
            start_time = time.time()
            is_alive = False
            
            try:
                # Simular ping (en implementación real usaría subprocess o ping3)
                await asyncio.sleep(0.1)  # Simular delay de ping
                import random
                is_alive = random.random() > 0.7  # 30% hosts activos para demo
                
            except Exception as e:
                self.logger.error(f"Ping failed for {ip}: {e}")
            
            # Actualizar resultado
            if ip not in self.results:
                self.results[ip] = ScanResult(ip=ip)
            
            self.results[ip].is_alive = is_alive
            self.results[ip].scan_duration_ms = (time.time() - start_time) * 1000
            
            # Actualizar progreso
            self.progress.scanned_ips += 1
            self.progress.current_ip = ip
            self.progress.elapsed_time = self.duration_seconds
            self._notify_progress()
    
    async def _port_scan(self, ip_list: List[str]) -> bool:
        """Ejecuta port scan en hosts activos."""
        active_ips = [ip for ip, result in self.results.items() 
                     if result.is_alive or self.include_offline]
        
        self.logger.debug(f"Starting port scan for {len(active_ips)} IPs on {len(self.scan_range.ports)} ports")
        
        tasks = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        for ip in active_ips:
            if self._cancel_event.is_set():
                break
            for port in self.scan_range.ports:
                task = self._scan_port(semaphore, ip, port)
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        total_open_ports = sum(len(result.open_ports) for result in self.results.values())
        self.logger.info(f"Port scan completed. {total_open_ports} open ports found")
        return True
    
    async def _scan_port(self, semaphore: asyncio.Semaphore, ip: str, port: int):
        """Escanea un puerto específico."""
        async with semaphore:
            if self._cancel_event.is_set():
                return
            
            try:
                # Simular port scan (en implementación real usaría socket connection)
                await asyncio.sleep(0.05)  # Simular delay de conexión
                import random
                is_open = random.random() > 0.8  # 20% puertos abiertos para demo
                
                if is_open:
                    if ip not in self.results:
                        self.results[ip] = ScanResult(ip=ip)
                    
                    if port not in self.results[ip].open_ports:
                        self.results[ip].open_ports.append(port)
                
                # Actualizar progreso
                self.progress.scanned_ports += 1
                self.progress.current_ip = ip
                self._notify_progress()
                
            except Exception as e:
                self.logger.error(f"Port scan failed for {ip}:{port}: {e}")
    
    async def _protocol_detection(self, ip_list: List[str]) -> bool:
        """Ejecuta detección de protocolos en puertos abiertos."""
        ips_with_ports = [(ip, result) for ip, result in self.results.items() 
                         if result.open_ports]
        
        self.logger.debug(f"Starting protocol detection for {len(ips_with_ports)} IPs")
        
        tasks = []
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        for ip, result in ips_with_ports:
            if self._cancel_event.is_set():
                break
            for port in result.open_ports:
                protocols = self.port_protocol_mapping.get(port, [ProtocolType.GENERIC])
                for protocol in protocols:
                    task = self._detect_protocol(semaphore, ip, port, protocol)
                    tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Actualizar contador de cámaras encontradas
        self.progress.cameras_found = len([r for r in self.results.values() if r.has_camera_protocols])
        self._notify_progress()
        
        self.logger.info(f"Protocol detection completed. {self.progress.cameras_found} cameras detected")
        return True
    
    async def _detect_protocol(self, semaphore: asyncio.Semaphore, ip: str, port: int, protocol: ProtocolType):
        """Detecta un protocolo específico en IP:Puerto."""
        async with semaphore:
            if self._cancel_event.is_set():
                return
            
            start_time = time.time()
            detected = False
            error_message = None
            details = {}
            
            try:
                # Simular detección de protocolo (en implementación real haría requests específicos)
                await asyncio.sleep(0.2)  # Simular delay de detección
                import random
                
                # Probabilidades diferentes por protocolo
                detection_rates = {
                    ProtocolType.ONVIF: 0.3,
                    ProtocolType.RTSP: 0.25,
                    ProtocolType.HTTP: 0.4,
                    ProtocolType.AMCREST: 0.15,
                    ProtocolType.GENERIC: 0.2
                }
                
                detected = random.random() < detection_rates.get(protocol, 0.2)
                
                if detected:
                    details = {
                        'device_info': f'Simulated {protocol.value} camera',
                        'capabilities': ['streaming', 'control']
                    }
                
            except Exception as e:
                error_message = str(e)
                self.logger.error(f"Protocol detection failed for {protocol.value} on {ip}:{port}: {e}")
            
            # Crear resultado de detección
            detection_result = ProtocolDetectionResult(
                ip=ip,
                port=port,
                protocol=protocol,
                detected=detected,
                response_time_ms=(time.time() - start_time) * 1000,
                details=details,
                error_message=error_message
            )
            
            # Añadir al resultado del IP
            if ip not in self.results:
                self.results[ip] = ScanResult(ip=ip)
            
            self.results[ip].detected_protocols.append(detection_result)
    
    async def _onvif_discovery(self, ip_list: List[str]) -> bool:
        """Ejecuta descubrimiento ONVIF usando WS-Discovery."""
        self.logger.debug("Starting ONVIF discovery")
        
        # Simular descubrimiento ONVIF
        await asyncio.sleep(2.0)  # Simular delay de discovery
        
        # En implementación real usaría onvif-zeep o wsdiscovery
        import random
        discovered_count = random.randint(0, 3)
        
        for i in range(discovered_count):
            ip = random.choice(ip_list)
            if ip not in self.results:
                self.results[ip] = ScanResult(ip=ip)
            
            # Añadir resultado ONVIF
            onvif_result = ProtocolDetectionResult(
                ip=ip,
                port=80,
                protocol=ProtocolType.ONVIF,
                detected=True,
                response_time_ms=500.0,
                details={'discovery_method': 'ws-discovery', 'device_type': 'NetworkVideoTransmitter'}
            )
            self.results[ip].detected_protocols.append(onvif_result)
            self.results[ip].open_ports.append(80)
            self.results[ip].is_alive = True
        
        self.logger.info(f"ONVIF discovery completed. {discovered_count} devices found")
        return True
    
    async def _upnp_discovery(self, ip_list: List[str]) -> bool:
        """Ejecuta descubrimiento UPnP."""
        self.logger.debug("Starting UPnP discovery")
        
        # Simular descubrimiento UPnP
        await asyncio.sleep(1.5)  # Simular delay de discovery
        
        # En implementación real usaría upnpclient o similar
        import random
        discovered_count = random.randint(0, 2)
        
        for i in range(discovered_count):
            ip = random.choice(ip_list)
            if ip not in self.results:
                self.results[ip] = ScanResult(ip=ip)
            
            # Añadir resultado genérico 
            upnp_result = ProtocolDetectionResult(
                ip=ip,
                port=8080,
                protocol=ProtocolType.GENERIC,
                detected=True,
                response_time_ms=300.0,
                details={'discovery_method': 'upnp', 'device_type': 'MediaServer'}
            )
            self.results[ip].detected_protocols.append(upnp_result)
            self.results[ip].open_ports.append(8080)
            self.results[ip].is_alive = True
        
        self.logger.info(f"UPnP discovery completed. {discovered_count} devices found")
        return True
    
    def _process_final_results(self):
        """Procesa y consolida resultados finales."""
        self.logger.debug("Processing final results")
        
        # Filtrar resultados según configuración
        if not self.include_offline:
            self.results = {ip: result for ip, result in self.results.items() 
                          if result.is_alive or result.has_camera_protocols}
        
        # Ordenar protocolos por prioridad en cada resultado
        for result in self.results.values():
            result.detected_protocols.sort(
                key=lambda x: (x.detected, -x.response_time_ms), 
                reverse=True
            )
        
        # Actualizar progreso final
        self.progress.cameras_found = len([r for r in self.results.values() if r.has_camera_protocols])
        self.progress.elapsed_time = self.duration_seconds
        self._notify_progress()
    
    # === Control de Escaneo ===
    
    def cancel_scan(self):
        """Cancela el escaneo en curso."""
        if not self.is_running:
            self.logger.warning("No scan is currently running")
            return
        
        self.logger.info("Cancelling scan...")
        self._cancel_event.set()
        self.status = ScanStatus.CANCELLED
        self.end_time = datetime.now()
    
    # === Resultados y Estadísticas ===
    
    def get_scan_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del escaneo."""
        camera_results = [r for r in self.results.values() if r.has_camera_protocols]
        
        return {
            'scan_id': self.scan_id,
            'status': self.status.value,
            'duration_seconds': self.duration_seconds,
            'range': {
                'start_ip': self.scan_range.start_ip,
                'end_ip': self.scan_range.end_ip,
                'ports': self.scan_range.ports,
                'total_ips': self.scan_range.ip_count,
                'total_combinations': self.scan_range.total_combinations
            },
            'progress': {
                'ip_progress': self.progress.ip_progress_percentage,
                'overall_progress': self.progress.overall_progress_percentage,
                'cameras_found': self.progress.cameras_found
            },
            'results': {
                'total_ips_scanned': len(self.results),
                'alive_ips': len([r for r in self.results.values() if r.is_alive]),
                'cameras_found': len(camera_results),
                'total_open_ports': sum(len(r.open_ports) for r in self.results.values()),
                'protocols_detected': len([p for r in self.results.values() for p in r.detected_protocols if p.detected])
            },
            'configuration': {
                'methods': [m.value for m in self.methods],
                'max_concurrent': self.max_concurrent,
                'timeout': self.timeout,
                'include_offline': self.include_offline
            },
            'errors': len(self.errors)
        }
    
    def get_camera_results(self) -> List[Dict[str, Any]]:
        """Obtiene resultados de cámaras detectadas."""
        camera_results = []
        
        for ip, result in self.results.items():
            if result.has_camera_protocols:
                camera_info = {
                    'ip': ip,
                    'hostname': result.hostname,
                    'is_alive': result.is_alive,
                    'open_ports': result.open_ports,
                    'best_protocol': result.best_protocol.value if result.best_protocol else None,
                    'all_protocols': [p.value for p in result.camera_protocols],
                    'scan_duration_ms': result.scan_duration_ms,
                    'detection_details': [
                        {
                            'protocol': det.protocol.value,
                            'port': det.port,
                            'detected': det.detected,
                            'response_time_ms': det.response_time_ms,
                            'details': det.details
                        }
                        for det in result.detected_protocols if det.detected
                    ]
                }
                camera_results.append(camera_info)
        
        return camera_results
    
    def get_all_results(self) -> List[Dict[str, Any]]:
        """Obtiene todos los resultados de escaneo."""
        all_results = []
        
        for ip, result in self.results.items():
            result_info = {
                'ip': ip,
                'hostname': result.hostname,
                'is_alive': result.is_alive,
                'open_ports': result.open_ports,
                'has_camera_protocols': result.has_camera_protocols,
                'camera_protocols': [p.value for p in result.camera_protocols],
                'scan_duration_ms': result.scan_duration_ms,
                'scan_timestamp': result.scan_timestamp.isoformat(),
                'detection_results': [
                    {
                        'protocol': det.protocol.value,
                        'port': det.port,
                        'detected': det.detected,
                        'response_time_ms': det.response_time_ms,
                        'error_message': det.error_message,
                        'details': det.details
                    }
                    for det in result.detected_protocols
                ]
            }
            all_results.append(result_info)
        
        return all_results
    
    # === Cleanup ===
    
    def cleanup(self):
        """Limpia recursos del modelo."""
        self.logger.info("Cleaning up scan model...")
        
        # Cancelar si está corriendo
        if self.is_running:
            self.cancel_scan()
        
        # Cerrar thread pool
        self.executor.shutdown(wait=True)
        
        self.logger.info("Scan model cleanup completed")
    
    def __str__(self) -> str:
        """Representación string del modelo."""
        return f"ScanModel({self.scan_id}, {self.status.value}, {len(self.results)} results)"
    
    def __repr__(self) -> str:
        """Representación detallada del modelo."""
        return f"ScanModel(scan_id='{self.scan_id}', range='{self.scan_range.start_ip}-{self.scan_range.end_ip}', status='{self.status.value}')" 