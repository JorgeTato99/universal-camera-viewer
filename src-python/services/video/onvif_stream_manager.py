"""
Stream Manager específico para protocolo ONVIF.

Implementa la captura de video desde cámaras ONVIF, obteniendo
primero la URL RTSP del stream y luego delegando a RTSP.
"""

import asyncio
from typing import Optional

from .rtsp_stream_manager import RTSPStreamManager
from ..protocol_handlers.onvif_handler import ONVIFHandler
from ...models.streaming import StreamStatus


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
    
    async def _initialize_connection(self) -> None:
        """Inicializa la conexión ONVIF y obtiene URL RTSP."""
        try:
            # Crear handler ONVIF
            self._onvif_handler = ONVIFHandler()
            
            # Conectar a la cámara ONVIF
            self.logger.info(f"Conectando a cámara ONVIF en {self.connection_config.ip}")
            
            connection_result = await self._onvif_handler.connect(
                ip=self.connection_config.ip,
                username=self.connection_config.username,
                password=self.connection_config.password,
                port=self.connection_config.port or 80
            )
            
            if not connection_result['success']:
                raise ConnectionError(f"Error conectando ONVIF: {connection_result.get('error')}")
            
            # Obtener información del dispositivo
            device_info = await self._onvif_handler.get_device_info()
            if device_info['success']:
                self.stream_model.metadata.update({
                    'manufacturer': device_info['data'].get('manufacturer'),
                    'model': device_info['data'].get('model'),
                    'firmware': device_info['data'].get('firmware_version')
                })
            
            # Obtener URL del stream principal
            stream_url_result = await self._get_stream_url()
            if not stream_url_result:
                raise ValueError("No se pudo obtener URL del stream ONVIF")
            
            # Guardar URL RTSP para uso posterior
            self.connection_config.rtsp_url = stream_url_result
            
            self.logger.info(f"URL RTSP obtenida via ONVIF: {self._sanitize_url(stream_url_result)}")
            
            # Delegar a la implementación RTSP
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
            # Obtener perfiles de media
            profiles_result = await self._onvif_handler.get_profiles()
            if not profiles_result['success'] or not profiles_result['data']:
                self.logger.error("No se pudieron obtener perfiles ONVIF")
                return None
            
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
            
            if not main_profile:
                self.logger.error("No se encontró un perfil válido")
                return None
            
            # Obtener URL del stream para el perfil
            profile_token = main_profile.get('token')
            if not profile_token:
                self.logger.error("Perfil sin token")
                return None
            
            stream_result = await self._onvif_handler.get_stream_uri(profile_token)
            if not stream_result['success']:
                self.logger.error(f"Error obteniendo stream URI: {stream_result.get('error')}")
                return None
            
            stream_url = stream_result['data']
            
            # Actualizar metadata con información del perfil
            self.stream_model.metadata.update({
                'profile_name': main_profile.get('name', 'Unknown'),
                'profile_token': profile_token,
                'video_encoding': main_profile.get('video_encoder', {}).get('encoding'),
                'video_resolution': main_profile.get('video_encoder', {}).get('resolution')
            })
            
            return stream_url
            
        except Exception as e:
            self.logger.error(f"Error obteniendo stream URL ONVIF: {e}")
            return None
    
    async def _close_connection(self) -> None:
        """Cierra las conexiones ONVIF y RTSP."""
        # Cerrar ONVIF
        if self._onvif_handler:
            await self._onvif_handler.disconnect()
            self._onvif_handler = None
        
        # Cerrar RTSP
        await super()._close_connection()
        
        self.logger.debug("Conexiones ONVIF y RTSP cerradas")