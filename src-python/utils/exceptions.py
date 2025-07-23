#!/usr/bin/env python3
"""
Excepciones personalizadas para Universal Camera Viewer.

Define la jerarquía de excepciones del dominio siguiendo las reglas
de error handling de la arquitectura MVP.
"""

from datetime import datetime
from typing import Dict, Any, Optional


class CameraViewerError(Exception):
    """
    Excepción base para Universal Camera Viewer.
    
    Todas las excepciones del dominio deben heredar de esta clase
    para mantener consistencia en el manejo de errores.
    """
    
    def __init__(self, message: str, error_code: str = "UNKNOWN", context: Optional[Dict[str, Any]] = None):
        """
        Inicializa la excepción base.
        
        Args:
            message: Mensaje descriptivo del error
            error_code: Código único del error para identificación
            context: Información adicional de contexto
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte excepción a diccionario para logging/serialización.
        
        Returns:
            Diccionario con toda la información del error
        """
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp.isoformat()
        }


# === Excepciones de Conexión ===

class ConnectionError(CameraViewerError):
    """Errores relacionados con conexiones de cámara."""
    pass


class CameraConnectionError(ConnectionError):
    """Error al conectar con cámara específica."""
    
    def __init__(self, ip: str, message: str, error_code: str = "CAM_CONN_FAILED"):
        """
        Inicializa error de conexión de cámara.
        
        Args:
            ip: Dirección IP de la cámara
            message: Descripción del error
            error_code: Código del error
        """
        super().__init__(
            message=f"Error conectando a cámara {ip}: {message}",
            error_code=error_code,
            context={'ip': ip}
        )
        self.ip = ip


class ConnectionTimeoutError(ConnectionError):
    """Error por timeout en conexión."""
    
    def __init__(self, ip: str, timeout: float):
        """
        Inicializa error de timeout.
        
        Args:
            ip: Dirección IP del destino
            timeout: Tiempo de timeout en segundos
        """
        super().__init__(
            message=f"Timeout conectando a {ip} después de {timeout}s",
            error_code="CONNECTION_TIMEOUT",
            context={'ip': ip, 'timeout': timeout}
        )


# === Excepciones de Escaneo ===

class ScanError(CameraViewerError):
    """Errores relacionados con escaneo de red."""
    pass


class NetworkScanTimeoutError(ScanError):
    """Timeout durante escaneo de red."""
    
    def __init__(self, network_range: str, timeout: float):
        """
        Inicializa error de timeout en escaneo.
        
        Args:
            network_range: Rango de red escaneado
            timeout: Tiempo de timeout en segundos
        """
        super().__init__(
            message=f"Timeout escaneando red {network_range} después de {timeout}s",
            error_code="SCAN_TIMEOUT",
            context={'network_range': network_range, 'timeout': timeout}
        )


class InvalidNetworkRangeError(ScanError):
    """Rango de red inválido para escaneo."""
    
    def __init__(self, network_range: str):
        """
        Inicializa error de rango inválido.
        
        Args:
            network_range: Rango de red inválido
        """
        super().__init__(
            message=f"Rango de red inválido: {network_range}",
            error_code="INVALID_NETWORK_RANGE",
            context={'network_range': network_range}
        )


# === Excepciones de Configuración ===

class ConfigurationError(CameraViewerError):
    """Errores de configuración."""
    pass


class MissingConfigurationError(ConfigurationError):
    """Error por configuración faltante."""
    
    def __init__(self, config_key: str):
        """
        Inicializa error de configuración faltante.
        
        Args:
            config_key: Clave de configuración faltante
        """
        super().__init__(
            message=f"Configuración requerida no encontrada: {config_key}",
            error_code="MISSING_CONFIG",
            context={'config_key': config_key}
        )


class InvalidConfigurationError(ConfigurationError):
    """Error por configuración inválida."""
    
    def __init__(self, config_key: str, value: Any, reason: str):
        """
        Inicializa error de configuración inválida.
        
        Args:
            config_key: Clave de configuración
            value: Valor inválido
            reason: Razón por la que es inválido
        """
        super().__init__(
            message=f"Configuración inválida para {config_key}: {reason}",
            error_code="INVALID_CONFIG",
            context={'config_key': config_key, 'value': value, 'reason': reason}
        )


