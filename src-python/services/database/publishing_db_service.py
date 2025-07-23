"""
Servicio de base de datos para configuración de publicación MediaMTX.

Gestiona la persistencia de configuraciones y estados de publicación
en la base de datos SQLite.
"""

import sqlite3
import json

from typing import Optional, Dict, List, Any
from datetime import datetime
from contextlib import contextmanager
import asyncio
from pathlib import Path
import hashlib
import base64
from cryptography.fernet import Fernet
import os

from models.publishing import PublishConfiguration, PublishStatus, PublisherProcess
from utils.exceptions import ServiceError
from services.logging_service import get_secure_logger


logger = get_secure_logger("services.database.publishing_db_service")


class PublishingDatabaseService:
    """
    Servicio para gestión de datos de publicación en BD.
    
    Responsabilidades:
    - CRUD de configuraciones MediaMTX
    - Persistencia de estado de publicaciones
    - Historial de publicaciones
    - Estadísticas de uso
    """
    
    def __init__(self, db_path: str = "data/camera_data.db"):
        """
        Inicializa el servicio de base de datos.
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.logger = logger
        self._initialized = False
        # Generar clave de encriptación o cargar desde variable de entorno
        self._init_encryption_key()
        
    @contextmanager
    def _get_connection(self):
        """
        Context manager para conexiones a BD.
        
        Yields:
            sqlite3.Connection: Conexión a la base de datos
            
        Raises:
            ServiceError: Si hay error de conexión
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Error de base de datos: {e}")
            raise ServiceError(f"Error de base de datos: {e}", error_code="DB_ERROR")
        finally:
            if conn:
                conn.close()
                
    async def initialize(self) -> None:
        """
        Inicializa el servicio y crea tablas si no existen.
        
        Crea las tablas necesarias para publicación si no están
        presentes en la base de datos.
        """
        if self._initialized:
            return
            
        self.logger.info("Inicializando PublishingDatabaseService")
        
        # Ejecutar en thread pool para no bloquear
        await asyncio.get_event_loop().run_in_executor(
            None, self._create_tables_if_needed
        )
        
        self._initialized = True
        self.logger.info("PublishingDatabaseService inicializado")
        
    def _create_tables_if_needed(self) -> None:
        """
        Crea las tablas de publicación si no existen.
        
        Esta función se ejecuta síncronamente en un thread pool.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si las tablas ya existen
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='publishing_configurations'
            """)
            
            if cursor.fetchone():
                self.logger.debug("Tablas de publicación ya existen")
                return
                
            self.logger.info("Creando tablas de publicación...")
            
            # Tabla de configuraciones MediaMTX
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS publishing_configurations (
                    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT NOT NULL UNIQUE,
                    mediamtx_url TEXT NOT NULL,
                    api_url TEXT,
                    api_enabled BOOLEAN DEFAULT 0,
                    username TEXT,
                    password_encrypted TEXT,
                    auth_enabled BOOLEAN DEFAULT 0,
                    use_tcp BOOLEAN DEFAULT 1,
                    max_reconnects INTEGER DEFAULT 3 CHECK (max_reconnects >= 0),
                    reconnect_delay REAL DEFAULT 5.0 CHECK (reconnect_delay > 0),
                    publish_path_template TEXT DEFAULT 'camera_{camera_id}',
                    is_active BOOLEAN DEFAULT 0,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT
                )
            """)
            
            # Tabla de estado de publicaciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS publishing_states (
                    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    config_id INTEGER NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('IDLE', 'STARTING', 'PUBLISHING', 'STOPPED', 'ERROR')),
                    publish_path TEXT NOT NULL,
                    process_pid INTEGER,
                    start_time TIMESTAMP,
                    stop_time TIMESTAMP,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    last_error_time TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
                    FOREIGN KEY (config_id) REFERENCES publishing_configurations (config_id) ON DELETE CASCADE,
                    UNIQUE(camera_id, is_active)
                )
            """)
            
            # Tabla de historial de publicaciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS publishing_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    config_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    publish_path TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    total_frames INTEGER DEFAULT 0,
                    average_fps REAL,
                    average_bitrate_kbps REAL,
                    total_data_mb REAL DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE,
                    FOREIGN KEY (config_id) REFERENCES publishing_configurations (config_id) ON DELETE CASCADE
                )
            """)
            
            # Tabla de métricas de publicación
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS publishing_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    metric_time TIMESTAMP NOT NULL,
                    fps REAL,
                    bitrate_kbps REAL,
                    frames INTEGER,
                    speed REAL,
                    quality REAL,
                    size_kb INTEGER,
                    time_seconds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (camera_id) ON DELETE CASCADE
                )
            """)
            
            # Índices para optimización
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_states_camera ON publishing_states(camera_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_states_active ON publishing_states(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_history_camera ON publishing_history(camera_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_history_time ON publishing_history(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_metrics_camera ON publishing_metrics(camera_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_metrics_session ON publishing_metrics(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pub_metrics_time ON publishing_metrics(metric_time)")
            
            # Trigger para actualizar updated_at
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_pub_config_timestamp 
                AFTER UPDATE ON publishing_configurations
                BEGIN
                    UPDATE publishing_configurations 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE rowid = NEW.rowid;
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_pub_state_timestamp 
                AFTER UPDATE ON publishing_states
                BEGIN
                    UPDATE publishing_states 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE rowid = NEW.rowid;
                END
            """)
            
            self.logger.info("Tablas de publicación creadas exitosamente")
            
    async def get_active_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración activa de MediaMTX con metadatos.
        
        Returns:
            Dict con configuración y metadatos si existe una activa, None si no
            
        Raises:
            ServiceError: Si hay error al obtener la configuración
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM publishing_configurations 
                    WHERE is_active = 1 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                config = self._row_to_config(row)
                return {
                    'config': config,
                    'config_id': row['config_id'],
                    'config_name': row['config_name'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
        
    async def get_configuration_by_name(self, name: str) -> Optional[PublishConfiguration]:
        """
        Obtiene una configuración por nombre.
        
        Args:
            name: Nombre de la configuración
            
        Returns:
            PublishConfiguration si existe, None si no
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM publishing_configurations 
                    WHERE config_name = ?
                """, (name,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                return self._row_to_config(row)
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
        
    async def get_all_configurations(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las configuraciones de MediaMTX.
        
        Returns:
            Lista de configuraciones con metadatos
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        config_id,
                        config_name,
                        mediamtx_url,
                        api_url,
                        api_enabled,
                        username,
                        auth_enabled,
                        use_tcp,
                        max_reconnects,
                        reconnect_delay,
                        publish_path_template,
                        is_active,
                        created_at,
                        updated_at,
                        created_by,
                        updated_by
                    FROM publishing_configurations
                    ORDER BY is_active DESC, updated_at DESC
                """)
                
                configs = []
                for row in cursor.fetchall():
                    configs.append({
                        'config_id': row['config_id'],
                        'config_name': row['config_name'],
                        'mediamtx_url': row['mediamtx_url'],
                        'api_url': row['api_url'],
                        'api_enabled': bool(row['api_enabled']),
                        'username': row['username'],
                        'auth_enabled': bool(row['auth_enabled']),
                        'use_tcp': bool(row['use_tcp']),
                        'max_reconnects': row['max_reconnects'],
                        'reconnect_delay': row['reconnect_delay'],
                        'publish_path_template': row['publish_path_template'],
                        'is_active': bool(row['is_active']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'created_by': row['created_by'],
                        'updated_by': row['updated_by']
                    })
                    
                return configs
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
        
    async def save_configuration(
        self,
        config: PublishConfiguration,
        name: str,
        set_active: bool = False,
        created_by: Optional[str] = None
    ) -> int:
        """
        Guarda una configuración en la base de datos.
        
        Args:
            config: Configuración a guardar
            name: Nombre único para la configuración
            set_active: Si establecer como configuración activa
            created_by: Usuario que crea la configuración
            
        Returns:
            ID de la configuración creada/actualizada
            
        Raises:
            ServiceError: Si hay error al guardar
        """
        def _save():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Si se marca como activa, desactivar otras
                if set_active:
                    cursor.execute("UPDATE publishing_configurations SET is_active = 0")
                    
                # Verificar si existe
                cursor.execute("SELECT config_id FROM publishing_configurations WHERE config_name = ?", (name,))
                existing = cursor.fetchone()
                
                if existing:
                    # Actualizar
                    cursor.execute("""
                        UPDATE publishing_configurations SET
                            mediamtx_url = ?,
                            api_url = ?,
                            api_enabled = ?,
                            username = ?,
                            password_encrypted = ?,
                            auth_enabled = ?,
                            use_tcp = ?,
                            max_reconnects = ?,
                            reconnect_delay = ?,
                            publish_path_template = ?,
                            is_active = ?,
                            metadata = ?,
                            updated_by = ?
                        WHERE config_name = ?
                    """, (
                        config.mediamtx_url,
                        config.api_url,
                        config.api_enabled,
                        config.username,
                        self._encrypt_password(config.password) if config.password else None,
                        config.auth_enabled,
                        config.use_tcp,
                        config.max_reconnects,
                        config.reconnect_delay,
                        config.publish_path_template,
                        set_active,
                        json.dumps(config.metadata) if config.metadata else None,
                        created_by,
                        name
                    ))
                    
                    return existing['config_id']
                else:
                    # Insertar
                    cursor.execute("""
                        INSERT INTO publishing_configurations (
                            config_name, mediamtx_url, api_url, api_enabled,
                            username, password_encrypted, auth_enabled,
                            use_tcp, max_reconnects, reconnect_delay,
                            publish_path_template, is_active, metadata,
                            created_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name,
                        config.mediamtx_url,
                        config.api_url,
                        config.api_enabled,
                        config.username,
                        self._encrypt_password(config.password) if config.password else None,
                        config.auth_enabled,
                        config.use_tcp,
                        config.max_reconnects,
                        config.reconnect_delay,
                        config.publish_path_template,
                        set_active,
                        json.dumps(config.metadata) if config.metadata else None,
                        created_by
                    ))
                    
                    return cursor.lastrowid
                    
        config_id = await asyncio.get_event_loop().run_in_executor(None, _save)
        self.logger.info(f"Configuración '{name}' guardada con ID {config_id}")
        return config_id
        
    async def delete_configuration(self, name: str) -> bool:
        """
        Elimina una configuración por nombre.
        
        Args:
            name: Nombre de la configuración a eliminar
            
        Returns:
            True si se eliminó, False si no existía
            
        Raises:
            ServiceError: Si la configuración está en uso
        """
        def _delete():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar si está en uso
                cursor.execute("""
                    SELECT COUNT(*) FROM publishing_states 
                    WHERE config_id = (
                        SELECT config_id FROM publishing_configurations 
                        WHERE config_name = ?
                    ) AND is_active = 1
                """, (name,))
                
                if cursor.fetchone()[0] > 0:
                    raise ServiceError(
                        f"No se puede eliminar la configuración '{name}' porque está en uso",
                        error_code="CONFIG_IN_USE"
                    )
                    
                # Eliminar
                cursor.execute("DELETE FROM publishing_configurations WHERE config_name = ?", (name,))
                return cursor.rowcount > 0
                
        deleted = await asyncio.get_event_loop().run_in_executor(None, _delete)
        if deleted:
            self.logger.info(f"Configuración '{name}' eliminada")
        return deleted
        
    async def save_publishing_state(
        self,
        camera_id: str,
        status: PublishStatus,
        config_id: int,
        publish_path: str,
        process_pid: Optional[int] = None,
        error: Optional[str] = None
    ) -> int:
        """
        Guarda o actualiza el estado de publicación de una cámara.
        
        Args:
            camera_id: ID de la cámara
            status: Estado actual
            config_id: ID de configuración usada
            publish_path: Path de publicación en MediaMTX
            process_pid: PID del proceso FFmpeg si aplica
            error: Mensaje de error si aplica
            
        Returns:
            ID del estado guardado
        """
        def _save():
            conn = None
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Usar transacción explícita para evitar condiciones de carrera
                cursor.execute("BEGIN EXCLUSIVE TRANSACTION")
                
                # Desactivar estados previos
                cursor.execute("""
                    UPDATE publishing_states 
                    SET is_active = 0, stop_time = CURRENT_TIMESTAMP 
                    WHERE camera_id = ? AND is_active = 1
                """, (camera_id,))
                
                # Insertar nuevo estado
                cursor.execute("""
                    INSERT INTO publishing_states (
                        camera_id, config_id, status, publish_path,
                        process_pid, start_time, error_count, last_error,
                        last_error_time
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
                """, (
                    camera_id,
                    config_id,
                    status.value,
                    publish_path,
                    process_pid,
                    1 if error else 0,
                    error,
                    datetime.utcnow() if error else None
                ))
                
                last_id = cursor.lastrowid
                conn.commit()
                return last_id
                
            except Exception as e:
                if conn:
                    conn.rollback()
                self.logger.error(f"Error guardando estado de publicación: {e}")
                raise ServiceError(f"Error guardando estado: {e}", error_code="DB_STATE_ERROR")
            finally:
                if conn:
                    conn.close()
                
        state_id = await asyncio.get_event_loop().run_in_executor(None, _save)
        self.logger.debug(f"Estado de publicación guardado para {camera_id}: {status.value}")
        return state_id
        
    async def update_publishing_state(
        self,
        camera_id: str,
        status: Optional[PublishStatus] = None,
        error: Optional[str] = None,
        increment_error: bool = False
    ) -> bool:
        """
        Actualiza el estado activo de publicación de una cámara.
        
        Args:
            camera_id: ID de la cámara
            status: Nuevo estado (si se proporciona)
            error: Mensaje de error (si aplica)
            increment_error: Si incrementar contador de errores
            
        Returns:
            True si se actualizó, False si no hay estado activo
        """
        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Construir query de actualización
                updates = []
                params = []
                
                if status:
                    updates.append("status = ?")
                    params.append(status.value)
                    
                if error:
                    updates.append("last_error = ?")
                    updates.append("last_error_time = ?")
                    params.extend([error, datetime.utcnow()])
                    
                if increment_error:
                    updates.append("error_count = error_count + 1")
                    
                if not updates:
                    return False
                    
                query = f"""
                    UPDATE publishing_states 
                    SET {', '.join(updates)}
                    WHERE camera_id = ? AND is_active = 1
                """
                params.append(camera_id)
                
                cursor.execute(query, params)
                return cursor.rowcount > 0
                
        updated = await asyncio.get_event_loop().run_in_executor(None, _update)
        if updated:
            self.logger.debug(f"Estado actualizado para {camera_id}")
        return updated
        
    async def get_active_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene todos los estados de publicación activos.
        
        Returns:
            Dict con camera_id como clave y estado como valor
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        ps.*,
                        pc.mediamtx_url,
                        pc.publish_path_template
                    FROM publishing_states ps
                    JOIN publishing_configurations pc ON ps.config_id = pc.config_id
                    WHERE ps.is_active = 1
                """)
                
                states = {}
                for row in cursor.fetchall():
                    states[row['camera_id']] = {
                        'state_id': row['state_id'],
                        'status': row['status'],
                        'publish_path': row['publish_path'],
                        'process_pid': row['process_pid'],
                        'start_time': row['start_time'],
                        'error_count': row['error_count'],
                        'last_error': row['last_error'],
                        'config_id': row['config_id'],
                        'mediamtx_url': row['mediamtx_url']
                    }
                    
                return states
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
        
    async def save_publishing_metrics(
        self,
        camera_id: str,
        session_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Guarda métricas de publicación.
        
        Args:
            camera_id: ID de la cámara
            session_id: ID de sesión de publicación
            metrics: Diccionario con métricas
        """
        def _save():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO publishing_metrics (
                        camera_id, session_id, metric_time,
                        fps, bitrate_kbps, frames, speed,
                        quality, size_kb, time_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    camera_id,
                    session_id,
                    datetime.utcnow(),
                    metrics.get('fps'),
                    metrics.get('bitrate_kbps'),
                    metrics.get('frames'),
                    metrics.get('speed'),
                    metrics.get('quality'),
                    metrics.get('size_kb'),
                    metrics.get('time_seconds')
                ))
                
        await asyncio.get_event_loop().run_in_executor(None, _save)
        
    async def finalize_publishing_session(
        self,
        camera_id: str,
        session_id: str,
        config_id: int,
        start_time: datetime,
        end_time: datetime,
        metrics_summary: Dict[str, Any],
        error: Optional[str] = None
    ) -> None:
        """
        Finaliza una sesión de publicación guardando en historial.
        
        Args:
            camera_id: ID de la cámara
            session_id: ID de sesión
            config_id: ID de configuración usada
            start_time: Tiempo de inicio
            end_time: Tiempo de fin
            metrics_summary: Resumen de métricas
            error: Error final si aplica
        """
        def _save():
            duration = (end_time - start_time).total_seconds()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener path desde estado
                cursor.execute("""
                    SELECT publish_path FROM publishing_states 
                    WHERE camera_id = ? AND is_active = 1
                """, (camera_id,))
                
                row = cursor.fetchone()
                publish_path = row['publish_path'] if row else f"camera_{camera_id}"
                
                cursor.execute("""
                    INSERT INTO publishing_history (
                        camera_id, config_id, session_id, status,
                        publish_path, start_time, end_time,
                        duration_seconds, total_frames, average_fps,
                        average_bitrate_kbps, total_data_mb,
                        error_count, last_error, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    camera_id,
                    config_id,
                    session_id,
                    'completed' if not error else 'failed',
                    publish_path,
                    start_time,
                    end_time,
                    duration,
                    metrics_summary.get('total_frames', 0),
                    metrics_summary.get('average_fps'),
                    metrics_summary.get('average_bitrate_kbps'),
                    metrics_summary.get('total_data_mb', 0),
                    metrics_summary.get('error_count', 0),
                    error,
                    json.dumps(metrics_summary)
                ))
                
        await asyncio.get_event_loop().run_in_executor(None, _save)
        self.logger.info(f"Sesión {session_id} finalizada para cámara {camera_id}")
        
    def _row_to_config(self, row: sqlite3.Row) -> PublishConfiguration:
        """
        Convierte una fila de BD a PublishConfiguration.
        
        Args:
            row: Fila de la tabla publishing_configurations
            
        Returns:
            PublishConfiguration con los datos
        """
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
        # Extraer puerto de api_url si existe
        api_port = 9997  # default
        if row['api_url']:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(row['api_url'])
                if parsed.port:
                    api_port = parsed.port
            except:
                pass
        
        return PublishConfiguration(
            mediamtx_url=row['mediamtx_url'],
            api_url=row['api_url'],
            api_port=api_port,
            api_enabled=bool(row['api_enabled']),
            username=row['username'],
            password=self._decrypt_password(row['password_encrypted']) if row['password_encrypted'] else None,
            auth_enabled=bool(row['auth_enabled']),
            use_tcp=bool(row['use_tcp']),
            max_reconnects=row['max_reconnects'],
            reconnect_delay=row['reconnect_delay'],
            publish_path_template=row['publish_path_template'],
            metadata=metadata
        )
    
    def _init_encryption_key(self):
        """
        Inicializa la clave de encriptación desde variable de entorno o genera una nueva.
        """
        key = os.environ.get('PUBLISHING_DB_KEY')
        if not key:
            # Intentar cargar desde archivo
            key_file = os.path.join(os.path.dirname(str(self.db_path)), '.db_key')
            if os.path.exists(key_file):
                try:
                    with open(key_file, 'rb') as f:
                        key = f.read()
                except Exception as e:
                    self.logger.error(f"Error leyendo clave de encriptación: {e}")
                    
            if not key:
                # Generar nueva clave
                key = Fernet.generate_key()
                # Guardar en archivo local (para desarrollo)
                try:
                    os.makedirs(os.path.dirname(key_file), exist_ok=True)
                    with open(key_file, 'wb') as f:
                        f.write(key)
                    self.logger.warning(f"Nueva clave de encriptación generada en {key_file}")
                except Exception as e:
                    self.logger.error(f"Error guardando clave: {e}")
        else:
            key = key.encode()
            
        try:
            self._cipher = Fernet(key)
        except Exception as e:
            self.logger.error(f"Error inicializando cifrado: {e}")
            # Fallback: usar cifrado simple
            self._cipher = None
        
    def _encrypt_password(self, password: Optional[str]) -> Optional[str]:
        """
        Encripta una contraseña.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Contraseña encriptada en base64 o None
        """
        if not password:
            return None
            
        if self._cipher:
            try:
                encrypted = self._cipher.encrypt(password.encode())
                return base64.b64encode(encrypted).decode('utf-8')
            except Exception as e:
                self.logger.error(f"Error encriptando contraseña: {e}")
                
        # Fallback: usar hash SHA256
        return hashlib.sha256(password.encode()).hexdigest()
            
    def _decrypt_password(self, encrypted: Optional[str]) -> Optional[str]:
        """
        Desencripta una contraseña.
        
        Args:
            encrypted: Contraseña encriptada en base64
            
        Returns:
            Contraseña en texto plano o None
        """
        if not encrypted:
            return None
            
        if self._cipher:
            try:
                decoded = base64.b64decode(encrypted.encode())
                decrypted = self._cipher.decrypt(decoded)
                return decrypted.decode('utf-8')
            except Exception as e:
                # Si falla, es posible que sea un hash antiguo
                self.logger.debug(f"No se pudo desencriptar, devolviendo como está: {e}")
                
        # Si no se puede desencriptar, devolver tal cual
        # (podría ser un hash SHA256 o contraseña antigua)
        return encrypted


# Instancia singleton
_db_service: Optional[PublishingDatabaseService] = None


def get_publishing_db_service(db_path: Optional[str] = None) -> PublishingDatabaseService:
    """
    Obtiene la instancia singleton del servicio.
    
    Args:
        db_path: Ruta a la BD (solo en primera llamada)
        
    Returns:
        PublishingDatabaseService singleton
    """
    global _db_service
    
    if _db_service is None:
        if db_path is None:
            db_path = "data/camera_data.db"
        _db_service = PublishingDatabaseService(db_path)
        
    return _db_service