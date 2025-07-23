"""
Servicio principal para publicación de streams RTSP a MediaMTX.

Gestiona el ciclo de vida de procesos FFmpeg para realizar relay
de streams RTSP desde cámaras hacia el servidor MediaMTX.
"""

import asyncio

from typing import Dict, Optional, List
from datetime import datetime

from services.base_service import BaseService
from models.publishing import (
    PublisherProcess, PublishStatus, PublishResult,
    PublishConfiguration, PublishErrorType
)
from services.camera_manager_service import camera_manager_service
from services.publishing.ffmpeg_manager import FFmpegManager
from utils.exceptions import ServiceError
from services.logging_service import get_secure_logger


class RTSPPublisherService(BaseService):
    """
    Servicio para publicar streams RTSP a MediaMTX usando FFmpeg.
    
    Responsabilidades:
    - Gestionar procesos FFmpeg para cada cámara
    - Manejar reconexiones automáticas
    - Reportar estado y métricas
    - Coordinar con otros servicios
    """
    
    def __init__(self, config: PublishConfiguration):
        """
        Inicializa el servicio.
        
        Args:
            config: Configuración de publicación
        """
        super().__init__()
        self._config = config
        self._processes: Dict[str, PublisherProcess] = {}
        self._ffmpeg_manager = FFmpegManager()
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> None:
        """Inicializa el servicio y verifica dependencias."""
        self.logger.info("Inicializando RTSPPublisherService")
        
        # Verificar que FFmpeg esté disponible
        if not await self._ffmpeg_manager.check_ffmpeg_available():
            raise ServiceError(
                "FFmpeg no está instalado o no es accesible",
                error_code="FFMPEG_NOT_FOUND"
            )
        
        self.logger.info("RTSPPublisherService inicializado correctamente")
    
    async def start_publishing(
        self,
        camera_id: str,
        force_restart: bool = False
    ) -> PublishResult:
        """
        Inicia la publicación de una cámara específica.
        
        Args:
            camera_id: ID de la cámara a publicar
            force_restart: Forzar reinicio si ya está publicando
            
        Returns:
            PublishResult con el resultado de la operación
        """
        try:
            # Verificar si ya está publicando
            if camera_id in self._processes:
                process = self._processes[camera_id]
                if process.is_active and not force_restart:
                    return PublishResult(
                        success=False,
                        camera_id=camera_id,
                        error="La cámara ya está publicando",
                        publish_path=self._config.get_publish_path(camera_id)
                    )
                elif force_restart:
                    await self.stop_publishing(camera_id)
            
            # Obtener información de la cámara
            camera = await camera_manager_service.get_camera(camera_id)
            if not camera:
                return PublishResult(
                    success=False,
                    camera_id=camera_id,
                    error="Cámara no encontrada",
                    error_type=PublishErrorType.STREAM_UNAVAILABLE
                )
            
            # Construir URLs
            source_url = await self._build_source_url(camera)
            target_url = self._build_target_url(camera_id)
            
            # Crear proceso
            process = PublisherProcess(
                camera_id=camera_id,
                status=PublishStatus.STARTING
            )
            self._processes[camera_id] = process
            
            # Construir comando FFmpeg
            cmd = self._build_ffmpeg_command(source_url, target_url)
            
            # Iniciar proceso
            self.logger.info(f"Iniciando publicación para cámara {camera_id}")
            self.logger.debug(f"Comando: {' '.join(cmd)}")
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
            )
            
            process.process = proc
            process.status = PublishStatus.PUBLISHING
            
            # Iniciar monitor del proceso
            asyncio.create_task(
                self._monitor_process(camera_id),
                name=f"monitor_{camera_id}"
            )
            
            return PublishResult(
                success=True,
                camera_id=camera_id,
                publish_path=self._config.get_publish_path(camera_id),
                process_id=proc.pid
            )
            
        except Exception as e:
            self.logger.error(f"Error iniciando publicación para {camera_id}: {e}")
            
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
        Detiene la publicación de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se detuvo correctamente
        """
        if camera_id not in self._processes:
            self.logger.warning(f"No hay proceso activo para cámara {camera_id}")
            return False
            
        process = self._processes[camera_id]
        process.status = PublishStatus.STOPPING
        
        if process.process and process.process.returncode is None:
            try:
                # Terminar proceso gracefully
                process.process.terminate()
                
                # Esperar hasta 5 segundos
                try:
                    await asyncio.wait_for(
                        process.process.wait(),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    # Forzar kill si no termina
                    self.logger.warning(f"Forzando kill para proceso {camera_id}")
                    process.process.kill()
                    await process.process.wait()
                    
            except Exception as e:
                self.logger.error(f"Error deteniendo proceso {camera_id}: {e}")
                return False
        
        # Actualizar estado y limpiar
        process.status = PublishStatus.STOPPED
        self._processes.pop(camera_id)
        
        self.logger.info(f"Publicación detenida para cámara {camera_id}")
        return True
    
    async def stop_all_publishing(self) -> Dict[str, bool]:
        """
        Detiene todas las publicaciones activas.
        
        Returns:
            Dict con resultados por cámara
        """
        results = {}
        camera_ids = list(self._processes.keys())
        
        for camera_id in camera_ids:
            results[camera_id] = await self.stop_publishing(camera_id)
            
        return results
    
    def get_publishing_status(self) -> Dict[str, PublisherProcess]:
        """Obtiene el estado de todas las publicaciones."""
        return self._processes.copy()
    
    def get_camera_status(self, camera_id: str) -> Optional[PublisherProcess]:
        """Obtiene el estado de publicación de una cámara específica."""
        return self._processes.get(camera_id)
    
    def is_publishing(self, camera_id: str) -> bool:
        """Verifica si una cámara está publicando."""
        process = self._processes.get(camera_id)
        return process.is_active if process else False
    
    async def _monitor_process(self, camera_id: str) -> None:
        """
        Monitorea un proceso FFmpeg y maneja reconexiones.
        
        Args:
            camera_id: ID de la cámara a monitorear
        """
        process = self._processes.get(camera_id)
        if not process or not process.process:
            return
            
        try:
            # Monitorear el proceso
            while camera_id in self._processes:
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
                        pass
                else:
                    # Proceso terminó
                    returncode = proc.returncode if proc else -1
                    self.logger.warning(
                        f"Proceso FFmpeg terminó para {camera_id} "
                        f"con código {returncode}"
                    )
                    
                    # Manejar reconexión si es necesario
                    if process.status == PublishStatus.PUBLISHING:
                        await self._handle_process_exit(camera_id, returncode)
                    
                    break
                    
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Error en monitor de proceso {camera_id}: {e}")
            
    async def _handle_process_exit(
        self,
        camera_id: str,
        returncode: int
    ) -> None:
        """Maneja la salida inesperada de un proceso."""
        process = self._processes.get(camera_id)
        if not process:
            return
            
        process.error_count += 1
        
        # Determinar tipo de error por código de salida
        if returncode == 1:
            process.error_type = PublishErrorType.CONNECTION_FAILED
        elif returncode == 255:
            process.error_type = PublishErrorType.AUTHENTICATION_FAILED
        else:
            process.error_type = PublishErrorType.PROCESS_CRASHED
            
        # Intentar reconectar si no se ha excedido el límite
        if process.error_count <= self._config.max_reconnects:
            process.status = PublishStatus.RECONNECTING
            self.logger.info(
                f"Reintentando publicación para {camera_id} "
                f"(intento {process.error_count}/{self._config.max_reconnects})"
            )
            
            # Esperar antes de reintentar
            await asyncio.sleep(self._config.reconnect_delay)
            
            # Reintentar
            result = await self.start_publishing(camera_id, force_restart=True)
            if not result.success:
                process.status = PublishStatus.ERROR
                process.last_error = result.error
        else:
            # Máximo de reintentos alcanzado
            process.status = PublishStatus.ERROR
            process.last_error = "Máximo de reintentos alcanzado"
            self.logger.error(
                f"Publicación fallida definitivamente para {camera_id}"
            )
    
    async def _handle_ffmpeg_output(
        self,
        camera_id: str,
        line: bytes
    ) -> None:
        """Procesa salida de FFmpeg para extraer métricas y errores."""
        try:
            text = line.decode('utf-8', errors='ignore').strip()
            if not text:
                return
                
            # Log para debugging
            if "error" in text.lower() or "warning" in text.lower():
                self.logger.warning(f"FFmpeg [{camera_id}]: {text}")
                
            # Parsear métricas si es posible
            metrics = self._ffmpeg_manager.parse_metrics(text)
            if metrics:
                process = self._processes.get(camera_id)
                if process:
                    process.update_metrics(**metrics)
                    
        except Exception as e:
            self.logger.error(f"Error procesando salida FFmpeg: {e}")
    
    async def _build_source_url(self, camera) -> str:
        """Construye URL RTSP de origen con credenciales."""
        # Obtener el endpoint RTSP principal
        rtsp_url = camera.get_endpoint_url('rtsp_main')
        
        if not rtsp_url:
            # Construir URL por defecto
            config = camera.connection_config
            auth = ""
            if config.username and config.password:
                auth = f"{config.username}:{config.password}@"
            
            port = config.rtsp_port or 554
            rtsp_url = f"rtsp://{auth}{config.ip}:{port}/stream"
            
        return rtsp_url
    
    def _build_target_url(self, camera_id: str) -> str:
        """Construye URL RTSP de destino para MediaMTX."""
        path = self._config.get_publish_path(camera_id)
        base_url = self._config.mediamtx_url
        
        # Agregar autenticación si está configurada
        if self._config.auth_enabled and self._config.username:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(base_url)
            netloc = f"{self._config.username}:{self._config.password}@{parsed.netloc}"
            base_url = urlunparse(parsed._replace(netloc=netloc))
            
        return f"{base_url}/{path}"
    
    def _build_ffmpeg_command(
        self,
        source_url: str,
        target_url: str
    ) -> List[str]:
        """Construye comando FFmpeg optimizado."""
        cmd = [
            'ffmpeg',
            '-nostdin',                    # No input interactivo
            '-loglevel', 'warning',        # Solo warnings y errores
            '-stats',                      # Mostrar estadísticas
            '-rtsp_transport', 'tcp',      # Forzar TCP
            '-stimeout', '5000000',        # Timeout 5 segundos
            '-i', source_url,              # Input
            '-c', 'copy',                  # No recodificar
            '-f', 'rtsp',                  # Output format
        ]
        
        # Agregar transporte TCP para salida si está configurado
        if self._config.use_tcp:
            cmd.extend(['-rtsp_transport', 'tcp'])
            
        cmd.append(target_url)
        
        return cmd
    
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        self.logger.info("Limpiando RTSPPublisherService")
        
        # Señalar shutdown
        self._shutdown_event.set()
        
        # Detener todas las publicaciones
        await self.stop_all_publishing()
        
        self.logger.info("RTSPPublisherService limpiado")


# Singleton del servicio
_publisher_service: Optional[RTSPPublisherService] = None


def get_publisher_service(config: Optional[PublishConfiguration] = None) -> RTSPPublisherService:
    """
    Obtiene la instancia singleton del servicio.
    
    Args:
        config: Configuración (requerida en primera llamada)
        
    Returns:
        Instancia del servicio
    """
    global _publisher_service
    
    if _publisher_service is None:
        if config is None:
            raise ValueError("Se requiere configuración en la primera inicialización")
        _publisher_service = RTSPPublisherService(config)
        
    return _publisher_service