class InvalidCredentialsError(ConfigurationError):
    """Error por credenciales inválidas."""
    
    def __init__(self, username: str, context: str = ""):
        """
        Inicializa error de credenciales inválidas.
        
        Args:
            username: Nombre de usuario inválido
            context: Contexto adicional del error
        """
        message = f"Credenciales inválidas para usuario '{username}'"
        if context:
            message += f": {context}"
        
        super().__init__(
            message=message,
            error_code="INVALID_CREDENTIALS",
            context={'username': username}
        )


# === Excepciones de Validación ===

class ValidationError(CameraViewerError):
    """Errores de validación de datos."""
    pass


class InvalidIPAddressError(ValidationError):
    """IP address inválida."""
    
    def __init__(self, ip: str):
        """
        Inicializa error de IP inválida.
        
        Args:
            ip: Dirección IP inválida
        """
        super().__init__(
            message=f"Dirección IP inválida: {ip}",
            error_code="INVALID_IP",
            context={'ip': ip}
        )


class InvalidPortError(ValidationError):
    """Puerto inválido."""
    
    def __init__(self, port: Any):
        """
        Inicializa error de puerto inválido.
        
        Args:
            port: Puerto inválido
        """
        super().__init__(
            message=f"Puerto inválido: {port}. Debe ser un número entre 1 y 65535",
            error_code="INVALID_PORT",
            context={'port': port}
        )


class MissingRequiredFieldError(ValidationError):
    """Campo requerido faltante."""
    
    def __init__(self, field_name: str, model_name: str):
        """
        Inicializa error de campo faltante.
        
        Args:
            field_name: Nombre del campo faltante
            model_name: Nombre del modelo/clase
        """
        super().__init__(
            message=f"Campo requerido '{field_name}' faltante en {model_name}",
            error_code="MISSING_FIELD",
            context={'field_name': field_name, 'model_name': model_name}
        )


# === Excepciones de Protocolo ===

class ProtocolError(CameraViewerError):
    """Errores específicos de protocolos (ONVIF, RTSP, etc.)."""
    pass


class ONVIFError(ProtocolError):
    """Error relacionado con protocolo ONVIF."""
    pass


class ONVIFAuthenticationError(ONVIFError):
    """Error de autenticación ONVIF."""
    
    def __init__(self, ip: str, username: str):
        """
        Inicializa error de autenticación ONVIF.
        
        Args:
            ip: Dirección IP de la cámara
            username: Usuario que falló autenticación
        """
        super().__init__(
            message=f"Autenticación ONVIF fallida para {ip} con usuario {username}",
            error_code="ONVIF_AUTH_FAILED",
            context={'ip': ip, 'username': username}
        )


class ONVIFServiceError(ONVIFError):
    """Error al acceder a servicios ONVIF."""
    
    def __init__(self, ip: str, service: str, reason: str):
        """
        Inicializa error de servicio ONVIF.
        
        Args:
            ip: Dirección IP de la cámara
            service: Nombre del servicio ONVIF
            reason: Razón del error
        """
        super().__init__(
            message=f"Error en servicio ONVIF {service} para {ip}: {reason}",
            error_code="ONVIF_SERVICE_ERROR",
            context={'ip': ip, 'service': service, 'reason': reason}
        )


class RTSPError(ProtocolError):
    """Error relacionado con protocolo RTSP."""
    pass


class RTSPConnectionError(RTSPError):
    """Error de conexión RTSP."""
    
    def __init__(self, rtsp_url: str, reason: str):
        """
        Inicializa error de conexión RTSP.
        
        Args:
            rtsp_url: URL RTSP que falló
            reason: Razón del error
        """
        super().__init__(
            message=f"Error conectando a stream RTSP: {reason}",
            error_code="RTSP_CONNECTION_FAILED",
            context={'rtsp_url': rtsp_url, 'reason': reason}
        )


