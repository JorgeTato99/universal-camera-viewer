#!/usr/bin/env python3
"""
MainPresenter - Presenter principal de la aplicación.

Coordina la lógica de negocio principal para:
- Gestión de la interfaz principal
- Coordinación entre diferentes presenters
- Gestión del estado global de la aplicación
- Control de cámaras múltiples
- Operaciones de escaneo y descubrimiento
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from presenters.base_presenter import BasePresenter, PresenterState
from presenters.camera_presenter import CameraPresenter
from presenters.scan_presenter import ScanPresenter
from presenters.config_presenter import ConfigPresenter
from models import CameraModel, ScanConfig
from services import (
    get_connection_service, 
    get_scan_service, 
    get_data_service, 
    get_config_service,
)
from services.protocol_service import ProtocolService


class MainPresenter(BasePresenter):
    """
    Presenter principal de la aplicación.
    
    Actúa como coordinador central de toda la aplicación:
    - Gestiona múltiples cámaras a través de CameraPresenters
    - Coordina operaciones de escaneo y descubrimiento
    - Maneja configuración global
    - Controla el estado general de la aplicación
    - Proporciona API unificada para la MainView
    """
    
    def __init__(self):
        """Inicializa el presenter principal."""
        super().__init__("MainPresenter")
        
        # Servicios principales
        self._connection_service = get_connection_service()
        self._scan_service = get_scan_service()
        self._data_service = get_data_service()
        self._config_service = get_config_service()
        self._protocol_service = ProtocolService()
        
        # Sub-presenters
        self._camera_presenters: Dict[str, CameraPresenter] = {}
        self._scan_presenter: Optional[ScanPresenter] = None
        self._config_presenter: Optional[ConfigPresenter] = None
        
        # Estado de la aplicación
        self._discovered_cameras: List[CameraModel] = []
        self._active_cameras: List[str] = []
        self._current_layout = 2  # columnas por defecto
        self._auto_scan_enabled = False
        
        # Callbacks para la view
        self._on_cameras_updated: Optional[Callable[[List[CameraModel]], None]] = None
        self._on_camera_status_changed: Optional[Callable[[str, str], None]] = None
        self._on_scan_progress: Optional[Callable[[int, int, str], None]] = None
        self._on_scan_completed: Optional[Callable[[List[CameraModel]], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
        
    async def _initialize_presenter(self) -> None:
        """Implementación de inicialización específica del presenter."""
        try:
            self.logger.info("Inicializando MainPresenter")
            
            # Inicializar servicios
            await self._initialize_services()
            
            # Crear sub-presenters
            await self._create_sub_presenters()
            
            # Cargar configuración inicial
            await self._load_initial_configuration()
            
            # Cargar cámaras guardadas
            await self._load_saved_cameras()
            
            # Configurar métricas
            await self._setup_metrics()
            
            self.logger.info("MainPresenter inicializado exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando MainPresenter: {str(e)}")
            raise
    
    async def _cleanup_presenter(self) -> None:
        """Implementación de limpieza específica del presenter."""
        try:
            self.logger.info("🧹 Limpiando MainPresenter")
            
            # Limpiar todos los camera presenters
            for camera_id in list(self._camera_presenters.keys()):
                await self._remove_camera_presenter(camera_id)
            
            # Limpiar sub-presenters
            if self._scan_presenter:
                await self._scan_presenter.cleanup_async()
            
            if self._config_presenter:
                await self._config_presenter.cleanup_async()
            
            # Limpiar servicios
            await self._protocol_service.cleanup()
            
            self.logger.info("MainPresenter limpiado")
            
        except Exception as e:
            self.logger.error(f"Error limpiando MainPresenter: {str(e)}")
    
    async def _initialize_services(self):
        """Inicializa todos los servicios necesarios."""
        try:
            # Inicializar servicios principales
            await self._data_service.initialize()
            await self._config_service.initialize()
            
            self.logger.info("Servicios inicializados")
            
        except Exception as e:
            self.logger.error(f"Error inicializando servicios: {str(e)}")
            raise
    
    async def _create_sub_presenters(self):
        """Crea los sub-presenters necesarios."""
        try:
            # Crear ScanPresenter
            self._scan_presenter = ScanPresenter()
            await self._scan_presenter.initialize_async()
            
            # Configurar callbacks del scan presenter - usar funciones wrapper síncronas
            self._scan_presenter.set_scan_progress_callback(self._on_scan_progress_wrapper)
            self._scan_presenter.set_scan_completed_callback(self._on_scan_completed_wrapper)
            self._scan_presenter.set_camera_discovered_callback(self._on_camera_discovered_wrapper)
            
            # Crear ConfigPresenter
            self._config_presenter = ConfigPresenter()
            await self._config_presenter.initialize_async()
            
            self.logger.info("Sub-presenters creados")
            
        except Exception as e:
            self.logger.error(f"Error creando sub-presenters: {str(e)}")
            raise
    
    # === Callback Wrappers Síncronos ===
    
    def _on_scan_progress_wrapper(self, current: int, total: int, message: str):
        """Wrapper síncrono para callback de progreso de escaneo."""
        if self._on_scan_progress:
            try:
                self._on_scan_progress(current, total, message)
            except Exception as e:
                self.logger.error(f"Error en callback de progreso: {str(e)}")
    
    def _on_scan_completed_wrapper(self, discovered_cameras: List[CameraModel]):
        """Wrapper síncrono para callback de escaneo completado."""
        self._discovered_cameras = discovered_cameras
        
        if self._on_scan_completed:
            try:
                self._on_scan_completed(discovered_cameras)
            except Exception as e:
                self.logger.error(f"Error en callback de completado: {str(e)}")
        
        self.logger.info(f"Escaneo completado: {len(discovered_cameras)} cámaras encontradas")
    
    def _on_camera_discovered_wrapper(self, camera: CameraModel):
        """Wrapper síncrono para callback de cámara descubierta."""
        self.logger.info(f"📹 Cámara descubierta: {camera.display_name} ({camera.connection_config.ip})")
    
    def _on_camera_connection_change_wrapper(self, camera_id: str, connected: bool, message: str):
        """Wrapper síncrono para callback de cambio de conexión."""
        status = "connected" if connected else "disconnected"
        
        if self._on_camera_status_changed:
            try:
                self._on_camera_status_changed(camera_id, status)
            except Exception as e:
                self.logger.error(f"Error en callback de estado: {str(e)}")
        
        self.logger.info(f"📹 Cámara {camera_id}: {status} - {message}")
    
    async def _load_initial_configuration(self):
        """Carga la configuración inicial de la aplicación."""
        try:
            # Cargar configuración de layout
            self._current_layout = await self._config_service.get_config_value(
                "ui.camera_grid_columns", 2
            )
            
            # Cargar configuración de auto-scan
            self._auto_scan_enabled = await self._config_service.get_config_value(
                "scan.auto_scan_enabled", False
            )
            
            self.logger.info("Configuración inicial cargada")
            
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {str(e)}")
    
    async def _load_saved_cameras(self):
        """Carga cámaras guardadas desde el DataService."""
        try:
            # Esta funcionalidad se implementará cuando DataService esté completamente integrado
            self.logger.info("📷 Cargando cámaras guardadas...")
            
            # Por ahora, crear algunas cámaras de ejemplo para demostración
            await self._create_demo_cameras()
            
        except Exception as e:
            self.logger.error(f"Error cargando cámaras: {str(e)}")
    
    async def _create_demo_cameras(self):
        """Crea cámaras de demostración para testing."""
        try:
            demo_cameras = [
                {
                    "id": "demo_camera_1",
                    "name": "Cámara Demo 1",
                    "ip": "192.168.1.100",
                    "brand": "Dahua",
                    "model": "IPC-HDW1200SP"
                },
                {
                    "id": "demo_camera_2", 
                    "name": "Cámara Demo 2",
                    "ip": "192.168.1.101",
                    "brand": "TP-Link",
                    "model": "Tapo C200"
                }
            ]
            
            for camera_data in demo_cameras:
                await self._add_camera_from_data(camera_data)
            
            self.logger.info(f"{len(demo_cameras)} cámaras demo creadas")
            
        except Exception as e:
            self.logger.error(f"Error creando cámaras demo: {str(e)}")
    
    async def _setup_metrics(self):
        """Configura las métricas del presenter principal."""
        # Usar métodos del BasePresenter que existan
        pass  # Por ahora sin métricas hasta que se corrijan los métodos del BasePresenter
    
    # === Gestión de Cámaras ===
    
    async def add_camera(self, camera_model: CameraModel) -> bool:
        """
        Agrega una nueva cámara al sistema.
        
        Args:
            camera_model: Modelo de la cámara a agregar
            
        Returns:
            True si se agregó exitosamente
        """
        try:
            camera_id = camera_model.camera_id
            
            if camera_id in self._camera_presenters:
                self.logger.warning(f"Cámara {camera_id} ya existe")
                return False
            
            # Crear presenter para la cámara
            camera_presenter = CameraPresenter(camera_id)
            await camera_presenter.initialize_async()
            
            # Configurar callbacks - usar wrapper síncrono
            camera_presenter.set_connection_change_callback(
                lambda connected, msg, cid=camera_id: 
                    self._on_camera_connection_change_wrapper(cid, connected, msg)
            )
            
            # Guardar presenter
            self._camera_presenters[camera_id] = camera_presenter
            self._active_cameras.append(camera_id)
            
            # Guardar en DataService
            await self._data_service.save_camera_data(camera_model)
            
            # Notificar cambio
            await self._notify_cameras_updated()
            
            self.logger.info(f"Cámara agregada: {camera_model.display_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error agregando cámara: {str(e)}")
            return False
    
    async def _add_camera_from_data(self, camera_data: Dict[str, Any]) -> bool:
        """Agrega cámara desde datos de diccionario."""
        try:
            from models import ConnectionConfig
            
            # Crear configuración de conexión
            connection_config = ConnectionConfig(
                ip=camera_data["ip"],
                username="admin",  # Default
                password=""  # Se obtendrá del ConfigService
            )
            
            # Crear modelo de cámara
            camera_model = CameraModel(
                brand=camera_data["brand"],
                model=camera_data["model"],
                display_name=camera_data["name"],
                connection_config=connection_config
            )
            
            return await self.add_camera(camera_model)
            
        except Exception as e:
            self.logger.error(f"Error creando cámara desde datos: {str(e)}")
            return False
    
    async def remove_camera(self, camera_id: str) -> bool:
        """
        Remueve una cámara del sistema.
        
        Args:
            camera_id: ID de la cámara a remover
            
        Returns:
            True si se removió exitosamente
        """
        try:
            if camera_id not in self._camera_presenters:
                return True
            
            # Remover presenter
            await self._remove_camera_presenter(camera_id)
            
            # Remover de lista activa
            if camera_id in self._active_cameras:
                self._active_cameras.remove(camera_id)
            
            # Notificar cambio
            await self._notify_cameras_updated()
            
            self.logger.info(f"Cámara removida: {camera_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removiendo cámara: {str(e)}")
            return False
    
    async def _remove_camera_presenter(self, camera_id: str):
        """Remueve y limpia un camera presenter."""
        if camera_id in self._camera_presenters:
            presenter = self._camera_presenters[camera_id]
            await presenter.cleanup_async()
            del self._camera_presenters[camera_id]
    
    async def connect_all_cameras(self) -> Dict[str, bool]:
        """
        Conecta todas las cámaras.
        
        Returns:
            Diccionario con resultado de conexión por cámara
        """
        results = {}
        
        for camera_id, presenter in self._camera_presenters.items():
            try:
                success = await presenter.connect_camera()
                results[camera_id] = success
                
                if success:
                    self.logger.info(f"Cámara {camera_id} conectada")
                else:
                    self.logger.warning(f"No se pudo conectar cámara {camera_id}")
                    
            except Exception as e:
                self.logger.error(f"Error conectando {camera_id}: {str(e)}")
                results[camera_id] = False
        
        return results
    
    async def disconnect_all_cameras(self) -> Dict[str, bool]:
        """
        Desconecta todas las cámaras.
        
        Returns:
            Diccionario con resultado de desconexión por cámara
        """
        results = {}
        
        for camera_id, presenter in self._camera_presenters.items():
            try:
                success = await presenter.disconnect_camera()
                results[camera_id] = success
                
            except Exception as e:
                self.logger.error(f"Error desconectando {camera_id}: {str(e)}")
                results[camera_id] = False
        
        return results
    
    # === Operaciones de Escaneo ===
    
    async def start_network_scan(self, custom_config: Optional[ScanConfig] = None) -> bool:
        """
        Inicia un escaneo de red para descubrir cámaras.
        
        Args:
            custom_config: Configuración personalizada de escaneo
            
        Returns:
            True si el escaneo se inició exitosamente
        """
        if not self._scan_presenter:
            return False
        
        try:
            success = await self._scan_presenter.start_network_scan(custom_config)
            
            if success:
                self.logger.info("Escaneo de red iniciado")
            else:
                self.logger.error("No se pudo iniciar escaneo")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error iniciando escaneo: {str(e)}")
            return False
    
    async def stop_current_scan(self) -> bool:
        """
        Detiene el escaneo actual.
        
        Returns:
            True si se detuvo exitosamente
        """
        if not self._scan_presenter:
            return True
        
        return await self._scan_presenter.stop_current_scan()
    
    # === Gestión de Layout ===
    
    async def set_camera_layout(self, columns: int) -> bool:
        """
        Cambia el layout de la grilla de cámaras.
        
        Args:
            columns: Número de columnas
            
        Returns:
            True si se cambió exitosamente
        """
        try:
            if columns < 1 or columns > 6:
                return False
            
            self._current_layout = columns
            
            # Guardar configuración
            await self._config_service.set_config_value("ui.camera_grid_columns", columns)
            
            # Notificar cambio
            await self._notify_cameras_updated()
            
            self.logger.info(f"Layout cambiado a {columns} columnas")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cambiando layout: {str(e)}")
            return False
    
    def get_current_layout(self) -> int:
        """Obtiene el layout actual."""
        return self._current_layout
    
    # === Gestión de Estado ===
    
    def get_camera_presenters(self) -> Dict[str, CameraPresenter]:
        """Obtiene todos los camera presenters."""
        return self._camera_presenters.copy()
    
    def get_camera_presenter(self, camera_id: str) -> Optional[CameraPresenter]:
        """Obtiene un camera presenter específico."""
        return self._camera_presenters.get(camera_id)
    
    def get_active_cameras(self) -> List[str]:
        """Obtiene lista de cámaras activas."""
        return self._active_cameras.copy()
    
    def get_discovered_cameras(self) -> List[CameraModel]:
        """Obtiene cámaras descubiertas en el último escaneo."""
        return self._discovered_cameras.copy()
    
    def is_scanning(self) -> bool:
        """Indica si hay un escaneo en progreso."""
        return self._scan_presenter.is_scanning() if self._scan_presenter else False
    
    async def _notify_cameras_updated(self):
        """Notifica cambios en las cámaras."""
        if self._on_cameras_updated:
            # Crear lista de modelos de cámaras activas
            camera_models = []
            for camera_id in self._active_cameras:
                presenter = self._camera_presenters.get(camera_id)
                if presenter:
                    model = presenter.get_camera_model()
                    if model:
                        camera_models.append(model)
            
            await self.execute_safe(self._on_cameras_updated, camera_models)
    
    # === Callbacks de View ===
    
    def set_cameras_updated_callback(self, callback: Callable[[List[CameraModel]], None]):
        """Establece callback para cambios en cámaras."""
        self._on_cameras_updated = callback
    
    def set_camera_status_changed_callback(self, callback: Callable[[str, str], None]):
        """Establece callback para cambios de estado de cámara."""
        self._on_camera_status_changed = callback
    
    def set_scan_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Establece callback para progreso de escaneo."""
        self._on_scan_progress = callback
    
    def set_scan_completed_callback(self, callback: Callable[[List[CameraModel]], None]):
        """Establece callback para completación de escaneo."""
        self._on_scan_completed = callback
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """Establece callback para errores."""
        self._on_error = callback
    
    # === Utilidades ===
    
    async def execute_safe(self, callback: Callable, *args, **kwargs):
        """Ejecuta callback de forma segura."""
        try:
            if callback:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error en callback: {str(e)}")
    
    def get_application_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la aplicación."""
        return {
            "total_cameras": len(self._camera_presenters),
            "active_cameras": len(self._active_cameras),
            "discovered_cameras": len(self._discovered_cameras),
            "current_layout": self._current_layout,
            "is_scanning": self.is_scanning(),
            "auto_scan_enabled": self._auto_scan_enabled
        }
    
    async def cleanup_async(self) -> None:
        """Limpia recursos del presenter principal."""
        await self._cleanup_presenter() 