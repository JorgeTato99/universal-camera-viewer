"""
Tablas de operación del sistema.

Contiene las definiciones de tablas para operaciones en tiempo real:
- camera_statistics: Métricas agregadas
- connection_logs: Historial de conexiones
- camera_events: Registro de eventos
"""

# Tabla de estadísticas - Métricas agregadas
# APIs FALTANTES:
# - GET /cameras/{id}/statistics - Estadísticas de cámara
# - GET /statistics/summary - Resumen global
# - POST /statistics/reset - Reiniciar estadísticas
# - GET /statistics/export - Exportar estadísticas
CAMERA_STATISTICS_TABLE = """
    CREATE TABLE camera_statistics (
        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL UNIQUE,
        total_connections INTEGER DEFAULT 0 CHECK (total_connections >= 0),
        successful_connections INTEGER DEFAULT 0 CHECK (successful_connections >= 0),
        failed_connections INTEGER DEFAULT 0 CHECK (failed_connections >= 0),
        total_uptime_seconds INTEGER DEFAULT 0 CHECK (total_uptime_seconds >= 0),
        total_data_mb REAL DEFAULT 0 CHECK (total_data_mb >= 0),
        average_fps REAL CHECK (average_fps >= 0),
        average_latency_ms INTEGER CHECK (average_latency_ms >= 0),
        max_concurrent_streams INTEGER DEFAULT 0,
        last_connection_at TIMESTAMP,
        last_disconnection_at TIMESTAMP,
        last_error_at TIMESTAMP,
        last_error_code TEXT,
        last_error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE
    )
"""

# Tabla de logs de conexión - Historial detallado
# APIs PARCIALMENTE IMPLEMENTADAS - Falta:
# - GET /connections/logs - Listar todos los logs con filtros
# - GET /connections/logs/stats - Estadísticas agregadas
# - DELETE /connections/logs - Limpiar logs antiguos
# - GET /connections/logs/export - Exportar logs
CONNECTION_LOGS_TABLE = """
    CREATE TABLE connection_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        session_id TEXT NOT NULL,       -- UUID de la sesión
        connection_type TEXT,
        protocol_used TEXT,
        endpoint_id INTEGER,
        credential_id INTEGER,
        status TEXT CHECK (status IN ('connecting', 'connected', 'disconnected', 'failed', 'timeout')),
        error_code TEXT,
        error_message TEXT,
        client_ip TEXT,                 -- IP del cliente que se conectó
        duration_seconds INTEGER,
        bytes_sent INTEGER,
        bytes_received INTEGER,
        average_fps REAL,
        started_at TIMESTAMP NOT NULL,
        ended_at TIMESTAMP,
        metadata JSON,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
        FOREIGN KEY (endpoint_id) REFERENCES camera_endpoints (endpoint_id) ON DELETE SET NULL,
        FOREIGN KEY (credential_id) REFERENCES camera_credentials (credential_id) ON DELETE SET NULL
    )
"""

# Tabla de eventos - Registro de eventos importantes
# APIs PARCIALMENTE IMPLEMENTADAS (solo WebSocket) - Falta:
# - GET /events - Listar eventos históricos
# - GET /events/{id} - Obtener detalle de evento
# - PUT /events/{id}/acknowledge - Reconocer evento
# - DELETE /events - Limpiar eventos antiguos
# - GET /events/stats - Estadísticas de eventos
CAMERA_EVENTS_TABLE = """
    CREATE TABLE camera_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id TEXT NOT NULL,
        event_type TEXT NOT NULL,       -- motion, connection_lost, tampering, etc.
        event_severity TEXT CHECK (event_severity IN ('info', 'warning', 'error', 'critical')),
        event_data JSON,
        is_acknowledged BOOLEAN DEFAULT 0,
        acknowledged_by TEXT,
        acknowledged_at TIMESTAMP,
        occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE
    )
"""


def get_operation_tables():
    """Retorna lista de tuplas (nombre_tabla, sql_create)."""
    return [
        ('camera_statistics', CAMERA_STATISTICS_TABLE),
        ('connection_logs', CONNECTION_LOGS_TABLE),
        ('camera_events', CAMERA_EVENTS_TABLE)
    ]


def get_table_names():
    """Retorna solo los nombres de las tablas de operación."""
    return [name for name, _ in get_operation_tables()]