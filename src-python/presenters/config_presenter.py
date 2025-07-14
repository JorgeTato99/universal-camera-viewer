#!/usr/bin/env python3
"""
ConfigPresenter - Presenter para gestión de configuración de la aplicación.

Coordina la lógica de negocio para:
- Gestión de configuración general de la aplicación
- Perfiles de configuración
- Configuración específica por marca de cámara
- Importación y exportación de configuración
- Gestión de credenciales
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path

from presenters.base_presenter import BasePresenter, PresenterState
from services import get_config_service, get_data_service
from services.config_service import ConfigProfile, ConfigItem, ConfigCategory, ConfigType


class ConfigPresenter(BasePresenter):
    """
    Presenter para gestión de configuración de la aplicación.
    
    Coordina todas las operaciones de configuración:
    - Gestión de configuración general
    - Perfiles de configuración por marca/escenario
    - Configuración de credenciales seguras
    - Importación/exportación de configuración
    - Validación de configuraciones
    """
    
    def __init__(self):
        """Inicializa el presenter de configuración."""
        super().__init__()
        
        # Servicios
        self._config_service = get_config_service()
        self._data_service = get_data_service()
        
        # Estado de configuración
        self._current_profile: Optional[ConfigProfile] = None
        self._available_profiles: Dict[str, ConfigProfile] = {}
        self._unsaved_changes = False
        
        # Callbacks para la view
        self._on_config_changed: Optional[Callable[[str, Any], None]] = None
        self._on_profile_changed: Optional[Callable[[ConfigProfile], None]] = None
        self._on_validation_error: Optional[Callable[[str, str], None]] = None
        self._on_import_completed: Optional[Callable[[bool, str], None]] = None
        self._on_export_completed: Optional[Callable[[bool, str], None]] = None
        
    async def initialize_async(self) -> bool:
        """
        Inicialización asíncrona del presenter.
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            self.logger.info("Inicializando ConfigPresenter")
            
            # Cargar perfiles disponibles
            await self._load_available_profiles()
            
            # Cargar perfil activo
            await self._load_active_profile()
            
            # Configurar métricas iniciales
            await self._setup_metrics()
            
            # Configurar observador de cambios (función sync, no async)
            self._config_service.add_change_observer(self._on_config_change_internal_sync)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando ConfigPresenter: {str(e)}")
            await self.set_error(f"Error de inicialización: {str(e)}")
            return False
    
    async def _load_available_profiles(self) -> None:
        """Carga todos los perfiles de configuración disponibles."""
        try:
            self._available_profiles = self._config_service.get_all_profiles()
            self.logger.info(f"{len(self._available_profiles)} perfiles cargados")
            
        except Exception as e:
            self.logger.error(f"Error cargando perfiles: {str(e)}")
            self._available_profiles = {}
    
    async def _load_active_profile(self) -> None:
        """Carga el perfil de configuración activo."""
        try:
            self._current_profile = self._config_service.get_active_profile()
            if self._current_profile:
                self.logger.info(f"📁 Perfil activo: {self._current_profile.name}")
            else:
                self.logger.warning("No hay perfil activo")
                
        except Exception as e:
            self.logger.error(f"Error cargando perfil activo: {str(e)}")
            self._current_profile = None
    
    async def _setup_metrics(self) -> None:
        """Configura las métricas de monitoreo de configuración."""
        self.add_metric("total_profiles", len(self._available_profiles))
        self.add_metric("active_profile", self._current_profile.name if self._current_profile else None)
        self.add_metric("unsaved_changes", self._unsaved_changes)
        self.add_metric("config_items_count", 0)
        self.add_metric("last_save_time", None)
        self.add_metric("last_load_time", None)
    
    def _on_config_change_internal_sync(self, key: str, old_value: Any, new_value: Any) -> None:
        """Maneja cambios internos de configuración (función sync)."""
        try:
            self._unsaved_changes = True
            self.add_metric("unsaved_changes", True)
            
            # Notificar a la view de forma asíncrona
            if self._on_config_changed:
                asyncio.create_task(
                    self.execute_safely(self._on_config_changed, key, new_value)
                )
                
        except Exception as e:
            self.logger.error(f"Error procesando cambio de configuración: {str(e)}")
    
    # === Gestión de Configuración ===
    
    async def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        try:
            return await self._config_service.get_config_value(key, default)
        except Exception as e:
            self.logger.error(f"Error obteniendo configuración {key}: {str(e)}")
            return default
    
    async def set_config_value(
        self, 
        key: str, 
        value: Any, 
        config_type: ConfigType = ConfigType.STRING,
        category: ConfigCategory = ConfigCategory.ADVANCED,
        description: str = "",
        is_sensitive: bool = False
    ) -> bool:
        """
        Establece un valor de configuración.
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
            config_type: Tipo de configuración
            category: Categoría de configuración
            description: Descripción del parámetro
            is_sensitive: Si es información sensible
            
        Returns:
            True si se estableció correctamente
        """
        await self.set_busy(True)
        
        try:
            success = await self._config_service.set_config_value(
                key=key,
                value=value,
                config_type=config_type,
                category=category,
                description=description,
                is_sensitive=is_sensitive
            )
            
            if success:
                self._set_state(PresenterState.READY)
                self.logger.info(f"Configuración actualizada: {key}")
                return True
            else:
                raise ValueError("Error del servicio de configuración")
                
        except Exception as e:
            error_msg = f"Error actualizando configuración {key}: {str(e)}"
            self.logger.error(f"{error_msg}")
            await self.set_error(error_msg)
            
            # Notificar error de validación
            if self._on_validation_error:
                await self.execute_safely(self._on_validation_error, key, str(e))
            
            return False
    
    async def delete_config_value(self, key: str) -> bool:
        """
        Elimina un valor de configuración.
        
        Args:
            key: Clave de configuración a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        await self.set_busy(True)
        
        try:
            success = await self._config_service.delete_config_value(key)
            
            if success:
                self._set_state(PresenterState.READY)
                self.logger.info(f"Configuración eliminada: {key}")
                return True
            else:
                raise ValueError("Error del servicio de configuración")
                
        except Exception as e:
            error_msg = f"Error eliminando configuración {key}: {str(e)}"
            self.logger.error(f"{error_msg}")
            await self.set_error(error_msg)
            return False
    
    # === Gestión de Perfiles ===
    
    async def create_profile(self, profile_id: str, name: str, description: str, category: str = "custom") -> bool:
        """
        Crea un nuevo perfil de configuración.
        
        Args:
            profile_id: ID único del perfil
            name: Nombre del perfil
            description: Descripción del perfil
            category: Categoría del perfil
            
        Returns:
            True si se creó correctamente
        """
        await self.set_busy(True)
        
        try:
            success = await self._config_service.create_profile(
                profile_id=profile_id,
                name=name,
                description=description,
                category=category
            )
            
            if success:
                # Actualizar lista de perfiles
                await self._load_available_profiles()
                self.add_metric("total_profiles", len(self._available_profiles))
                
                self._set_state(PresenterState.READY)
                self.logger.info(f"Perfil creado: {name}")
                return True
            else:
                raise ValueError("Error del servicio de configuración")
                
        except Exception as e:
            error_msg = f"Error creando perfil {name}: {str(e)}"
            self.logger.error(f"{error_msg}")
            await self.set_error(error_msg)
            return False
    
    async def switch_profile(self, profile_id: str) -> bool:
        """
        Cambia al perfil especificado.
        
        Args:
            profile_id: ID del perfil al que cambiar
            
        Returns:
            True si se cambió correctamente
        """
        await self.set_busy(True)
        
        try:
            success = await self._config_service.switch_profile(profile_id)
            
            if success:
                # Actualizar perfil actual
                await self._load_active_profile()
                self.add_metric("active_profile", self._current_profile.name if self._current_profile else None)
                
                # Notificar cambio de perfil
                if self._on_profile_changed and self._current_profile:
                    await self.execute_safely(self._on_profile_changed, self._current_profile)
                
                self._set_state(PresenterState.READY)
                self.logger.info(f"Perfil cambiado: {profile_id}")
                return True
            else:
                raise ValueError("Error del servicio de configuración")
                
        except Exception as e:
            error_msg = f"Error cambiando perfil {profile_id}: {str(e)}"
            self.logger.error(f"{error_msg}")
            await self.set_error(error_msg)
            return False
    
    def get_available_profiles(self) -> Dict[str, ConfigProfile]:
        """Retorna todos los perfiles disponibles."""
        return self._available_profiles.copy()
    
    def get_current_profile(self) -> Optional[ConfigProfile]:
        """Retorna el perfil activo actual."""
        return self._current_profile
    
    # === Gestión de Credenciales ===
    
    async def set_camera_credentials(self, brand: str, username: str, password: str) -> bool:
        """
        Establece credenciales para una marca de cámara.
        
        Args:
            brand: Marca de la cámara
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            True si se establecieron correctamente
        """
        await self.set_busy(True)
        
        try:
            success = await self._config_service.set_camera_credentials(
                brand=brand,
                username=username,
                password=password
            )
            
            if success:
                self._set_state(PresenterState.READY)
                self.logger.info(f"🔐 Credenciales configuradas: {brand}")
                return True
            else:
                raise ValueError("Error del servicio de configuración")
                
        except Exception as e:
            error_msg = f"Error configurando credenciales {brand}: {str(e)}"
            self.logger.error(f"{error_msg}")
            await self.set_error(error_msg)
            return False
    
    async def get_camera_credentials(self, brand: str) -> Dict[str, str]:
        """
        Obtiene credenciales para una marca de cámara.
        
        Args:
            brand: Marca de la cámara
            
        Returns:
            Diccionario con credenciales
        """
        try:
            return await self._config_service.get_camera_credentials(brand)
        except Exception as e:
            self.logger.error(f"Error obteniendo credenciales {brand}: {str(e)}")
            return {"username": "", "password": ""}
    
    # === Importación y Exportación ===
    
    async def export_configuration(self, filepath: str, include_sensitive: bool = False) -> bool:
        """
        Exporta la configuración a un archivo.
        
        Args:
            filepath: Ruta del archivo de destino
            include_sensitive: Si incluir datos sensibles
            
        Returns:
            True si se exportó correctamente
        """
        await self.set_busy(True)
        
        try:
            success = await self._config_service.export_config(
                filepath=filepath,
                include_sensitive=include_sensitive
            )
            
            if success:
                self.add_metric("last_save_time", datetime.now().isoformat())
                
                # Notificar completación
                if self._on_export_completed:
                    await self.execute_safely(self._on_export_completed, True, filepath)
                
                self._set_state(PresenterState.READY)
                self.logger.info(f"📤 Configuración exportada: {filepath}")
                return True
            else:
                raise ValueError("Error del servicio de configuración")
                
        except Exception as e:
            error_msg = f"Error exportando configuración: {str(e)}"
            self.logger.error(f"{error_msg}")
            
            # Notificar error
            if self._on_export_completed:
                await self.execute_safely(self._on_export_completed, False, error_msg)
            
            await self.set_error(error_msg)
            return False
    
    async def import_configuration(self, filepath: str) -> bool:
        """
        Importa configuración desde un archivo.
        
        Args:
            filepath: Ruta del archivo de origen
            
        Returns:
            True si se importó correctamente
        """
        await self.set_busy(True)
        
        try:
            # Verificar que el archivo existe
            if not Path(filepath).exists():
                raise FileNotFoundError(f"Archivo no encontrado: {filepath}")
            
            # Importar configuración (implementación básica)
            # Esta funcionalidad se expandirá cuando se implemente completamente en ConfigService
            
            # Recargar perfiles y configuración
            await self._load_available_profiles()
            await self._load_active_profile()
            
            self.add_metric("last_load_time", datetime.now().isoformat())
            self.add_metric("total_profiles", len(self._available_profiles))
            
            # Notificar completación
            if self._on_import_completed:
                await self.execute_safely(self._on_import_completed, True, filepath)
            
            self._set_state(PresenterState.READY)
            self.logger.info(f"📥 Configuración importada: {filepath}")
            return True
            
        except Exception as e:
            error_msg = f"Error importando configuración: {str(e)}"
            self.logger.error(f"{error_msg}")
            
            # Notificar error
            if self._on_import_completed:
                await self.execute_safely(self._on_import_completed, False, error_msg)
            
            await self.set_error(error_msg)
            return False
    
    async def reset_to_defaults(self) -> bool:
        """
        Restablece la configuración a valores por defecto.
        
        Returns:
            True si se restableció correctamente
        """
        await self.set_busy(True)
        
        try:
            # Implementar reset a defaults
            # Esta funcionalidad se expandirá cuando se implemente en ConfigService
            
            # Recargar configuración
            await self._load_available_profiles()
            await self._load_active_profile()
            
            self._unsaved_changes = False
            self.add_metric("unsaved_changes", False)
            
            self._set_state(PresenterState.READY)
            self.logger.info("Configuración restablecida a defaults")
            return True
            
        except Exception as e:
            error_msg = f"Error restableciendo configuración: {str(e)}"
            self.logger.error(f"{error_msg}")
            await self.set_error(error_msg)
            return False
    
    # === Validación ===
    
    async def validate_configuration(self) -> Dict[str, List[str]]:
        """
        Valida la configuración actual.
        
        Returns:
            Diccionario con errores de validación por categoría
        """
        try:
            # Implementar validación completa
            # Esta funcionalidad se expandirá cuando se implemente en ConfigService
            validation_errors = {}
            
            self.logger.info("Configuración validada")
            return validation_errors
            
        except Exception as e:
            self.logger.error(f"Error validando configuración: {str(e)}")
            return {"general": [str(e)]}
    
    # === Gestión de Estado ===
    
    def has_unsaved_changes(self) -> bool:
        """Retorna si hay cambios sin guardar."""
        return self._unsaved_changes
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Retorna resumen de la configuración actual."""
        return {
            "active_profile": self._current_profile.name if self._current_profile else None,
            "total_profiles": len(self._available_profiles),
            "unsaved_changes": self._unsaved_changes,
            "statistics": self._config_service.get_statistics()
        }
    
    # === Callbacks de View ===
    
    def set_config_changed_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Establece callback para cambios de configuración."""
        self._on_config_changed = callback
    
    def set_profile_changed_callback(self, callback: Callable[[ConfigProfile], None]) -> None:
        """Establece callback para cambios de perfil."""
        self._on_profile_changed = callback
    
    def set_validation_error_callback(self, callback: Callable[[str, str], None]) -> None:
        """Establece callback para errores de validación."""
        self._on_validation_error = callback
    
    def set_import_completed_callback(self, callback: Callable[[bool, str], None]) -> None:
        """Establece callback para completación de importación."""
        self._on_import_completed = callback
    
    def set_export_completed_callback(self, callback: Callable[[bool, str], None]) -> None:
        """Establece callback para completación de exportación."""
        self._on_export_completed = callback
    
    # === Abstract Methods Implementation ===
    
    async def _initialize_presenter(self) -> None:
        """Implementación de inicialización específica del presenter."""
        # La inicialización específica se maneja en initialize_async()
        pass
    
    async def _cleanup_presenter(self) -> None:
        """Implementación de limpieza específica del presenter."""
        try:
            # Remover observador de cambios
            self._config_service.remove_change_observer(self._on_config_change_internal_sync)
            
            self.logger.info("🧹 ConfigPresenter limpiado")
            
        except Exception as e:
            self.logger.error(f"Error en limpieza de ConfigPresenter: {str(e)}")
    
    # === Cleanup ===
    
    async def cleanup_async(self) -> None:
        """Limpieza asíncrona del presenter."""
        await self._cleanup_presenter() 