"""
Presenter para gestión de servidores MediaMTX remotos.

Coordina las operaciones CRUD de servidores MediaMTX siguiendo
el patrón MVP. Gestiona la autenticación, validación y estado
de conexión de los servidores remotos.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from presenters.base_presenter import BasePresenter
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.mediamtx.auth_service import get_auth_service as get_mediamtx_auth_service
from services.encryption_service_v2 import EncryptionServiceV2
from services.logging_service import get_secure_logger
from utils.exceptions import ValidationError, ServiceError
from utils.sanitizers import sanitize_url


logger = get_secure_logger("presenters.mediamtx_servers")


class MediaMTXServersPresenter(BasePresenter):
    """
    Presenter para gestión de servidores MediaMTX remotos.
    
    Responsabilidades:
    - CRUD de servidores MediaMTX
    - Coordinación con servicio de autenticación
    - Validación de configuraciones
    - Gestión de estado de conexión
    - Emisión de eventos para actualizaciones
    """
    
    def __init__(self):
        """Inicializa el presenter de servidores MediaMTX."""
        super().__init__()
        self._db_service = None
        self._auth_service = None
        self._encryption_service = None
        self.logger = logger
        
    async def _initialize_presenter(self) -> None:
        """Inicializa servicios requeridos."""
        self._db_service = get_mediamtx_db_service()
        self._auth_service = get_mediamtx_auth_service()
        self._encryption_service = EncryptionServiceV2()
        
        self.logger.info("MediaMTXServersPresenter inicializado")
        
    async def _cleanup_presenter(self) -> None:
        """Limpia recursos del presenter."""
        # Los servicios son singleton, no necesitan cleanup
        self.logger.info("MediaMTXServersPresenter cleanup completado")
    
    # === Métodos públicos ===
    
    async def get_servers(
        self, 
        page: int = 1, 
        page_size: int = 10,
        include_auth_status: bool = True
    ) -> Dict[str, Any]:
        """
        Obtiene lista paginada de servidores MediaMTX.
        
        Args:
            page: Número de página (1-indexed)
            page_size: Tamaño de página
            include_auth_status: Si incluir estado de autenticación
            
        Returns:
            Dict con:
            - total: número total de servidores
            - page: página actual
            - page_size: tamaño de página
            - items: lista de servidores
        """
        try:
            await self.set_busy(True)
            
            # Validar parámetros
            if page < 1:
                raise ValidationError("La página debe ser >= 1")
            if page_size < 1 or page_size > 100:
                raise ValidationError("El tamaño de página debe estar entre 1 y 100")
            
            # Calcular offset
            offset = (page - 1) * page_size
            
            # Obtener servidores de BD
            servers = await self._db_service.get_servers()
            total = len(servers)
            
            # Aplicar paginación
            start_idx = offset
            end_idx = offset + page_size
            paginated_servers = servers[start_idx:end_idx]
            
            # Enriquecer con estado de autenticación si se solicita
            if include_auth_status:
                for server in paginated_servers:
                    server_id = server['server_id']
                    
                    # Obtener estado de autenticación
                    auth_info = await self._auth_service.get_token_info(server_id)
                    server['is_authenticated'] = auth_info is not None
                    server['auth_expires_at'] = auth_info.get('expires_at') if auth_info else None
                    
                    # Sanitizar URLs para logs/respuesta
                    server['api_url'] = sanitize_url(server['api_url'])
                    server['rtsp_url'] = sanitize_url(server['rtsp_url'])
                    
                    # No incluir contraseña en respuesta
                    server.pop('password_encrypted', None)
            
            self.logger.info(
                f"Obtenidos {len(paginated_servers)} servidores "
                f"(página {page}/{max(1, (total + page_size - 1) // page_size)})"
            )
            
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'items': paginated_servers
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo servidores: {str(e)}")
            await self.set_error(f"Error obteniendo servidores: {str(e)}")
            raise
        finally:
            await self.set_busy(False)
    
    async def get_server(self, server_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene detalles de un servidor específico.
        
        Args:
            server_id: ID del servidor
            
        Returns:
            Dict con información del servidor o None si no existe
        """
        try:
            await self.set_busy(True)
            
            # Obtener servidor de BD
            server = await self._db_service.get_server_by_id(server_id)
            if not server:
                return None
            
            # Enriquecer con estado de autenticación
            auth_info = await self._auth_service.get_token_info(server_id)
            server['is_authenticated'] = auth_info is not None
            server['auth_expires_at'] = auth_info.get('expires_at') if auth_info else None
            
            # Obtener métricas agregadas
            metrics = await self._db_service.get_server_metrics(server_id)
            server['metrics'] = metrics
            
            # Sanitizar URLs
            server['api_url'] = sanitize_url(server['api_url'])
            server['rtsp_url'] = sanitize_url(server['rtsp_url'])
            
            # No incluir contraseña
            server.pop('password_encrypted', None)
            
            self.logger.info(f"Obtenido servidor {server_id}: {server['server_name']}")
            
            return server
            
        except Exception as e:
            self.logger.error(f"Error obteniendo servidor {server_id}: {str(e)}")
            await self.set_error(f"Error obteniendo servidor: {str(e)}")
            raise
        finally:
            await self.set_busy(False)
    
    async def create_server(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo servidor MediaMTX.
        
        Args:
            server_data: Datos del servidor a crear
            
        Returns:
            Dict con información del servidor creado
            
        Raises:
            ValidationError: Si los datos son inválidos
            ServiceError: Si hay error al crear
        """
        try:
            await self.set_busy(True)
            
            # Validar datos requeridos
            required_fields = ['server_name', 'api_url', 'rtsp_url']
            for field in required_fields:
                if field not in server_data or not server_data[field]:
                    raise ValidationError(f"El campo {field} es requerido")
            
            # Validar URLs
            api_url = server_data['api_url']
            rtsp_url = server_data['rtsp_url']
            
            if not api_url.startswith(('http://', 'https://')):
                raise ValidationError("API URL debe comenzar con http:// o https://")
            
            if not rtsp_url.startswith('rtsp://'):
                raise ValidationError("RTSP URL debe comenzar con rtsp://")
            
            # Verificar que el nombre sea único
            existing_servers = await self._db_service.get_servers()
            for server in existing_servers:
                if server['server_name'].lower() == server_data['server_name'].lower():
                    raise ValidationError(f"Ya existe un servidor con el nombre '{server_data['server_name']}'")
            
            # Preparar datos para inserción
            server_to_create = {
                'server_name': server_data['server_name'],
                'rtsp_url': rtsp_url,
                'rtsp_port': server_data.get('rtsp_port', 8554),
                'api_url': api_url,
                'api_port': server_data.get('api_port', 8000),
                'api_enabled': server_data.get('api_enabled', True),
                'username': server_data.get('username'),
                'password': server_data.get('password'),
                'auth_enabled': server_data.get('auth_enabled', True),
                'use_tcp': server_data.get('use_tcp', True),
                'max_reconnects': server_data.get('max_reconnects', 3),
                'reconnect_delay': server_data.get('reconnect_delay', 5.0),
                'publish_path_template': server_data.get('publish_path_template', 'ucv_{camera_code}'),
                'is_active': server_data.get('is_active', True),
                'is_default': server_data.get('is_default', False),
                'health_check_interval': server_data.get('health_check_interval', 30),
                'metadata': server_data.get('metadata', {})
            }
            
            # Crear servidor en la base de datos
            server_id = await self._db_service.create_server(server_to_create)
            
            # Obtener el servidor recién creado
            created_server = await self._db_service.get_server_by_id(server_id)
            
            if not created_server:
                raise ServiceError("Error obteniendo servidor después de crearlo")
            
            # Emitir evento de servidor creado
            await self._emit_event("server_created", {
                'server_id': server_id,
                'server_name': created_server['server_name'],
                'api_url': sanitize_url(created_server['api_url'])
            })
            
            # Formatear respuesta
            return {
                'server_id': created_server['server_id'],
                'server_name': created_server['server_name'],
                'api_url': sanitize_url(created_server['api_url']),
                'rtsp_url': sanitize_url(created_server['rtsp_url']),
                'rtsp_port': created_server['rtsp_port'],
                'api_port': created_server['api_port'],
                'is_active': created_server['is_active'],
                'is_default': created_server['is_default'],
                'is_authenticated': False,
                'auth_expires_at': None,
                'last_health_status': created_server['last_health_status'],
                'last_health_check': created_server['last_health_check'],
                'created_at': created_server['created_at'],
                'updated_at': created_server['updated_at'],
                'metrics': {
                    'total_publications': 0,
                    'active_publications': 0,
                    'total_cameras': 0,
                    'last_publication': None
                }
            }
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creando servidor: {str(e)}")
            await self.set_error(f"Error creando servidor: {str(e)}")
            raise ServiceError(f"Error creando servidor: {str(e)}")
        finally:
            await self.set_busy(False)
    
    async def update_server(
        self, 
        server_id: int, 
        server_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza un servidor MediaMTX existente.
        
        Args:
            server_id: ID del servidor a actualizar
            server_data: Datos a actualizar
            
        Returns:
            Dict con información del servidor actualizado
            
        Raises:
            ValidationError: Si los datos son inválidos
            ServiceError: Si hay error al actualizar
        """
        try:
            await self.set_busy(True)
            
            # Verificar que el servidor existe
            existing_server = await self._db_service.get_server_by_id(server_id)
            if not existing_server:
                raise ValidationError(f"Servidor {server_id} no encontrado")
            
            # Validar URLs si se proporcionan
            if 'api_url' in server_data:
                api_url = server_data['api_url']
                if api_url and not api_url.startswith(('http://', 'https://')):
                    raise ValidationError("API URL debe comenzar con http:// o https://")
            
            if 'rtsp_url' in server_data:
                rtsp_url = server_data['rtsp_url']
                if rtsp_url and not rtsp_url.startswith('rtsp://'):
                    raise ValidationError("RTSP URL debe comenzar con rtsp://")
            
            # Si se actualiza el nombre, verificar que sea único
            if 'server_name' in server_data:
                new_name = server_data['server_name']
                if new_name != existing_server['server_name']:
                    servers = await self._db_service.get_servers()
                    for server in servers:
                        if (server['server_name'].lower() == new_name.lower() and 
                            server['server_id'] != server_id):
                            raise ValidationError(f"Ya existe un servidor con el nombre '{new_name}'")
            
            # Actualizar servidor en la base de datos
            success = await self._db_service.update_server(server_id, server_data)
            
            if not success:
                raise ServiceError("No se pudo actualizar el servidor")
            
            # Si cambian credenciales o URL, invalidar token de autenticación
            credential_fields = ['username', 'password', 'api_url']
            if any(field in server_data for field in credential_fields):
                self.logger.info(f"Credenciales modificadas, invalidando token para servidor {server_id}")
                try:
                    await self._auth_service.logout(server_id)
                except Exception as e:
                    self.logger.warning(f"Error invalidando token: {e}")
            
            # Obtener servidor actualizado
            updated_server = await self._db_service.get_server_by_id(server_id)
            if not updated_server:
                raise ServiceError("Error obteniendo servidor después de actualizar")
            
            # Emitir evento de servidor actualizado
            await self._emit_event("server_updated", {
                'server_id': server_id,
                'server_name': updated_server['server_name'],
                'fields_updated': list(server_data.keys())
            })
            
            # Obtener estado de autenticación
            auth_info = await self._auth_service.get_token_info(server_id)
            
            # Obtener métricas
            metrics = await self._db_service.get_server_metrics(server_id)
            
            # Formatear respuesta
            return {
                'server_id': updated_server['server_id'],
                'server_name': updated_server['server_name'],
                'api_url': sanitize_url(updated_server['api_url']),
                'rtsp_url': sanitize_url(updated_server['rtsp_url']),
                'is_active': updated_server['is_active'],
                'is_default': updated_server['is_default'],
                'is_authenticated': auth_info is not None,
                'auth_expires_at': auth_info.get('expires_at') if auth_info else None,
                'last_health_status': updated_server['last_health_status'],
                'last_health_check': updated_server['last_health_check'],
                'created_at': updated_server['created_at'],
                'updated_at': updated_server['updated_at'],
                'metrics': metrics
            }
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando servidor {server_id}: {str(e)}")
            await self.set_error(f"Error actualizando servidor: {str(e)}")
            raise ServiceError(f"Error actualizando servidor: {str(e)}")
        finally:
            await self.set_busy(False)
    
    async def delete_server(self, server_id: int) -> bool:
        """
        Elimina un servidor MediaMTX.
        
        Args:
            server_id: ID del servidor a eliminar
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            ValidationError: Si el servidor no puede eliminarse
            ServiceError: Si hay error al eliminar
        """
        try:
            await self.set_busy(True)
            
            # Verificar que el servidor existe
            server = await self._db_service.get_server_by_id(server_id)
            if not server:
                raise ValidationError(f"Servidor {server_id} no encontrado")
            
            # Verificar que no tenga publicaciones activas
            metrics = await self._db_service.get_server_metrics(server_id)
            if metrics.get('active_publications', 0) > 0:
                raise ValidationError(
                    f"No se puede eliminar el servidor porque tiene {metrics['active_publications']} publicaciones activas"
                )
            
            # Limpiar tokens de autenticación
            try:
                await self._auth_service.logout(server_id)
            except Exception as e:
                self.logger.warning(f"Error limpiando tokens para servidor {server_id}: {e}")
            
            # Eliminar servidor de la base de datos
            success = await self._db_service.delete_server(server_id)
            
            if not success:
                raise ServiceError("No se pudo eliminar el servidor")
            
            # Emitir evento de servidor eliminado
            await self._emit_event("server_deleted", {
                'server_id': server_id,
                'server_name': server['server_name']
            })
            
            self.logger.info(f"Servidor {server_id} ({server['server_name']}) eliminado")
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error eliminando servidor {server_id}: {str(e)}")
            await self.set_error(f"Error eliminando servidor: {str(e)}")
            raise ServiceError(f"Error eliminando servidor: {str(e)}")
        finally:
            await self.set_busy(False)
    
    async def test_connection(self, server_id: int) -> Dict[str, Any]:
        """
        Prueba la conexión con un servidor MediaMTX.
        
        Args:
            server_id: ID del servidor a probar
            
        Returns:
            Dict con resultado de la prueba:
            - success: bool indicando si la conexión fue exitosa
            - message: mensaje descriptivo
            - details: detalles adicionales (opcional)
            - latency_ms: latencia en milisegundos (si exitoso)
        """
        try:
            await self.set_busy(True)
            
            # Obtener servidor
            server = await self._db_service.get_server_by_id(server_id)
            if not server:
                raise ValidationError(f"Servidor {server_id} no encontrado")
            
            self.logger.info(f"Probando conexión con servidor {server['server_name']}")
            
            # Intentar autenticar para probar conexión
            start_time = datetime.utcnow()
            
            try:
                # Si tiene credenciales, intentar autenticar
                if server['username'] and server['auth_enabled']:
                    # Necesitamos la contraseña desencriptada
                    # TODO: El servicio de auth debería manejar esto internamente
                    result = await self._auth_service.validate_server_connection(
                        server_id,
                        test_auth=True
                    )
                else:
                    # Solo probar conectividad básica
                    result = await self._auth_service.validate_server_connection(
                        server_id,
                        test_auth=False
                    )
                
                end_time = datetime.utcnow()
                latency_ms = int((end_time - start_time).total_seconds() * 1000)
                
                if result:
                    return {
                        'success': True,
                        'message': 'Conexión exitosa',
                        'latency_ms': latency_ms,
                        'details': {
                            'server_name': server['server_name'],
                            'api_url': sanitize_url(server['api_url']),
                            'auth_required': server['auth_enabled']
                        }
                    }
                else:
                    return {
                        'success': False,
                        'message': 'No se pudo conectar con el servidor',
                        'details': {
                            'server_name': server['server_name'],
                            'api_url': sanitize_url(server['api_url'])
                        }
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Error de conexión: {str(e)}',
                    'details': {
                        'server_name': server['server_name'],
                        'error': str(e)
                    }
                }
                
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error probando conexión con servidor {server_id}: {str(e)}")
            await self.set_error(f"Error probando conexión: {str(e)}")
            raise ServiceError(f"Error probando conexión: {str(e)}")
        finally:
            await self.set_busy(False)
    
    async def get_server_status(self, server_id: int) -> Dict[str, Any]:
        """
        Obtiene el estado detallado de un servidor.
        
        Args:
            server_id: ID del servidor
            
        Returns:
            Dict con estado detallado y métricas
        """
        try:
            await self.set_busy(True)
            
            # Obtener información básica
            server = await self.get_server(server_id)
            if not server:
                raise ValidationError(f"Servidor {server_id} no encontrado")
            
            # Agregar información de estado adicional
            status = {
                'server': server,
                'connection': {
                    'is_online': False,  # TODO: Implementar verificación real
                    'last_check': datetime.utcnow().isoformat(),
                    'response_time_ms': None
                },
                'authentication': {
                    'is_authenticated': server['is_authenticated'],
                    'expires_at': server['auth_expires_at']
                },
                'publications': {
                    'active': 0,  # TODO: Obtener de BD
                    'total_today': 0,
                    'total_week': 0
                },
                'health': {
                    'status': server.get('last_health_status', 'unknown'),
                    'last_check': server.get('last_health_check'),
                    'uptime_percent': 0.0  # TODO: Calcular desde histórico
                }
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del servidor {server_id}: {str(e)}")
            await self.set_error(f"Error obteniendo estado: {str(e)}")
            raise
        finally:
            await self.set_busy(False)


# Singleton instance
_presenter_instance = None


def get_mediamtx_servers_presenter() -> MediaMTXServersPresenter:
    """
    Obtiene la instancia singleton del presenter.
    
    Returns:
        MediaMTXServersPresenter singleton
    """
    global _presenter_instance
    
    if _presenter_instance is None:
        _presenter_instance = MediaMTXServersPresenter()
    
    return _presenter_instance