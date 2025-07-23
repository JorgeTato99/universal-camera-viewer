"""
Cliente HTTP base para MediaMTX API.

Proporciona funcionalidad compartida para todos los clientes de API:
- Gestión de sesiones HTTP
- Autenticación automática
- Manejo de errores consistente
- Retry con backoff exponencial
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, Type, TypeVar, Union
from urllib.parse import urljoin
import json

from services.base_service import BaseService
from services.mediamtx.auth_service import get_auth_service
from services.logging_service import get_secure_logger
from utils.exceptions import (
    ServiceError, 
    MediaMTXAPIError, 
    MediaMTXConnectionError,
    MediaMTXAuthenticationError
)
from utils.sanitizers import sanitize_url


logger = get_secure_logger("services.mediamtx.api_base")

T = TypeVar('T')


class MediaMTXAPIBase(BaseService):
    """
    Cliente base para interactuar con la API de MediaMTX.
    
    Proporciona:
    - Gestión de sesión HTTP reutilizable
    - Autenticación automática con JWT
    - Reintentos con backoff exponencial
    - Manejo consistente de errores
    """
    
    def __init__(self):
        """Inicializa el cliente base."""
        super().__init__()
        self.logger = logger
        self._auth_service = get_auth_service()
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Configuración de reintentos
        self.max_retries = 3
        self.retry_delay = 1.0  # segundos
        self.retry_backoff = 2.0  # factor de multiplicación
        
    async def initialize(self) -> None:
        """Inicializa el cliente HTTP."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'UniversalCameraViewer/0.9.17',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )
    
    async def cleanup(self) -> None:
        """Limpia recursos del cliente."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _make_request(
        self,
        method: str,
        url: str,
        server_id: int,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Realiza una petición HTTP con autenticación y reintentos.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            url: URL completa del endpoint
            server_id: ID del servidor para autenticación
            data: Datos para el body (JSON)
            params: Parámetros de query string
            headers: Headers adicionales
            retry_count: Contador interno de reintentos
            
        Returns:
            Respuesta parseada como dict
            
        Raises:
            MediaMTXAPIError: Error de la API
            MediaMTXConnectionError: Error de conexión
            MediaMTXAuthenticationError: Error de autenticación
        """
        # Asegurar sesión inicializada
        if not self._session:
            await self.initialize()
        
        # Obtener headers de autenticación
        auth_headers = await self._auth_service.get_auth_headers(server_id)
        if not auth_headers:
            raise MediaMTXAuthenticationError(
                "No hay token de autenticación disponible",
                server_id=server_id
            )
        
        # Combinar headers
        request_headers = {**auth_headers}
        if headers:
            request_headers.update(headers)
        
        try:
            self.logger.debug(f"{method} {sanitize_url(url)}")
            
            async with self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers
            ) as response:
                response_text = await response.text()
                
                # Intentar parsear como JSON
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {'raw_response': response_text}
                
                # Manejar códigos de estado
                if response.status == 401:
                    # Token inválido/expirado
                    raise MediaMTXAuthenticationError(
                        "Token de autenticación inválido o expirado",
                        server_id=server_id
                    )
                
                elif response.status == 404:
                    raise MediaMTXAPIError(
                        f"Endpoint no encontrado: {method} {url}",
                        status_code=404,
                        response_data=response_data
                    )
                
                elif response.status >= 400:
                    # Error de cliente o servidor
                    error_msg = response_data.get('error', response_data.get('message', 'Error desconocido'))
                    raise MediaMTXAPIError(
                        f"Error de API: {error_msg}",
                        status_code=response.status,
                        response_data=response_data
                    )
                
                # Respuesta exitosa
                return response_data
                
        except aiohttp.ClientError as e:
            # Error de conexión - reintentar si es posible
            if retry_count < self.max_retries:
                delay = self.retry_delay * (self.retry_backoff ** retry_count)
                self.logger.warning(
                    f"Error de conexión, reintentando en {delay}s (intento {retry_count + 1}/{self.max_retries})"
                )
                await asyncio.sleep(delay)
                
                return await self._make_request(
                    method=method,
                    url=url,
                    server_id=server_id,
                    data=data,
                    params=params,
                    headers=headers,
                    retry_count=retry_count + 1
                )
            
            # Sin más reintentos
            raise MediaMTXConnectionError(
                f"Error de conexión después de {self.max_retries} intentos: {str(e)}",
                original_error=e
            )
            
        except MediaMTXAuthenticationError:
            # No reintentar errores de autenticación
            raise
            
        except MediaMTXAPIError as e:
            # Errores 5xx pueden ser transitorios, reintentar
            if e.status_code and e.status_code >= 500 and retry_count < self.max_retries:
                delay = self.retry_delay * (self.retry_backoff ** retry_count)
                self.logger.warning(
                    f"Error del servidor ({e.status_code}), reintentando en {delay}s"
                )
                await asyncio.sleep(delay)
                
                return await self._make_request(
                    method=method,
                    url=url,
                    server_id=server_id,
                    data=data,
                    params=params,
                    headers=headers,
                    retry_count=retry_count + 1
                )
            
            # No reintentar otros errores
            raise
    
    async def get(
        self,
        endpoint: str,
        server_id: int,
        base_url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Realiza una petición GET.
        
        Args:
            endpoint: Ruta del endpoint (ej: 'api/v1/cameras')
            server_id: ID del servidor para autenticación
            base_url: URL base del servidor
            params: Parámetros de query string
            headers: Headers adicionales
            
        Returns:
            Respuesta como diccionario
        """
        url = urljoin(base_url.rstrip('/') + '/', endpoint)
        return await self._make_request(
            method='GET',
            url=url,
            server_id=server_id,
            params=params,
            headers=headers
        )
    
    async def post(
        self,
        endpoint: str,
        server_id: int,
        base_url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Realiza una petición POST.
        
        Args:
            endpoint: Ruta del endpoint
            server_id: ID del servidor para autenticación
            base_url: URL base del servidor
            data: Datos para el body
            headers: Headers adicionales
            
        Returns:
            Respuesta como diccionario
        """
        url = urljoin(base_url.rstrip('/') + '/', endpoint)
        return await self._make_request(
            method='POST',
            url=url,
            server_id=server_id,
            data=data,
            headers=headers
        )
    
    async def put(
        self,
        endpoint: str,
        server_id: int,
        base_url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Realiza una petición PUT.
        
        Args:
            endpoint: Ruta del endpoint
            server_id: ID del servidor para autenticación
            base_url: URL base del servidor
            data: Datos para el body
            headers: Headers adicionales
            
        Returns:
            Respuesta como diccionario
        """
        url = urljoin(base_url.rstrip('/') + '/', endpoint)
        return await self._make_request(
            method='PUT',
            url=url,
            server_id=server_id,
            data=data,
            headers=headers
        )
    
    async def delete(
        self,
        endpoint: str,
        server_id: int,
        base_url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Realiza una petición DELETE.
        
        Args:
            endpoint: Ruta del endpoint
            server_id: ID del servidor para autenticación
            base_url: URL base del servidor
            headers: Headers adicionales
            
        Returns:
            Respuesta como diccionario
        """
        url = urljoin(base_url.rstrip('/') + '/', endpoint)
        return await self._make_request(
            method='DELETE',
            url=url,
            server_id=server_id,
            headers=headers
        )
    
    def build_url(self, base_url: str, *path_segments: str) -> str:
        """
        Construye una URL uniendo segmentos de forma segura.
        
        Args:
            base_url: URL base
            path_segments: Segmentos de la ruta
            
        Returns:
            URL completa
        """
        url = base_url.rstrip('/')
        for segment in path_segments:
            url = urljoin(url + '/', segment.lstrip('/'))
        return url