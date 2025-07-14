"""
RTSPHandler - Manejador unificado de protocolo RTSP para cámaras IP.

Migra y consolida funcionalidad de:
- RTSPConnection (Dahua)
- TPLinkConnection (TP-Link Tapo)  
- SterenConnection (Steren CCTV-235)

Utiliza perfiles de URL por marca en lugar de clases separadas.
"""

import asyncio
import cv2
import logging
from typing import Optional, Dict, Any, List
import numpy as np

from .base_handler import BaseHandler
from ..protocol_service import ConnectionState, ProtocolCapabilities, StreamingConfig
from ...models import ConnectionConfig


class RTSPHandler(BaseHandler):
    """
    Manejador unificado de protocolo RTSP para cámaras IP.
    
    Soporta múltiples marcas mediante perfiles de URL:
    - Dahua: /cam/realmonitor?channel=X&subtype=Y
    - TP-Link: /stream1, /stream2, /stream8
    - Steren: /live/channel0, /live/channel1
    - Genérico: URLs RTSP estándar
    """
    
    # Perfiles de URL por marca
    URL_PROFILES = {
        'dahua': {
            'main': "rtsp://{username}:{password}@{ip}:{rtsp_port}/cam/realmonitor?channel=1&subtype=0",
            'sub': "rtsp://{username}:{password}@{ip}:{rtsp_port}/cam/realmonitor?channel=1&subtype=1",
            'qualities': {
                'main': 'HD (1920x1080) - H264',
                'sub': 'SD (704x576) - H264'
            },
            'default_rtsp_port': 554
        },
        'tplink': {
            'main': "rtsp://{username}:{password}@{ip}:{rtsp_port}/stream1",
            'sub': "rtsp://{username}:{password}@{ip}:{rtsp_port}/stream2", 
            'jpeg': "rtsp://{username}:{password}@{ip}:{rtsp_port}/stream8",
            'qualities': {
                'main': 'HD (2560x1440) - H264',
                'sub': 'SD (640x360) - H264',
                'jpeg': 'JPEG Stream'
            },
            'default_rtsp_port': 554
        },
        'steren': {
            'main': "rtsp://{username}:{password}@{ip}:{rtsp_port}/live/channel0",
            'sub': "rtsp://{username}:{password}@{ip}:{rtsp_port}/live/channel1",
            'qualities': {
                'main': 'Ultra HD (2560x1440) - HEVC',
                'sub': 'Standard (640x360) - H264'
            },
            'default_rtsp_port': 5543
        },
        'generic': {
            'main': "rtsp://{username}:{password}@{ip}:{rtsp_port}/live",
            'sub': "rtsp://{username}:{password}@{ip}:{rtsp_port}/live2",
            'qualities': {
                'main': 'Main Stream',
                'sub': 'Sub Stream'
            },
            'default_rtsp_port': 554
        }
    }
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el handler RTSP con compatibilidad dual.
        
        Formatos soportados:
        - Nuevo: RTSPHandler(config: ConnectionConfig, streaming_config: StreamingConfig)
        - Antiguo: RTSPHandler(camera_ip: str, credentials: dict)
        - Legacy: RTSPHandler(config_manager)
        """
        super().__init__(*args, **kwargs)
        
        # Configuración específica RTSP
        self._setup_rtsp_config()
        
        # Estado RTSP
        self.rtsp_url: Optional[str] = None
        self.current_stream_type = 'main'
        self.detected_brand = 'generic'
        
        # Cache para optimización
        self._stream_urls_cache: Optional[Dict[str, str]] = None
        self._frame_properties_cache: Optional[Dict[str, Any]] = None
    
    def _setup_rtsp_config(self):
        """Configura parámetros específicos RTSP."""
        # Detectar configuración según API utilizada
        if hasattr(self, 'config') and self.config:
            # Nueva API
            self.ip = self.config.ip
            self.username = self.config.username
            self.password = self.config.password
            self.rtsp_port = getattr(self.config, 'rtsp_port', 554)
            self.channel = getattr(self.config, 'channel', 1)
            self.subtype = getattr(self.config, 'subtype', 0)
        else:
            # API antigua/legacy - ya configurado en BaseHandler
            self.ip = self.camera_ip
            self.rtsp_port = getattr(self, 'rtsp_port', 554)
            self.channel = getattr(self, 'channel', 1)
            self.subtype = getattr(self, 'subtype', 0)
        
        # Detectar marca para configuración específica
        self._detect_brand()
    
    def _detect_brand(self):
        """Detecta la marca de cámara para usar el perfil correcto."""
        # Detectar por configuración específica
        if hasattr(self, 'config_manager'):
            config_manager = self.config_manager
            
            # TP-Link
            if (hasattr(config_manager, 'tplink_ip') and 
                getattr(config_manager, 'tplink_ip', None)):
                self.detected_brand = 'tplink'
                self.ip = config_manager.tplink_ip
                self.username = getattr(config_manager, 'tplink_user', 'admin')
                self.password = getattr(config_manager, 'tplink_password', '')
                return
            
            # Steren
            if (hasattr(config_manager, 'steren_ip') and 
                getattr(config_manager, 'steren_ip', None)):
                self.detected_brand = 'steren'
                self.ip = config_manager.steren_ip
                self.username = getattr(config_manager, 'steren_user', 'admin')
                self.password = getattr(config_manager, 'steren_password', '')
                self.rtsp_port = getattr(config_manager, 'steren_rtsp_port', 5543)
                return
        
        # Detectar por puerto RTSP
        if self.rtsp_port == 5543:
            self.detected_brand = 'steren'
        elif self.rtsp_port == 554:
            # Podría ser TP-Link o Dahua, asumir genérico
            self.detected_brand = 'generic'
        else:
            self.detected_brand = 'generic'
        
        self.logger.info(f"Marca detectada: {self.detected_brand}")
    
    def _get_stream_urls(self) -> Dict[str, str]:
        """
        Obtiene URLs de stream según la marca detectada.
        
        Returns:
            Diccionario con URLs de stream por tipo
        """
        if self._stream_urls_cache:
            return self._stream_urls_cache
        
        profile = self.URL_PROFILES.get(self.detected_brand, self.URL_PROFILES['generic'])
        
        # Usar puerto por defecto si no se especificó
        if not hasattr(self, 'rtsp_port') or not self.rtsp_port:
            self.rtsp_port = profile['default_rtsp_port']
        
        # Construir URLs
        urls = {}
        for stream_type, url_template in profile.items():
            if stream_type not in ['qualities', 'default_rtsp_port']:
                urls[stream_type] = url_template.format(
                    username=self.username,
                    password=self.password,
                    ip=self.ip,
                    rtsp_port=self.rtsp_port,
                    channel=getattr(self, 'channel', 1),
                    subtype=getattr(self, 'subtype', 0)
                )
        
        self._stream_urls_cache = urls
        return urls
    
    def _get_stream_qualities(self) -> Dict[str, str]:
        """Obtiene descripción de calidades por marca."""
        profile = self.URL_PROFILES.get(self.detected_brand, self.URL_PROFILES['generic'])
        return profile.get('qualities', {})
    
    async def connect(self) -> bool:
        """
        Establece conexión RTSP con la cámara.
        
        Returns:
            True si la conexión fue exitosa
        """
        self._set_state(ConnectionState.CONNECTING)
        
        try:
            if not self.username or not self.password:
                self.logger.warning("Conectando RTSP sin credenciales")
            
            self.logger.info(f"Iniciando conexión RTSP a {self.ip}:{self.rtsp_port} ({self.detected_brand})")
            
            # Intentar establecer conexión
            success = await self._establish_connection()
            
            if success:
                self._set_state(ConnectionState.CONNECTED)
                self.logger.info(f"Conexión RTSP establecida: {self.detected_brand} - {self.current_stream_type}")
                return True
            else:
                self._set_state(ConnectionState.ERROR)
                return False
                
        except Exception as e:
            self.logger.error(f"Error de conexión RTSP: {str(e)}")
            self._set_state(ConnectionState.ERROR)
            return False
    
    async def _establish_connection(self) -> bool:
        """
        Establece la conexión RTSP probando múltiples URLs.
        
        Returns:
            True si alguna conexión fue exitosa
        """
        stream_urls = self._get_stream_urls()
        qualities = self._get_stream_qualities()
        
        # Probar URLs en orden de prioridad
        for stream_type, url in stream_urls.items():
            try:
                self.logger.info(f"Probando stream '{stream_type}': {qualities.get(stream_type, 'Unknown')}")
                
                # Crear VideoCapture en thread separado
                loop = asyncio.get_event_loop()
                cap = await loop.run_in_executor(None, self._create_video_capture, url)
                
                if cap and cap.isOpened():
                    # Probar leer un frame
                    ret, frame = await loop.run_in_executor(None, cap.read)
                    
                    if ret and frame is not None:
                        self._stream_handle = cap
                        self.rtsp_url = url
                        self.current_stream_type = stream_type
                        
                        # Cache propiedades del frame
                        await self._cache_frame_properties(frame)
                        
                        quality_desc = qualities.get(stream_type, 'Unknown')
                        self.logger.info(f"Conexión RTSP exitosa: {quality_desc}")
                        return True
                    else:
                        cap.release()
                else:
                    if cap:
                        cap.release()
                        
            except Exception as e:
                self.logger.debug(f"Error con stream '{stream_type}': {str(e)}")
                continue
        
        self.logger.error("No se pudo establecer conexión RTSP con ninguna URL")
        return False
    
    def _create_video_capture(self, url: str) -> Optional[cv2.VideoCapture]:
        """Crea VideoCapture con optimizaciones (método síncrono)."""
        try:
            # Suprimir warnings de FFmpeg/OpenCV
            cv2.setLogLevel(3)
            
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                # Optimizaciones RTSP
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo para latencia baja
                cap.set(cv2.CAP_PROP_FPS, 30)  # FPS objetivo
                # Usar fourcc estándar H264 de OpenCV
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('H', '2', '6', '4'))
                return cap
        except Exception as e:
            self.logger.error(f"Error creando VideoCapture: {str(e)}")
        return None
    
    async def _cache_frame_properties(self, frame: np.ndarray):
        """Cache propiedades del frame para optimización."""
        try:
            if self._stream_handle:
                height, width = frame.shape[:2]
                fps = self._stream_handle.get(cv2.CAP_PROP_FPS)
                fourcc = int(self._stream_handle.get(cv2.CAP_PROP_FOURCC))
                
                self._frame_properties_cache = {
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "fourcc": fourcc,
                    "buffer_size": int(self._stream_handle.get(cv2.CAP_PROP_BUFFERSIZE))
                }
                
                self.logger.info(f"Propiedades: {width}x{height} @ {fps} FPS")
        except Exception as e:
            self.logger.debug(f"Error cacheando propiedades: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Cierra la conexión RTSP.
        
        Returns:
            True si se desconectó correctamente
        """
        try:
            # Detener streaming si está activo
            if self.is_streaming:
                await self.stop_streaming()
            
            # Cerrar stream handle
            if self._stream_handle:
                self._stream_handle.release()
                self._stream_handle = None
            
            # Limpiar estado
            self.rtsp_url = None
            self._stream_urls_cache = None
            self._frame_properties_cache = None
            
            self._set_state(ConnectionState.DISCONNECTED)
            self.logger.info("Conexión RTSP cerrada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cerrando conexión RTSP: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Prueba la conexión RTSP sin establecerla permanentemente.
        
        Returns:
            True si la conexión es posible
        """
        try:
            stream_urls = self._get_stream_urls()
            
            # Probar primera URL disponible
            for stream_type, url in stream_urls.items():
                try:
                    loop = asyncio.get_event_loop()
                    test_cap = await loop.run_in_executor(None, cv2.VideoCapture, url)
                    
                    if test_cap and test_cap.isOpened():
                        ret, frame = await loop.run_in_executor(None, test_cap.read)
                        test_cap.release()
                        
                        if ret and frame is not None:
                            return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Test de conexión RTSP falló: {str(e)}")
            return False
    
    async def capture_snapshot(self) -> Optional[bytes]:
        """
        Captura un snapshot de la cámara vía RTSP.
        
        Returns:
            Datos de la imagen en bytes o None si falla
        """
        if not self.is_connected or not self._stream_handle:
            self.logger.error("Conexión RTSP no establecida")
            return None
        
        try:
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(None, self._stream_handle.read)
            
            if ret and frame is not None:
                # Codificar frame como JPEG
                success, encoded_img = cv2.imencode('.jpg', frame)
                if success:
                    return encoded_img.tobytes()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error capturando snapshot RTSP: {str(e)}")
            return None
    
    async def start_streaming(self) -> bool:
        """
        Inicia el streaming de video RTSP.
        
        Returns:
            True si el streaming se inició exitosamente
        """
        if self.is_streaming:
            return True
        
        if not self.is_connected or not self._stream_handle:
            self.logger.error("Conexión RTSP no establecida para streaming")
            return False
        
        try:
            # Iniciar worker thread para streaming
            self._streaming_active = True
            self._streaming_thread = asyncio.create_task(self._streaming_worker())
            
            self._set_state(ConnectionState.STREAMING)
            self.logger.info("Streaming RTSP iniciado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando streaming RTSP: {str(e)}")
            return False
    
    async def stop_streaming(self) -> bool:
        """
        Detiene el streaming de video.
        
        Returns:
            True si el streaming se detuvo exitosamente
        """
        try:
            self._streaming_active = False
            
            # Cancelar worker thread
            if self._streaming_thread:
                self._streaming_thread.cancel()
                try:
                    await self._streaming_thread
                except asyncio.CancelledError:
                    pass
                self._streaming_thread = None
            
            self._set_state(ConnectionState.CONNECTED)
            return True
            
        except Exception as e:
            self.logger.error(f"Error deteniendo streaming RTSP: {str(e)}")
            return False
    
    async def _streaming_worker(self):
        """Worker asíncrono para streaming de frames RTSP."""
        while self._streaming_active and self._stream_handle:
            try:
                # Leer frame de forma no bloqueante
                loop = asyncio.get_event_loop()
                ret, frame = await loop.run_in_executor(None, self._stream_handle.read)
                
                if ret and frame is not None:
                    # Actualizar estadísticas
                    self._update_frame_stats(frame)
                    
                    # Notificar callbacks
                    self._notify_frame_callbacks(frame)
                else:
                    # Sleep corto si no hay frame
                    await asyncio.sleep(0.001)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._streaming_active:
                    self.logger.error(f"Error en streaming worker RTSP: {str(e)}")
                break
    
    def get_capabilities(self) -> ProtocolCapabilities:
        """Obtiene capacidades RTSP."""
        return ProtocolCapabilities(
            supports_streaming=True,
            supports_snapshots=True,
            supports_ptz=False,  # Depende de la cámara específica
            supports_audio=False,
            max_resolution="2560x1440",  # TP-Link/Steren máximo
            supported_codecs=["H264", "HEVC", "MJPEG"]
        )
    
    # ==========================================
    # MÉTODOS ESPECÍFICOS RTSP (Compatibilidad)
    # ==========================================
    
    def get_frame_properties(self) -> Dict[str, Any]:
        """
        Obtiene las propiedades del stream de video.
        
        Returns:
            Diccionario con propiedades del stream
        """
        if self._frame_properties_cache:
            return self._frame_properties_cache.copy()
        
        if not self.is_connected or not self._stream_handle:
            return {}
        
        try:
            properties = {
                "width": int(self._stream_handle.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self._stream_handle.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": self._stream_handle.get(cv2.CAP_PROP_FPS),
                "fourcc": int(self._stream_handle.get(cv2.CAP_PROP_FOURCC)),
                "buffer_size": int(self._stream_handle.get(cv2.CAP_PROP_BUFFERSIZE))
            }
            
            # Cache para futuras consultas
            self._frame_properties_cache = properties
            return properties
            
        except Exception as e:
            self.logger.error(f"Error obteniendo propiedades del stream: {str(e)}")
            return {}
    
    def get_stream_info(self) -> Dict[str, Any]:
        """
        Obtiene información completa del stream actual.
        
        Returns:
            Diccionario con información del stream
        """
        stream_urls = self._get_stream_urls()
        qualities = self._get_stream_qualities()
        properties = self.get_frame_properties()
        
        return {
            'brand': self.detected_brand,
            'current_stream': self.current_stream_type,
            'quality': qualities.get(self.current_stream_type, 'Unknown'),
            'url': self.rtsp_url,
            'available_streams': list(stream_urls.keys()),
            'properties': properties
        }
    
    async def switch_stream_quality(self, stream_type: str) -> bool:
        """
        Cambia la calidad del stream.
        
        Args:
            stream_type: Tipo de stream ('main', 'sub', 'jpeg')
            
        Returns:
            True si el cambio fue exitoso
        """
        stream_urls = self._get_stream_urls()
        
        if stream_type not in stream_urls:
            self.logger.error(f"Stream type '{stream_type}' no disponible para {self.detected_brand}")
            return False
        
        try:
            # Detener streaming actual si está activo
            was_streaming = self.is_streaming
            if was_streaming:
                await self.stop_streaming()
            
            # Cerrar conexión actual
            if self._stream_handle:
                self._stream_handle.release()
                self._stream_handle = None
            
            # Intentar nueva conexión
            new_url = stream_urls[stream_type]
            loop = asyncio.get_event_loop()
            cap = await loop.run_in_executor(None, self._create_video_capture, new_url)
            
            if cap and cap.isOpened():
                ret, frame = await loop.run_in_executor(None, cap.read)
                
                if ret and frame is not None:
                    self._stream_handle = cap
                    self.rtsp_url = new_url
                    self.current_stream_type = stream_type
                    
                    # Actualizar cache de propiedades
                    await self._cache_frame_properties(frame)
                    
                    # Reanudar streaming si estaba activo
                    if was_streaming:
                        await self.start_streaming()
                    
                    qualities = self._get_stream_qualities()
                    quality_desc = qualities.get(stream_type, 'Unknown')
                    self.logger.info(f"Stream cambiado a '{stream_type}': {quality_desc}")
                    return True
                else:
                    cap.release()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error cambiando stream quality: {str(e)}")
            return False
    
    def get_available_streams(self) -> List[Dict[str, str]]:
        """
        Obtiene lista de streams disponibles.
        
        Returns:
            Lista de diccionarios con información de streams
        """
        stream_urls = self._get_stream_urls()
        qualities = self._get_stream_qualities()
        
        streams = []
        for stream_type in stream_urls:
            streams.append({
                'type': stream_type,
                'quality': qualities.get(stream_type, 'Unknown'),
                'current': stream_type == self.current_stream_type
            })
        
        return streams 