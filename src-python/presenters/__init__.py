#!/usr/bin/env python3
"""
Presenters Package - MVP Architecture
====================================

Capa de presentación que maneja la lógica de coordinación entre
las vistas (UI) y los modelos de negocio.

Presenters disponibles:
- BasePresenter: Clase base con funcionalidad común
- CameraPresenter: Gestión individual de cámaras
- ScanPresenter: Operaciones de escaneo y descubrimiento
- ConfigPresenter: Gestión de configuración
- MainPresenter: Coordinador principal de la aplicación
"""

from presenters.base_presenter import BasePresenter, PresenterState
from presenters.camera_presenter import CameraPresenter
from presenters.scan_presenter import ScanPresenter  
from presenters.config_presenter import ConfigPresenter
from presenters.main_presenter import MainPresenter
from presenters.theme_presenter import ThemePresenter, theme_presenter

# MediaMTX presenters
from presenters.mediamtx_servers_presenter import (
    MediaMTXServersPresenter,
    get_mediamtx_servers_presenter
)

# Singleton instances para reutilización
_main_presenter_instance = None
_camera_presenter_instances = {}
_scan_presenter_instance = None
_config_presenter_instance = None
_theme_presenter_instance = None
_mediamtx_servers_presenter_instance = None


def get_main_presenter() -> MainPresenter:
    """
    Obtiene la instancia singleton del MainPresenter.
    
    Returns:
        Instancia de MainPresenter
    """
    global _main_presenter_instance
    if _main_presenter_instance is None:
        _main_presenter_instance = MainPresenter()
    return _main_presenter_instance


def get_camera_presenter(camera_id: str) -> CameraPresenter:
    """
    Obtiene una instancia de CameraPresenter para la cámara especificada.
    
    Args:
        camera_id: ID único de la cámara
        
    Returns:
        Instancia de CameraPresenter
    """
    global _camera_presenter_instances
    if camera_id not in _camera_presenter_instances:
        _camera_presenter_instances[camera_id] = CameraPresenter(camera_id)
    return _camera_presenter_instances[camera_id]


def get_scan_presenter() -> ScanPresenter:
    """
    Obtiene la instancia singleton del ScanPresenter.
    
    Returns:
        Instancia de ScanPresenter
    """
    global _scan_presenter_instance
    if _scan_presenter_instance is None:
        _scan_presenter_instance = ScanPresenter()
    return _scan_presenter_instance


def get_config_presenter() -> ConfigPresenter:
    """
    Obtiene la instancia singleton del ConfigPresenter.
    
    Returns:
        Instancia de ConfigPresenter
    """
    global _config_presenter_instance
    if _config_presenter_instance is None:
        _config_presenter_instance = ConfigPresenter()
    return _config_presenter_instance


def get_theme_presenter() -> ThemePresenter:
    """
    Obtiene la instancia singleton del ThemePresenter.
    
    Returns:
        Instancia de ThemePresenter
    """
    global _theme_presenter_instance
    if _theme_presenter_instance is None:
        _theme_presenter_instance = theme_presenter
    return _theme_presenter_instance


async def cleanup_all_presenters():
    """Limpia todas las instancias de presenters."""
    global _main_presenter_instance, _camera_presenter_instances
    global _scan_presenter_instance, _config_presenter_instance
    global _theme_presenter_instance
    
    # Cleanup MainPresenter
    if _main_presenter_instance:
        await _main_presenter_instance.cleanup_async()
        _main_presenter_instance = None
    
    # Cleanup CameraPresenters
    for presenter in _camera_presenter_instances.values():
        await presenter.cleanup_async()
    _camera_presenter_instances.clear()
    
    # Cleanup ScanPresenter
    if _scan_presenter_instance:
        await _scan_presenter_instance.cleanup_async()
        _scan_presenter_instance = None
    
    # Cleanup ConfigPresenter
    if _config_presenter_instance:
        await _config_presenter_instance.cleanup_async()
        _config_presenter_instance = None
    
    # Cleanup ThemePresenter
    if _theme_presenter_instance:
        await _theme_presenter_instance.cleanup_async()
        _theme_presenter_instance = None


__all__ = [
    # Base
    "BasePresenter",
    "PresenterState",
    
    # Concrete Presenters
    "CameraPresenter",
    "ScanPresenter", 
    "ConfigPresenter",
    "MainPresenter",
    "ThemePresenter",
    "MediaMTXServersPresenter",
    
    # Singleton instances
    "theme_presenter",
    
    # Factory Functions
    "get_main_presenter",
    "get_camera_presenter",
    "get_scan_presenter",
    "get_config_presenter",
    "get_theme_presenter",
    "get_mediamtx_servers_presenter",
    "cleanup_all_presenters",
] 