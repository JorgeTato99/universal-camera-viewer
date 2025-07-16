"""
ONVIFHandler - Manejador de protocolo ONVIF para cámaras IP.

Migra funcionalidad de ONVIFConnection (src_old) hacia la nueva arquitectura MVP
manteniendo compatibilidad y mejorando con patrones async/await.
"""

import asyncio
import cv2
import logging
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

try:
    from onvif import ONVIFCamera
    from onvif.exceptions import ONVIFError
    ONVIF_AVAILABLE = True
except ImportError:
    ONVIF_AVAILABLE = False

from services.protocol_handlers.base_handler import BaseHandler
from services.protocol_service import ConnectionState, ProtocolCapabilities, StreamingConfig
from models import ConnectionConfig


class ONVIFHandler(BaseHandler):
    """
    Manejador de protocolo ONVIF para cámaras IP.
    
    Implementa conexión completa usando el estándar ONVIF para:
    - Detección automática de marcas (Dahua, TP-Link, etc.)
    - Snapshots vía ONVIF
    - Streaming RTSP optimizado
    - Información de dispositivo
    - Compatibilidad con API antigua y nueva
    """
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el handler ONVIF con compatibilidad dual.
        
        Formatos soportados:
        - Nuevo: ONVIFHandler(config: ConnectionConfig, streaming_config: StreamingConfig)
        - Antiguo: ONVIFHandler(camera_ip: str, credentials: dict)
        - Legacy: ONVIFHandler(config_manager)
        """
        super().__init__(*args, **kwargs)
        
        if not ONVIF_AVAILABLE:
            raise ImportError("Dependencias ONVIF no disponibles. Instala: pip install onvif-zeep")
        
        # Configuración específica ONVIF
        self._setup_onvif_config()
        
        # Estado ONVIF
        self._camera: Optional[ONVIFCamera] = None
        self._media_service: Optional[Any] = None
        self._device_service: Optional[Any] = None
        self._profiles: List[Any] = []
        self._snapshot_uri: Optional[str] = None
        self._stream_uri: Optional[str] = None
        
        # Cache para optimización
        self._device_info_cache: Optional[Dict[str, Any]] = None
        self._rtsp_urls_cache: Optional[List[str]] = None
    
    def _setup_onvif_config(self):
        """Configura parámetros específicos ONVIF."""
        # Detectar configuración según API utilizada
        if hasattr(self, 'config') and self.config:
            # Nueva API
            self.ip = self.config.ip
            self.username = self.config.username
            self.password = self.config.password
            self.onvif_port = getattr(self.config, 'onvif_port', 80)
        else:
            # API antigua/legacy - ya configurado en BaseHandler
            self.ip = self.camera_ip
            self.onvif_port = getattr(self, 'port', 80)
        
        # Detectar marca para configuración específica
        self._detect_brand_config()
    
    def _detect_brand_config(self):
        """Detecta configuración específica por marca de cámara."""
        # Detectar TP-Link por puerto o configuración
        if (hasattr(self, 'config_manager') and 
            (hasattr(self.config_manager, 'tplink_ip') or 
             getattr(self, 'onvif_port', 80) == 2020)):
            self._is_tplink = True
            self.onvif_port = 2020  # Puerto común TP-Link
        else:
            # Asumir Dahua/genérico por defecto
            self._is_tplink = False
            if self.onvif_port == 80:
                self.onvif_port = 80  # Puerto común Dahua
    
    async def connect(self) -> bool:
        """
        Establece conexión ONVIF con la cámara.
        
        Returns:
            True si la conexión fue exitosa
        """
        self._set_state(ConnectionState.CONNECTING)
        
        try:
            self.logger.info(f"Iniciando conexión ONVIF a {self.ip}:{self.onvif_port}")
            self.logger.debug(f"Credenciales - Usuario: {self.username}, Password: {'*' * len(self.password) if self.password else 'None'}")
            
            # Crear cámara ONVIF en thread separado para evitar bloqueo
            loop = asyncio.get_event_loop()
            self.logger.debug("Creando instancia de cámara ONVIF...")
            
            self._camera = await loop.run_in_executor(
                None,
                self._create_onvif_camera
            )
            
            if not self._camera:
                self.logger.error("No se pudo crear instancia de cámara ONVIF")
                raise ConnectionError("No se pudo crear cámara ONVIF")
            
            # Crear servicios
            self._device_service = self._camera.create_devicemgmt_service()
            self._media_service = self._camera.create_media_service()
            
            # Verificar conexión
            device_info = await loop.run_in_executor(
                None,
                self._device_service.GetDeviceInformation
            )
            
            if device_info and hasattr(device_info, 'Manufacturer'):
                self.logger.info(f"Conectado a {device_info.Manufacturer} {device_info.Model}")
                
                # Cache device info
                self._device_info_cache = {
                    'manufacturer': device_info.Manufacturer,
                    'model': device_info.Model,
                    'firmware': getattr(device_info, 'FirmwareVersion', 'N/A'),
                    'serial': getattr(device_info, 'SerialNumber', 'N/A'),
                    'hardware': getattr(device_info, 'HardwareId', 'N/A')
                }
            
            # Obtener perfiles
            self._profiles = await loop.run_in_executor(
                None,
                self._media_service.GetProfiles
            )
            
            self.logger.info(f"Perfiles encontrados: {len(self._profiles)}")
            
            # Configurar URIs de snapshot y stream
            await self._setup_media_uris()
            
            self._set_state(ConnectionState.CONNECTED)
            return True
            
        except ONVIFError as e:
            # Ya se manejó en _create_onvif_camera
            self._set_state(ConnectionState.ERROR)
            return False
        except ConnectionError as e:
            # Error ya formateado desde _create_onvif_camera
            self._set_state(ConnectionState.ERROR)
            return False
        except Exception as e:
            self.logger.error(f"Error inesperado: {type(e).__name__}: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                import traceback
                self.logger.debug(f"Traceback completo:\n{traceback.format_exc()}")
            self._set_state(ConnectionState.ERROR)
            return False
    
    def _create_onvif_camera(self) -> Optional[ONVIFCamera]:
        """
        Crea instancia de cámara ONVIF (método síncrono para executor).
        
        Returns:
            Instancia de ONVIFCamera o None si falla
        """
        try:
            self.logger.debug(f"Creando ONVIFCamera con IP: {self.ip}, Puerto: {self.onvif_port}")
            self.logger.debug(f"Usuario: {self.username}")
            self.logger.debug(f"Password (longitud): {len(self.password) if self.password else 0}")
            self.logger.debug(f"Password (primeros 3 chars): {self.password[:3] if self.password and len(self.password) >= 3 else 'N/A'}")
            
            camera = ONVIFCamera(
                self.ip,
                self.onvif_port,
                self.username,
                self.password
            )
            
            self.logger.debug("ONVIFCamera creada exitosamente")
            return camera
            
        except Exception as e:
            error_msg = str(e)
            # Mensajes más amigables para errores comunes
            if "Remote end closed connection" in error_msg:
                self.logger.error(f"Puerto {self.onvif_port} no responde a ONVIF. ¿Es el puerto correcto?")
            elif "401" in error_msg or "Unauthorized" in error_msg:
                self.logger.error("Credenciales incorrectas para ONVIF")
            elif "timeout" in error_msg.lower():
                self.logger.error(f"Timeout conectando a {self.ip}:{self.onvif_port}")
            else:
                self.logger.error(f"Error ONVIF: {type(e).__name__}: {error_msg}")
            
            # Solo mostrar traceback en modo debug
            if self.logger.isEnabledFor(logging.DEBUG):
                import traceback
                self.logger.debug(f"Traceback completo:\n{traceback.format_exc()}")
            return None
    
    async def _setup_media_uris(self):
        """Configura las URIs de snapshot y streaming desde los perfiles."""
        if not self._profiles:
            self.logger.warning("No hay perfiles de media disponibles")
            return
        
        try:
            # Usar el primer perfil por defecto
            profile = self._profiles[0]
            profile_token = self._get_profile_token(profile)
            
            loop = asyncio.get_event_loop()
            
            # Configurar Snapshot URI
            try:
                if self._media_service:
                    media_service = self._media_service  # Variable local para type checker
                    snapshot_uri = await loop.run_in_executor(
                        None,
                        lambda: media_service.GetSnapshotUri({'ProfileToken': profile_token})
                    )
                    if snapshot_uri and hasattr(snapshot_uri, 'Uri'):
                        self._snapshot_uri = snapshot_uri.Uri
                        self.logger.info(f"Snapshot URI configurada: {self._snapshot_uri}")
            except Exception as e:
                self.logger.warning(f"No se pudo obtener Snapshot URI: {str(e)}")
            
            # Configurar Stream URI  
            try:
                if self._media_service:
                    media_service = self._media_service  # Variable local para type checker
                    stream_uri = await loop.run_in_executor(
                        None,
                        lambda: media_service.GetStreamUri({
                            'StreamSetup': {
                                'Stream': 'RTP-Unicast',
                                'Transport': {'Protocol': 'RTSP'}
                            },
                            'ProfileToken': profile_token
                        })
                    )
                    if stream_uri and hasattr(stream_uri, 'Uri'):
                        self._stream_uri = stream_uri.Uri
                        self.logger.info(f"Stream URI configurada: {self._stream_uri}")
            except Exception as e:
                self.logger.warning(f"No se pudo obtener Stream URI: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error configurando URIs de media: {str(e)}")
    
    def _get_profile_token(self, profile) -> str:
        """
        Obtiene el token del perfil manejando diferentes formatos.
        
        Args:
            profile: Objeto perfil ONVIF
            
        Returns:
            Token del perfil
        """
        if hasattr(profile, '_token'):
            return profile._token
        elif hasattr(profile, 'token'):
            return profile.token
        else:
            return getattr(profile, 'Name', 'MainProfile')
    
    async def disconnect(self) -> bool:
        """
        Cierra la conexión ONVIF.
        
        Returns:
            True si se desconectó correctamente
        """
        try:
            # Detener streaming si está activo
            if self.is_streaming:
                await self.stop_streaming()
            
            # Limpiar recursos ONVIF
            self._camera = None
            self._media_service = None
            self._device_service = None
            self._profiles = []
            self._snapshot_uri = None
            self._stream_uri = None
            
            # Limpiar cache
            self._device_info_cache = None
            self._rtsp_urls_cache = None
            
            self._set_state(ConnectionState.DISCONNECTED)
            self.logger.info("Conexión ONVIF cerrada")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cerrando conexión ONVIF: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Prueba la conexión ONVIF sin establecerla permanentemente.
        
        Returns:
            True si la conexión es posible
        """
        try:
            # Crear conexión temporal
            temp_camera = await asyncio.get_event_loop().run_in_executor(
                None, self._create_onvif_camera
            )
            
            if not temp_camera:
                return False
            
            # Probar servicio básico
            temp_device_service = temp_camera.create_devicemgmt_service()
            await asyncio.get_event_loop().run_in_executor(
                None, temp_device_service.GetDeviceInformation
            )
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Test de conexión ONVIF falló: {str(e)}")
            return False
    
    async def capture_snapshot(self) -> Optional[bytes]:
        """
        Captura un snapshot de la cámara vía ONVIF.
        
        Returns:
            Datos de la imagen en bytes o None si falla
        """
        if not self.is_connected or not self._snapshot_uri:
            self.logger.error("Conexión ONVIF no establecida o Snapshot URI no disponible")
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Realizar petición HTTP al snapshot URI de forma asíncrona
            import requests.auth
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    self._snapshot_uri,  # type: ignore
                    auth=requests.auth.HTTPDigestAuth(self.username, self.password),
                    timeout=10
                )
            )
            
            if response.status_code == 200:
                return response.content
            else:
                self.logger.error(f"Error en snapshot: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturando snapshot: {str(e)}")
            return None
    
    async def start_streaming(self) -> bool:
        """
        Inicia el streaming de video ONVIF/RTSP.
        
        Returns:
            True si el streaming se inició exitosamente
        """
        if self.is_streaming:
            return True
        
        try:
            self._set_state(ConnectionState.CONNECTING)
            
            # Intentar configurar stream
            stream_url = await self._get_best_stream_url()
            if not stream_url:
                self.logger.error("No se pudo obtener URL de stream")
                return False
            
            # Crear VideoCapture en thread separado
            loop = asyncio.get_event_loop()
            self._stream_handle = await loop.run_in_executor(
                None, self._create_video_capture, stream_url
            )
            
            if not self._stream_handle or not self._stream_handle.isOpened():
                self.logger.error("No se pudo abrir stream de video")
                return False
            
            # Iniciar worker thread para streaming
            self._streaming_active = True
            self._streaming_thread = asyncio.create_task(self._streaming_worker())
            
            self._set_state(ConnectionState.STREAMING)
            self.logger.info("Streaming ONVIF iniciado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando streaming: {str(e)}")
            self._set_state(ConnectionState.ERROR)
            return False
    
    def _create_video_capture(self, stream_url: str) -> Optional[cv2.VideoCapture]:
        """Crea VideoCapture con optimizaciones (método síncrono)."""
        try:
            # Suprimir warnings de FFmpeg/OpenCV
            cv2.setLogLevel(3)
            
            cap = cv2.VideoCapture(stream_url)
            if cap.isOpened():
                # Optimizaciones
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_FPS, 30)
                # Usar fourcc estándar H264 de OpenCV
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('H', '2', '6', '4'))
                return cap
        except Exception as e:
            self.logger.error(f"Error creando VideoCapture: {str(e)}")
        return None
    
    async def _get_best_stream_url(self) -> Optional[str]:
        """Obtiene la mejor URL de stream disponible."""
        # Intentar Stream URI de ONVIF primero
        if self._stream_uri:
            return self._stream_uri
        
        # Fallback: URLs RTSP según marca
        if not self._rtsp_urls_cache:
            self._rtsp_urls_cache = self._get_rtsp_urls()
        
        # Probar URLs en orden de prioridad
        for url in self._rtsp_urls_cache:
            try:
                # Test rápido de conectividad
                loop = asyncio.get_event_loop()
                test_cap = await loop.run_in_executor(
                    None, cv2.VideoCapture, url
                )
                
                if test_cap and test_cap.isOpened():
                    test_cap.release()
                    return url
                    
            except Exception:
                continue
        
        return None
    
    def _get_rtsp_urls(self) -> List[str]:
        """
        Obtiene lista de URLs RTSP posibles según la marca detectada.
        
        Returns:
            Lista de URLs RTSP para probar
        """
        try:
            if self._is_tplink:
                # URLs para TP-Link Tapo
                return [
                    f"rtsp://{self.username}:{self.password}@{self.ip}:554/stream1",
                    f"rtsp://{self.username}:{self.password}@{self.ip}:554/stream2",
                    f"rtsp://{self.ip}:554/stream1",
                ]
            else:
                # URLs para Dahua
                return [
                    f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=0",
                    f"rtsp://{self.username}:{self.password}@{self.ip}:554/cam/realmonitor?channel=1&subtype=1",
                ]
        except Exception as e:
            self.logger.error(f"Error obteniendo URLs RTSP: {str(e)}")
            return []
    
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
            
            # Cerrar stream handle
            if self._stream_handle:
                self._stream_handle.release()
                self._stream_handle = None
            
            self._set_state(ConnectionState.CONNECTED)
            return True
            
        except Exception as e:
            self.logger.error(f"Error deteniendo streaming: {str(e)}")
            return False
    
    async def _streaming_worker(self):
        """Worker asíncrono para streaming de frames."""
        frame_times = []
        
        while self._streaming_active and self._stream_handle:
            try:
                # Leer frame de forma no bloqueante
                loop = asyncio.get_event_loop()
                ret, frame = await loop.run_in_executor(
                    None, self._stream_handle.read
                )
                
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
                    self.logger.error(f"Error en streaming worker: {str(e)}")
                break
    
    def get_capabilities(self) -> ProtocolCapabilities:
        """Obtiene capacidades ONVIF."""
        return ProtocolCapabilities(
            supports_streaming=True,
            supports_snapshots=True,
            supports_ptz=False,  # TODO: Implementar PTZ
            supports_audio=False,
            max_resolution="1920x1080",
            supported_codecs=["H264", "MJPEG"]
        )
    
    # ==========================================
    # MÉTODOS ESPECÍFICOS ONVIF (Compatibilidad)
    # ==========================================
    
    async def get_device_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada del dispositivo vía ONVIF.
        
        Returns:
            Diccionario con información del dispositivo
        """
        # Usar cache si está disponible
        if self._device_info_cache:
            return self._device_info_cache.copy()
        
        if not self.is_connected or not self._device_service:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            device_info = await loop.run_in_executor(
                None, self._device_service.GetDeviceInformation
            )
            
            if device_info and hasattr(device_info, 'Manufacturer'):
                result = {
                    'manufacturer': device_info.Manufacturer,
                    'model': device_info.Model,
                    'firmware': getattr(device_info, 'FirmwareVersion', 'N/A'),
                    'serial': getattr(device_info, 'SerialNumber', 'N/A'),
                    'hardware': getattr(device_info, 'HardwareId', 'N/A')
                }
                
                # Cache para futuras consultas
                self._device_info_cache = result
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información del dispositivo: {str(e)}")
            return None
    
    def get_profiles(self) -> Dict[str, Any]:
        """
        Obtiene la lista de perfiles de media disponibles.
        
        Returns:
            Diccionario con success y data
        """
        try:
            if self._profiles:
                self.logger.info(f"Obteniendo información de {len(self._profiles)} perfiles")
                
                # Convertir perfiles ONVIF a formato estándar
                profiles_data = []
                for i, profile in enumerate(self._profiles):
                    # Debug del perfil
                    self.logger.debug(f"Perfil {i}: tipo={type(profile)}")
                    self.logger.debug(f"Perfil {i} atributos: {[attr for attr in dir(profile) if not attr.startswith('_')][:10]}")
                    
                    token = self._get_profile_token(profile)
                    name = getattr(profile, 'Name', 'Unknown')
                    
                    self.logger.info(f"Perfil {i}: name={name}, token={token}")
                    
                    profile_data = {
                        'token': token,
                        'name': name
                    }
                    
                    # Agregar información de codificación si está disponible
                    if hasattr(profile, 'VideoEncoderConfiguration'):
                        encoder = profile.VideoEncoderConfiguration
                        profile_data['video_encoder'] = {
                            'encoding': getattr(encoder, 'Encoding', 'H264'),
                            'resolution': {
                                'width': getattr(getattr(encoder, 'Resolution', None), 'Width', 0),
                                'height': getattr(getattr(encoder, 'Resolution', None), 'Height', 0)
                            }
                        }
                    
                    profiles_data.append(profile_data)
                
                return {
                    'success': True,
                    'data': profiles_data
                }
            else:
                return {
                    'success': False,
                    'data': [],
                    'error': 'No profiles available'
                }
        except Exception as e:
            self.logger.error(f"Error obteniendo perfiles: {e}")
            return {
                'success': False,
                'data': [],
                'error': str(e)
            }
    
    async def get_stream_uri(self, profile_token: str) -> Dict[str, Any]:
        """
        Obtiene la URI del stream para un perfil específico.
        
        Args:
            profile_token: Token del perfil
            
        Returns:
            Diccionario con success y data (URL)
        """
        if not self._media_service:
            return {
                'success': False,
                'error': 'Media service not available'
            }
        
        try:
            loop = asyncio.get_event_loop()
            stream_uri = await loop.run_in_executor(
                None,
                lambda: self._media_service.GetStreamUri({
                    'StreamSetup': {
                        'Stream': 'RTP-Unicast',
                        'Transport': {'Protocol': 'RTSP'}
                    },
                    'ProfileToken': profile_token
                })
            )
            
            if stream_uri and hasattr(stream_uri, 'Uri'):
                return {
                    'success': True,
                    'data': stream_uri.Uri
                }
            else:
                return {
                    'success': False,
                    'error': 'No URI in response'
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo stream URI: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Método de compatibilidad síncrono
    def get_device_info_sync(self) -> Optional[Dict[str, Any]]:
        """Versión síncrona de get_device_info para compatibilidad."""
        if self._device_info_cache:
            return self._device_info_cache.copy()
        
        # Para compatibilidad, ejecutar de forma síncrona
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get_device_info())
        except RuntimeError:
            # Si no hay loop, crear uno temporal
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.get_device_info())
            finally:
                loop.close() 