class RTSPAuthenticationError(RTSPError):
    """Error de autenticación RTSP."""
    
    def __init__(self, rtsp_url: str):
        """
        Inicializa error de autenticación RTSP.
        
        Args:
            rtsp_url: URL RTSP que requiere autenticación
        """
        super().__init__(
            message="Autenticación RTSP fallida o credenciales incorrectas",
            error_code="RTSP_AUTH_FAILED",
            context={'rtsp_url': rtsp_url}
        )


# === Excepciones de Servicio ===

class ServiceError(CameraViewerError):
    """Error genérico de servicio."""
    pass


class MediaMTXAPIError(ServiceError):
    """Error al comunicarse con la API de MediaMTX."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None, endpoint: Optional[str] = None):
        """
        Inicializa error de API MediaMTX.
        
        Args:
            message: Mensaje descriptivo del error
            status_code: Código HTTP de respuesta si aplica
            response_data: Datos de respuesta de la API
            endpoint: Endpoint de la API que falló
        """
        self.status_code = status_code
        self.response_data = response_data or {}
        
        super().__init__(
            message=message,
            error_code="MEDIAMTX_API_ERROR",
            context={
                'endpoint': endpoint,
                'status_code': status_code,
                'response_data': response_data
            }
        )


class MediaMTXConnectionError(ServiceError):
    """Error de conexión con servidor MediaMTX."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Inicializa error de conexión MediaMTX.
        
        Args:
            message: Mensaje descriptivo del error
            original_error: Excepción original si existe
        """
        super().__init__(
            message=message,
            error_code="MEDIAMTX_CONNECTION_ERROR",
            context={
                'original_error': str(original_error) if original_error else None
            }
        )


class MediaMTXAuthenticationError(ServiceError):
    """Error de autenticación con servidor MediaMTX."""
    
    def __init__(self, message: str, server_id: Optional[int] = None):
        """
        Inicializa error de autenticación MediaMTX.
        
        Args:
            message: Mensaje descriptivo del error
            server_id: ID del servidor si aplica
        """
        super().__init__(
            message=message,
            error_code="MEDIAMTX_AUTH_ERROR",
            context={
                'server_id': server_id
            }
        )


# === Excepciones de Streaming ===

class StreamingError(CameraViewerError):
    """Errores relacionados con streaming de video."""
    pass


class StreamNotAvailableError(StreamingError):
    """Stream no disponible."""
    
    def __init__(self, camera_id: str, reason: str):
        """
        Inicializa error de stream no disponible.
        
        Args:
            camera_id: ID de la cámara
            reason: Razón por la que no está disponible
        """
        super().__init__(
            message=f"Stream no disponible para cámara {camera_id}: {reason}",
            error_code="STREAM_NOT_AVAILABLE",
            context={'camera_id': camera_id, 'reason': reason}
        )


class StreamDecodingError(StreamingError):
    """Error decodificando stream de video."""
    
    def __init__(self, camera_id: str, codec: str):
        """
        Inicializa error de decodificación.
        
        Args:
            camera_id: ID de la cámara
            codec: Codec que falló
        """
        super().__init__(
            message=f"Error decodificando stream de cámara {camera_id} con codec {codec}",
            error_code="STREAM_DECODE_ERROR",
            context={'camera_id': camera_id, 'codec': codec}
        )


# === Excepciones de Persistencia ===

class PersistenceError(CameraViewerError):
    """Errores relacionados con persistencia de datos."""
    pass


class CameraNotFoundError(PersistenceError):
    """Error cuando no se encuentra una cámara en la base de datos."""
    
    def __init__(self, camera_id: str):
        """
        Inicializa error de cámara no encontrada.
        
        Args:
            camera_id: ID de la cámara que no se encontró
        """
        super().__init__(
            message=f"Cámara con ID '{camera_id}' no encontrada",
            error_code="CAMERA_NOT_FOUND",
            context={'camera_id': camera_id}
        )


class CameraAlreadyExistsError(PersistenceError):
    """Error cuando se intenta crear una cámara que ya existe."""
    
    def __init__(self, camera_id: str):
        """
        Inicializa error de cámara ya existente.
        
        Args:
            camera_id: ID de la cámara que ya existe
        """
        super().__init__(
            message=f"Cámara con ID '{camera_id}' ya existe",
            error_code="CAMERA_ALREADY_EXISTS",
            context={'camera_id': camera_id}
        )


class DatabaseError(PersistenceError):
    """Error de base de datos."""
    
    def __init__(self, operation: str, reason: str):
        """
        Inicializa error de base de datos.
        
        Args:
            operation: Operación que falló
            reason: Razón del error
        """
        super().__init__(
            message=f"Error en operación de base de datos '{operation}': {reason}",
            error_code="DATABASE_ERROR",
            context={'operation': operation, 'reason': reason}
        )


class FileAccessError(PersistenceError):
    """Error accediendo a archivos."""
    
    def __init__(self, file_path: str, operation: str):
        """
        Inicializa error de acceso a archivo.
        
        Args:
            file_path: Ruta del archivo
            operation: Operación que falló (read/write/delete)
        """
        super().__init__(
            message=f"Error {operation} archivo {file_path}",
            error_code="FILE_ACCESS_ERROR",
            context={'file_path': file_path, 'operation': operation}
        )


# === Utilidades para Error Handling ===

def format_error_for_user(error: Exception) -> str:
    """
    Formatea un error para mostrar al usuario.
    
    Args:
        error: Excepción a formatear
        
    Returns:
        Mensaje amigable para el usuario
    """
    if isinstance(error, CameraViewerError):
        # Errores del dominio tienen mensajes apropiados
        return error.message
    elif isinstance(error, ConnectionRefusedError):
        return "No se pudo establecer conexión. Verifique que el dispositivo esté encendido."
    elif isinstance(error, TimeoutError):
        return "La operación tardó demasiado tiempo. Por favor intente nuevamente."
    elif isinstance(error, PermissionError):
        return "Sin permisos para realizar esta operación."
    else:
        # Error genérico
        return "Ha ocurrido un error inesperado. Por favor intente nuevamente."


def is_retryable_error(error: Exception) -> bool:
    """
    Determina si un error es recuperable con reintentos.
    
    Args:
        error: Excepción a evaluar
        
    Returns:
        True si el error puede ser reintentado
    """
    retryable_errors = (
        ConnectionTimeoutError,
        ConnectionRefusedError,
        TimeoutError,
        RTSPConnectionError,
    )
    
    return isinstance(error, retryable_errors)


__all__ = [
    # Base
    'CameraViewerError',
    
    # Conexión
    'ConnectionError',
    'CameraConnectionError',
    'ConnectionTimeoutError',
    
    # Escaneo
    'ScanError',
    'NetworkScanTimeoutError',
    'InvalidNetworkRangeError',
    
    # Configuración
    'ConfigurationError',
    'MissingConfigurationError',
    'InvalidConfigurationError',
    'InvalidCredentialsError',
    
    # Validación
    'ValidationError',
    'InvalidIPAddressError',
    'InvalidPortError',
    'MissingRequiredFieldError',
    
    # Protocolos
    'ProtocolError',
    'ONVIFError',
    'ONVIFAuthenticationError',
    'ONVIFServiceError',
    'RTSPError',
    'RTSPConnectionError',
    'RTSPAuthenticationError',
    
    # Servicio
    'ServiceError',
    'MediaMTXAPIError',
    'MediaMTXConnectionError',
    'MediaMTXAuthenticationError',
    
    # Streaming
    'StreamingError',
    'StreamNotAvailableError',
    'StreamDecodingError',
    
    # Persistencia
    'PersistenceError',
    'CameraNotFoundError',
    'CameraAlreadyExistsError',
    'DatabaseError',
    'FileAccessError',
    
    # Utilidades
    'format_error_for_user',
    'is_retryable_error',
]