"""
Configuración del servidor FastAPI
"""

from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación FastAPI."""
    
    # Servidor
    app_name: str = "Universal Camera Viewer API"
    app_version: str = "0.9.20"
    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # WebSocket
    ws_heartbeat_interval: int = 30  # segundos
    ws_max_connections_per_client: int = 5
    
    # Streaming
    default_stream_quality: str = "medium"
    default_stream_fps: int = 30
    max_stream_fps: int = 60
    stream_buffer_size: int = 10  # frames
    
    # Límites
    max_cameras_per_session: int = 16
    scan_timeout: int = 300  # segundos
    connection_timeout: int = 10  # segundos
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "api.log"
    
    # Seguridad (para futuro)
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_prefix = "UCV_"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Obtener configuración cacheada.
    
    Returns:
        Settings: Instancia única de configuración
    """
    return Settings()


# Instancia global de configuración
settings = get_settings()