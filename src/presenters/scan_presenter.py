#!/usr/bin/env python3
"""
ScanPresenter - Presenter para operaciones de escaneo de red y descubrimiento de cámaras.

Coordina la lógica de negocio para:
- Escaneo de red para descubrir cámaras
- Detección de protocolos y marcas
- Gestión de resultados de escaneo
- Cache inteligente de descubrimientos
- Estadísticas de escaneo
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
from ipaddress import IPv4Network, IPv4Address

from .base_presenter import BasePresenter, PresenterState
from ..models import ScanModel, CameraModel, ScanConfig, ScanResult
from ..services import get_scan_service, get_data_service, get_config_service


class ScanPresenter(BasePresenter):
    """
    Presenter para operaciones de escaneo de red y descubrimiento de cámaras.
    
    Coordina todas las operaciones de escaneo:
    - Descubrimiento automático de cámaras en red
    - Detección de protocolos soportados
    - Identificación de marcas y modelos
    - Gestión de cache de resultados
    - Estadísticas y métricas de escaneo
    """
    
    def __init__(self):
        """Inicializa el presenter de escaneo."""
        super().__init__("ScanPresenter")
        
        # Servicios
        self._scan_service = get_scan_service()
        self._data_service = get_data_service()
        self._config_service = get_config_service()
        
        # Estado de escaneo
        self._current_scan: Optional[ScanModel] = None
        self._scan_results: List[ScanResult] = []
        self._discovered_cameras: List[CameraModel] = []
        
        # Configuración de escaneo
        self._scan_config: Optional[ScanConfig] = None
        self._auto_scan_enabled = False
        self._auto_scan_interval = 300  # 5 minutos
        
        # Estadísticas
        self._total_scans = 0
        self._total_cameras_found = 0
        self._last_scan_time: Optional[datetime] = None
        self._average_scan_duration = 0.0
        
        # Callbacks para la view
        self._on_scan_started: Optional[Callable[[], None]] = None
        self._on_scan_progress: Optional[Callable[[int, int, str], None]] = None
        self._on_scan_completed: Optional[Callable[[List[CameraModel]], None]] = None
        self._on_camera_discovered: Optional[Callable[[CameraModel], None]] = None
        self._on_scan_error: Optional[Callable[[str], None]] = None
        
    async def initialize_async(self) -> bool:
        """
        Inicialización asíncrona del presenter.
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            self.logger.info("🔍 Inicializando ScanPresenter")
            
            # Cargar configuración de escaneo
            await self._load_scan_configuration()
            
            # Configurar métricas iniciales
            await self._setup_metrics()
            
            # Cargar resultados de escaneos anteriores
            await self._load_cached_results()
            
            # Inicializar auto-scan si está habilitado
            if self._auto_scan_enabled:
                await self._setup_auto_scan()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando ScanPresenter: {str(e)}")
            await self.set_error(f"Error de inicialización: {str(e)}")
            return False
    
    async def _load_scan_configuration(self) -> None:
        """Carga la configuración de escaneo desde ConfigService."""
        try:
            # Configuración de red
            network_range = await self._config_service.get_config_value(
                "scan.network_range", "192.168.1.0/24"
            )
            
            # Puertos a escanear
            ports_config = await self._config_service.get_config_value(
                "scan.ports", [80, 8080, 554, 8554, 443]
            )
            
            # Timeout de conexión
            timeout = await self._config_service.get_config_value(
                "scan.timeout", 5.0
            )
            
            # Threads concurrentes
            max_threads = await self._config_service.get_config_value(
                "scan.max_threads", 50
            )
            
            # Auto-scan
            self._auto_scan_enabled = await self._config_service.get_config_value(
                "scan.auto_scan_enabled", False
            )
            
            self._auto_scan_interval = await self._config_service.get_config_value(
                "scan.auto_scan_interval", 300
            )
            
            # Crear configuración de escaneo
            self._scan_config = ScanConfig(
                network_ranges=[network_range],
                ports=ports_config,
                timeout=timeout,
                max_threads=max_threads,
                include_onvif=True,
                include_rtsp=True,
                include_http=True,
                test_authentication=True
            )
            
            self.logger.info("📋 Configuración de escaneo cargada")
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando configuración de escaneo: {str(e)}")
            # Usar configuración por defecto
            self._scan_config = ScanConfig(
                network_ranges=["192.168.1.0/24"],
                ports=[80, 8080, 554, 8554],
                timeout=5.0,
                max_threads=50
            )
    
    async def _setup_metrics(self) -> None:
        """Configura las métricas de monitoreo del escaneo."""
        self.add_metric("total_scans", 0)
        self.add_metric("total_cameras_found", 0)
        self.add_metric("last_scan_duration", 0.0)
        self.add_metric("average_scan_duration", 0.0)
        self.add_metric("cached_results_count", 0)
        self.add_metric("auto_scan_enabled", self._auto_scan_enabled)
        self.add_metric("current_scan_progress", 0)
        self.add_metric("last_scan_time", None)
    
    async def _load_cached_results(self) -> None:
        """Carga resultados de escaneos anteriores desde cache."""
        try:
            # Cargar resultados recientes desde DataService
            # Esta funcionalidad se expandirá cuando se integre completamente DataService
            self.update_metric("cached_results_count", len(self._scan_results))
            self.logger.info("💾 Resultados de cache cargados")
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando cache: {str(e)}")
    
    async def _setup_auto_scan(self) -> None:
        """Configura el escaneo automático si está habilitado."""
        if self._auto_scan_enabled:
            await self.start_background_task(
                "auto_scan",
                self._auto_scan_task,
                "Escaneo automático de red"
            )
            self.logger.info(f"🔄 Auto-scan habilitado (cada {self._auto_scan_interval}s)")
    
    async def _auto_scan_task(self) -> None:
        """Tarea de fondo para escaneo automático."""
        while self._auto_scan_enabled and not self._shutdown:
            try:
                await asyncio.sleep(self._auto_scan_interval)
                
                if not self._shutdown and self._auto_scan_enabled:
                    self.logger.info("🔄 Iniciando escaneo automático")
                    await self.start_network_scan()
                    
            except Exception as e:
                if not self._shutdown:
                    self.logger.error(f"❌ Error en escaneo automático: {str(e)}")
                break
    
    # === Operaciones de Escaneo ===
    
    async def start_network_scan(self, config: Optional[ScanConfig] = None) -> bool:
        """
        Inicia un escaneo de red para descubrir cámaras.
        
        Args:
            config: Configuración específica de escaneo (opcional)
            
        Returns:
            True si el escaneo se inició correctamente
        """
        if self._current_scan and self._current_scan.is_running:
            self.logger.warning("⚠️ Ya hay un escaneo en progreso")
            return False
        
        await self.set_busy("Iniciando escaneo de red...")
        
        try:
            # Usar configuración proporcionada o la por defecto
            scan_config = config or self._scan_config
            
            if not scan_config:
                raise ValueError("No hay configuración de escaneo disponible")
            
            # Crear nuevo modelo de escaneo
            self._current_scan = ScanModel(
                scan_id=f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                config=scan_config,
                start_time=datetime.now()
            )
            
            # Limpiar resultados anteriores
            self._scan_results.clear()
            self._discovered_cameras.clear()
            
            # Notificar inicio de escaneo
            if self._on_scan_started:
                await self.execute_safe(self._on_scan_started)
            
            # Iniciar escaneo a través del servicio
            await self.start_background_task(
                "network_scan",
                self._execute_network_scan,
                "Escaneo de red en progreso"
            )
            
            self.logger.info(f"🔍 Escaneo de red iniciado: {self._current_scan.scan_id}")
            return True
            
        except Exception as e:
            error_msg = f"Error iniciando escaneo: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            if self._on_scan_error:
                await self.execute_safe(self._on_scan_error, error_msg)
            
            await self.set_error(error_msg)
            return False
    
    async def _execute_network_scan(self) -> None:
        """Ejecuta el escaneo de red en tarea de fondo."""
        try:
            if not self._current_scan:
                return
            
            scan_start_time = datetime.now()
            
            # Ejecutar escaneo a través del servicio
            results = await self._scan_service.scan_network(
                self._current_scan.config,
                progress_callback=self._on_scan_progress_internal
            )
            
            # Procesar resultados
            self._scan_results = results
            self._discovered_cameras = self._extract_cameras_from_results(results)
            
            # Actualizar modelo de escaneo
            self._current_scan.results = results
            self._current_scan.end_time = datetime.now()
            self._current_scan.is_running = False
            self._current_scan.cameras_found = len(self._discovered_cameras)
            
            # Actualizar estadísticas
            scan_duration = (self._current_scan.end_time - scan_start_time).total_seconds()
            self._total_scans += 1
            self._total_cameras_found += len(self._discovered_cameras)
            self._last_scan_time = self._current_scan.end_time
            
            # Calcular duración promedio
            if self._total_scans > 0:
                self._average_scan_duration = (
                    (self._average_scan_duration * (self._total_scans - 1) + scan_duration) 
                    / self._total_scans
                )
            
            # Actualizar métricas
            self.update_metric("total_scans", self._total_scans)
            self.update_metric("total_cameras_found", self._total_cameras_found)
            self.update_metric("last_scan_duration", round(scan_duration, 2))
            self.update_metric("average_scan_duration", round(self._average_scan_duration, 2))
            self.update_metric("last_scan_time", self._last_scan_time.isoformat())
            self.update_metric("current_scan_progress", 100)
            
            # Guardar resultados en DataService
            await self._save_scan_results()
            
            # Notificar completación
            if self._on_scan_completed:
                await self.execute_safe(self._on_scan_completed, self._discovered_cameras)
            
            await self.set_ready(f"Escaneo completado - {len(self._discovered_cameras)} cámaras encontradas")
            self.logger.info(f"✅ Escaneo completado: {len(self._discovered_cameras)} cámaras en {scan_duration:.2f}s")
            
        except Exception as e:
            error_msg = f"Error ejecutando escaneo: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            if self._current_scan:
                self._current_scan.is_running = False
                self._current_scan.error_message = error_msg
            
            if self._on_scan_error:
                await self.execute_safe(self._on_scan_error, error_msg)
            
            await self.set_error(error_msg)
    
    async def _on_scan_progress_internal(self, current: int, total: int, message: str) -> None:
        """Maneja el progreso interno del escaneo."""
        try:
            progress_percent = int((current / total) * 100) if total > 0 else 0
            self.update_metric("current_scan_progress", progress_percent)
            
            if self._on_scan_progress:
                await self.execute_safe(self._on_scan_progress, current, total, message)
                
        except Exception as e:
            self.logger.error(f"❌ Error procesando progreso: {str(e)}")
    
    def _extract_cameras_from_results(self, results: List[ScanResult]) -> List[CameraModel]:
        """
        Extrae modelos de cámara desde los resultados de escaneo.
        
        Args:
            results: Resultados del escaneo
            
        Returns:
            Lista de modelos de cámara descubiertas
        """
        cameras = []
        
        for result in results:
            if result.device_info and result.device_info.get("is_camera", False):
                try:
                    camera = CameraModel(
                        name=result.device_info.get("name", f"Camera_{result.ip}"),
                        brand=result.device_info.get("brand", "Unknown"),
                        model=result.device_info.get("model", "Unknown"),
                        ip_address=result.ip,
                        protocols=result.protocols
                    )
                    cameras.append(camera)
                    
                    # Notificar descubrimiento individual
                    if self._on_camera_discovered:
                        asyncio.create_task(
                            self.execute_safe(self._on_camera_discovered, camera)
                        )
                        
                except Exception as e:
                    self.logger.error(f"❌ Error creando modelo de cámara: {str(e)}")
        
        return cameras
    
    async def _save_scan_results(self) -> None:
        """Guarda los resultados del escaneo en DataService."""
        try:
            if self._current_scan and self._discovered_cameras:
                # Guardar cada cámara descubierta
                for camera in self._discovered_cameras:
                    await self._data_service.save_camera_data(camera)
                
                # Guardar datos del escaneo
                # Esta funcionalidad se expandirá cuando se integre completamente DataService
                
                self.logger.info(f"💾 Resultados guardados: {len(self._discovered_cameras)} cámaras")
                
        except Exception as e:
            self.logger.error(f"❌ Error guardando resultados: {str(e)}")
    
    # === Operaciones de Control ===
    
    async def stop_current_scan(self) -> bool:
        """
        Detiene el escaneo actual si está en progreso.
        
        Returns:
            True si se detuvo exitosamente
        """
        if not self._current_scan or not self._current_scan.is_running:
            self.logger.warning("⚠️ No hay escaneo en progreso para detener")
            return True
        
        try:
            await self.set_busy("Deteniendo escaneo...")
            
            # Detener tarea de escaneo
            await self.stop_background_task("network_scan")
            
            # Actualizar estado del escaneo
            if self._current_scan:
                self._current_scan.is_running = False
                self._current_scan.end_time = datetime.now()
                self._current_scan.error_message = "Escaneo detenido por usuario"
            
            await self.set_ready("Escaneo detenido")
            self.logger.info("⏹️ Escaneo detenido por usuario")
            return True
            
        except Exception as e:
            error_msg = f"Error deteniendo escaneo: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            await self.set_error(error_msg)
            return False
    
    async def toggle_auto_scan(self, enabled: bool) -> bool:
        """
        Habilita o deshabilita el escaneo automático.
        
        Args:
            enabled: True para habilitar, False para deshabilitar
            
        Returns:
            True si se cambió exitosamente
        """
        try:
            self._auto_scan_enabled = enabled
            self.update_metric("auto_scan_enabled", enabled)
            
            # Guardar configuración
            await self._config_service.set_config_value(
                "scan.auto_scan_enabled", enabled
            )
            
            if enabled:
                # Iniciar auto-scan
                await self._setup_auto_scan()
                self.logger.info("🔄 Auto-scan habilitado")
            else:
                # Detener auto-scan
                await self.stop_background_task("auto_scan")
                self.logger.info("⏹️ Auto-scan deshabilitado")
            
            return True
            
        except Exception as e:
            error_msg = f"Error configurando auto-scan: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            await self.set_error(error_msg)
            return False
    
    async def update_scan_configuration(self, config: ScanConfig) -> bool:
        """
        Actualiza la configuración de escaneo.
        
        Args:
            config: Nueva configuración de escaneo
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            self._scan_config = config
            
            # Guardar configuración en ConfigService
            await self._config_service.set_config_value(
                "scan.network_range", config.network_ranges[0] if config.network_ranges else "192.168.1.0/24"
            )
            await self._config_service.set_config_value("scan.ports", config.ports)
            await self._config_service.set_config_value("scan.timeout", config.timeout)
            await self._config_service.set_config_value("scan.max_threads", config.max_threads)
            
            self.logger.info("📋 Configuración de escaneo actualizada")
            return True
            
        except Exception as e:
            error_msg = f"Error actualizando configuración: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            await self.set_error(error_msg)
            return False
    
    # === Gestión de Estado ===
    
    def is_scanning(self) -> bool:
        """Retorna si hay un escaneo en progreso."""
        return (self._current_scan is not None and 
                self._current_scan.is_running)
    
    def get_current_scan(self) -> Optional[ScanModel]:
        """Retorna el escaneo actual."""
        return self._current_scan
    
    def get_discovered_cameras(self) -> List[CameraModel]:
        """Retorna las cámaras descubiertas en el último escaneo."""
        return self._discovered_cameras.copy()
    
    def get_scan_results(self) -> List[ScanResult]:
        """Retorna los resultados detallados del último escaneo."""
        return self._scan_results.copy()
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas de escaneo."""
        return {
            "total_scans": self._total_scans,
            "total_cameras_found": self._total_cameras_found,
            "last_scan_time": self._last_scan_time.isoformat() if self._last_scan_time else None,
            "average_scan_duration": self._average_scan_duration,
            "auto_scan_enabled": self._auto_scan_enabled,
            "auto_scan_interval": self._auto_scan_interval
        }
    
    # === Callbacks de View ===
    
    def set_scan_started_callback(self, callback: Callable[[], None]) -> None:
        """Establece callback para inicio de escaneo."""
        self._on_scan_started = callback
    
    def set_scan_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """Establece callback para progreso de escaneo."""
        self._on_scan_progress = callback
    
    def set_scan_completed_callback(self, callback: Callable[[List[CameraModel]], None]) -> None:
        """Establece callback para finalización de escaneo."""
        self._on_scan_completed = callback
    
    def set_camera_discovered_callback(self, callback: Callable[[CameraModel], None]) -> None:
        """Establece callback para descubrimiento de cámara individual."""
        self._on_camera_discovered = callback
    
    def set_scan_error_callback(self, callback: Callable[[str], None]) -> None:
        """Establece callback para errores de escaneo."""
        self._on_scan_error = callback
    
    # === Abstract Methods Implementation ===
    
    async def _initialize_presenter(self) -> None:
        """Implementación de inicialización específica del presenter."""
        # La inicialización específica se maneja en initialize_async()
        pass
    
    async def _cleanup_presenter(self) -> None:
        """Implementación de limpieza específica del presenter."""
        try:
            # Detener escaneo si está en progreso
            if self.is_scanning():
                await self.stop_current_scan()
            
            # Detener auto-scan
            self._auto_scan_enabled = False
            await self.stop_background_task("auto_scan")
            
            self.logger.info("🧹 ScanPresenter limpiado")
            
        except Exception as e:
            self.logger.error(f"❌ Error en limpieza de ScanPresenter: {str(e)}")
    
    # === Cleanup ===
    
    async def cleanup_async(self) -> None:
        """Limpieza asíncrona del presenter."""
        await self._cleanup_presenter() 