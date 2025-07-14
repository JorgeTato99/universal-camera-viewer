#!/usr/bin/env python3
"""
DataService - Servicio de gestión de datos y persistencia.

Proporciona funcionalidades completas de:
- Persistencia de datos (SQLite/DuckDB)
- Cache inteligente
- Exportación de datos
- Gestión de historial
- Almacenamiento de snapshots
- Análisis de datos
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import csv
import tempfile
import shutil

# Importaciones para análisis de datos
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

from dataclasses import dataclass, field
from enum import Enum

try:
    from ..models import CameraModel, ConnectionModel, ScanModel
except ImportError:
    # Fallback para ejecución directa
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from models import CameraModel, ConnectionModel, ScanModel


class DatabaseType(Enum):
    """Tipos de base de datos soportados."""
    SQLITE = "sqlite"
    DUCKDB = "duckdb"
    MEMORY = "memory"


class ExportFormat(Enum):
    """Formatos de exportación soportados."""
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "xlsx"


@dataclass
class DataServiceConfig:
    """Configuración del DataService."""
    database_type: DatabaseType = DatabaseType.SQLITE
    database_path: str = "data/camera_data.db"
    cache_size_mb: int = 50
    cache_ttl_hours: int = 24
    auto_cleanup_days: int = 30
    enable_compression: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = 6
    max_snapshots_per_camera: int = 100
    enable_analytics: bool = True
    
    # Configuración de exportación
    export_directory: str = "exports"
    max_export_file_size_mb: int = 100
    
    # Configuración de historial
    max_scan_history: int = 1000
    max_connection_history: int = 500


@dataclass
class CameraData:
    """Datos persistidos de una cámara."""
    camera_id: str
    brand: str
    model: str
    ip: str
    last_seen: datetime
    connection_count: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    total_uptime_minutes: int = 0
    snapshots_count: int = 0
    protocols: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanData:
    """Datos persistidos de un escaneo."""
    scan_id: str
    target_ip: str
    timestamp: datetime
    duration_seconds: float
    ports_scanned: int
    ports_found: int
    authentication_tested: bool
    successful_auths: int
    protocols_detected: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SnapshotData:
    """Datos de un snapshot."""
    snapshot_id: str
    camera_id: str
    file_path: str
    timestamp: datetime
    file_size_bytes: int
    resolution: str
    format: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataService:
    """
    Servicio de gestión de datos y persistencia.
    
    Características principales:
    - Base de datos SQLite/DuckDB para persistencia
    - Cache inteligente con TTL
    - Exportación a múltiples formatos
    - Gestión de historial
    - Análisis de datos automático
    - Backup automático
    - Limpieza automática
    """
    
    def __init__(self, config: Optional[DataServiceConfig] = None):
        """
        Inicializa el DataService.
        
        Args:
            config: Configuración del servicio
        """
        self.config = config or DataServiceConfig()
        self.logger = logging.getLogger("DataService")
        
        # Estado del servicio
        self._initialized = False
        self._shutdown = False
        
        # Base de datos
        self._db_connection: Optional[Union[sqlite3.Connection, Any]] = None
        self._db_lock = threading.RLock()
        
        # Cache en memoria
        self._camera_cache: Dict[str, CameraData] = {}
        self._scan_cache: Dict[str, ScanData] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_lock = threading.RLock()
        
        # Estadísticas
        self._stats = {
            "cameras_tracked": 0,
            "scans_recorded": 0,
            "snapshots_stored": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "export_operations": 0,
            "backup_operations": 0
        }
        
        # Tareas de fondo
        self._background_tasks = []
        self._executor = None
        
    async def initialize(self) -> bool:
        """
        Inicializa el servicio de datos.
        
        Returns:
            True si se inicializó correctamente
        """
        if self._initialized:
            return True
        
        try:
            self.logger.info("Inicializando DataService...")
            
            # Crear directorios necesarios
            self._create_directories()
            
            # Inicializar base de datos
            await self._initialize_database()
            
            # Inicializar cache
            await self._initialize_cache()
            
            # Inicializar executor para tareas de fondo
            from concurrent.futures import ThreadPoolExecutor
            self._executor = ThreadPoolExecutor(
                max_workers=3,
                thread_name_prefix="data_service"
            )
            
            # Iniciar tareas de fondo
            await self._start_background_tasks()
            
            self._initialized = True
            self.logger.info("DataService inicializado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando DataService: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Cierra el servicio y libera recursos."""
        if not self._initialized or self._shutdown:
            return
        
        self.logger.info("Cerrando DataService...")
        self._shutdown = True
        
        # Detener tareas de fondo
        for task in self._background_tasks:
            task.cancel()
        
        # Cerrar executor
        if self._executor:
            self._executor.shutdown(wait=True)
        
        # Cerrar base de datos
        await self._close_database()
        
        self.logger.info("DataService cerrado correctamente")
    
    def _create_directories(self) -> None:
        """Crea los directorios necesarios."""
        directories = [
            Path(self.config.database_path).parent,
            Path(self.config.export_directory),
            Path("data/snapshots"),
            Path("data/cache"),
            Path("data/backups")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def _initialize_database(self) -> None:
        """Inicializa la base de datos."""
        if self.config.database_type == DatabaseType.SQLITE:
            await self._initialize_sqlite()
        elif self.config.database_type == DatabaseType.DUCKDB and DUCKDB_AVAILABLE:
            await self._initialize_duckdb()
        else:
            # Fallback a SQLite en memoria
            self.config.database_type = DatabaseType.MEMORY
            await self._initialize_sqlite_memory()
    
    async def _initialize_sqlite(self) -> None:
        """Inicializa base de datos SQLite."""
        self._db_connection = sqlite3.connect(
            self.config.database_path,
            check_same_thread=False
        )
        self._db_connection.row_factory = sqlite3.Row
        
        # Crear tablas
        await self._create_tables_sqlite()
        
        self.logger.info(f"📀 Base de datos SQLite inicializada: {self.config.database_path}")
    
    async def _initialize_sqlite_memory(self) -> None:
        """Inicializa base de datos SQLite en memoria."""
        self._db_connection = sqlite3.connect(":memory:", check_same_thread=False)
        self._db_connection.row_factory = sqlite3.Row
        await self._create_tables_sqlite()
        
        self.logger.info("Base de datos SQLite en memoria inicializada")
    
    async def _initialize_duckdb(self) -> None:
        """Inicializa base de datos DuckDB."""
        self._db_connection = duckdb.connect(self.config.database_path)
        await self._create_tables_duckdb()
        
        self.logger.info(f"🦆 Base de datos DuckDB inicializada: {self.config.database_path}")
    
    async def _create_tables_sqlite(self) -> None:
        """Crea las tablas necesarias en SQLite."""
        if not self._db_connection:
            raise RuntimeError("Base de datos no inicializada")
            
        cursor = self._db_connection.cursor()
        
        # Tabla de cámaras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                camera_id TEXT PRIMARY KEY,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                ip TEXT NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                connection_count INTEGER DEFAULT 0,
                successful_connections INTEGER DEFAULT 0,
                failed_connections INTEGER DEFAULT 0,
                total_uptime_minutes INTEGER DEFAULT 0,
                snapshots_count INTEGER DEFAULT 0,
                protocols TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de escaneos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                target_ip TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                duration_seconds REAL NOT NULL,
                ports_scanned INTEGER NOT NULL,
                ports_found INTEGER NOT NULL,
                authentication_tested BOOLEAN DEFAULT FALSE,
                successful_auths INTEGER DEFAULT 0,
                protocols_detected TEXT,
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                camera_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                resolution TEXT,
                format TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (camera_id) REFERENCES cameras (camera_id)
            )
        """)
        
        # Tabla de configuraciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configurations (
                config_key TEXT PRIMARY KEY,
                config_value TEXT NOT NULL,
                config_type TEXT DEFAULT 'string',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cameras_ip ON cameras(ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cameras_brand ON cameras(brand)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_ip ON scans(target_ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_camera ON snapshots(camera_id)")
        
        self._db_connection.commit()
    
    async def _create_tables_duckdb(self) -> None:
        """Crea las tablas necesarias en DuckDB."""
        # Similar a SQLite pero optimizado para análisis
        pass  # Implementación simplificada por ahora
    
    async def _initialize_cache(self) -> None:
        """Inicializa el cache en memoria."""
        # Cargar datos frecuentes al cache
        await self._load_recent_cameras_to_cache()
        await self._load_recent_scans_to_cache()
        
        self.logger.info(f"🧠 Cache inicializado: {len(self._camera_cache)} cámaras, {len(self._scan_cache)} escaneos")
    
    async def _load_recent_cameras_to_cache(self) -> None:
        """Carga cámaras recientes al cache."""
        if not self._db_connection:
            return
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT * FROM cameras 
                    WHERE last_seen > datetime('now', '-1 day')
                    ORDER BY last_seen DESC 
                    LIMIT 50
                """)
                
                for row in cursor.fetchall():
                    camera_data = CameraData(
                        camera_id=row['camera_id'],
                        brand=row['brand'],
                        model=row['model'],
                        ip=row['ip'],
                        last_seen=datetime.fromisoformat(row['last_seen']),
                        connection_count=row['connection_count'],
                        successful_connections=row['successful_connections'],
                        failed_connections=row['failed_connections'],
                        total_uptime_minutes=row['total_uptime_minutes'],
                        snapshots_count=row['snapshots_count'],
                        protocols=json.loads(row['protocols'] or '[]'),
                        metadata=json.loads(row['metadata'] or '{}')
                    )
                    
                    with self._cache_lock:
                        self._camera_cache[camera_data.camera_id] = camera_data
                        self._cache_timestamps[f"camera_{camera_data.camera_id}"] = datetime.now()
                        
        except Exception as e:
            self.logger.error(f"Error cargando cámaras al cache: {e}")
    
    async def _load_recent_scans_to_cache(self) -> None:
        """Carga escaneos recientes al cache."""
        if not self._db_connection:
            return
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT * FROM scans 
                    WHERE timestamp > datetime('now', '-1 hour')
                    ORDER BY timestamp DESC 
                    LIMIT 20
                """)
                
                for row in cursor.fetchall():
                    scan_data = ScanData(
                        scan_id=row['scan_id'],
                        target_ip=row['target_ip'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        duration_seconds=row['duration_seconds'],
                        ports_scanned=row['ports_scanned'],
                        ports_found=row['ports_found'],
                        authentication_tested=bool(row['authentication_tested']),
                        successful_auths=row['successful_auths'],
                        protocols_detected=json.loads(row['protocols_detected'] or '[]'),
                        results=json.loads(row['results'] or '{}')
                    )
                    
                    with self._cache_lock:
                        self._scan_cache[scan_data.scan_id] = scan_data
                        self._cache_timestamps[f"scan_{scan_data.scan_id}"] = datetime.now()
                        
        except Exception as e:
            self.logger.error(f"Error cargando escaneos al cache: {e}")
    
    # === Métodos de persistencia de cámaras ===
    
    async def save_camera_data(self, camera: CameraModel) -> bool:
        """
        Guarda o actualiza datos de una cámara.
        
        Args:
            camera: Modelo de cámara a guardar
            
        Returns:
            True si se guardó correctamente
        """
        try:
            # Obtener protocolos soportados de manera segura
            protocols = []
            if hasattr(camera, 'capabilities') and camera.capabilities and hasattr(camera.capabilities, 'supported_protocols'):
                protocols = [p.value if hasattr(p, 'value') else str(p) for p in camera.capabilities.supported_protocols]
            elif hasattr(camera, 'get_available_protocols'):
                available_protocols = camera.get_available_protocols()
                protocols = [p.value if hasattr(p, 'value') else str(p) for p in available_protocols]
            elif hasattr(camera, 'protocol') and camera.protocol:
                protocols = [camera.protocol.value] if hasattr(camera.protocol, 'value') else [str(camera.protocol)]
                
            camera_data = CameraData(
                camera_id=camera.camera_id,
                brand=camera.brand,
                model=camera.model,
                ip=camera.ip,
                last_seen=datetime.now(),
                protocols=protocols
            )
            
            # Actualizar cache
            with self._cache_lock:
                if camera.camera_id in self._camera_cache:
                    existing = self._camera_cache[camera.camera_id]
                    camera_data.connection_count = existing.connection_count
                    camera_data.successful_connections = existing.successful_connections
                    camera_data.failed_connections = existing.failed_connections
                    camera_data.total_uptime_minutes = existing.total_uptime_minutes
                    camera_data.snapshots_count = existing.snapshots_count
                
                self._camera_cache[camera.camera_id] = camera_data
                self._cache_timestamps[f"camera_{camera.camera_id}"] = datetime.now()
            
            # Guardar en base de datos
            await self._save_camera_to_db(camera_data)
            
            self._stats["cameras_tracked"] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando cámara {camera.camera_id}: {e}")
            return False
    
    async def _save_camera_to_db(self, camera_data: CameraData) -> None:
        """Guarda cámara en base de datos."""
        if not self._db_connection:
            raise RuntimeError("Base de datos no inicializada")
            
        with self._db_lock:
            cursor = self._db_connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cameras 
                (camera_id, brand, model, ip, last_seen, connection_count, 
                 successful_connections, failed_connections, total_uptime_minutes,
                 snapshots_count, protocols, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                camera_data.camera_id,
                camera_data.brand,
                camera_data.model,
                camera_data.ip,
                camera_data.last_seen.isoformat(),
                camera_data.connection_count,
                camera_data.successful_connections,
                camera_data.failed_connections,
                camera_data.total_uptime_minutes,
                camera_data.snapshots_count,
                json.dumps(camera_data.protocols),
                json.dumps(camera_data.metadata)
            ))
            self._db_connection.commit()
    
    async def get_camera_data(self, camera_id: str) -> Optional[CameraData]:
        """
        Obtiene datos de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Datos de la cámara o None si no existe
        """
        # Verificar cache primero
        with self._cache_lock:
            if camera_id in self._camera_cache:
                cache_key = f"camera_{camera_id}"
                if cache_key in self._cache_timestamps:
                    cache_age = datetime.now() - self._cache_timestamps[cache_key]
                    if cache_age < timedelta(hours=self.config.cache_ttl_hours):
                        self._stats["cache_hits"] += 1
                        return self._camera_cache[camera_id]
        
        # Buscar en base de datos
        self._stats["cache_misses"] += 1
        return await self._get_camera_from_db(camera_id)
    
    async def _get_camera_from_db(self, camera_id: str) -> Optional[CameraData]:
        """Obtiene cámara desde base de datos."""
        if not self._db_connection:
            return None
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("SELECT * FROM cameras WHERE camera_id = ?", (camera_id,))
                row = cursor.fetchone()
                
                if row:
                    # Acceso seguro a los campos de la row
                    def safe_get(field_name: str, default: Any = None) -> Any:
                        try:
                            return row[field_name] if row else default
                        except (KeyError, TypeError, IndexError):
                            return default
                    
                    camera_data = CameraData(
                        camera_id=safe_get('camera_id', ''),
                        brand=safe_get('brand', ''),
                        model=safe_get('model', ''),
                        ip=safe_get('ip', ''),
                        last_seen=datetime.fromisoformat(safe_get('last_seen', datetime.now().isoformat())),
                        connection_count=safe_get('connection_count', 0),
                        successful_connections=safe_get('successful_connections', 0),
                        failed_connections=safe_get('failed_connections', 0),
                        total_uptime_minutes=safe_get('total_uptime_minutes', 0),
                        snapshots_count=safe_get('snapshots_count', 0),
                        protocols=json.loads(safe_get('protocols') or '[]'),
                        metadata=json.loads(safe_get('metadata') or '{}')
                    )
                    
                    # Actualizar cache
                    with self._cache_lock:
                        self._camera_cache[camera_id] = camera_data
                        self._cache_timestamps[f"camera_{camera_id}"] = datetime.now()
                    
                    return camera_data
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo cámara {camera_id}: {e}")
        
        return None
    
    # === Métodos de exportación ===
    
    async def export_data(self, format: ExportFormat, filter_params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Exporta datos en el formato especificado.
        
        Args:
            format: Formato de exportación
            filter_params: Parámetros de filtrado
            
        Returns:
            Ruta del archivo exportado o None si falla
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = Path(self.config.export_directory)
            
            if format == ExportFormat.CSV:
                filename = f"camera_export_{timestamp}.csv"
                filepath = export_path / filename
                await self._export_to_csv(filepath, filter_params)
                
            elif format == ExportFormat.JSON:
                filename = f"camera_export_{timestamp}.json"
                filepath = export_path / filename
                await self._export_to_json(filepath, filter_params)
                
            elif format == ExportFormat.HTML:
                filename = f"camera_report_{timestamp}.html"
                filepath = export_path / filename
                await self._export_to_html(filepath, filter_params)
                
            else:
                self.logger.error(f"Formato de exportación no soportado: {format}")
                return None
            
            self._stats["export_operations"] += 1
            self.logger.info(f"📤 Datos exportados: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error exportando datos: {e}")
            return None
    
    async def _export_to_csv(self, filepath: Path, filter_params: Optional[Dict[str, Any]] = None) -> None:
        """Exporta datos a CSV."""
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Headers
            writer.writerow([
                'Camera ID', 'Brand', 'Model', 'IP', 'Last Seen',
                'Connection Count', 'Successful Connections', 'Failed Connections',
                'Uptime Minutes', 'Snapshots Count', 'Protocols'
            ])
            
            # Data
            cameras = await self._get_filtered_cameras(filter_params)
            for camera in cameras:
                writer.writerow([
                    camera.camera_id, camera.brand, camera.model, camera.ip,
                    camera.last_seen.isoformat(), camera.connection_count,
                    camera.successful_connections, camera.failed_connections,
                    camera.total_uptime_minutes, camera.snapshots_count,
                    ', '.join(camera.protocols)
                ])
    
    async def _export_to_json(self, filepath: Path, filter_params: Optional[Dict[str, Any]] = None) -> None:
        """Exporta datos a JSON."""
        cameras = await self._get_filtered_cameras(filter_params)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_cameras": len(cameras),
            "cameras": [asdict(camera) for camera in cameras],
            "statistics": self.get_statistics()
        }
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, default=str)
    
    async def _export_to_html(self, filepath: Path, filter_params: Optional[Dict[str, Any]] = None) -> None:
        """Exporta datos a HTML."""
        cameras = await self._get_filtered_cameras(filter_params)
        stats = self.get_statistics()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Camera System Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .stats {{ background-color: #e7f3ff; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Camera System Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="stats">
                <h2>Statistics</h2>
                <p>Total Cameras: {stats['cameras_tracked']}</p>
                <p>Total Scans: {stats['scans_recorded']}</p>
                <p>Total Snapshots: {stats['snapshots_stored']}</p>
                <p>Cache Hit Rate: {stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) * 100:.1f}%</p>
            </div>
            
            <h2>Cameras</h2>
            <table>
                <tr>
                    <th>Camera ID</th>
                    <th>Brand</th>
                    <th>Model</th>
                    <th>IP</th>
                    <th>Last Seen</th>
                    <th>Connections</th>
                    <th>Success Rate</th>
                    <th>Protocols</th>
                </tr>
        """
        
        for camera in cameras:
            success_rate = 0
            if camera.connection_count > 0:
                success_rate = (camera.successful_connections / camera.connection_count) * 100
            
            html_content += f"""
                <tr>
                    <td>{camera.camera_id}</td>
                    <td>{camera.brand}</td>
                    <td>{camera.model}</td>
                    <td>{camera.ip}</td>
                    <td>{camera.last_seen.strftime('%Y-%m-%d %H:%M')}</td>
                    <td>{camera.connection_count}</td>
                    <td>{success_rate:.1f}%</td>
                    <td>{', '.join(camera.protocols)}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(filepath, 'w', encoding='utf-8') as htmlfile:
            htmlfile.write(html_content)
    
    async def _get_filtered_cameras(self, filter_params: Optional[Dict[str, Any]] = None) -> List[CameraData]:
        """Obtiene cámaras con filtros aplicados."""
        if not self._db_connection:
            return []
            
        # Implementación simplificada - obtener todas las cámaras
        cameras = []
        
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("SELECT * FROM cameras ORDER BY last_seen DESC")
                
                for row in cursor.fetchall():
                    camera_data = CameraData(
                        camera_id=row['camera_id'],
                        brand=row['brand'],
                        model=row['model'],
                        ip=row['ip'],
                        last_seen=datetime.fromisoformat(row['last_seen']),
                        connection_count=row['connection_count'],
                        successful_connections=row['successful_connections'],
                        failed_connections=row['failed_connections'],
                        total_uptime_minutes=row['total_uptime_minutes'],
                        snapshots_count=row['snapshots_count'],
                        protocols=json.loads(row['protocols'] or '[]'),
                        metadata=json.loads(row['metadata'] or '{}')
                    )
                    cameras.append(camera_data)
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo cámaras filtradas: {e}")
        
        return cameras
    
    # === Métodos de estadísticas ===
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del servicio."""
        return {
            **self._stats,
            "cache_size": len(self._camera_cache) + len(self._scan_cache),
            "database_type": self.config.database_type.value,
            "uptime_minutes": (datetime.now() - datetime.now()).total_seconds() / 60  # Placeholder
        }
    
    async def get_camera_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas específicas de cámaras."""
        if not self._db_connection:
            return {}
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                
                # Función auxiliar para acceso seguro
                def safe_fetchone_get(cursor_result: Any, field: str, default: Any = 0) -> Any:
                    try:
                        row = cursor_result
                        if row and hasattr(row, '__getitem__'):
                            return row[field]
                        return default
                    except (KeyError, TypeError):
                        return default
                
                # Estadísticas básicas
                cursor.execute("SELECT COUNT(*) as total FROM cameras")
                result = cursor.fetchone()
                total_cameras = safe_fetchone_get(result, 'total', 0)
                
                cursor.execute("SELECT brand, COUNT(*) as count FROM cameras GROUP BY brand")
                brands = {}
                for row in cursor.fetchall():
                    try:
                        brand = row['brand'] if row else 'unknown'
                        count = row['count'] if row else 0
                        brands[brand] = count
                    except (KeyError, TypeError):
                        continue
                
                cursor.execute("SELECT AVG(successful_connections) as avg_success FROM cameras")
                result = cursor.fetchone()
                avg_success = safe_fetchone_get(result, 'avg_success', 0)
                
                return {
                    "total_cameras": total_cameras,
                    "brands_distribution": brands,
                    "average_success_rate": avg_success,
                    "cache_hit_rate": self._stats['cache_hits'] / max(1, self._stats['cache_hits'] + self._stats['cache_misses'])
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de cámaras: {e}")
            return {}
    
    # === Tareas de fondo ===
    
    async def _start_background_tasks(self) -> None:
        """Inicia las tareas de fondo."""
        # Tarea de limpieza de cache
        cache_cleanup_task = asyncio.create_task(self._cache_cleanup_worker())
        self._background_tasks.append(cache_cleanup_task)
        
        # Tarea de backup automático
        if self.config.backup_enabled:
            backup_task = asyncio.create_task(self._backup_worker())
            self._background_tasks.append(backup_task)
        
        # Tarea de limpieza de datos antiguos
        cleanup_task = asyncio.create_task(self._data_cleanup_worker())
        self._background_tasks.append(cleanup_task)
        
        self.logger.info(f"Iniciadas {len(self._background_tasks)} tareas de fondo")
    
    async def _cache_cleanup_worker(self) -> None:
        """Worker para limpieza periódica del cache."""
        while not self._shutdown:
            try:
                await asyncio.sleep(3600)  # Cada hora
                
                current_time = datetime.now()
                ttl = timedelta(hours=self.config.cache_ttl_hours)
                
                with self._cache_lock:
                    # Limpiar entradas expiradas
                    expired_keys = [
                        key for key, timestamp in self._cache_timestamps.items()
                        if current_time - timestamp > ttl
                    ]
                    
                    for key in expired_keys:
                        if key.startswith("camera_"):
                            camera_id = key.replace("camera_", "")
                            self._camera_cache.pop(camera_id, None)
                        elif key.startswith("scan_"):
                            scan_id = key.replace("scan_", "")
                            self._scan_cache.pop(scan_id, None)
                        
                        self._cache_timestamps.pop(key, None)
                    
                    if expired_keys:
                        self.logger.info(f"🧹 Cache limpiado: {len(expired_keys)} entradas eliminadas")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en limpieza de cache: {e}")
    
    async def _backup_worker(self) -> None:
        """Worker para backup automático."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.config.backup_interval_hours * 3600)
                await self._create_backup()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en backup automático: {e}")
    
    async def _create_backup(self) -> bool:
        """Crea un backup de la base de datos."""
        if not self._db_connection:
            return True # No hay nada que hacer backup en memoria
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = Path("data/backups") / f"backup_{timestamp}.db"
            
            # Copiar base de datos
            shutil.copy2(self.config.database_path, backup_path)
            
            self._stats["backup_operations"] += 1
            self.logger.info(f"Backup creado: {backup_path}")
            
            # Limpiar backups antiguos (mantener solo los últimos 10)
            backup_dir = Path("data/backups")
            backups = sorted(backup_dir.glob("backup_*.db"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
            return False
    
    async def _data_cleanup_worker(self) -> None:
        """Worker para limpieza de datos antiguos."""
        while not self._shutdown:
            try:
                await asyncio.sleep(24 * 3600)  # Cada 24 horas
                await self._cleanup_old_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en limpieza de datos: {e}")
    
    async def _cleanup_old_data(self) -> None:
        """Limpia datos antiguos según configuración."""
        if not self._db_connection:
            return
            
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.auto_cleanup_days)
            
            with self._db_lock:
                cursor = self._db_connection.cursor()
                
                # Limpiar escaneos antiguos
                cursor.execute("DELETE FROM scans WHERE timestamp < ?", (cutoff_date.isoformat(),))
                scans_deleted = cursor.rowcount
                
                # Limpiar snapshots antiguos
                cursor.execute("DELETE FROM snapshots WHERE timestamp < ?", (cutoff_date.isoformat(),))
                snapshots_deleted = cursor.rowcount
                
                self._db_connection.commit()
                
                if scans_deleted > 0 or snapshots_deleted > 0:
                    self.logger.info(f"🧹 Datos antiguos eliminados: {scans_deleted} escaneos, {snapshots_deleted} snapshots")
                    
        except Exception as e:
            self.logger.error(f"Error limpiando datos antiguos: {e}")
    
    async def _close_database(self) -> None:
        """Cierra la conexión a la base de datos."""
        if self._db_connection:
            with self._db_lock:
                self._db_connection.close()
                self._db_connection = None


# Función global para obtener instancia del servicio
_data_service_instance: Optional[DataService] = None


def get_data_service(config: Optional[DataServiceConfig] = None) -> DataService:
    """
    Obtiene la instancia global del DataService.
    
    Args:
        config: Configuración opcional
        
    Returns:
        Instancia del DataService
    """
    global _data_service_instance
    
    if _data_service_instance is None:
        _data_service_instance = DataService(config)
    
    return _data_service_instance 