"""
Tablas principales del sistema.

Contiene las definiciones de las tablas fundamentales:
- cameras: Información básica de cámaras
- camera_credentials: Credenciales de acceso
- camera_protocols: Protocolos soportados
- camera_endpoints: URLs y endpoints
- camera_capabilities: Capacidades y features
- stream_profiles: Perfiles de streaming
"""

# Tabla de cámaras - Información básica e inmutable
CAMERAS_TABLE = """
    CREATE TABLE cameras (
        camera_id TEXT PRIMARY KEY,  -- UUID v4
        code TEXT UNIQUE,             -- Código legible único (ej: Dahua_IPC-HDW1200SP_192_168_1_100)
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        display_name TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        mac_address TEXT,
        firmware_version TEXT,
        hardware_version TEXT,
        serial_number TEXT UNIQUE,    -- Serial del fabricante si está disponible
        location TEXT,
        description TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT,              -- Usuario que creó el registro
        updated_by TEXT,              -- Usuario que actualizó
        CHECK (camera_id LIKE '________-____-____-____-____________'),  -- Validar formato UUID
        CHECK (length(display_name) > 0)
    )
"""

# Tabla de credenciales - Separada por seguridad y múltiples por cámara
CAMERA_CREDENTIALS_TABLE = """
    CREATE TABLE camera_credentials (
        credential_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        credential_name TEXT NOT NULL,  -- Nombre descriptivo (ej: "Admin", "Viewer")
        username TEXT NOT NULL,
        password_encrypted TEXT NOT NULL,
        auth_type TEXT DEFAULT 'basic' CHECK (auth_type IN ('basic', 'digest', 'bearer', 'api_key')),
        api_key TEXT,                   -- Para autenticación por API key
        certificate_path TEXT,          -- Para autenticación por certificado
        is_active BOOLEAN DEFAULT 1,
        is_default BOOLEAN DEFAULT 0,
        last_used TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
        UNIQUE(camera_id, credential_name),
        CHECK (length(username) > 0 OR api_key IS NOT NULL)
    )
"""

# Tabla de protocolos - Configuración por protocolo
CAMERA_PROTOCOLS_TABLE = """
    CREATE TABLE camera_protocols (
        protocol_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        protocol_type TEXT NOT NULL CHECK (protocol_type IN ('ONVIF', 'RTSP', 'HTTP', 'HTTPS', 'WEBSOCKET')),
        port INTEGER NOT NULL CHECK (port > 0 AND port <= 65535),
        is_enabled BOOLEAN DEFAULT 1,
        is_primary BOOLEAN DEFAULT 0,
        version TEXT,                   -- Versión del protocolo (ej: "2.0" para ONVIF)
        path TEXT,                      -- Path base para el protocolo
        configuration JSON,             -- Configuración específica del protocolo
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
        UNIQUE(camera_id, protocol_type, port)
    )
"""

# Tabla de endpoints/URLs descubiertas
# APIs PARCIALMENTE IMPLEMENTADAS - Falta:
# - POST /cameras/{id}/endpoints - Crear endpoint manual
# - PUT /cameras/{id}/endpoints/{id} - Actualizar endpoint
# - DELETE /cameras/{id}/endpoints/{id} - Eliminar endpoint
# - POST /cameras/{id}/endpoints/{id}/verify - Verificar endpoint
CAMERA_ENDPOINTS_TABLE = """
    CREATE TABLE camera_endpoints (
        endpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        endpoint_type TEXT NOT NULL,    -- rtsp_main, rtsp_sub, snapshot, onvif_device, etc.
        endpoint_name TEXT NOT NULL,    -- Nombre descriptivo
        url TEXT NOT NULL,
        protocol_id INTEGER,            -- Referencia al protocolo usado
        credential_id INTEGER,          -- Credencial requerida para este endpoint
        is_verified BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        last_verified TIMESTAMP,
        response_time_ms INTEGER,
        priority INTEGER DEFAULT 0,     -- Para ordenar endpoints preferidos
        metadata JSON,                  -- Información adicional del endpoint
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
        FOREIGN KEY (protocol_id) REFERENCES camera_protocols (protocol_id) ON DELETE SET NULL,
        FOREIGN KEY (credential_id) REFERENCES camera_credentials (credential_id) ON DELETE SET NULL,
        UNIQUE(camera_id, endpoint_type, url)
    )
"""

# Tabla de capacidades - Features soportadas
# APIs FALTANTES:
# - GET /cameras/{id}/capabilities - Listar capacidades
# - POST /cameras/{id}/capabilities/detect - Auto-detectar capacidades
# - PUT /cameras/{id}/capabilities/{type} - Actualizar capacidad
# - GET /capabilities/types - Listar tipos de capacidades
CAMERA_CAPABILITIES_TABLE = """
    CREATE TABLE camera_capabilities (
        capability_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        capability_type TEXT NOT NULL,
        capability_name TEXT NOT NULL,
        is_supported BOOLEAN DEFAULT 1,
        configuration JSON,
        verified_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
        UNIQUE(camera_id, capability_type)
    )
"""

# Tabla de perfiles de streaming
STREAM_PROFILES_TABLE = """
    CREATE TABLE stream_profiles (
        profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        profile_name TEXT NOT NULL,
        profile_token TEXT,             -- Token ONVIF si aplica
        stream_type TEXT DEFAULT 'main' CHECK (stream_type IN ('main', 'sub', 'third')),
        encoding TEXT CHECK (encoding IN ('H264', 'H265', 'MJPEG', 'MPEG4')),
        resolution TEXT,                -- "1920x1080", "1280x720", etc.
        framerate INTEGER CHECK (framerate > 0 AND framerate <= 120),
        bitrate INTEGER CHECK (bitrate > 0),
        quality TEXT CHECK (quality IN ('highest', 'high', 'medium', 'low', 'lowest')),
        gop_interval INTEGER,           -- Group of Pictures interval
        is_default BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        endpoint_id INTEGER,            -- Endpoint asociado a este perfil
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
        FOREIGN KEY (endpoint_id) REFERENCES camera_endpoints (endpoint_id) ON DELETE SET NULL,
        UNIQUE(camera_id, profile_name)
    )
"""


def get_core_tables():
    """Retorna lista de tuplas (nombre_tabla, sql_create)."""
    return [
        ('cameras', CAMERAS_TABLE),
        ('camera_credentials', CAMERA_CREDENTIALS_TABLE),
        ('camera_protocols', CAMERA_PROTOCOLS_TABLE),
        ('camera_endpoints', CAMERA_ENDPOINTS_TABLE),
        ('camera_capabilities', CAMERA_CAPABILITIES_TABLE),
        ('stream_profiles', STREAM_PROFILES_TABLE)
    ]


def get_table_names():
    """Retorna solo los nombres de las tablas principales."""
    return [name for name, _ in get_core_tables()]