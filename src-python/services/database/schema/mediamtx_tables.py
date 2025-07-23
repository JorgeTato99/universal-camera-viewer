"""
Tablas para integración con MediaMTX.

Contiene las definiciones para publicación RTSP a MediaMTX:
- mediamtx_servers: Servidores MediaMTX configurados
- camera_publications: Publicaciones activas
- publication_history: Historial de publicaciones
- publication_metrics: Métricas en tiempo real
- publication_viewers: Tracking de consumidores
- mediamtx_paths: Configuración de paths
"""

# Servidores MediaMTX
MEDIAMTX_SERVERS_TABLE = """
    CREATE TABLE mediamtx_servers (
        server_id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_name TEXT NOT NULL UNIQUE,
        rtsp_url TEXT NOT NULL,
        rtsp_port INTEGER DEFAULT 8554,
        api_url TEXT,
        api_port INTEGER DEFAULT 9997,
        api_enabled BOOLEAN DEFAULT 1,
        username TEXT,
        password_encrypted TEXT,
        auth_enabled BOOLEAN DEFAULT 0,
        use_tcp BOOLEAN DEFAULT 1,
        max_reconnects INTEGER DEFAULT 3 CHECK (max_reconnects >= 0),
        reconnect_delay REAL DEFAULT 5.0 CHECK (reconnect_delay > 0),
        publish_path_template TEXT DEFAULT 'ucv_{camera_code}',
        is_active BOOLEAN DEFAULT 0,
        is_default BOOLEAN DEFAULT 0,
        health_check_interval INTEGER DEFAULT 30,
        last_health_check TIMESTAMP,
        last_health_status TEXT CHECK (last_health_status IN ('healthy', 'unhealthy', 'unknown')),
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT,
        updated_by TEXT
    )
"""

# Publicaciones de cámaras
CAMERA_PUBLICATIONS_TABLE = """
    CREATE TABLE camera_publications (
        publication_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        server_id INTEGER NOT NULL,
        session_id TEXT NOT NULL UNIQUE,
        publish_path TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('IDLE', 'STARTING', 'PUBLISHING', 'STOPPED', 'ERROR')),
        process_pid INTEGER,
        ffmpeg_command TEXT,
        start_time TIMESTAMP,
        stop_time TIMESTAMP,
        error_count INTEGER DEFAULT 0,
        last_error TEXT,
        last_error_time TIMESTAMP,
        -- Campos para integración remota
        remote_camera_id TEXT,
        publish_url TEXT,
        webrtc_url TEXT,
        publish_token TEXT,
        is_remote BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
        FOREIGN KEY (server_id) REFERENCES mediamtx_servers (server_id) ON DELETE CASCADE,
        UNIQUE(camera_id, is_active)
    )
"""

# Historial de publicaciones
PUBLICATION_HISTORY_TABLE = """
    CREATE TABLE publication_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        server_id INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        publish_path TEXT NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP,
        duration_seconds INTEGER,
        total_frames INTEGER DEFAULT 0,
        average_fps REAL,
        average_bitrate_kbps REAL,
        total_data_mb REAL DEFAULT 0,
        max_viewers INTEGER DEFAULT 0,
        total_viewer_time_seconds INTEGER DEFAULT 0,
        error_count INTEGER DEFAULT 0,
        termination_reason TEXT CHECK (termination_reason IN ('completed', 'user_stopped', 'error', 'server_shutdown', 'camera_disconnected')),
        last_error TEXT,
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
        FOREIGN KEY (server_id) REFERENCES mediamtx_servers (server_id) ON DELETE CASCADE
    )
"""

