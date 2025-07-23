"""
Presenter para gestión de autenticación MediaMTX.

Coordina la lógica de negocio entre la vista (API) y los servicios
de autenticación, siguiendo el patrón MVP.
"""

import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from presenters.base_presenter import BasePresenter
from services.mediamtx.auth_service import get_auth_service
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.logging_service import get_secure_logger
from utils.exceptions import ServiceError, ValidationError
from utils.sanitizers import sanitize_url


logger = get_secure_logger("presenters.mediamtx_auth_presenter")


class MediaMTXAuthPresenter(BasePresenter):
    """
    Presenter para autenticación con servidores MediaMTX.
    
    Responsabilidades:
    - Coordinar login/logout de servidores
    - Validar configuraciones antes de autenticar
    - Gestionar estado de autenticación
    - Proveer información de estado a la vista
    """
    
    def __init__(self):
        """Inicializa el presenter de autenticación."""
        super().__init__()
        self.logger = logger
        
        # Servicios
        self._auth_service = get_auth_service()
        self._db_service = get_mediamtx_db_service()
        
        # Estado interno
        self._server_auth_status: Dict[int, Dict[str, Any]] = {}
        
    async def _initialize_presenter(self) -> None:
        """Inicialización específica del presenter."""
        self.logger.info("Inicializando MediaMTXAuthPresenter")
        
        # Inicializar servicio de autenticación
        await self._auth_service.initialize()
        
        # Cargar estado inicial de servidores
        await self._load_server_auth_status()
        
    async def _cleanup_presenter(self) -> None:
        """Limpieza específica del presenter."""
        self.logger.info("Limpiando MediaMTXAuthPresenter")
        self._server_auth_status.clear()
    
    async def _load_server_auth_status(self) -> None:
        """Carga el estado de autenticación de todos los servidores."""
        try:
            servers = await self._db_service.get_all_servers()
            
            for server in servers:
                server_id = server['server_id']
                
                # Verificar si hay token válido
                token = await self._auth_service.get_valid_token(server_id)
                
                self._server_auth_status[server_id] = {
                    'server_name': server['server_name'],
                    'api_url': server['api_url'],
                    'is_authenticated': token is not None,
                    'last_check': datetime.utcnow()
                }
                
            self.logger.info(f"Estado de autenticación cargado para {len(servers)} servidores")
            
        except Exception as e:
            self.logger.error(f"Error cargando estado de autenticación: {str(e)}")
    
    async def authenticate_server(
        self,
        server_id: int,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Autentica con un servidor MediaMTX.
        
        Args:
            server_id: ID del servidor
            username: Usuario
            password: Contraseña
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            await self.set_busy(True)
            
            # Validar servidor existe
            server = await self._db_service.get_server_by_id(server_id)
            if not server:
                raise ValidationError(f"Servidor {server_id} no encontrado")
            
            # Validar servidor activo
            if not server.get('is_active'):
                raise ValidationError(f"Servidor {server['server_name']} no está activo")
            
            # Validar URL de API
            api_url = server.get('api_url')
            if not api_url:
                raise ValidationError(f"Servidor {server['server_name']} no tiene API URL configurada")
            
            self.logger.info(f"Autenticando con servidor {server_id} ({server['server_name']})")
            
            # Intentar autenticación
            success, error_msg = await self._auth_service.login(
                server_id=server_id,
                username=username,
                password=password,
                api_url=api_url
            )
            
            # Actualizar estado interno
            self._server_auth_status[server_id] = {
                'server_name': server['server_name'],
                'api_url': api_url,
                'is_authenticated': success,
                'last_check': datetime.utcnow(),
                'last_error': error_msg if not success else None
            }
            
            # Emitir evento
            await self._emit_event("auth_status_changed", {
                'server_id': server_id,
                'authenticated': success
            })
            
            if success:
                self.logger.info(f"Autenticación exitosa para servidor {server_id}")
                return {
                    'success': True,
                    'server_id': server_id,
                    'server_name': server['server_name'],
                    'message': 'Autenticación exitosa'
                }
            else:
                self.logger.warning(f"Fallo de autenticación para servidor {server_id}: {error_msg}")
                return {
                    'success': False,
                    'server_id': server_id,
                    'server_name': server['server_name'],
                    'error': error_msg or 'Error de autenticación'
                }
                
        except ValidationError as e:
            self.logger.error(f"Error de validación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
        except Exception as e:
            self.logger.error(f"Error inesperado durante autenticación: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
            
        finally:
            await self.set_busy(False)
    
    async def logout_server(self, server_id: int) -> Dict[str, Any]:
        """
        Cierra sesión de un servidor MediaMTX.
        
        Args:
            server_id: ID del servidor
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            await self.set_busy(True)
            
            # Validar servidor existe
            server = await self._db_service.get_server_by_id(server_id)
            if not server:
                raise ValidationError(f"Servidor {server_id} no encontrado")
            
            self.logger.info(f"Cerrando sesión de servidor {server_id} ({server['server_name']})")
            
            # Cerrar sesión
            await self._auth_service.logout(server_id)
            
            # Actualizar estado interno
            if server_id in self._server_auth_status:
                self._server_auth_status[server_id]['is_authenticated'] = False
                self._server_auth_status[server_id]['last_check'] = datetime.utcnow()
            
            # Emitir evento
            await self._emit_event("auth_status_changed", {
                'server_id': server_id,
                'authenticated': False
            })
            
            return {
                'success': True,
                'server_id': server_id,
                'server_name': server['server_name'],
                'message': 'Sesión cerrada exitosamente'
            }
            
        except ValidationError as e:
            self.logger.error(f"Error de validación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
        except Exception as e:
            self.logger.error(f"Error cerrando sesión: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
            
        finally:
            await self.set_busy(False)
    
    async def get_auth_status(self, server_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene el estado de autenticación.
        
        Args:
            server_id: ID del servidor específico o None para todos
            
        Returns:
            Dict con estado de autenticación
        """
        try:
            if server_id:
                # Estado de un servidor específico
                if server_id not in self._server_auth_status:
                    # Intentar cargar
                    server = await self._db_service.get_server_by_id(server_id)
                    if not server:
                        return {
                            'success': False,
                            'error': f'Servidor {server_id} no encontrado'
                        }
                    
                    token = await self._auth_service.get_valid_token(server_id)
                    self._server_auth_status[server_id] = {
                        'server_name': server['server_name'],
                        'api_url': server['api_url'],
                        'is_authenticated': token is not None,
                        'last_check': datetime.utcnow()
                    }
                
                status = self._server_auth_status[server_id]
                return {
                    'success': True,
                    'server_id': server_id,
                    'server_name': status['server_name'],
                    'api_url': sanitize_url(status['api_url']),
                    'is_authenticated': status['is_authenticated'],
                    'last_check': status['last_check'].isoformat(),
                    'last_error': status.get('last_error')
                }
                
            else:
                # Estado de todos los servidores
                servers_status = []
                
                for sid, status in self._server_auth_status.items():
                    servers_status.append({
                        'server_id': sid,
                        'server_name': status['server_name'],
                        'api_url': sanitize_url(status['api_url']),
                        'is_authenticated': status['is_authenticated'],
                        'last_check': status['last_check'].isoformat(),
                        'last_error': status.get('last_error')
                    })
                
                return {
                    'success': True,
                    'servers': servers_status,
                    'authenticated_count': sum(1 for s in servers_status if s['is_authenticated']),
                    'total_count': len(servers_status)
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de autenticación: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
    
    async def refresh_auth_status(self) -> None:
        """Refresca el estado de autenticación de todos los servidores."""
        try:
            self.logger.info("Refrescando estado de autenticación")
            await self._load_server_auth_status()
            
            # Emitir evento
            await self._emit_event("auth_status_refreshed", {
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error refrescando estado: {str(e)}")
    
    async def validate_server_connection(self, server_id: int) -> Dict[str, Any]:
        """
        Valida la conexión con un servidor MediaMTX.
        
        Args:
            server_id: ID del servidor
            
        Returns:
            Dict con resultado de la validación
        """
        try:
            # Verificar si hay token válido
            token = await self._auth_service.get_valid_token(server_id)
            
            if not token:
                return {
                    'success': False,
                    'server_id': server_id,
                    'error': 'No hay sesión activa',
                    'needs_auth': True
                }
            
            # TODO: Hacer petición de prueba a la API para validar token
            # Por ahora asumimos que si hay token, está válido
            
            return {
                'success': True,
                'server_id': server_id,
                'message': 'Conexión válida',
                'is_authenticated': True
            }
            
        except Exception as e:
            self.logger.error(f"Error validando conexión: {str(e)}")
            return {
                'success': False,
                'server_id': server_id,
                'error': f'Error de validación: {str(e)}'
            }


# Instancia singleton
_presenter: Optional[MediaMTXAuthPresenter] = None


def get_mediamtx_auth_presenter() -> MediaMTXAuthPresenter:
    """
    Obtiene la instancia singleton del presenter.
    
    Returns:
        MediaMTXAuthPresenter singleton
    """
    global _presenter
    
    if _presenter is None:
        _presenter = MediaMTXAuthPresenter()
        
    return _presenter