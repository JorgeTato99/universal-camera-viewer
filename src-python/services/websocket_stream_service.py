"""
Servicio para gestión de streaming por WebSocket.

Este servicio actúa como intermediario entre los handlers de WebSocket
y los presenters, manteniendo la arquitectura MVP.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import socket
import subprocess
import platform

from services.base_service import BaseService
from services.camera_manager_service import camera_manager_service
from presenters.streaming.video_stream_presenter import VideoStreamPresenter
from models import ConnectionConfig
from models.streaming import StreamProtocol
from config.settings import settings
from utils.exceptions import StreamingError


class WebSocketStreamService(BaseService):
    """
    Servicio que gestiona el streaming de video a través de WebSocket.
    
    Responsabilidades:
    - Gestionar la conexión con cámaras
    - Coordinar con el VideoStreamPresenter
    - Validar conectividad de red
    - Manejar configuraciones de cámara
    """
    
    def __init__(self):
        """Inicializa el servicio."""
        super().__init__()
        self._presenter: Optional[VideoStreamPresenter] = None
        self._active_streams: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> None:
        """Inicializa el servicio y sus dependencias."""
        self.logger.info("Initializing WebSocketStreamService")
        self._presenter = VideoStreamPresenter()
        await self._presenter.initialize()
        
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        if self._presenter:
            await self._presenter.cleanup()
        self._active_streams.clear()
        
    async def check_camera_connectivity(self, ip: str, port: int = 554) -> bool:
        """
        Verifica si una cámara es accesible en la red.
        
        Args:
            ip: Dirección IP de la cámara
            port: Puerto a verificar (default: 554 para RTSP)
            
        Returns:
            True si la cámara es accesible
        """
        try:
            # Verificar con socket TCP
            self.logger.info(f"Checking connectivity to {ip}:{port}")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                self.logger.info(f"Port {port} accessible on {ip}")
                return True
            else:
                self.logger.warning(f"Port {port} not accessible on {ip}")
                
                # Intentar ping como fallback
                return await self._check_ping(ip)
                
        except Exception as e:
            self.logger.error(f"Error checking connectivity: {e}")
            return False
            
    async def _check_ping(self, ip: str) -> bool:
        """Verifica conectividad mediante ping."""
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-w', '1000', ip] if platform.system().lower() == 'windows' else ['ping', param, '1', '-W', '1', ip]
            
            # Ejecutar ping de forma asíncrona
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                self.logger.info(f"Ping successful to {ip}")
                return True
            else:
                self.logger.error(f"No ping response from {ip}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing ping: {e}")
            return False
            
    async def start_camera_stream(
        self,
        camera_id: str,
        stream_config: Dict[str, Any],
        on_frame_callback: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Inicia el streaming de una cámara.
        
        Args:
            camera_id: ID de la cámara
            stream_config: Configuración del stream
            on_frame_callback: Callback para frames recibidos
            
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            # Validar parámetros
            if not camera_id:
                raise ValueError("camera_id es requerido")
                
            # Obtener configuración de la cámara
            camera_config = await self._get_camera_configuration(camera_id)
            
            # Verificar conectividad si está habilitado
            if stream_config.get('check_connectivity', True):
                is_accessible = await self.check_camera_connectivity(
                    camera_config['ip'],
                    camera_config.get('rtsp_port', 554)
                )
                
                if not is_accessible:
                    return {
                        'success': False,
                        'error': 'Camera not accessible on network',
                        'camera_id': camera_id
                    }
            
            # Crear configuración de conexión
            connection_config = self._create_connection_config(camera_config)
            
            # Determinar protocolo
            protocol = StreamProtocol(camera_config.get('protocol', 'rtsp').lower())
            
            # Opciones del stream
            options = {
                'targetFps': stream_config.get('fps', 30),
                'bufferSize': stream_config.get('buffer_size', 5),
                'quality': stream_config.get('quality', 'medium')
            }
            
            # Iniciar stream a través del presenter
            success = await self._presenter.start_camera_stream(
                camera_id=camera_id,
                connection_config=connection_config,
                protocol=protocol,
                options=options,
                on_frame_callback=on_frame_callback
            )
            
            if success:
                # Guardar información del stream activo
                self._active_streams[camera_id] = {
                    'config': camera_config,
                    'stream_config': stream_config,
                    'started_at': datetime.utcnow(),
                    'protocol': protocol.value
                }
                
                return {
                    'success': True,
                    'camera_id': camera_id,
                    'protocol': protocol.value,
                    'message': 'Stream started successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to start stream',
                    'camera_id': camera_id
                }
                
        except StreamingError as e:
            # Re-lanzar errores específicos de streaming
            self.logger.error(f"Streaming error for {camera_id}: {e.to_dict()}")
            return {
                'success': False,
                'error': e.message,
                'error_code': e.error_code,
                'camera_id': camera_id
            }
        except Exception as e:
            # Envolver errores inesperados
            self.logger.error(f"Unexpected error starting stream for {camera_id}: {e}", exc_info=True)
            wrapped_error = StreamingError(
                message=f"Error inesperado iniciando stream: {str(e)}",
                error_code="STREAM_START_FAILED",
                context={'camera_id': camera_id, 'original_error': str(e)}
            )
            return {
                'success': False,
                'error': wrapped_error.message,
                'error_code': wrapped_error.error_code,
                'camera_id': camera_id
            }
            
    async def stop_camera_stream(self, camera_id: str) -> Dict[str, Any]:
        """
        Detiene el streaming de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Diccionario con el resultado
        """
        try:
            if camera_id not in self._active_streams:
                return {
                    'success': False,
                    'error': 'Stream not active',
                    'camera_id': camera_id
                }
                
            # Detener a través del presenter
            success = await self._presenter.stop_camera_stream(camera_id)
            
            if success:
                # Limpiar información del stream
                self._active_streams.pop(camera_id, None)
                
                return {
                    'success': True,
                    'camera_id': camera_id,
                    'message': 'Stream stopped successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to stop stream',
                    'camera_id': camera_id
                }
                
        except StreamingError as e:
            # Re-lanzar errores específicos de streaming
            self.logger.error(f"Streaming error stopping {camera_id}: {e.to_dict()}")
            return {
                'success': False,
                'error': e.message,
                'error_code': e.error_code,
                'camera_id': camera_id
            }
        except Exception as e:
            # Envolver errores inesperados
            self.logger.error(f"Unexpected error stopping stream for {camera_id}: {e}", exc_info=True)
            wrapped_error = StreamingError(
                message=f"Error inesperado deteniendo stream: {str(e)}",
                error_code="STREAM_STOP_FAILED",
                context={'camera_id': camera_id, 'original_error': str(e)}
            )
            return {
                'success': False,
                'error': wrapped_error.message,
                'error_code': wrapped_error.error_code,
                'camera_id': camera_id
            }
            
    async def get_stream_metrics(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene métricas del stream activo.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Métricas del stream o None
        """
        if camera_id not in self._active_streams:
            return None
            
        # Obtener métricas del presenter
        presenter_streams = self._presenter.get_active_streams()
        
        if camera_id in presenter_streams:
            metrics = presenter_streams[camera_id]
            
            # Agregar información adicional
            stream_info = self._active_streams[camera_id]
            metrics['uptime_seconds'] = (
                datetime.utcnow() - stream_info['started_at']
            ).total_seconds()
            
            return metrics
            
        return None
        
    async def _get_camera_configuration(self, camera_id: str) -> Dict[str, Any]:
        """
        Obtiene la configuración de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Configuración de la cámara
        """
        try:
            # Obtener cámara desde el servicio
            camera = await camera_manager_service.get_camera(camera_id)
            
            # Construir configuración desde el modelo de cámara
            self.logger.debug(f"[WebSocketStream] Construyendo config para {camera_id}:")
            self.logger.debug(f"  - Username: {camera.connection_config.username}")
            self.logger.debug(f"  - Password (longitud): {len(camera.connection_config.password) if camera.connection_config.password else 0}")
            self.logger.debug(f"  - Password (primeros 3): {camera.connection_config.password[:3] if camera.connection_config.password and len(camera.connection_config.password) >= 3 else 'N/A'}")
            
            config = {
                'ip': camera.connection_config.ip,
                'username': camera.connection_config.username,
                'password': camera.connection_config.password,
                'rtsp_port': camera.connection_config.rtsp_port,
                'onvif_port': camera.connection_config.onvif_port,
                'http_port': camera.connection_config.http_port,
                'protocol': camera.protocol.value if camera.protocol else 'rtsp',
                'brand': camera.brand,
                'timeout': camera.connection_config.timeout,
                'max_retries': camera.connection_config.max_retries
            }
            
            # Agregar información adicional desde endpoints descubiertos
            rtsp_endpoint = camera.get_endpoint_url('rtsp_main')
            if rtsp_endpoint:
                # Extraer el path de la URL completa
                import urllib.parse
                parsed = urllib.parse.urlparse(rtsp_endpoint)
                # Incluir tanto el path como los query parameters
                config['rtsp_path'] = parsed.path
                if parsed.query:
                    config['rtsp_path'] += f"?{parsed.query}"
                self.logger.info(f"Usando path RTSP desde endpoint descubierto: {config['rtsp_path']}")
            else:
                # Path por defecto según la marca
                if camera.brand.lower() == 'dahua':
                    config['rtsp_path'] = '/cam/realmonitor?channel=1&subtype=0'
                else:
                    config['rtsp_path'] = '/stream1'
                self.logger.info(f"Usando path RTSP por defecto para {camera.brand}: {config['rtsp_path']}")
            
            self.logger.info(f"Configuración obtenida para cámara {camera_id}: IP={config['ip']}, Protocol={config['protocol']}")
            return config
            
        except Exception as e:
            self.logger.error(f"Error obteniendo configuración de cámara {camera_id}: {e}")
            raise StreamingError(
                message=f"No se pudo obtener configuración de cámara: {str(e)}",
                error_code="CAMERA_CONFIG_ERROR",
                context={'camera_id': camera_id}
            )
            
    def _create_connection_config(self, camera_config: Dict[str, Any]) -> ConnectionConfig:
        """
        Crea un objeto ConnectionConfig desde la configuración.
        
        Args:
            camera_config: Diccionario con configuración
            
        Returns:
            Objeto ConnectionConfig
        """
        config = ConnectionConfig(
            ip=camera_config['ip'],
            username=camera_config.get('username', ''),
            password=camera_config.get('password', ''),
            rtsp_port=camera_config.get('rtsp_port', 554),
            onvif_port=camera_config.get('onvif_port', 80),
            http_port=camera_config.get('http_port', 80),
            timeout=camera_config.get('timeout', 10),
            max_retries=camera_config.get('max_retries', 3)
        )
        
        # Agregar atributos adicionales necesarios
        for key in ['protocol', 'channel', 'subtype', 'port', 'brand', 'rtsp_path']:
            if key in camera_config:
                setattr(config, key, camera_config[key])
                
        # Alias para compatibilidad
        if hasattr(config, 'rtsp_port'):
            config.port = config.rtsp_port  # type: ignore
            
        return config
        
    def get_active_streams(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene información de todos los streams activos."""
        return self._active_streams.copy()
        
    def is_streaming(self, camera_id: str) -> bool:
        """Verifica si una cámara está transmitiendo."""
        return camera_id in self._active_streams


# Instancia singleton del servicio
websocket_stream_service = WebSocketStreamService()