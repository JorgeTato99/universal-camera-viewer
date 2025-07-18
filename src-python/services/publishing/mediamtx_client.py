"""
Cliente asíncrono para la API REST de MediaMTX.

Proporciona acceso a las funcionalidades de gestión y monitoreo
del servidor MediaMTX.
"""

import aiohttp
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.publishing.mediamtx_models import PathInfo, PathList
from utils.exceptions import ServiceError


class MediaMTXClient:
    """
    Cliente para interactuar con la API de MediaMTX.
    
    Endpoints principales:
    - /v3/paths/list: Lista todos los paths
    - /v3/paths/get/{name}: Info de un path específico
    - /v3/paths/kick/{name}: Desconectar publisher/readers
    """
    
    def __init__(
        self,
        api_url: str,
        timeout: int = 10,
        max_retries: int = 3
    ):
        """
        Inicializa el cliente.
        
        Args:
            api_url: URL base de la API (ej: http://localhost:9997)
            timeout: Timeout para requests en segundos
            max_retries: Intentos máximos por request
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.logger = logging.getLogger(self.__class__.__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
        
    async def connect(self) -> None:
        """
        Establece la sesión HTTP.
        
        Crea una sesión reutilizable con configuración optimizada
        para múltiples requests concurrentes.
        
        Raises:
            RuntimeError: Si ya existe una sesión activa
        """
        if self._session and not self._session.closed:
            self.logger.warning("Ya existe una sesión activa, no se creará una nueva")
            return
            
        self.logger.debug(f"Creando sesión HTTP para MediaMTX API en {self.api_url}")
        
        try:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(
                    limit=10,
                    force_close=True,  # Cerrar conexiones después de cada request
                    enable_cleanup_closed=True  # Limpiar conexiones cerradas
                )
            )
            self.logger.info("Sesión HTTP establecida con MediaMTX")
            
        except Exception as e:
            self.logger.error(f"Error creando sesión HTTP: {e}")
            raise
            
    async def close(self) -> None:
        """
        Cierra la sesión HTTP.
        
        Asegura que todas las conexiones se cierren correctamente
        y libera los recursos asociados.
        """
        if self._session:
            self.logger.debug("Cerrando sesión HTTP con MediaMTX")
            try:
                await self._session.close()
                self._session = None
                self.logger.info("Sesión HTTP cerrada correctamente")
            except Exception as e:
                self.logger.error(f"Error cerrando sesión HTTP: {e}")
                # Forzar None aunque falle el cierre
                self._session = None
            
    async def check_health(self) -> bool:
        """
        Verifica que MediaMTX esté operativo.
        
        Realiza un health check rápido verificando la disponibilidad
        de la API sin procesar la respuesta completa.
        
        Returns:
            True si el servidor responde correctamente (HTTP 200)
            
        Raises:
            ServiceError: Si no hay sesión establecida
        """
        if not self._session or self._session.closed:
            raise ServiceError(
                "No hay sesión HTTP activa. Llama a connect() primero",
                error_code="NO_SESSION"
            )
            
        self.logger.debug("Verificando salud de MediaMTX")
        
        try:
            async with self._session.get(
                f"{self.api_url}/v3/paths/list",
                timeout=aiohttp.ClientTimeout(total=3)  # Timeout corto para health check
            ) as resp:
                is_healthy = resp.status == 200
                
                if is_healthy:
                    self.logger.debug("MediaMTX operativo")
                else:
                    self.logger.warning(f"MediaMTX no saludable: HTTP {resp.status}")
                    
                return is_healthy
                
        except asyncio.TimeoutError:
            self.logger.error("Timeout verificando salud de MediaMTX")
            return False
        except aiohttp.ClientError as e:
            self.logger.error(f"Error de conexión verificando salud: {e}")
            return False
        except Exception as e:
            self.logger.exception("Error inesperado verificando salud de MediaMTX")
            return False
            
    async def get_paths(self) -> List[PathInfo]:
        """
        Lista todos los paths activos.
        
        Obtiene la lista completa de paths registrados en MediaMTX,
        incluyendo información sobre publishers y readers.
        
        Returns:
            Lista de PathInfo con todos los paths activos
            
        Raises:
            ServiceError: Si hay error en la comunicación o respuesta
        """
        if not self._session or self._session.closed:
            raise ServiceError(
                "No hay sesión HTTP activa. Llama a connect() primero",
                error_code="NO_SESSION"
            )
            
        self.logger.debug("Obteniendo lista de paths desde MediaMTX")
        
        for attempt in range(self.max_retries):
            try:
                async with self._session.get(f"{self.api_url}/v3/paths/list") as resp:
                    if resp.status != 200:
                        error_body = await resp.text()
                        self.logger.error(f"Error HTTP {resp.status}: {error_body}")
                        raise ServiceError(
                            f"Error obteniendo paths: HTTP {resp.status}",
                            error_code="MEDIAMTX_API_ERROR"
                        )
                        
                    data = await resp.json()
                    
                    # Validar estructura de respuesta
                    if not isinstance(data, dict) or 'items' not in data:
                        self.logger.warning(f"Respuesta inesperada de MediaMTX: {data}")
                        data = {'items': {}}
                        
                    # MediaMTX devuelve un dict con los paths como keys
                    path_list = PathList(items=data.get('items', {}))
                    
                    self.logger.info(f"Obtenidos {len(path_list.paths)} paths activos")
                    return path_list.paths
                    
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout obteniendo paths (intento {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise ServiceError(
                        "Timeout obteniendo paths desde MediaMTX",
                        error_code="MEDIAMTX_TIMEOUT"
                    )
                await asyncio.sleep(1)  # Espera antes de reintentar
                
            except aiohttp.ClientError as e:
                self.logger.error(f"Error de conexión (intento {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise ServiceError(
                        f"Error de conexión con MediaMTX: {e}",
                        error_code="MEDIAMTX_CONNECTION_ERROR"
                    )
                await asyncio.sleep(1)
            
    async def get_path_info(self, name: str) -> Optional[PathInfo]:
        """
        Obtiene información de un path específico.
        
        Args:
            name: Nombre del path (sin /)
            
        Returns:
            PathInfo con detalles del path o None si no existe
            
        Raises:
            ValueError: Si el nombre del path es inválido
            ServiceError: Si hay error en la comunicación
        """
        if not name or not name.strip():
            raise ValueError("El nombre del path no puede estar vacío")
            
        if not self._session or self._session.closed:
            raise ServiceError(
                "No hay sesión HTTP activa. Llama a connect() primero",
                error_code="NO_SESSION"
            )
            
        # Limpiar nombre del path
        clean_name = name.strip().lstrip('/')
        self.logger.debug(f"Obteniendo información del path '{clean_name}'")
        
        try:
            async with self._session.get(
                f"{self.api_url}/v3/paths/get/{clean_name}"
            ) as resp:
                if resp.status == 404:
                    self.logger.debug(f"Path '{clean_name}' no encontrado")
                    return None
                elif resp.status != 200:
                    error_body = await resp.text()
                    self.logger.error(f"Error HTTP {resp.status} para path '{clean_name}': {error_body}")
                    raise ServiceError(
                        f"Error obteniendo path {clean_name}: HTTP {resp.status}",
                        error_code="MEDIAMTX_API_ERROR"
                    )
                    
                data = await resp.json()
                
                # Validar que la respuesta tenga la estructura esperada
                if not isinstance(data, dict):
                    self.logger.warning(f"Respuesta inesperada para path '{clean_name}': {data}")
                    return None
                    
                path_info = PathInfo(**data)
                
                self.logger.info(f"Path '{clean_name}' encontrado - "
                               f"Publisher: {path_info.source is not None}, "
                               f"Readers: {len(path_info.readers)}")
                
                return path_info
                
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout obteniendo información del path '{clean_name}'")
            raise ServiceError(
                f"Timeout obteniendo path {clean_name}",
                error_code="MEDIAMTX_TIMEOUT"
            )
        except aiohttp.ClientError as e:
            self.logger.error(f"Error de conexión obteniendo path '{clean_name}': {e}")
            raise ServiceError(
                f"Error de conexión con MediaMTX: {e}",
                error_code="MEDIAMTX_CONNECTION_ERROR"
            )
        except ValueError as e:
            # Error parseando JSON o creando PathInfo
            self.logger.error(f"Error parseando respuesta para path '{clean_name}': {e}")
            return None
            
    async def kick_publisher(self, name: str) -> bool:
        """
        Desconecta el publisher actual de un path.
        
        Fuerza la desconexión del publisher activo, útil para
        resolver conflictos o forzar reconexiones.
        
        Args:
            name: Nombre del path
            
        Returns:
            True si se desconectó exitosamente o no había publisher
            
        Raises:
            ValueError: Si el nombre del path es inválido
            ServiceError: Si hay error grave en la comunicación
        """
        if not name or not name.strip():
            raise ValueError("El nombre del path no puede estar vacío")
            
        if not self._session or self._session.closed:
            raise ServiceError(
                "No hay sesión HTTP activa. Llama a connect() primero",
                error_code="NO_SESSION"
            )
            
        clean_name = name.strip().lstrip('/')
        self.logger.info(f"Desconectando publisher del path '{clean_name}'")
        
        try:
            async with self._session.post(
                f"{self.api_url}/v3/paths/kick/{clean_name}/publisher"
            ) as resp:
                if resp.status == 200:
                    self.logger.info(f"Publisher desconectado exitosamente de '{clean_name}'")
                    return True
                elif resp.status == 404:
                    self.logger.debug(f"No hay publisher activo en '{clean_name}'")
                    return True  # No hay publisher, consideramos exitoso
                else:
                    error_body = await resp.text()
                    self.logger.error(f"Error HTTP {resp.status} desconectando publisher: {error_body}")
                    return False
                    
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout desconectando publisher de '{clean_name}'")
            return False
        except aiohttp.ClientError as e:
            self.logger.error(f"Error de conexión desconectando publisher: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"Error inesperado desconectando publisher de '{clean_name}'")
            return False
            
    async def wait_for_path(
        self,
        name: str,
        timeout: float = 30.0,
        check_interval: float = 1.0
    ) -> bool:
        """
        Espera hasta que un path esté activo.
        
        Realiza polling periódico hasta que el path tenga un publisher
        activo o se alcance el timeout.
        
        Args:
            name: Nombre del path
            timeout: Tiempo máximo de espera en segundos
            check_interval: Intervalo entre verificaciones en segundos
            
        Returns:
            True si el path está activo antes del timeout
            
        Raises:
            ValueError: Si los parámetros son inválidos
            ServiceError: Si hay error grave en la comunicación
        """
        if not name or not name.strip():
            raise ValueError("El nombre del path no puede estar vacío")
        if timeout <= 0:
            raise ValueError("El timeout debe ser mayor a 0")
        if check_interval <= 0:
            raise ValueError("El intervalo de verificación debe ser mayor a 0")
            
        clean_name = name.strip().lstrip('/')
        self.logger.info(f"Esperando activación del path '{clean_name}' (timeout: {timeout}s)")
        
        start_time = datetime.utcnow()
        checks_count = 0
        
        try:
            while (datetime.utcnow() - start_time).total_seconds() < timeout:
                checks_count += 1
                
                try:
                    path_info = await self.get_path_info(clean_name)
                    
                    if path_info and path_info.source:
                        elapsed = (datetime.utcnow() - start_time).total_seconds()
                        self.logger.info(
                            f"Path '{clean_name}' activo después de {elapsed:.1f}s "
                            f"y {checks_count} verificaciones"
                        )
                        return True
                        
                except ServiceError as e:
                    # Solo logear, no fallar en caso de errores temporales
                    self.logger.warning(f"Error verificando path (intento {checks_count}): {e}")
                    
                # Calcular tiempo restante para log
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                remaining = timeout - elapsed
                
                if checks_count % 5 == 0:  # Log cada 5 verificaciones
                    self.logger.debug(
                        f"Path '{clean_name}' aún no activo. "
                        f"Tiempo restante: {remaining:.1f}s"
                    )
                    
                # Evitar última espera innecesaria
                if remaining > check_interval:
                    await asyncio.sleep(check_interval)
                else:
                    await asyncio.sleep(max(0.1, remaining))
                    
            # Timeout alcanzado
            self.logger.warning(
                f"Timeout esperando activación del path '{clean_name}' "
                f"después de {checks_count} verificaciones"
            )
            return False
            
        except asyncio.CancelledError:
            self.logger.info(f"Espera cancelada para path '{clean_name}'")
            raise
        except Exception as e:
            self.logger.exception(f"Error inesperado esperando path '{clean_name}'")
            raise ServiceError(
                f"Error esperando activación del path: {str(e)}",
                error_code="WAIT_PATH_ERROR"
            )