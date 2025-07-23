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
from services.encryption_service_v2 import get_encryption_service
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
        
        total_lifetime = self.expires_at - datetime.utcnow()
        threshold = total_lifetime * 0.8
        return datetime.utcnow() >= (self.expires_at - threshold)
    
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
        self._encryption_service = get_encryption_service()
        self._db_service = get_mediamtx_db_service()
        
        # Cache de tokens en memoria
        self._token_cache: Dict[int, AuthToken] = {}
        
        # Tareas de refresco automático
        self._refresh_tasks: Dict[int, asyncio.Task] = {}
        
        # Cliente HTTP compartido
        self._session: Optional[aiohttp.ClientSession] = None
        
        self._initialized = True
        
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
                
                # Crear objeto token
                token = AuthToken(
                    access_token=decrypted_token,
                    token_type=token_data.get('token_type', 'bearer'),
                    expires_at=token_data.get('expires_at'),
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
            
            # Crear objeto
            return AuthToken(
                access_token=decrypted_token,
                token_type=token_data.get('token_type', 'bearer'),
                expires_at=token_data.get('expires_at'),
                username=token_data.get('username'),
                role=token_data.get('role'),
                user_id=token_data.get('user_id')
            )
            
        except Exception as e:
            self.logger.error(f"Error cargando token: {str(e)}")
            return None
    
    async def _schedule_token_refresh(self, server_id: int) -> None:
        """Programa el refresco automático de un token."""
        # Cancelar tarea existente si hay
        if server_id in self._refresh_tasks:
            self._refresh_tasks[server_id].cancel()
        
        # TODO: Implementar cuando MediaMTX soporte refresh tokens
        # Por ahora no programamos refresco automático
        self.logger.debug(f"Refresco automático no implementado para servidor {server_id}")
    
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