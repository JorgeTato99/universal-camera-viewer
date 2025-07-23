"""
Stream Manager específico para protocolo ONVIF.

Implementa la captura de video desde cámaras ONVIF, obteniendo
primero la URL RTSP del stream y luego delegando a RTSP.
"""

import asyncio
from typing import Optional

from services.video.rtsp_stream_manager import RTSPStreamManager
from services.protocol_handlers.onvif_handler import ONVIFHandler
from models.streaming import StreamStatus
from utils.sanitizers import sanitize_url


class ONVIFStreamManager(RTSPStreamManager):
    """
    Stream Manager para protocolo ONVIF.
    
    Utiliza ONVIF para obtener la URL del stream RTSP
    y luego delega la captura a RTSPStreamManager.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa el manager ONVIF."""
        super().__init__(*args, **kwargs)
        self._onvif_handler: Optional[ONVIFHandler] = None
        self._rtsp_url: Optional[str] = None
    
    async def _initialize_connection(self) -> None:
        """Inicializa la conexión ONVIF y obtiene URL RTSP."""
        try:
            self.logger.info(f"Inicializando conexión ONVIF para {self.connection_config.ip}")
            self.logger.debug(f"Config - IP: {self.connection_config.ip}, Username: {self.connection_config.username}, ONVIF Port: {self.connection_config.onvif_port}")
            
            # Crear handler ONVIF
            try:
                # Log de conexión config
                self.logger.debug(f"ConnectionConfig para ONVIFHandler:")
                self.logger.debug(f"  - IP: {self.connection_config.ip}")
                self.logger.debug(f"  - Username: {self.connection_config.username}")
                self.logger.debug(f"  - Password (longitud): {len(self.connection_config.password) if self.connection_config.password else 0}")
                self.logger.debug(f"  - ONVIF Port: {self.connection_config.onvif_port}")
                
                # ONVIFHandler espera ConnectionConfig y StreamingConfig
                from services.protocol_service import StreamingConfig
                streaming_config = StreamingConfig()
                self._onvif_handler = ONVIFHandler(self.connection_config, streaming_config)
                self.logger.debug("ONVIFHandler creado exitosamente")
            except Exception as e:
                self.logger.error(f"Error creando ONVIFHandler: {e}")
                self.logger.error(f"Tipo de error: {type(e).__name__}")
                import traceback
                self.logger.error(f"Traceback:\n{traceback.format_exc()}")
                raise
            
            # Conectar a la cámara ONVIF
            self.logger.info(f"Conectando a cámara ONVIF en {self.connection_config.ip}")
            
            try:
                # El ONVIFHandler ya tiene la configuración desde el constructor
                connection_success = await self._onvif_handler.connect()
                self.logger.debug(f"Resultado de conexión ONVIF: {connection_success}")
                
                if not connection_success:
                    raise ConnectionError("Error conectando ONVIF: No se pudo establecer conexión")
            except Exception as e:
                self.logger.error(f"Error en connect de ONVIFHandler: {e}")
                import traceback
                self.logger.error(f"Traceback:\n{traceback.format_exc()}")
                raise
            
            # Obtener información del dispositivo
            try:
                device_info = await self._onvif_handler.get_device_info()
                if isinstance(device_info, dict) and device_info.get('success'):
                    self.stream_model.metadata.update({
                        'manufacturer': device_info['data'].get('manufacturer'),
                        'model': device_info['data'].get('model'),
                        'firmware': device_info['data'].get('firmware_version')
                    })
            except Exception as e:
                self.logger.warning(f"No se pudo obtener información del dispositivo: {e}")
            
            # Obtener URL del stream principal
            stream_url_result = await self._get_stream_url()
            if not stream_url_result:
                raise ValueError("No se pudo obtener URL del stream ONVIF")
            
            # Guardar URL RTSP para uso posterior
            self._rtsp_url = stream_url_result
            
            self.logger.info(f"URL RTSP obtenida via ONVIF: {sanitize_url(stream_url_result)}")
            
            # La implementación base de RTSP usará _build_rtsp_url que sobrescribimos
            await super()._initialize_connection()
            
        except Exception as e:
            self.logger.error(f"Error inicializando conexión ONVIF: {e}")
            raise
    
    async def _get_stream_url(self) -> Optional[str]:
        """
        Obtiene la URL RTSP del stream principal via ONVIF.
        
        Returns:
            URL RTSP o None si falla
        """
        if not self._onvif_handler:
            return None
        
        try:
            # Para cámaras Dahua, usar directamente la URL estándar
            # ya que las URLs de ONVIF con proto=Onvif requieren autenticación especial
            brand = getattr(self.connection_config, 'brand', '').lower()
            if brand == 'dahua':
                self.logger.info("Cámara Dahua detectada, usando URL RTSP estándar")
                rtsp_url = self._build_fallback_rtsp_url()
                if rtsp_url:
                    self.logger.info(f"URL RTSP para Dahua: {sanitize_url(rtsp_url)}")
                    return rtsp_url
            
            # Para otras marcas, intentar obtener perfiles ONVIF
            try:
                profiles_result = self._onvif_handler.get_profiles()
                if profiles_result['success'] and profiles_result['data']:
                    profiles = profiles_result['data']
                    
                    # Buscar el perfil principal (usualmente el primero)
                    main_profile = None
                    for profile in profiles:
                        # Preferir perfiles con mayor resolución
                        if main_profile is None:
                            main_profile = profile
                        else:
                            # Comparar resoluciones si están disponibles
                            if 'video_encoder' in profile:
                                current_res = profile['video_encoder'].get('resolution', {})
                                main_res = main_profile.get('video_encoder', {}).get('resolution', {})
                                
                                current_pixels = current_res.get('width', 0) * current_res.get('height', 0)
                                main_pixels = main_res.get('width', 0) * main_res.get('height', 0)
                                
                                if current_pixels > main_pixels:
                                    main_profile = profile
                    
                    if main_profile:
                        # Obtener URL del stream para el perfil
                        profile_token = main_profile.get('token')
                        if profile_token:
                            stream_result = await self._onvif_handler.get_stream_uri(profile_token)
                            if stream_result['success']:
                                stream_url = stream_result['data']
                                
                                # Para Dahua, si la URL contiene proto=Onvif, usar la URL estándar
                                if 'proto=Onvif' in stream_url:
                                    self.logger.info("URL ONVIF con proto=Onvif detectada, usando URL estándar")
                                    rtsp_url = self._build_fallback_rtsp_url()
                                    if rtsp_url:
                                        return rtsp_url
                                
                                # Agregar credenciales a la URL si no las tiene
                                if '@' not in stream_url and self.connection_config.username and self.connection_config.password:
                                    # Parsear la URL para insertar credenciales
                                    import urllib.parse
                                    parsed = urllib.parse.urlparse(stream_url)
                                    # Reconstruir con credenciales
                                    auth = f"{self.connection_config.username}:{self.connection_config.password}@"
                                    stream_url = f"{parsed.scheme}://{auth}{parsed.netloc}{parsed.path}"
                                    if parsed.query:
                                        stream_url += f"?{parsed.query}"
                                    self.logger.info(f"Credenciales agregadas a URL RTSP")
                                
                                # Actualizar metadata con información del perfil
                                self.stream_model.metadata.update({
                                    'profile_name': main_profile.get('name', 'Unknown'),
                                    'profile_token': profile_token,
                                    'video_encoding': main_profile.get('video_encoder', {}).get('encoding'),
                                    'video_resolution': main_profile.get('video_encoder', {}).get('resolution')
                                })
                                
                                self.logger.info(f"URL RTSP obtenida desde ONVIF: {sanitize_url(stream_url)}")
                                return stream_url
                            else:
                                self.logger.error(f"Error obteniendo stream URI: {stream_result.get('error')}")
            except Exception as e:
                self.logger.warning(f"No se pudieron obtener perfiles ONVIF: {e}")
            
            # Fallback: usar URL RTSP estándar de la cámara
            self.logger.info("Usando fallback de URL RTSP estándar")
            
            # Construir URL RTSP manual basado en la marca
            rtsp_url = self._build_fallback_rtsp_url()
            if rtsp_url:
                self.logger.info(f"URL RTSP fallback: {sanitize_url(rtsp_url)}")
                return rtsp_url
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo stream URL ONVIF: {e}")
            return None
    
    def _build_fallback_rtsp_url(self) -> Optional[str]:
        """
        Construye URL RTSP de fallback cuando ONVIF falla.
        
        Returns:
            URL RTSP basada en la marca de la cámara
        """
        try:
            config = self.connection_config
            
            # Si ya hay una URL rtsp_main configurada, usarla
            if hasattr(config, 'rtsp_main') and config.rtsp_main:
                return config.rtsp_main
            
            # Si hay un rtsp_path configurado, usarlo
            if hasattr(config, 'rtsp_path') and config.rtsp_path:
                if config.username and config.password:
                    auth = f"{config.username}:{config.password}@"
                else:
                    auth = ""
                rtsp_port = getattr(config, 'rtsp_port', 554)
                rtsp_url = f"rtsp://{auth}{config.ip}:{rtsp_port}{config.rtsp_path}"
                self.logger.info(f"Usando rtsp_path configurado: {config.rtsp_path}")
                return rtsp_url
            
            # Construir URL basada en credenciales y puerto
            if config.username and config.password:
                auth = f"{config.username}:{config.password}@"
            else:
                auth = ""
            
            # Puerto RTSP por defecto o configurado
            rtsp_port = getattr(config, 'rtsp_port', 554)
            
            # Path según la marca detectada
            brand = getattr(config, 'brand', 'dahua').lower()
            self.logger.info(f"Marca detectada para fallback: {brand}")
            
            # Paths conocidos por marca
            brand_paths = {
                'dahua': '/cam/realmonitor?channel=1&subtype=0',
                'hikvision': '/Streaming/Channels/101',
                'tplink': '/stream1',  # TP-Link usa stream1/stream2
                'tp-link': '/stream1',  # Variante con guión
                'tapo': '/stream1',     # Cámaras Tapo de TP-Link
                'axis': '/axis-media/media.amp',
                'bosch': '/rtsp_tunnel',
                'panasonic': '/MediaInput/h264/stream_1',
                'steren': '/live/ch00_0',  # Steren CCTV
                'reolink': '/h264Preview_01_main',
                'xiaomi': '/live/ch0',
                'default': '/cam/realmonitor?channel=1&subtype=0'  # Dahua por defecto
            }
            
            path = brand_paths.get(brand, brand_paths['default'])
            
            # Construir URL completa
            rtsp_url = f"rtsp://{auth}{config.ip}:{rtsp_port}{path}"
            
            return rtsp_url
            
        except Exception as e:
            self.logger.error(f"Error construyendo URL RTSP fallback: {e}")
            return None
    
    async def _close_connection(self) -> None:
        """Cierra las conexiones ONVIF y RTSP."""
        # Cerrar ONVIF
        if self._onvif_handler:
            await self._onvif_handler.disconnect()
            self._onvif_handler = None
        
        # Cerrar RTSP
        await super()._close_connection()
    
    def _build_rtsp_url(self) -> str:
        """
        Construye URL RTSP - sobrescribe el método de RTSPStreamManager.
        
        Returns:
            URL RTSP obtenida via ONVIF
        """
        if self._rtsp_url:
            return self._rtsp_url
        else:
            # Fallback al método base si no tenemos URL de ONVIF
            return super()._build_rtsp_url()