"""
Servicio principal para publicación de streams RTSP a MediaMTX.

Gestiona el ciclo de vida de procesos FFmpeg para realizar relay
de streams RTSP desde cámaras hacia el servidor MediaMTX.
"""

import asyncio

from typing import Dict, Optional, List
from datetime import datetime
import uuid

from services.base_service import BaseService
from models.publishing import (
    PublisherProcess, PublishStatus, PublishResult,
    PublishConfiguration, PublishErrorType
)
from api.schemas.requests.mediamtx_requests import TerminationReason
from services.camera_manager_service import camera_manager_service
from utils.sanitizers import sanitize_command, sanitize_url
from services.publishing.ffmpeg_manager import FFmpegManager
from utils.exceptions import ServiceError
from services.logging_service import get_secure_logger


class RTSPPublisherService(BaseService):
    """
    Servicio para publicar streams RTSP a MediaMTX usando FFmpeg.
    
    Este servicio implementa el patrón Singleton y gestiona múltiples
    procesos FFmpeg para realizar relay de streams RTSP.
    
    Responsabilidades:
    - Gestionar procesos FFmpeg para cada cámara
    - Manejar reconexiones automáticas
    - Reportar estado y métricas
    - Coordinar con otros servicios
    
    Attributes:
        _config: Configuración de publicación
        _processes: Diccionario de procesos activos por camera_id
        _ffmpeg_manager: Gestor de FFmpeg
        _shutdown_event: Evento para señalizar shutdown
    """
    
    def __init__(self, config: PublishConfiguration):
        """
        Inicializa el servicio con la configuración proporcionada.
        
        Args:
            config: Configuración de publicación a MediaMTX
        """
        super().__init__()
        self._config = config
        self._processes: Dict[str, PublisherProcess] = {}
        self._ffmpeg_manager = FFmpegManager()
        self._shutdown_event = asyncio.Event()
        self.logger = get_secure_logger("services.publishing.rtsp_publisher_service")
        self._db_service = None  # Se inicializa en initialize()
        self._config_id = None  # ID de configuración en BD
        
    async def initialize(self) -> None:
        """
        Inicializa el servicio y verifica dependencias.
        
        Realiza las siguientes verificaciones:
        - Disponibilidad de FFmpeg en el sistema
        - Conectividad con MediaMTX (si API está habilitada)
        - Conexión con base de datos para persistencia
        
        Raises:
            ServiceError: Si FFmpeg no está disponible o hay error de configuración
        """
        self.logger.info("Inicializando RTSPPublisherService")
        self.logger.debug(f"Configuración: MediaMTX URL={self._config.mediamtx_url}, " 
                         f"API habilitada={self._config.api_enabled}, "
                         f"Reintentos máximos={self._config.max_reconnects}")
        
        try:
            # Verificar que FFmpeg esté disponible
            self.logger.debug("Verificando disponibilidad de FFmpeg...")
            if not await self._ffmpeg_manager.check_ffmpeg_available():
                error_msg = "FFmpeg no está instalado o no es accesible en el sistema"
                self.logger.error(error_msg)
                raise ServiceError(error_msg, error_code="FFMPEG_NOT_FOUND")
            
            self.logger.info("FFmpeg verificado correctamente")
            
            # Inicializar servicio de BD
            from services.database import get_publishing_db_service
            self._db_service = get_publishing_db_service()
            await self._db_service.initialize()
            
            # Obtener ID de configuración activa
            config_data = await self._db_service.get_active_configuration()
            if config_data:
                self._config_id = config_data['config_id']
                self.logger.debug(f"Usando configuración ID {self._config_id}: {config_data['config_name']}")
            else:
                self.logger.warning("No hay configuración activa en BD, usando ID por defecto")
                self._config_id = 1
            
            # Restaurar estados activos desde BD
            active_states = await self._db_service.get_active_states()
            self.logger.info(f"Encontrados {len(active_states)} estados activos en BD")
            
            # Por ahora solo loguear, no restaurar procesos
            # TODO: Implementar restauración de procesos si es necesario
            
            # Verificar conectividad con MediaMTX si está configurado
            if self._config.api_enabled:
                api_url = self._config.get_api_url()
                self.logger.debug(f"Verificación de API MediaMTX pendiente en {api_url}")
                # TODO: Implementar verificación de API MediaMTX
                
        except ServiceError:
            raise
        except Exception as e:
            self.logger.exception("Error inesperado durante inicialización")
            raise ServiceError(
                f"Error inicializando servicio: {str(e)}",
                error_code="INIT_ERROR"
            )
            
        self.logger.info("RTSPPublisherService inicializado correctamente")
    
    async def start_publishing(
        self,
        camera_id: str,
        force_restart: bool = False,
        target_url: Optional[str] = None,
        source_url: Optional[str] = None,
        is_remote: bool = False,
        agent_command: Optional[str] = None
    ) -> PublishResult:
        """
        Inicia la publicación de una cámara específica a MediaMTX.
        
        Args:
            camera_id: Identificador único de la cámara
            force_restart: Si True, reinicia la publicación aunque ya esté activa
            target_url: URL de destino personalizada (para publicación remota)
            source_url: URL de origen personalizada (opcional)
            is_remote: Indica si es una publicación remota
            
        Returns:
            PublishResult con el estado de la operación
            
        Raises:
            Exception: Errores no controlados durante el inicio
        """
        self.logger.info(f"Solicitando publicación para cámara {camera_id} "
                        f"(force_restart={force_restart})")
        
        try:
            # Verificar si ya está publicando
            if camera_id in self._processes:
                process = self._processes[camera_id]
                if process.is_active and not force_restart:
                    self.logger.info(f"Cámara {camera_id} ya está publicando")
                    return PublishResult(
                        success=False,
                        camera_id=camera_id,
                        error="La cámara ya está publicando",
                        publish_path=self._config.get_publish_path(camera_id)
                    )
                elif force_restart:
                    self.logger.info(f"Forzando reinicio de publicación para {camera_id}")
                    await self.stop_publishing(camera_id)
            
            # Obtener información de la cámara
            self.logger.debug(f"Obteniendo información de cámara {camera_id}")
            camera = await camera_manager_service.get_camera(camera_id)
            if not camera:
                self.logger.warning(f"Cámara {camera_id} no encontrada en el sistema")
                return PublishResult(
                    success=False,
                    camera_id=camera_id,
                    error="Cámara no encontrada en el sistema",
                    error_type=PublishErrorType.STREAM_UNAVAILABLE
                )
            
            # Construir URLs (usar las proporcionadas o construir las normales)
            if not source_url:
                source_url = await self._build_source_url(camera)
            else:
                self.logger.debug(f"Usando URL de origen externa: {sanitize_url(source_url)}")
                
            if not target_url:
                target_url = self._build_target_url(camera_id)
            else:
                self.logger.debug(f"Usando URL de destino externa: {sanitize_url(target_url)}")
            
            self.logger.debug(f"URLs finales - Origen: {sanitize_url(source_url)}, "
                            f"Destino: {sanitize_url(target_url)}, "
                            f"Es remoto: {is_remote}")
            
            # Crear proceso con session_id único
            process = PublisherProcess(
                camera_id=camera_id,
                status=PublishStatus.STARTING
            )
            # Agregar session_id para tracking
            process.session_id = str(uuid.uuid4())
            self._processes[camera_id] = process
            
            # Construir comando FFmpeg
            # TODO: Para publicaciones remotas, usar agent_command proporcionado por el servidor
            # if is_remote and agent_command:
            #     cmd = shlex.split(agent_command)
            # else:
            cmd = self._build_ffmpeg_command(source_url, target_url)
            
            # Iniciar proceso
            self.logger.info(f"Iniciando proceso FFmpeg para cámara {camera_id}")
            self.logger.debug(f"Comando FFmpeg: {sanitize_command(' '.join(cmd))}")
            
            # Usar helper para compatibilidad con Windows y Python 3.13+
            from utils.async_helpers import create_subprocess_safely
            proc = await create_subprocess_safely(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
            )
            
            process.process = proc
            process.status = PublishStatus.PUBLISHING
            
            self.logger.info(f"Proceso FFmpeg iniciado con PID {proc.pid} para cámara {camera_id}")
            
            # Guardar estado en BD si tenemos servicio
            if self._db_service and self._config_id:
                try:
                    await self._db_service.save_publishing_state(
                        camera_id=camera_id,
                        status=PublishStatus.PUBLISHING,
                        config_id=self._config_id,
                        publish_path=self._config.get_publish_path(camera_id),
                        process_pid=proc.pid
                    )
                except Exception as e:
                    self.logger.error(f"Error guardando estado en BD: {e}")
            
            # Iniciar monitor del proceso
            monitor_task = asyncio.create_task(
                self._monitor_process(camera_id),
                name=f"monitor_{camera_id}"
            )
            
            self.logger.debug(f"Monitor de proceso iniciado para {camera_id}")
            
            return PublishResult(
                success=True,
                camera_id=camera_id,
                publish_path=self._config.get_publish_path(camera_id),
                process_id=proc.pid
            )
            
        except asyncio.CancelledError:
            self.logger.warning(f"Publicación cancelada para {camera_id}")
            raise
        except Exception as e:
            self.logger.exception(f"Error iniciando publicación para {camera_id}")
            
            # Limpiar proceso si falló
            if camera_id in self._processes:
                self._processes.pop(camera_id)
                
            return PublishResult(
                success=False,
                camera_id=camera_id,
                error=str(e),
                error_type=PublishErrorType.UNKNOWN
            )
    
    async def stop_publishing(self, camera_id: str) -> bool:
        """
        Detiene la publicación de una cámara específica.
        
        Intenta terminar el proceso de forma elegante (SIGTERM) y si no
        responde en 5 segundos, fuerza la terminación (SIGKILL).
        
        Args:
            camera_id: Identificador único de la cámara
            
        Returns:
            True si se detuvo correctamente, False si no había proceso activo
        """
        if camera_id not in self._processes:
            self.logger.debug(f"No hay proceso activo para cámara {camera_id}")
            return False
            
        self.logger.info(f"Deteniendo publicación para cámara {camera_id}")
        
        process = self._processes[camera_id]
        # Nota: STOPPING se maneja solo en frontend, aquí pasamos directo a STOPPED
        process.status = PublishStatus.STOPPED
        
        if process.process and process.process.returncode is None:
            try:
                # Terminar proceso gracefully
                self.logger.debug(f"Enviando SIGTERM a proceso {process.process.pid}")
                process.process.terminate()
                
                # Esperar hasta 5 segundos
                try:
                    await asyncio.wait_for(
                        process.process.wait(),
                        timeout=5.0
                    )
                    self.logger.info(f"Proceso terminado correctamente para {camera_id}")
                except asyncio.TimeoutError:
                    # Forzar kill si no termina
                    self.logger.warning(f"Timeout esperando terminación, forzando SIGKILL para {camera_id}")
                    process.process.kill()
                    await process.process.wait()
                    
            except Exception as e:
                self.logger.error(f"Error deteniendo proceso {camera_id}: {e}")
                return False
        
        # Actualizar estado y limpiar
        process.status = PublishStatus.STOPPED
        self._processes.pop(camera_id)
        
        # Mover a historial y actualizar estado en BD
        if self._db_service:
            try:
                # Determinar razón de terminación
                termination_reason = TerminationReason.USER_STOPPED
                if process.error_count > 0:
                    termination_reason = TerminationReason.ERROR
                
                # Mover publicación al historial
                await self._db_service.move_publication_to_history(
                    camera_id=camera_id,
                    termination_reason=termination_reason
                )
                
                # Actualizar estado final
                await self._db_service.update_publishing_state(
                    camera_id=camera_id,
                    status=PublishStatus.STOPPED
                )
            except Exception as e:
                self.logger.error(f"Error actualizando BD al detener: {e}")
        
        self.logger.info(f"Publicación detenida exitosamente para cámara {camera_id}")
        return True
    
    async def stop_all_publishing(self) -> Dict[str, bool]:
        """
        Detiene todas las publicaciones activas.
        
        Útil durante el shutdown del servicio o para operaciones
        de mantenimiento masivo.
        
        Returns:
            Diccionario con resultados por cámara {camera_id: success}
        """
        self.logger.info(f"Deteniendo todas las publicaciones ({len(self._processes)} activas)")
        
        results = {}
        camera_ids = list(self._processes.keys())
        
        for camera_id in camera_ids:
            results[camera_id] = await self.stop_publishing(camera_id)
            
        self.logger.info(f"Detención masiva completada. Exitosas: {sum(results.values())}, "
                        f"Fallidas: {len(results) - sum(results.values())}")
        
        return results
    
    def get_publishing_status(self) -> Dict[str, PublisherProcess]:
        """
        Obtiene el estado actual de todas las publicaciones.
        
        Returns:
            Diccionario con procesos de publicación por camera_id
        """
        return self._processes.copy()
    
    def get_camera_status(self, camera_id: str) -> Optional[PublisherProcess]:
        """
        Obtiene el estado de publicación de una cámara específica.
        
        Args:
            camera_id: Identificador único de la cámara
            
        Returns:
            PublisherProcess si existe, None si no está publicando
        """
        return self._processes.get(camera_id)
    
    def is_publishing(self, camera_id: str) -> bool:
        """
        Verifica si una cámara está publicando activamente.
        
        Args:
            camera_id: Identificador único de la cámara
            
        Returns:
            True si la cámara está publicando, False en caso contrario
        """
        process = self._processes.get(camera_id)
        return process.is_active if process else False
    
    async def _monitor_process(self, camera_id: str) -> None:
        """
        Monitorea un proceso FFmpeg y maneja reconexiones automáticas.
        
        Este método corre en background para cada proceso activo y:
        - Lee y procesa la salida de FFmpeg
        - Detecta errores y terminaciones inesperadas
        - Maneja reconexión automática según configuración
        
        Args:
            camera_id: Identificador único de la cámara a monitorear
        """
        process = self._processes.get(camera_id)
        if not process or not process.process:
            self.logger.warning(f"No se puede monitorear proceso para {camera_id}: no existe")
            return
            
        self.logger.debug(f"Monitor iniciado para proceso {camera_id} (PID: {process.process.pid})")
        
        try:
            # Monitorear el proceso
            while camera_id in self._processes and not self._shutdown_event.is_set():
                proc = process.process
                if proc and proc.returncode is None:
                    # Leer stderr para logs
                    try:
                        line = await asyncio.wait_for(
                            proc.stderr.readline(),
                            timeout=1.0
                        )
                        if line:
                            await self._handle_ffmpeg_output(camera_id, line)
                    except asyncio.TimeoutError:
                        # Normal, no hay salida
                        pass
                else:
                    # Proceso terminó
                    returncode = proc.returncode if proc else -1
                    self.logger.warning(
                        f"Proceso FFmpeg terminó inesperadamente para {camera_id} "
                        f"con código {returncode}"
                    )
                    
                    # Manejar reconexión si es necesario
                    if process.status == PublishStatus.PUBLISHING:
                        await self._handle_process_exit(camera_id, returncode)
                    
                    break
                    
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            self.logger.debug(f"Monitor cancelado para {camera_id}")
            raise
        except Exception as e:
            self.logger.exception(f"Error en monitor de proceso {camera_id}")
            
        self.logger.debug(f"Monitor finalizado para {camera_id}")
            
    async def _handle_process_exit(
        self,
        camera_id: str,
        returncode: int
    ) -> None:
        """
        Maneja la salida inesperada de un proceso FFmpeg.
        
        Determina el tipo de error basado en el código de salida y
        decide si reintentar según la configuración.
        
        Args:
            camera_id: Identificador único de la cámara
            returncode: Código de salida del proceso FFmpeg
        """
        process = self._processes.get(camera_id)
        if not process:
            return
            
        process.error_count += 1
        
        # Determinar tipo de error por código de salida
        if returncode == 1:
            process.error_type = PublishErrorType.CONNECTION_FAILED
            error_desc = "Fallo de conexión"
        elif returncode == 255:
            process.error_type = PublishErrorType.AUTHENTICATION_FAILED
            error_desc = "Fallo de autenticación"
        else:
            process.error_type = PublishErrorType.PROCESS_CRASHED
            error_desc = f"Proceso terminó con código {returncode}"
            
        self.logger.error(f"Error en publicación de {camera_id}: {error_desc}")
            
        # Intentar reconectar si no se ha excedido el límite
        if process.error_count <= self._config.max_reconnects:
            # Nota: RECONNECTING se maneja solo en frontend
            # Backend mantiene ERROR pero con metadata indicando reconexión
            process.status = PublishStatus.ERROR
            process.metrics['is_reconnecting'] = True
            process.metrics['reconnect_attempt'] = process.error_count
            process.metrics['max_reconnects'] = self._config.max_reconnects
            
            self.logger.info(
                f"Reintentando publicación para {camera_id} "
                f"(intento {process.error_count}/{self._config.max_reconnects})"
            )
            
            # Actualizar estado en BD con metadata de reconexión
            if self._db_service:
                try:
                    await self._db_service.update_publishing_state(
                        camera_id=camera_id,
                        status=PublishStatus.ERROR,
                        error=f"{error_desc} (reconectando...)",
                        increment_error=True,
                        metrics={
                            'is_reconnecting': True,
                            'reconnect_attempt': process.error_count
                        }
                    )
                except Exception as e:
                    self.logger.error(f"Error actualizando estado en BD: {e}")
            
            # Esperar antes de reintentar (backoff exponencial)
            delay = min(self._config.reconnect_delay * process.error_count, 60)
            self.logger.debug(f"Esperando {delay} segundos antes de reintentar")
            await asyncio.sleep(delay)
            
            # Reintentar
            result = await self.start_publishing(camera_id, force_restart=True)
            if not result.success:
                process.status = PublishStatus.ERROR
                process.last_error = result.error
                process.metrics['is_reconnecting'] = False
                self.logger.error(f"Fallo al reintentar publicación: {result.error}")
        else:
            # Máximo de reintentos alcanzado
            process.status = PublishStatus.ERROR
            process.last_error = f"Máximo de reintentos alcanzado ({self._config.max_reconnects})"
            process.metrics['is_reconnecting'] = False
            self.logger.error(
                f"Publicación fallida definitivamente para {camera_id}: "
                f"{process.last_error}"
            )
    
    async def _handle_ffmpeg_output(
        self,
        camera_id: str,
        line: bytes
    ) -> None:
        """
        Procesa una línea de salida de FFmpeg.
        
        Extrae métricas y detecta errores/warnings en la salida.
        
        Args:
            camera_id: Identificador único de la cámara
            line: Línea de salida de FFmpeg (stderr)
        """
        try:
            text = line.decode('utf-8', errors='ignore').strip()
            if not text:
                return
                
            # Log según el nivel
            if "error" in text.lower():
                self.logger.error(f"FFmpeg [{camera_id}]: {text}")
            elif "warning" in text.lower():
                self.logger.warning(f"FFmpeg [{camera_id}]: {text}")
            else:
                # Log verbose para debugging
                self.logger.debug(f"FFmpeg [{camera_id}]: {text}")
                
            # Parsear métricas si es posible
            metrics = self._ffmpeg_manager.parse_metrics(text)
            if metrics:
                process = self._processes.get(camera_id)
                if process:
                    process.update_metrics(**metrics)
                    self.logger.debug(f"Métricas actualizadas para {camera_id}: {metrics}")
                    
        except Exception as e:
            self.logger.error(f"Error procesando salida FFmpeg: {e}")
    
    async def _build_source_url(self, camera) -> str:
        """
        Construye la URL RTSP de origen con credenciales.
        
        Args:
            camera: Objeto de cámara con información de conexión
            
        Returns:
            URL RTSP completa con credenciales
        """
        # Usar el método get_rtsp_url() del modelo de cámara
        url = camera.get_rtsp_url()
        self.logger.debug(f"URL origen construida: {url}")
        return url
    
    def _build_target_url(self, camera_id: str) -> str:
        """
        Construye la URL RTSP de destino para MediaMTX.
        
        Args:
            camera_id: Identificador único de la cámara
            
        Returns:
            URL RTSP completa para publicar en MediaMTX
        """
        path = self._config.get_publish_path(camera_id)
        base_url = self._config.mediamtx_url
        
        # Agregar autenticación si está configurada
        if self._config.auth_enabled and self._config.username:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(base_url)
            netloc = f"{self._config.username}:{self._config.password}@{parsed.netloc}"
            base_url = urlunparse(parsed._replace(netloc=netloc))
            
        target_url = f"{base_url}/{path}"
        self.logger.debug(f"URL destino construida: {sanitize_url(target_url)}")
        return target_url
    
    def _build_ffmpeg_command(
        self,
        source_url: str,
        target_url: str
    ) -> List[str]:
        """
        Construye el comando FFmpeg optimizado para relay de video.
        
        Utiliza -c copy para evitar recodificación y minimizar CPU/latencia.
        Detecta automáticamente el formato de salida según la URL de destino.
        
        Args:
            source_url: URL RTSP de origen (cámara)
            target_url: URL de destino (RTSP para local, RTMP para remoto)
            
        Returns:
            Lista de argumentos para subprocess
        """
        # Detectar formato de salida basado en la URL de destino
        output_format = 'rtsp'  # Por defecto RTSP para servidores locales
        if target_url.startswith('rtmp://'):
            output_format = 'flv'  # FLV es el formato correcto para RTMP
            self.logger.debug("Detectado destino RTMP, usando formato FLV")
        elif target_url.startswith('rtsp://'):
            output_format = 'rtsp'
            self.logger.debug("Detectado destino RTSP, usando formato RTSP")
        
        cmd = [
            'ffmpeg',
            '-nostdin',                    # No input interactivo
            '-loglevel', 'warning',        # Solo warnings y errores
            '-stats',                      # Mostrar estadísticas
            '-rtsp_transport', 'tcp',      # Forzar TCP para estabilidad en origen
            '-stimeout', '5000000',        # Timeout 5 segundos
            '-i', source_url,              # Input
            '-c', 'copy',                  # No recodificar (relay directo)
            '-f', output_format,           # Output format según destino
        ]
        
        # Solo agregar transporte TCP para RTSP (no aplica para RTMP)
        if self._config.use_tcp and output_format == 'rtsp':
            cmd.extend(['-rtsp_transport', 'tcp'])
            
        cmd.append(target_url)
        
        return cmd
    
    async def cleanup(self) -> None:
        """
        Limpia todos los recursos del servicio.
        
        Detiene todas las publicaciones activas y libera recursos.
        Debe llamarse durante el shutdown de la aplicación.
        """
        self.logger.info("Iniciando limpieza de RTSPPublisherService")
        
        # Señalar shutdown
        self._shutdown_event.set()
        
        # Detener todas las publicaciones
        await self.stop_all_publishing()
        
        # Limpiar recursos adicionales
        self._processes.clear()
        
        self.logger.info("RTSPPublisherService limpiado correctamente")


# Singleton del servicio
_publisher_service: Optional[RTSPPublisherService] = None


def get_publisher_service(config: Optional[PublishConfiguration] = None) -> RTSPPublisherService:
    """
    Obtiene la instancia singleton del servicio de publicación.
    
    Args:
        config: Configuración (requerida en primera llamada)
        
    Returns:
        Instancia única del servicio RTSPPublisherService
        
    Raises:
        ValueError: Si no se proporciona configuración en la primera llamada
    """
    global _publisher_service
    
    if _publisher_service is None:
        if config is None:
            raise ValueError(
                "Se requiere configuración en la primera inicialización del servicio"
            )
        _publisher_service = RTSPPublisherService(config)
        
    return _publisher_service