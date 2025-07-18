"""
Tablas de almacenamiento.

Contiene las definiciones para gestión de archivos multimedia:
- snapshots: Capturas de imagen
- recordings: Grabaciones de video
"""

# Tabla de snapshots
# APIs FALTANTES:
# - GET /snapshots - Listar snapshots
# - POST /cameras/{id}/snapshots - Capturar snapshot
# - GET /snapshots/{id} - Obtener snapshot
# - DELETE /snapshots/{id} - Eliminar snapshot
# - GET /snapshots/{id}/download - Descargar snapshot
# - POST /snapshots/cleanup - Limpiar snapshots antiguos
SNAPSHOTS_TABLE = """
    CREATE TABLE snapshots (
        snapshot_id TEXT PRIMARY KEY,   -- UUID
        camera_id TEXT NOT NULL,
        file_path TEXT NOT NULL UNIQUE,
        thumbnail_path TEXT,
        capture_time TIMESTAMP NOT NULL,
        file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes > 0),
        width INTEGER CHECK (width > 0),
        height INTEGER CHECK (height > 0),
        format TEXT CHECK (format IN ('JPEG', 'PNG', 'WEBP')),
        quality INTEGER CHECK (quality > 0 AND quality <= 100),
        trigger_type TEXT,              -- manual, motion, scheduled, etc.
        is_archived BOOLEAN DEFAULT 0,
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE
    )
"""

# Tabla de grabaciones
# APIs FALTANTES:
# - GET /recordings - Listar grabaciones
# - POST /cameras/{id}/recordings/start - Iniciar grabación
# - POST /cameras/{id}/recordings/stop - Detener grabación
# - GET /recordings/{id} - Obtener info de grabación
# - DELETE /recordings/{id} - Eliminar grabación
# - GET /recordings/{id}/download - Descargar grabación
# - GET /recordings/{id}/stream - Stream de grabación
RECORDINGS_TABLE = """
    CREATE TABLE recordings (
        recording_id TEXT PRIMARY KEY,  -- UUID
        camera_id TEXT NOT NULL,
        file_path TEXT NOT NULL UNIQUE,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
        file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes > 0),
        format TEXT CHECK (format IN ('MP4', 'AVI', 'MKV', 'MOV')),
        codec TEXT,
        resolution TEXT,
        framerate INTEGER,
        bitrate INTEGER,
        has_audio BOOLEAN DEFAULT 0,
        trigger_type TEXT,
        is_archived BOOLEAN DEFAULT 0,
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
        CHECK (end_time > start_time)
    )
"""


def get_storage_tables():
    """Retorna lista de tuplas (nombre_tabla, sql_create)."""
    return [
        ('snapshots', SNAPSHOTS_TABLE),
        ('recordings', RECORDINGS_TABLE)
    ]


def get_table_names():
    """Retorna solo los nombres de las tablas de almacenamiento."""
    return [name for name, _ in get_storage_tables()]