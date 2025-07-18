"""
Funciones auxiliares compartidas para los routers de cameras_v2.
"""
from typing import List
import logging

from api.models.camera_models import (
    CameraResponse,
    CredentialsResponse,
    ProtocolResponse,
    EndpointResponse,
    StreamProfileResponse,
    CameraStatisticsResponse,
    CameraCapabilitiesResponse,
    ProtocolType
)

logger = logging.getLogger(__name__)


def build_camera_response(camera_model) -> CameraResponse:
    """
    Construye una respuesta de cámara desde el modelo de dominio.
    
    Args:
        camera_model: Instancia de CameraModel
        
    Returns:
        CameraResponse para la API
        
    Raises:
        ValueError: Si el modelo de cámara es inválido
    """
    try:
        # Validar entrada
        if not camera_model:
            raise ValueError("camera_model no puede ser None")
            
        # Credenciales (sin contraseña)
        credentials = CredentialsResponse(
            username=getattr(camera_model.connection_config, 'username', ''),
            auth_type=getattr(camera_model.connection_config, 'auth_type', 'basic'),
            is_configured=bool(getattr(camera_model.connection_config, 'password', False))
        )
        
        # Protocolos
        protocols = []
        supported_protocols = getattr(camera_model.capabilities, 'supported_protocols', [])
        for idx, protocol in enumerate(supported_protocols):
            port = 80  # Default
            if protocol == ProtocolType.RTSP:
                port = getattr(camera_model.connection_config, 'rtsp_port', 554)
            elif protocol == ProtocolType.ONVIF:
                port = getattr(camera_model.connection_config, 'onvif_port', 80)
            elif protocol == ProtocolType.HTTP:
                port = getattr(camera_model.connection_config, 'http_port', 80)
                
            protocols.append(ProtocolResponse(
                protocol_type=protocol,
                port=port,
                is_enabled=True,
                is_primary=idx == 0
            ))
        
        # Endpoints descubiertos
        endpoints = []
        discovered_endpoints = getattr(camera_model.capabilities, 'discovered_endpoints', [])
        for endpoint in discovered_endpoints:
            try:
                endpoints.append(EndpointResponse(
                    protocol_type=getattr(endpoint, 'protocol', 'unknown'),
                    path=getattr(endpoint, 'path', ''),
                    description=getattr(endpoint, 'description', ''),
                    requires_auth=getattr(endpoint, 'requires_auth', True),
                    is_verified=getattr(endpoint, 'is_verified', False)
                ))
            except Exception as e:
                logger.warning(f"Error procesando endpoint: {e}")
        
        # Perfiles de streaming
        stream_profiles = []
        profiles = getattr(camera_model.capabilities, 'stream_profiles', [])
        for profile in profiles:
            try:
                stream_profiles.append(StreamProfileResponse(
                    profile_id=getattr(profile, 'profile_id', ''),
                    name=getattr(profile, 'name', ''),
                    resolution=getattr(profile, 'resolution', ''),
                    fps=getattr(profile, 'fps', 0),
                    quality=getattr(profile, 'quality', 'medium'),
                    codec=getattr(profile, 'codec', 'h264'),
                    is_main_stream=getattr(profile, 'is_main_stream', False)
                ))
            except Exception as e:
                logger.warning(f"Error procesando perfil de streaming: {e}")
        
        # Estadísticas
        stats_data = getattr(camera_model, 'statistics', {})
        if not isinstance(stats_data, dict):
            stats_data = {}
            
        statistics = CameraStatisticsResponse(
            total_connections=stats_data.get('total_connections', 0),
            successful_connections=stats_data.get('successful_connections', 0),
            failed_connections=stats_data.get('failed_connections', 0),
            total_snapshots=stats_data.get('total_snapshots', 0),
            last_connection_time=stats_data.get('last_connection_time'),
            last_snapshot_time=stats_data.get('last_snapshot_time'),
            average_fps=stats_data.get('average_fps', 0.0),
            total_streaming_time=stats_data.get('total_streaming_time', 0),
            bandwidth_usage=stats_data.get('bandwidth_usage', 0)
        )
        
        # Capacidades
        features = getattr(camera_model.capabilities, 'features', {})
        if not isinstance(features, dict):
            features = {}
            
        capabilities = CameraCapabilitiesResponse(
            supports_onvif=ProtocolType.ONVIF in supported_protocols,
            supports_rtsp=ProtocolType.RTSP in supported_protocols,
            supports_http=ProtocolType.HTTP in supported_protocols,
            supports_https=ProtocolType.HTTPS in supported_protocols,
            supports_ptz=features.get('ptz', False),
            supports_audio=features.get('audio', False),
            supports_motion_detection=features.get('motion_detection', False),
            supports_night_vision=features.get('night_vision', False),
            supports_two_way_audio=features.get('two_way_audio', False),
            max_resolution=getattr(camera_model.capabilities, 'max_resolution', '1920x1080'),
            max_fps=getattr(camera_model.capabilities, 'max_fps', 30),
            has_sd_card=features.get('sd_card', False),
            has_cloud_storage=features.get('cloud_storage', False)
        )
        
        return CameraResponse(
            camera_id=getattr(camera_model, 'camera_id', ''),
            brand=getattr(camera_model, 'brand', 'Unknown'),
            model=getattr(camera_model, 'model', 'Unknown'),
            display_name=getattr(camera_model, 'display_name', ''),
            ip_address=getattr(camera_model.connection_config, 'ip', ''),
            mac_address=getattr(camera_model, 'mac_address', ''),
            status=getattr(camera_model, 'status', 'unknown'),
            is_active=getattr(camera_model, 'is_active', False),
            is_connected=getattr(camera_model, 'is_connected', False),
            is_streaming=getattr(camera_model, 'is_streaming', False),
            firmware_version=getattr(camera_model, 'firmware_version', ''),
            hardware_version=getattr(camera_model, 'hardware_version', ''),
            serial_number=getattr(camera_model, 'serial_number', ''),
            location=getattr(camera_model, 'location', ''),
            description=getattr(camera_model, 'description', ''),
            credentials=credentials,
            protocols=protocols,
            endpoints=endpoints,
            stream_profiles=stream_profiles,
            capabilities=capabilities,
            statistics=statistics,
            created_at=getattr(camera_model, 'created_at', None),
            updated_at=getattr(camera_model, 'last_updated', None)
        )
        
    except Exception as e:
        logger.error(f"Error construyendo respuesta de cámara: {e}", exc_info=True)
        raise ValueError(f"Error al construir respuesta de cámara: {str(e)}")