# Métricas en tiempo real
PUBLICATION_METRICS_TABLE = """
    CREATE TABLE publication_metrics (
        metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
        publication_id INTEGER NOT NULL,
        metric_time TIMESTAMP NOT NULL,
        fps REAL,
        bitrate_kbps REAL,
        frames INTEGER,
        speed REAL,
        quality_score REAL CHECK (quality_score >= 0 AND quality_score <= 100),
        size_kb INTEGER,
        time_seconds REAL,
        dropped_frames INTEGER DEFAULT 0,
        viewer_count INTEGER DEFAULT 0,
        cpu_usage_percent REAL,
        memory_usage_mb REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (publication_id) REFERENCES camera_publications (publication_id) ON DELETE CASCADE
    )
"""

# Viewers/Consumidores
PUBLICATION_VIEWERS_TABLE = """
    CREATE TABLE publication_viewers (
        viewer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        publication_id INTEGER NOT NULL,
        viewer_ip TEXT NOT NULL,
        viewer_user_agent TEXT,
        protocol_used TEXT CHECK (protocol_used IN ('RTSP', 'RTMP', 'HLS', 'WebRTC', 'SRT')),
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP,
        duration_seconds INTEGER,
        bytes_received INTEGER DEFAULT 0,
        quality_changes INTEGER DEFAULT 0,
        buffer_events INTEGER DEFAULT 0,
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (publication_id) REFERENCES camera_publications (publication_id) ON DELETE CASCADE
    )
"""

# Tokens de autenticación para servidores MediaMTX remotos
MEDIAMTX_AUTH_TOKENS_TABLE = """
    CREATE TABLE mediamtx_auth_tokens (
        token_id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id INTEGER NOT NULL,
        access_token TEXT NOT NULL,
        token_type TEXT DEFAULT 'bearer',
        expires_at TIMESTAMP,
        refresh_token TEXT,
        refresh_expires_at TIMESTAMP,
        username TEXT,
        role TEXT,
        user_id TEXT,
        last_used_at TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (server_id) REFERENCES mediamtx_servers (server_id) ON DELETE CASCADE,
        UNIQUE(server_id, is_active)
    )
"""

# Configuración de paths MediaMTX
MEDIAMTX_PATHS_TABLE = """
    CREATE TABLE mediamtx_paths (
        path_id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id INTEGER NOT NULL,
        path_name TEXT NOT NULL,
        source_type TEXT CHECK (source_type IN ('publisher', 'redirect', 'rpiCamera', 'rtsp', 'rtmp', 'hls', 'udp', 'webrtc')),
        source_url TEXT,
        record_enabled BOOLEAN DEFAULT 0,
        record_path TEXT,
        record_format TEXT CHECK (record_format IN ('fmp4', 'mpegts')),
        record_segment_duration INTEGER DEFAULT 3600,
        playback_enabled BOOLEAN DEFAULT 1,
        authentication_required BOOLEAN DEFAULT 0,
        allowed_ips JSON,
        publish_user TEXT,
        publish_password_encrypted TEXT,
        read_user TEXT,
        read_password_encrypted TEXT,
        run_on_init TEXT,
        run_on_demand TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (server_id) REFERENCES mediamtx_servers (server_id) ON DELETE CASCADE,
        UNIQUE(server_id, path_name)
    )
"""


def get_mediamtx_tables():
    """Retorna lista de tuplas (nombre_tabla, sql_create)."""
    return [
        ('mediamtx_servers', MEDIAMTX_SERVERS_TABLE),
        ('camera_publications', CAMERA_PUBLICATIONS_TABLE),
        ('publication_history', PUBLICATION_HISTORY_TABLE),
        ('publication_metrics', PUBLICATION_METRICS_TABLE),
        ('publication_viewers', PUBLICATION_VIEWERS_TABLE),
        ('mediamtx_auth_tokens', MEDIAMTX_AUTH_TOKENS_TABLE),
        ('mediamtx_paths', MEDIAMTX_PATHS_TABLE)
    ]


def get_table_names():
    """Retorna solo los nombres de las tablas de MediaMTX."""
    return [name for name, _ in get_mediamtx_tables()]