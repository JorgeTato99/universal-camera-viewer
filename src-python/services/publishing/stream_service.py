"""
Servicio para gestión de streams de publicación con FFmpeg.

Gestiona procesos FFmpeg activos para streaming de cámaras hacia
servidores MediaMTX remotos, incluyendo monitoreo y recuperación.
"""

import asyncio
import json
import time
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from services.base_service import BaseService
from services.publishing.ffmpeg_manager import FFmpegManager
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.logging_service import get_secure_logger
from utils.exceptions import ServiceError, ValidationError
from utils.async_helpers import create_subprocess_safely


logger = get_secure_logger("services.publishing.stream")


class StreamStatus(Enum):
    """Estados posibles de un stream."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"
    RESTARTING = "restarting"


@dataclass
class StreamMetrics:
    """Métricas de un stream activo."""
    fps: float = 0.0
    bitrate_kbps: int = 0
    frames_sent: int = 0
    frames_dropped: int = 0
    duration_seconds: int = 0
    last_update: datetime = field(default_factory=datetime.utcnow)
    errors: List[str] = field(default_factory=list)


@dataclass
class StreamHandle:
    """Maneja un proceso de streaming FFmpeg."""
    session_id: str
    camera_id: str
    server_id: int
    process: Optional[asyncio.subprocess.Process] = None
    status: StreamStatus = StreamStatus.INITIALIZING
    metrics: StreamMetrics = field(default_factory=StreamMetrics)
    start_time: datetime = field(default_factory=datetime.utcnow)
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    command: str = ""
    
    @property
    def is_running(self) -> bool:
        """Verifica si el proceso está ejecutándose."""
        return (
            self.process is not None and 
            self.process.returncode is None and
            self.status == StreamStatus.RUNNING
        )


class PublishingStreamService(BaseService):
    """
    Servicio singleton para gestión de streams de publicación.
    
    Responsabilidades:
    - Iniciar/detener procesos FFmpeg
    - Monitorear salud de streams
    - Extraer métricas en tiempo real
    - Recuperación automática de fallos
    - Persistir métricas en BD
    """
    
    _instance: Optional['PublishingStreamService'] = None
    
    def __new__(cls) -> 'PublishingStreamService':
        """Implementa patrón singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el servicio."""
        # Solo inicializar una vez
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        self._initialized = True
        
        # Componentes
        self._ffmpeg_manager = FFmpegManager()
        self._db_service = get_mediamtx_db_service()
        
        # Estado interno
        self._active_streams: Dict[str, StreamHandle] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Configuración
        self.max_restart_attempts = 3
        self.restart_delay_seconds = 5.0
        self.metrics_update_interval = 2.0  # segundos
        self.health_check_interval = 10.0  # segundos
        
    async def initialize(self) -> None:
        """Inicializa el servicio y componentes."""
        if self._is_initialized:
            return
            
        self.logger.info("Inicializando PublishingStreamService")
        
        # Verificar FFmpeg disponible
        if not await self._ffmpeg_manager.check_ffmpeg_available():
            raise ServiceError(
                "FFmpeg no está disponible. Instala FFmpeg para publicar streams.",
                error_code="FFMPEG_NOT_AVAILABLE"
            )
        
        # Iniciar monitor en background
        self._monitor_task = asyncio.create_task(self._monitor_streams())
        
        # TODO: Recuperar streams activos de la BD al reiniciar
        # Por ahora, asumimos inicio limpio
        
        self._is_initialized = True
        self.logger.info("PublishingStreamService inicializado")
    
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        self.logger.info("Limpiando PublishingStreamService")
        
        # Señalar shutdown
        self._shutdown_event.set()
        
        # Detener todos los streams
        for session_id in list(self._active_streams.keys()):
            await self.stop_stream(session_id, reason="Service shutdown")
        
        # Cancelar monitor
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        self._is_initialized = False
        self.logger.info("PublishingStreamService limpiado")
    
    async def start_stream(
        self,
        session_id: str,
        camera_id: str,
        server_id: int,
        agent_command: str
    ) -> Tuple[bool, str]:
        """
        Inicia un nuevo stream de publicación.
        
        Args:
            session_id: ID único de sesión
            camera_id: ID de la cámara local
            server_id: ID del servidor MediaMTX
            agent_command: Comando FFmpeg completo
            
        Returns:
            Tuple (éxito, mensaje)
        """
        try:
            # Validar parámetros
            if not all([session_id, camera_id, agent_command]):
                raise ValidationError("Parámetros requeridos faltantes")
            
            # Verificar si ya existe
            if session_id in self._active_streams:
                if self._active_streams[session_id].is_running:
                    return True, "Stream ya está activo"
                else:
                    # Limpiar handle anterior
                    del self._active_streams[session_id]
            
            self.logger.info(
                f"Iniciando stream - Sesión: {session_id}, "
                f"Cámara: {camera_id}, Servidor: {server_id}"
            )
            
            # Crear handle
            handle = StreamHandle(
                session_id=session_id,
                camera_id=camera_id,
                server_id=server_id,
                command=agent_command
            )
            
            # Iniciar proceso FFmpeg
            success = await self._start_ffmpeg_process(handle)
            
            if success:
                # Registrar stream activo
                self._active_streams[session_id] = handle
                
                # Emitir evento
                self._emit_event('stream_started', {
                    'session_id': session_id,
                    'camera_id': camera_id,
                    'server_id': server_id
                })
                
                return True, "Stream iniciado exitosamente"
            else:
                return False, "Error iniciando proceso FFmpeg"
                
        except Exception as e:
            self.logger.error(f"Error iniciando stream: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def stop_stream(
        self,
        session_id: str,
        reason: str = "User requested"
    ) -> Tuple[bool, str]:
        """
        Detiene un stream activo.
        
        Args:
            session_id: ID de sesión del stream
            reason: Razón de la detención
            
        Returns:
            Tuple (éxito, mensaje)
        """
        try:
            handle = self._active_streams.get(session_id)
            if not handle:
                return False, "Stream no encontrado"
            
            self.logger.info(
                f"Deteniendo stream {session_id} - Razón: {reason}"
            )
            
            # Cambiar estado
            handle.status = StreamStatus.STOPPED
            
            # Terminar proceso
            if handle.process and handle.process.returncode is None:
                try:
                    handle.process.terminate()
                    await asyncio.wait_for(
                        handle.process.wait(), 
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    # Forzar kill si no termina
                    handle.process.kill()
                    await handle.process.wait()
            
            # Guardar métricas finales
            await self._save_final_metrics(handle, reason)
            
            # Limpiar
            del self._active_streams[session_id]
            
            # Emitir evento
            self._emit_event('stream_stopped', {
                'session_id': session_id,
                'camera_id': handle.camera_id,
                'reason': reason
            })
            
            return True, "Stream detenido"
            
        except Exception as e:
            self.logger.error(f"Error deteniendo stream: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def get_stream_metrics(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene métricas actuales de un stream.
        
        Args:
            session_id: ID de sesión
            
        Returns:
            Dict con métricas o None si no existe
        """
        handle = self._active_streams.get(session_id)
        if not handle:
            return None
        
        return {
            'session_id': session_id,
            'camera_id': handle.camera_id,
            'server_id': handle.server_id,
            'status': handle.status.value,
            'is_running': handle.is_running,
            'start_time': handle.start_time.isoformat(),
            'duration_seconds': int((datetime.utcnow() - handle.start_time).total_seconds()),
            'restart_count': handle.restart_count,
            'metrics': {
                'fps': handle.metrics.fps,
                'bitrate_kbps': handle.metrics.bitrate_kbps,
                'frames_sent': handle.metrics.frames_sent,
                'frames_dropped': handle.metrics.frames_dropped,
                'last_update': handle.metrics.last_update.isoformat(),
                'error_count': len(handle.metrics.errors)
            }
        }
    
    async def get_all_streams(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de todos los streams activos.
        
        Returns:
            Lista de streams con sus métricas
        """
        streams = []
        for session_id in self._active_streams:
            metrics = await self.get_stream_metrics(session_id)
            if metrics:
                streams.append(metrics)
        return streams
    
    async def restart_stream(self, session_id: str) -> Tuple[bool, str]:
        """
        Reinicia un stream.
        
        Args:
            session_id: ID de sesión
            
        Returns:
            Tuple (éxito, mensaje)
        """
        handle = self._active_streams.get(session_id)
        if not handle:
            return False, "Stream no encontrado"
        
        self.logger.info(f"Reiniciando stream {session_id}")
        
        # Incrementar contador
        handle.restart_count += 1
        handle.last_restart = datetime.utcnow()
        handle.status = StreamStatus.RESTARTING
        
        # Detener proceso actual
        if handle.process and handle.process.returncode is None:
            handle.process.terminate()
            try:
                await asyncio.wait_for(handle.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                handle.process.kill()
                await handle.process.wait()
        
        # Esperar antes de reiniciar
        await asyncio.sleep(self.restart_delay_seconds)
        
        # Reiniciar
        success = await self._start_ffmpeg_process(handle)
        
        if success:
            return True, "Stream reiniciado exitosamente"
        else:
            handle.status = StreamStatus.ERROR
            return False, "Error reiniciando stream"
    
    async def _start_ffmpeg_process(self, handle: StreamHandle) -> bool:
        """
        Inicia el proceso FFmpeg para un stream.
        
        Args:
            handle: Handle del stream
            
        Returns:
            True si se inició exitosamente
        """
        try:
            # Parsear comando
            # El comando viene como string, necesitamos dividirlo
            import shlex
            cmd_parts = shlex.split(handle.command)
            
            # Verificar que el servicio esté inicializado
            if not self._is_initialized:
                await self.initialize()
            
            # Si el comando no empieza con ffmpeg, agregarlo
            if cmd_parts and cmd_parts[0] != 'ffmpeg':
                cmd_parts = ['ffmpeg'] + cmd_parts
            
            self.logger.info(f"Comando FFmpeg completo: {' '.join(cmd_parts)}")
            self.logger.debug(f"Ejecutando comando FFmpeg: {' '.join(cmd_parts[:5])}...")
            
            # Crear proceso
            process = await create_subprocess_safely(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            handle.process = process
            handle.status = StreamStatus.RUNNING
            
            # Iniciar tareas de lectura de output
            asyncio.create_task(self._read_ffmpeg_output(handle))
            
            # Verificar que el proceso inició correctamente
            # Esperar un momento para ver si falla inmediatamente
            await asyncio.sleep(1.0)
            
            if process.returncode is not None:
                # Proceso terminó inmediatamente
                handle.status = StreamStatus.ERROR
                return False
            
            self.logger.info(f"Proceso FFmpeg iniciado para sesión {handle.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando FFmpeg: {str(e)}", exc_info=True)
            handle.status = StreamStatus.ERROR
            handle.metrics.errors.append(str(e))
            return False
    
    async def _read_ffmpeg_output(self, handle: StreamHandle) -> None:
        """
        Lee y procesa la salida de FFmpeg.
        
        Args:
            handle: Handle del stream
        """
        if not handle.process or not handle.process.stderr:
            return
        
        try:
            while handle.is_running:
                line = await handle.process.stderr.readline()
                if not line:
                    break
                
                # Decodificar línea
                line_str = line.decode('utf-8', errors='ignore').strip()
                
                # Parsear métricas si es posible
                metrics = self._ffmpeg_manager.parse_metrics(line_str)
                if metrics:
                    # Actualizar métricas del handle
                    handle.metrics.fps = metrics.get('fps', handle.metrics.fps)
                    handle.metrics.bitrate_kbps = metrics.get('bitrate_kbps', handle.metrics.bitrate_kbps)
                    handle.metrics.frames_sent = metrics.get('frame', handle.metrics.frames_sent)
                    handle.metrics.frames_dropped = metrics.get('drop', handle.metrics.frames_dropped)
                    handle.metrics.last_update = datetime.utcnow()
                
                # Detectar errores
                # TODO: Corregir is_error_line en FFmpegManager
                # if self._ffmpeg_manager.is_error_line(line_str):
                #     handle.metrics.errors.append(line_str)
                #     self.logger.warning(f"Error FFmpeg en {handle.session_id}: {line_str}")
                    
                    # Si hay muchos errores, considerar reiniciar
                    if len(handle.metrics.errors) > 10:
                        handle.status = StreamStatus.ERROR
            
        except Exception as e:
            self.logger.error(f"Error leyendo output FFmpeg: {str(e)}")
        
        # El proceso terminó
        if handle.process:
            await handle.process.wait()
            if handle.status == StreamStatus.RUNNING:
                handle.status = StreamStatus.ERROR
    
    async def _monitor_streams(self) -> None:
        """
        Tarea en background para monitorear streams activos.
        
        - Verifica salud de procesos
        - Guarda métricas periódicamente
        - Reinicia streams caídos si es necesario
        """
        self.logger.info("Monitor de streams iniciado")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # Revisar cada stream
                    for session_id, handle in list(self._active_streams.items()):
                        # Verificar si el proceso sigue vivo
                        if handle.process and handle.process.returncode is not None:
                            # Proceso terminó
                            if handle.status == StreamStatus.RUNNING:
                                handle.status = StreamStatus.ERROR
                                self.logger.error(
                                    f"Stream {session_id} terminó inesperadamente "
                                    f"con código {handle.process.returncode}"
                                )
                                
                                # Intentar reiniciar si no ha excedido límite
                                if handle.restart_count < self.max_restart_attempts:
                                    self.logger.info(
                                        f"Intentando reiniciar stream {session_id} "
                                        f"(intento {handle.restart_count + 1}/{self.max_restart_attempts})"
                                    )
                                    asyncio.create_task(self.restart_stream(session_id))
                                else:
                                    # Demasiados reintentos, detener
                                    self.logger.error(
                                        f"Stream {session_id} excedió límite de reintentos"
                                    )
                                    asyncio.create_task(
                                        self.stop_stream(session_id, "Max restarts exceeded")
                                    )
                        
                        # Guardar métricas periódicamente
                        if handle.is_running and handle.metrics.last_update:
                            time_since_update = (
                                datetime.utcnow() - handle.metrics.last_update
                            ).total_seconds()
                            
                            if time_since_update < self.metrics_update_interval * 2:
                                # Métricas recientes, guardar en BD
                                await self._save_metrics_to_db(handle)
                    
                except Exception as e:
                    self.logger.error(f"Error en monitor de streams: {str(e)}")
                
                # Esperar antes de siguiente chequeo
                await asyncio.sleep(self.health_check_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Monitor de streams cancelado")
            raise
        
        self.logger.info("Monitor de streams finalizado")
    
    async def _save_metrics_to_db(self, handle: StreamHandle) -> None:
        """
        Guarda métricas actuales en la base de datos.
        
        Args:
            handle: Handle del stream
            
        TODO: Implementar tabla publication_metrics en BD
        Por ahora solo logging
        """
        try:
            # TODO: Cuando se implemente la tabla publication_metrics
            # await self._db_service.save_publication_metrics(
            #     session_id=handle.session_id,
            #     fps=handle.metrics.fps,
            #     bitrate_kbps=handle.metrics.bitrate_kbps,
            #     frames_sent=handle.metrics.frames_sent,
            #     frames_dropped=handle.metrics.frames_dropped
            # )
            
            # Por ahora solo log
            self.logger.debug(
                f"Métricas de {handle.session_id}: "
                f"FPS={handle.metrics.fps:.1f}, "
                f"Bitrate={handle.metrics.bitrate_kbps}kbps, "
                f"Frames={handle.metrics.frames_sent}/{handle.metrics.frames_dropped}"
            )
            
        except Exception as e:
            self.logger.error(f"Error guardando métricas: {str(e)}")
    
    async def _save_final_metrics(
        self,
        handle: StreamHandle,
        termination_reason: str
    ) -> None:
        """
        Guarda métricas finales cuando un stream termina.
        
        Args:
            handle: Handle del stream
            termination_reason: Razón de terminación
        """
        try:
            duration = int((datetime.utcnow() - handle.start_time).total_seconds())
            
            # TODO: Implementar guardado en publication_history
            # await self._db_service.end_publication_session(
            #     session_id=handle.session_id,
            #     duration_seconds=duration,
            #     frames_sent=handle.metrics.frames_sent,
            #     frames_dropped=handle.metrics.frames_dropped,
            #     average_fps=handle.metrics.fps,
            #     average_bitrate_kbps=handle.metrics.bitrate_kbps,
            #     error_count=len(handle.metrics.errors),
            #     termination_reason=termination_reason
            # )
            
            self.logger.info(
                f"Stream {handle.session_id} finalizado - "
                f"Duración: {duration}s, "
                f"Frames: {handle.metrics.frames_sent}, "
                f"Errores: {len(handle.metrics.errors)}"
            )
            
        except Exception as e:
            self.logger.error(f"Error guardando métricas finales: {str(e)}")


# Instancia singleton
_service_instance: Optional[PublishingStreamService] = None


def get_publishing_stream_service() -> PublishingStreamService:
    """
    Obtiene la instancia singleton del servicio.
    
    Returns:
        PublishingStreamService singleton
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = PublishingStreamService()
        # No podemos hacer await aquí, pero el servicio se inicializará
        # cuando se use por primera vez
    
    return _service_instance