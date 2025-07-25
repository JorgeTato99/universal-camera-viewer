"""
Servicio de autenticación para servidores MediaMTX remotos.

Este servicio gestiona:
- Autenticación JWT con servidores remotos
- Almacenamiento seguro de tokens
- Refresco automático de tokens
- Gestión del ciclo de vida de tokens
"""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import jwt
from urllib.parse import urljoin

from services.base_service import BaseService
from services.encryption_service_v2 import EncryptionServiceV2
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.logging_service import get_secure_logger
from utils.exceptions import ServiceError, MediaMTXAPIError
from utils.sanitizers import sanitize_url


logger = get_secure_logger("services.mediamtx.auth_service")


class AuthToken:
    """Representa un token de autenticación JWT."""
    
    def __init__(
        self,
        access_token: str,
        token_type: str = "bearer",
        expires_at: Optional[datetime] = None,
        refresh_token: Optional[str] = None,
        refresh_expires_at: Optional[datetime] = None,
        username: Optional[str] = None,
        role: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        self.access_token = access_token
        self.token_type = token_type
        self.expires_at = expires_at or self._extract_expiry(access_token)
        self.refresh_token = refresh_token
        self.refresh_expires_at = refresh_expires_at
        self.username = username
        self.role = role
        self.user_id = user_id
        
    def _extract_expiry(self, token: str) -> Optional[datetime]:
        """Extrae la fecha de expiración del JWT."""
        try:
            # Decodificar sin verificar (solo para leer claims)
            payload = jwt.decode(token, options={"verify_signature": False})
            if 'exp' in payload:
                return datetime.fromtimestamp(payload['exp'])
        except Exception:
            pass
        # Por defecto, asumir 6 meses como en el test
        return datetime.utcnow() + timedelta(days=180)
    
    @property
    def is_expired(self) -> bool:
        """Verifica si el token está expirado."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at
    
    @property
    def needs_refresh(self) -> bool:
        """Verifica si el token necesita refresco (80% del tiempo de vida)."""
        if not self.expires_at:
            return False
        
        # Calcular tiempo restante
        time_remaining = self.expires_at - datetime.utcnow()
        
        # Refrescar cuando quede menos del 20% del tiempo o menos de 1 hora
        if time_remaining <= timedelta(hours=1):
            return True
            
        # Para tokens de larga duración (6 meses), refrescar cuando quede 20%
        total_seconds = (self.expires_at - datetime.utcnow()).total_seconds()
        if total_seconds > 0:
            # Asumiendo que el token fue creado hace poco, estimar vida total
            # Para tokens de 6 meses, refrescar cuando queden ~36 días
            return time_remaining <= timedelta(days=36)
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para persistencia."""
        return {
            'access_token': self.access_token,
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'refresh_token': self.refresh_token,
            'refresh_expires_at': self.refresh_expires_at.isoformat() if self.refresh_expires_at else None,
            'username': self.username,
            'role': self.role,
            'user_id': self.user_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthToken':
        """Crea desde diccionario."""
        return cls(
            access_token=data['access_token'],
            token_type=data.get('token_type', 'bearer'),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            refresh_token=data.get('refresh_token'),
            refresh_expires_at=datetime.fromisoformat(data['refresh_expires_at']) if data.get('refresh_expires_at') else None,
            username=data.get('username'),
            role=data.get('role'),
            user_id=data.get('user_id')
        )


class MediaMTXAuthService(BaseService):
    """
    Servicio de autenticación para servidores MediaMTX remotos.
    
    Gestiona el ciclo completo de autenticación:
    - Login con credenciales
    - Almacenamiento seguro de tokens
    - Refresco automático
    - Validación de tokens
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """Garantiza singleton thread-safe."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el servicio de autenticación."""
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        self.logger = logger
        
        # Servicios dependientes
        self._encryption_service = EncryptionServiceV2()
        self._db_service = get_mediamtx_db_service()
        
        # Cache de tokens en memoria
        self._token_cache: Dict[int, AuthToken] = {}
        
        # Tareas de refresco automático
        self._refresh_tasks: Dict[int, asyncio.Task] = {}
        
        # Cliente HTTP compartido
        self._session: Optional[aiohttp.ClientSession] = None
        
        self._initialized = False
        
    async def initialize(self) -> None:
        """Inicializa el servicio y carga tokens existentes."""
        if self._initialized:
            return
            
        self.logger.info("Inicializando MediaMTXAuthService")
        
        # Crear sesión HTTP
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'UniversalCameraViewer/0.9.17'}
        )
        
        # Cargar tokens activos de la base de datos
        await self._load_active_tokens()
        
        self._initialized = True
        self.logger.info("MediaMTXAuthService inicializado correctamente")
    
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        self.logger.info("Limpiando MediaMTXAuthService")
        
        # Cancelar tareas de refresco
        for task in self._refresh_tasks.values():
            task.cancel()
        
        # Esperar a que terminen
        if self._refresh_tasks:
            await asyncio.gather(*self._refresh_tasks.values(), return_exceptions=True)
        
        # Cerrar sesión HTTP
        if self._session:
            await self._session.close()
        
        self._token_cache.clear()
        self._refresh_tasks.clear()
        self._initialized = False
    
    async def login(
        self,
        server_id: int,
        username: str,
        password: str,
        api_url: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Autentica con un servidor MediaMTX remoto.
        
        Args:
            server_id: ID del servidor en la BD
            username: Nombre de usuario
            password: Contraseña
            api_url: URL base de la API (ej: http://31.220.104.212:8000)
            
        Returns:
            Tupla (éxito, mensaje_error)
        """
        try:
            # Construir URL de login
            login_url = urljoin(api_url.rstrip('/') + '/', 'api/v1/auth/login')
            
            self.logger.info(f"Autenticando con servidor {server_id} en {sanitize_url(login_url)}")
            
            # Preparar payload
            payload = {
                "username": username,
                "password": password
            }
            
            # Realizar petición
            async with self._session.post(login_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Crear objeto token
                    token = AuthToken(
                        access_token=data['access_token'],
                        token_type=data.get('token_type', 'bearer'),
                        username=data.get('username', username),
                        role=data.get('role'),
                        user_id=data.get('user_id')
                    )
                    
                    # Guardar en cache
                    self._token_cache[server_id] = token
                    
                    # Persistir en BD (encriptado)
                    await self._save_token(server_id, token)
                    
                    # Programar refresco automático
                    await self._schedule_token_refresh(server_id)
                    
                    self.logger.info(f"Autenticación exitosa para servidor {server_id}")
                    return True, None
                    
                else:
                    error_text = await response.text()
                    self.logger.warning(f"Error de autenticación: {response.status} - {error_text}")
                    
                    if response.status == 401:
                        return False, "Credenciales inválidas"
                    elif response.status == 404:
                        return False, "Endpoint de login no encontrado"
                    else:
                        return False, f"Error del servidor: {response.status}"
                        
        except aiohttp.ClientError as e:
            self.logger.error(f"Error de conexión: {str(e)}")
            return False, f"Error de conexión: {str(e)}"
            
        except Exception as e:
            self.logger.error(f"Error inesperado durante login: {str(e)}")
            return False, f"Error inesperado: {str(e)}"
    
    async def get_valid_token(self, server_id: int) -> Optional[str]:
        """
        Obtiene un token válido para el servidor.
        
        Si el token está expirado o próximo a expirar, intenta refrescarlo.
        
        Args:
            server_id: ID del servidor
            
        Returns:
            Token de acceso válido o None si no hay
        """
        # Verificar cache
        if server_id in self._token_cache:
            token = self._token_cache[server_id]
            
            if not token.is_expired:
                # Actualizar último uso
                await self._update_last_used(server_id)
                return token.access_token
            else:
                self.logger.warning(f"Token expirado para servidor {server_id}")
        
        # Intentar cargar de BD
        token = await self._load_token(server_id)
        if token and not token.is_expired:
            self._token_cache[server_id] = token
            await self._update_last_used(server_id)
            return token.access_token
        
        # No hay token válido
        self.logger.warning(f"No hay token válido para servidor {server_id}")
        return None
    
    async def refresh_token(self, server_id: int) -> Tuple[bool, Optional[str]]:
        """
        Refresca el token de un servidor.
        
        Args:
            server_id: ID del servidor
            
        Returns:
            Tupla (éxito, mensaje_error)
        """
        # TODO: Implementar cuando MediaMTX soporte refresh tokens
        # Por ahora, MediaMTX no implementa refresh tokens estándar
        self.logger.warning("Refresh de tokens no implementado en MediaMTX actual")
        return False, "Refresh de tokens no soportado"
    
    async def logout(self, server_id: int) -> None:
        """
        Cierra sesión y elimina tokens de un servidor.
        
        Args:
            server_id: ID del servidor
        """
        self.logger.info(f"Cerrando sesión para servidor {server_id}")
        
        # Cancelar tarea de refresco
        if server_id in self._refresh_tasks:
            self._refresh_tasks[server_id].cancel()
            del self._refresh_tasks[server_id]
        
        # Eliminar de cache
        if server_id in self._token_cache:
            del self._token_cache[server_id]
        
        # Marcar como inactivo en BD
        await self._deactivate_token(server_id)
    
    async def get_auth_headers(self, server_id: int) -> Optional[Dict[str, str]]:
        """
        Obtiene headers de autenticación para peticiones HTTP.
        
        Args:
            server_id: ID del servidor
            
        Returns:
            Dict con headers o None si no hay token
        """
        token = await self.get_valid_token(server_id)
        if not token:
            return None
            
        return {
            'Authorization': f'Bearer {token}'
        }
    
    async def get_token_info(self, server_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene información sobre el token de un servidor.
        
        Args:
            server_id: ID del servidor
            
        Returns:
            Dict con información del token o None si no existe
        """
        try:
            # Primero verificar cache
            if server_id in self._token_cache:
                token = self._token_cache[server_id]
                return {
                    'server_id': server_id,
                    'expires_at': token.expires_at.isoformat() if token.expires_at else None,
                    'is_expired': token.is_expired,
                    'username': token.username,
                    'role': token.role,
                    'user_id': token.user_id
                }
            
            # Si no está en cache, intentar cargar de BD
            token_data = await self._db_service.get_auth_token(server_id)
            if token_data:
                # No desencriptar el token completo, solo devolver metadatos
                expires_at = token_data.get('expires_at')
                created_at = token_data.get('created_at')
                
                return {
                    'server_id': server_id,
                    'expires_at': expires_at.isoformat() if expires_at and hasattr(expires_at, 'isoformat') else expires_at,
                    'created_at': created_at.isoformat() if created_at and hasattr(created_at, 'isoformat') else created_at,
                    'username': token_data.get('username'),
                    'role': token_data.get('role'),
                    'user_id': token_data.get('user_id'),
                    'is_active': token_data.get('is_active', True)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información del token: {str(e)}")
            return None
    
    async def validate_token(self, server_id: int, api_url: str) -> Tuple[bool, Optional[str]]:
        """
        Valida un token realizando una petición de prueba a la API.
        
        Args:
            server_id: ID del servidor
            api_url: URL base de la API
            
        Returns:
            Tupla (válido, mensaje_error)
        """
        try:
            # Obtener token actual
            token = await self.get_valid_token(server_id)
            if not token:
                return False, "No hay token disponible"
            
            # Headers de autorización
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Construir URL de validación - usamos el endpoint de cámaras
            validate_url = urljoin(api_url.rstrip('/') + '/', 'api/v1/cameras')
            
            self.logger.info(f"Validando token para servidor {server_id} con {sanitize_url(validate_url)}")
            
            # Realizar petición GET
            async with self._session.get(validate_url, headers=headers) as response:
                if response.status == 200:
                    # Token válido
                    data = await response.json()
                    self.logger.info(f"Token válido para servidor {server_id}, {len(data.get('cameras', []))} cámaras encontradas")
                    return True, None
                    
                elif response.status == 401:
                    # Token inválido o expirado
                    self.logger.warning(f"Token inválido/expirado para servidor {server_id}")
                    # Eliminar token del cache
                    if server_id in self._token_cache:
                        del self._token_cache[server_id]
                    return False, "Token inválido o expirado"
                    
                else:
                    error_text = await response.text()
                    self.logger.warning(f"Error validando token: {response.status} - {error_text}")
                    return False, f"Error del servidor: {response.status}"
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Error de conexión validando token: {str(e)}")
            return False, f"Error de conexión: {str(e)}"
            
        except Exception as e:
            self.logger.error(f"Error inesperado validando token: {str(e)}")
            return False, f"Error inesperado: {str(e)}"
    
    # === Métodos privados ===
    
    async def _load_active_tokens(self) -> None:
        """Carga tokens activos desde la base de datos."""
        try:
            tokens = await self._db_service.get_active_auth_tokens()
            
            for token_data in tokens:
                server_id = token_data['server_id']
                
                # Desencriptar token
                encrypted_token = token_data['access_token']
                decrypted_token = self._encryption_service.decrypt(encrypted_token)
                
                # Convertir expires_at a datetime si es string
                expires_at = token_data.get('expires_at')
                if expires_at and isinstance(expires_at, str):
                    try:
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    except:
                        expires_at = None
                
                # Crear objeto token
                token = AuthToken(
                    access_token=decrypted_token,
                    token_type=token_data.get('token_type', 'bearer'),
                    expires_at=expires_at,
                    username=token_data.get('username'),
                    role=token_data.get('role'),
                    user_id=token_data.get('user_id')
                )
                
                # Solo cargar si no está expirado
                if not token.is_expired:
                    self._token_cache[server_id] = token
                    await self._schedule_token_refresh(server_id)
                    
            self.logger.info(f"Cargados {len(self._token_cache)} tokens activos")
            
        except Exception as e:
            self.logger.error(f"Error cargando tokens: {str(e)}")
    
    async def _save_token(self, server_id: int, token: AuthToken) -> None:
        """Guarda un token en la base de datos (encriptado)."""
        try:
            # Encriptar token
            encrypted_token = self._encryption_service.encrypt(token.access_token)
            
            # Preparar datos
            token_data = {
                'server_id': server_id,
                'access_token': encrypted_token,
                'token_type': token.token_type,
                'expires_at': token.expires_at,
                'refresh_token': self._encryption_service.encrypt(token.refresh_token) if token.refresh_token else None,
                'refresh_expires_at': token.refresh_expires_at,
                'username': token.username,
                'role': token.role,
                'user_id': token.user_id
            }
            
            # Guardar en BD
            await self._db_service.save_auth_token(token_data)
            
        except Exception as e:
            self.logger.error(f"Error guardando token: {str(e)}")
            raise ServiceError(f"Error guardando token: {str(e)}", error_code="TOKEN_SAVE_ERROR")
    
    async def _load_token(self, server_id: int) -> Optional[AuthToken]:
        """Carga un token desde la base de datos."""
        try:
            token_data = await self._db_service.get_auth_token(server_id)
            if not token_data:
                return None
            
            # Desencriptar
            decrypted_token = self._encryption_service.decrypt(token_data['access_token'])
            
            # Convertir expires_at de string a datetime si es necesario
            expires_at = token_data.get('expires_at')
            if expires_at and isinstance(expires_at, str):
                try:
                    # Intentar parsear el datetime
                    if expires_at.endswith('Z'):
                        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    else:
                        expires_at = datetime.fromisoformat(expires_at)
                except:
                    self.logger.warning(f"No se pudo parsear expires_at: {expires_at}")
                    expires_at = None
            
            # Crear objeto
            return AuthToken(
                access_token=decrypted_token,
                token_type=token_data.get('token_type', 'bearer'),
                expires_at=expires_at,
                username=token_data.get('username'),
                role=token_data.get('role'),
                user_id=token_data.get('user_id')
            )
            
        except Exception as e:
            self.logger.error(f"Error cargando token: {str(e)}")
            return None
    
    async def _schedule_token_refresh(self, server_id: int) -> None:
        """
        Programa la verificación y renovación proactiva de un token.
        
        Como MediaMTX no soporta refresh tokens, implementamos verificación
        periódica y re-autenticación proactiva antes de que expire.
        """
        # Cancelar tarea existente si hay
        if server_id in self._refresh_tasks:
            self._refresh_tasks[server_id].cancel()
            
        # Obtener token del cache
        token = self._token_cache.get(server_id)
        if not token or not token.expires_at:
            return
            
        # Calcular cuándo verificar (cuando quede 20% del tiempo o 1 hora)
        time_remaining = token.expires_at - datetime.utcnow()
        
        # Para tokens de 6 meses, verificar cuando queden ~36 días
        if time_remaining > timedelta(days=36):
            check_in = time_remaining - timedelta(days=36)
        elif time_remaining > timedelta(hours=1):
            # Para tokens más cortos, verificar cuando quede 20%
            check_in = timedelta(seconds=time_remaining.total_seconds() * 0.8)
        else:
            # Si queda menos de 1 hora, verificar en 30 minutos
            check_in = timedelta(minutes=30)
            
        self.logger.info(
            f"Programando verificación de token para servidor {server_id} "
            f"en {check_in.total_seconds() / 3600:.1f} horas"
        )
        
        # Crear tarea de verificación
        task = asyncio.create_task(self._token_check_task(server_id, check_in))
        self._refresh_tasks[server_id] = task
        
    async def _token_check_task(self, server_id: int, delay: timedelta) -> None:
        """
        Tarea que verifica y renueva el token cuando sea necesario.
        
        Args:
            server_id: ID del servidor
            delay: Tiempo de espera antes de verificar
        """
        try:
            # Esperar el tiempo calculado
            await asyncio.sleep(delay.total_seconds())
            
            # Verificar si el token sigue siendo válido
            token = self._token_cache.get(server_id)
            if not token:
                return
                
            self.logger.info(f"Verificando token para servidor {server_id}")
            
            # Si el token necesita renovación
            if token.needs_refresh:
                self.logger.warning(
                    f"Token para servidor {server_id} necesita renovación "
                    f"(expira en {(token.expires_at - datetime.utcnow()).days} días)"
                )
                
                # Emitir evento para que el presenter maneje la renovación
                # TODO: Implementar sistema de eventos cuando sea necesario
                # Por ahora solo registramos en log
                
            # Reprogramar siguiente verificación
            await self._schedule_token_refresh(server_id)
            
        except asyncio.CancelledError:
            self.logger.debug(f"Tarea de verificación cancelada para servidor {server_id}")
        except Exception as e:
            self.logger.error(f"Error en tarea de verificación: {str(e)}")
    
    async def _update_last_used(self, server_id: int) -> None:
        """Actualiza el timestamp de último uso del token."""
        try:
            await self._db_service.update_token_last_used(server_id)
        except Exception as e:
            self.logger.error(f"Error actualizando último uso: {str(e)}")
    
    async def _deactivate_token(self, server_id: int) -> None:
        """Marca un token como inactivo en la BD."""
        try:
            await self._db_service.deactivate_auth_token(server_id)
        except Exception as e:
            self.logger.error(f"Error desactivando token: {str(e)}")


# Instancia singleton
_auth_service: Optional[MediaMTXAuthService] = None


def get_auth_service() -> MediaMTXAuthService:
    """
    Obtiene la instancia singleton del servicio de autenticación.
    
    Returns:
        MediaMTXAuthService singleton
    """
    global _auth_service
    
    if _auth_service is None:
        _auth_service = MediaMTXAuthService()
        
    return _auth_service