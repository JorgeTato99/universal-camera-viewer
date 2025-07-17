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
    # Usar ruta absoluta basada en el proyecto
    database_path: str = str(Path(__file__).parent.parent.parent / "data" / "camera_data.db")
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
        """Crea las tablas necesarias en SQLite con diseño normalizado 3FN."""
        if not self._db_connection:
            raise RuntimeError("Base de datos no inicializada")
            
        # Usar el script create_database.py para crear la estructura
        from services.create_database import DatabaseCreator
        
        # Verificar si necesita crear las tablas
        cursor = self._db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cameras'")
        
        if not cursor.fetchone():
            self.logger.info("Base de datos no existe, creando estructura...")
            
            # Cerrar conexión actual
            self._db_connection.close()
            self._db_connection = None
            
            # Crear base de datos usando el script dedicado
            creator = DatabaseCreator(self.config.database_path)
            if not creator.create_database():
                raise RuntimeError("Error creando estructura de base de datos")
            
            # Reconectar a la nueva base de datos
            self._db_connection = sqlite3.connect(
                self.config.database_path,
                check_same_thread=False
            )
            self._db_connection.row_factory = sqlite3.Row
            
            # Habilitar claves foráneas
            self._db_connection.execute("PRAGMA foreign_keys = ON")
            
            self.logger.info("Base de datos creada y reconectada exitosamente")
    
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
        """Carga cámaras recientes al cache usando la nueva estructura 3FN."""
        if not self._db_connection:
            return
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                # Query actualizada para nueva estructura
                cursor.execute("""
                    SELECT 
                        c.camera_id, c.brand, c.model, c.ip_address,
                        cs.last_connection_at, cs.total_connections,
                        cs.successful_connections, cs.failed_connections,
                        cs.total_uptime_seconds
                    FROM cameras c
                    LEFT JOIN camera_statistics cs ON c.camera_id = cs.camera_id
                    WHERE cs.last_connection_at > datetime('now', '-1 day')
                       OR c.created_at > datetime('now', '-1 day')
                    ORDER BY COALESCE(cs.last_connection_at, c.created_at) DESC 
                    LIMIT 50
                """)
                
                for row in cursor.fetchall():
                    # Obtener protocolos de la cámara
                    cursor.execute("""
                        SELECT protocol_type FROM camera_protocols 
                        WHERE camera_id = ? AND is_enabled = 1
                    """, (row[0],))
                    protocols = [p[0] for p in cursor.fetchall()]
                    
                    camera_data = CameraData(
                        camera_id=row[0],
                        brand=row[1],
                        model=row[2],
                        ip=row[3],
                        last_seen=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                        connection_count=row[5] or 0,
                        successful_connections=row[6] or 0,
                        failed_connections=row[7] or 0,
                        total_uptime_minutes=int((row[8] or 0) / 60),
                        snapshots_count=0,  # Campo no existe en nueva estructura
                        protocols=protocols,
                        metadata={}
                    )
                    
                    with self._cache_lock:
                        self._camera_cache[camera_data.camera_id] = camera_data
                        self._cache_timestamps[f"camera_{camera_data.camera_id}"] = datetime.now()
                        
        except Exception as e:
            self.logger.error(f"Error cargando cámaras al cache desde nueva estructura: {e}")
    
    async def _load_recent_scans_to_cache(self) -> None:
        """Carga escaneos recientes al cache."""
        if not self._db_connection:
            return
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                # Por ahora omitir carga de escaneos ya que la tabla se llama network_scans
                # y tiene estructura diferente. Necesita adaptación completa.
                pass  # TODO: Adaptar a nueva estructura network_scans
                
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
        DEPRECATED: Use save_camera_with_config() para la nueva estructura 3FN.
        
        Guarda o actualiza datos de una cámara.
        Este método es un wrapper de compatibilidad para código legacy.
        
        Args:
            camera: Modelo de cámara a guardar
            
        Returns:
            True si se guardó correctamente
        """
        self.logger.warning(
            f"DEPRECATED: save_camera_data() llamado para {camera.camera_id}. "
            "Use save_camera_with_config() para la nueva estructura 3FN."
        )
        
        try:
            # Extraer credenciales del modelo si están disponibles
            credentials = {}
            if hasattr(camera, 'connection_config') and camera.connection_config:
                credentials = {
                    'username': getattr(camera.connection_config, 'username', 'admin'),
                    'password': getattr(camera.connection_config, 'password', '')
                }
            
            # Extraer endpoints si están disponibles
            endpoints = []
            if hasattr(camera, 'stream_url') and camera.stream_url:
                endpoints.append({
                    'type': 'rtsp_main',
                    'url': camera.stream_url,
                    'protocol': 'RTSP',
                    'verified': True
                })
            
            # Llamar al nuevo método
            result = await self.save_camera_with_config(camera, credentials, endpoints)
            
            if result:
                self._stats["cameras_tracked"] += 1
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error en wrapper save_camera_data para {camera.camera_id}: {e}")
            return False
    
    async def _save_camera_to_db(self, camera_data: CameraData) -> None:
        """
        DEPRECATED: Método interno para compatibilidad con estructura antigua.
        
        Este método mapea la estructura antigua a la nueva estructura 3FN.
        """
        if not self._db_connection:
            raise RuntimeError("Base de datos no inicializada")
            
        self.logger.warning(
            "DEPRECATED: _save_camera_to_db() usa estructura antigua. "
            "Migrando automáticamente a nueva estructura 3FN."
        )
        
        # Crear un modelo temporal para usar el método nuevo
        temp_model = CameraModel(
            brand=camera_data.brand,
            model=camera_data.model,
            display_name=f"{camera_data.brand} {camera_data.model}",
            connection_config=ConnectionConfig(
                ip=camera_data.ip,
                username="admin",
                password=""
            )
        )
        temp_model.camera_id = camera_data.camera_id
        
        # Usar el método nuevo con credenciales vacías
        await self.save_camera_with_config(temp_model, {'username': 'admin', 'password': ''})
        
        # Actualizar estadísticas si es necesario
        if any([camera_data.connection_count, camera_data.successful_connections, 
                camera_data.failed_connections, camera_data.total_uptime_minutes]):
            await self.update_connection_stats(
                camera_data.camera_id,
                success=camera_data.successful_connections > 0,
                connection_time=camera_data.total_uptime_minutes * 60 if camera_data.total_uptime_minutes else 0
            )
    
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
        """
        DEPRECATED: Método que mapea la nueva estructura 3FN a la estructura antigua.
        
        Este método mantiene compatibilidad con código que espera CameraData.
        """
        if not self._db_connection:
            return None
            
        try:
            # Usar el método nuevo para obtener configuración completa
            full_config = await self.get_camera_full_config(camera_id)
            
            if not full_config:
                return None
            
            # Mapear a estructura antigua
            camera = full_config.get('camera', {})
            stats = full_config.get('statistics', {})
            protocols = [p['type'] for p in full_config.get('protocols', [])]
            
            camera_data = CameraData(
                camera_id=camera.get('camera_id', ''),
                brand=camera.get('brand', ''),
                model=camera.get('model', ''),
                ip=camera.get('ip_address', ''),
                last_seen=datetime.fromisoformat(stats.get('last_connection_at', datetime.now().isoformat())),
                connection_count=stats.get('total_connections', 0),
                successful_connections=stats.get('successful_connections', 0),
                failed_connections=stats.get('failed_connections', 0),
                total_uptime_minutes=int(stats.get('total_uptime_seconds', 0) / 60),
                snapshots_count=stats.get('snapshots_taken', 0),
                protocols=protocols,
                metadata=camera.get('metadata', {})
            )
            
            # Actualizar cache
            with self._cache_lock:
                self._camera_cache[camera_id] = camera_data
                self._cache_timestamps[f"camera_{camera_id}"] = datetime.now()
            
            self.logger.debug(
                f"Mapeado cámara {camera_id} de nueva estructura 3FN a CameraData legacy"
            )
            
            return camera_data
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo cámara {camera_id} desde nueva estructura: {e}")
        
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
        """Obtiene cámaras con filtros aplicados usando nueva estructura 3FN."""
        if not self._db_connection:
            return []
            
        cameras = []
        
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                # Query actualizada para nueva estructura
                cursor.execute("""
                    SELECT 
                        c.camera_id, c.brand, c.model, c.ip_address,
                        cs.last_connection_at, cs.total_connections,
                        cs.successful_connections, cs.failed_connections,
                        cs.total_uptime_seconds
                    FROM cameras c
                    LEFT JOIN camera_statistics cs ON c.camera_id = cs.camera_id
                    WHERE c.is_active = 1
                    ORDER BY COALESCE(cs.last_connection_at, c.created_at) DESC
                """)
                
                for row in cursor.fetchall():
                    # Obtener protocolos de la cámara
                    cursor.execute("""
                        SELECT protocol_type FROM camera_protocols 
                        WHERE camera_id = ? AND is_enabled = 1
                    """, (row[0],))
                    protocols = [p[0] for p in cursor.fetchall()]
                    
                    camera_data = CameraData(
                        camera_id=row[0],
                        brand=row[1],
                        model=row[2],
                        ip=row[3],
                        last_seen=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                        connection_count=row[5] or 0,
                        successful_connections=row[6] or 0,
                        failed_connections=row[7] or 0,
                        total_uptime_minutes=int((row[8] or 0) / 60),
                        snapshots_count=0,  # Campo no existe en nueva estructura
                        protocols=protocols,
                        metadata={}
                    )
                    cameras.append(camera_data)
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo cámaras filtradas desde nueva estructura: {e}")
        
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
                # TODO: Adaptar a nueva estructura network_scans
                scans_deleted = 0  # cursor.execute("DELETE FROM network_scans WHERE start_time < ?", (cutoff_date.isoformat(),))
                
                # Limpiar snapshots antiguos
                cursor.execute("DELETE FROM snapshots WHERE timestamp < ?", (cutoff_date.isoformat(),))
                snapshots_deleted = cursor.rowcount
                
                self._db_connection.commit()
                
                if scans_deleted > 0 or snapshots_deleted > 0:
                    self.logger.info(f"🧹 Datos antiguos eliminados: {scans_deleted} escaneos, {snapshots_deleted} snapshots")
                    
        except Exception as e:
            self.logger.error(f"Error limpiando datos antiguos: {e}")
    
    # ================== NUEVOS MÉTODOS CRUD PARA ESTRUCTURA 3FN ==================
    
    async def save_camera_with_config(self, camera: CameraModel, credentials: Dict[str, str],
                                    endpoints: List[Dict[str, Any]] = None) -> bool:
        """
        Guarda una cámara con su configuración completa en la nueva estructura.
        
        Args:
            camera: Modelo de cámara
            credentials: Diccionario con username y password
            endpoints: Lista de endpoints/URLs descubiertas
            
        Returns:
            bool: True si se guardó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                
                # Iniciar transacción
                cursor.execute("BEGIN TRANSACTION")
                
                # 1. Guardar cámara básica
                cursor.execute("""
                    INSERT OR REPLACE INTO cameras (
                        camera_id, brand, model, display_name, ip_address,
                        is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    camera.camera_id,
                    camera.brand,
                    camera.model,
                    camera.display_name or f"{camera.brand} {camera.model}",
                    camera.ip,
                    True,
                    datetime.now(),
                    datetime.now()
                ))
                
                # 2. Guardar credenciales encriptadas
                if credentials:
                    from .encryption_service import encryption_service
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO camera_credentials (
                            camera_id, credential_name, username, password_encrypted, 
                            auth_type, is_default
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        camera.camera_id,
                        'Credencial Principal',  # Nombre por defecto
                        credentials.get('username', 'admin'),
                        encryption_service.encrypt(credentials.get('password', '')),
                        'basic',
                        True
                    ))
                
                # 3. Guardar protocolos
                protocols = camera.protocols if hasattr(camera, 'protocols') else ['ONVIF', 'RTSP']
                for idx, protocol in enumerate(protocols):
                    port = self._get_port_for_protocol(camera, protocol)
                    cursor.execute("""
                        INSERT OR REPLACE INTO camera_protocols (
                            camera_id, protocol_type, port, 
                            is_enabled, is_primary
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        camera.camera_id,
                        protocol.upper(),
                        port,
                        True,
                        idx == 0
                    ))
                
                # 4. Guardar endpoints si se proporcionan
                if endpoints:
                    for endpoint in endpoints:
                        cursor.execute("""
                            INSERT INTO camera_endpoints (
                                camera_id, endpoint_type, url, protocol,
                                is_verified, priority
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            camera.camera_id,
                            endpoint.get('type', 'rtsp_main'),
                            endpoint.get('url'),
                            endpoint.get('protocol', 'RTSP'),
                            endpoint.get('verified', False),
                            endpoint.get('priority', 0)
                        ))
                
                # 5. Crear registro de estadísticas
                cursor.execute("""
                    INSERT OR IGNORE INTO camera_statistics (
                        camera_id, total_connections, successful_connections,
                        failed_connections, total_uptime_seconds
                    ) VALUES (?, ?, ?, ?, ?)
                """, (camera.camera_id, 0, 0, 0, 0))
                
                # Confirmar transacción
                self._db_connection.commit()
                
                # Actualizar cache
                self._camera_cache[camera.camera_id] = CameraData(
                    camera_id=camera.camera_id,
                    brand=camera.brand,
                    model=camera.model,
                    ip=camera.ip,
                    last_seen=datetime.now(),
                    connection_count=0,
                    successful_connections=0,
                    failed_connections=0,
                    total_uptime_minutes=0,
                    snapshots_count=0,
                    protocols=protocols,
                    metadata={}
                )
                
                self.logger.info(f"Cámara {camera.camera_id} guardada con configuración completa")
                return True
                
        except Exception as e:
            self.logger.error(f"Error guardando cámara con configuración: {e}")
            if self._db_connection:
                self._db_connection.rollback()
            return False
    
    async def get_camera_full_config(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración completa de una cámara desde la nueva estructura.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Dict con toda la configuración o None si no existe
        """
        if not self._db_connection:
            return None
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                
                # Obtener datos básicos
                cursor.execute("""
                    SELECT * FROM cameras WHERE camera_id = ?
                """, (camera_id,))
                camera_row = cursor.fetchone()
                
                if not camera_row:
                    return None
                
                # Convertir a diccionario
                camera_data = dict(zip([col[0] for col in cursor.description], camera_row))
                
                # Obtener credenciales
                cursor.execute("""
                    SELECT username, password_encrypted 
                    FROM camera_credentials 
                    WHERE camera_id = ? AND is_default = 1
                """, (camera_id,))
                cred_row = cursor.fetchone()
                
                if cred_row:
                    from .encryption_service import encryption_service
                    camera_data['credentials'] = {
                        'username': cred_row[0],
                        'password': encryption_service.decrypt(cred_row[1]) if cred_row[1] else ''
                    }
                
                # Obtener protocolos
                cursor.execute("""
                    SELECT protocol_type, port, is_primary 
                    FROM camera_protocols 
                    WHERE camera_id = ? AND is_enabled = 1
                    ORDER BY is_primary DESC
                """, (camera_id,))
                protocols = []
                for row in cursor.fetchall():
                    protocols.append({
                        'type': row[0],
                        'port': row[1],
                        'is_primary': bool(row[2])
                    })
                camera_data['protocols'] = protocols
                
                # Obtener endpoints
                cursor.execute("""
                    SELECT endpoint_type, url, is_verified, priority 
                    FROM camera_endpoints 
                    WHERE camera_id = ?
                    ORDER BY priority ASC, is_verified DESC
                """, (camera_id,))
                endpoints = []
                for row in cursor.fetchall():
                    endpoints.append({
                        'type': row[0],
                        'url': row[1],
                        'verified': bool(row[2]),
                        'priority': row[3]
                    })
                camera_data['endpoints'] = endpoints
                
                # Obtener estadísticas
                cursor.execute("""
                    SELECT * FROM camera_statistics WHERE camera_id = ?
                """, (camera_id,))
                stats_row = cursor.fetchone()
                if stats_row:
                    camera_data['statistics'] = dict(zip(
                        [col[0] for col in cursor.description], stats_row
                    ))
                
                return camera_data
                
        except Exception as e:
            self.logger.error(f"Error obteniendo configuración completa: {e}")
            return None
    
    async def save_discovered_endpoint(self, camera_id: str, endpoint_type: str, 
                                     url: str, verified: bool = False) -> bool:
        """
        Guarda un endpoint/URL descubierto para una cámara.
        
        Args:
            camera_id: ID de la cámara
            endpoint_type: Tipo de endpoint (rtsp_main, snapshot, etc)
            url: URL completa
            verified: Si fue verificada exitosamente
            
        Returns:
            bool: True si se guardó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                
                # Verificar si ya existe
                cursor.execute("""
                    SELECT endpoint_id FROM camera_endpoints 
                    WHERE camera_id = ? AND endpoint_type = ? AND url = ?
                """, (camera_id, endpoint_type, url))
                
                if cursor.fetchone():
                    # Actualizar verificación
                    cursor.execute("""
                        UPDATE camera_endpoints 
                        SET is_verified = ?, last_verified = ?
                        WHERE camera_id = ? AND endpoint_type = ? AND url = ?
                    """, (verified, datetime.now() if verified else None,
                         camera_id, endpoint_type, url))
                else:
                    # Insertar nuevo
                    cursor.execute("""
                        INSERT INTO camera_endpoints (
                            camera_id, endpoint_type, url, 
                            is_verified, last_verified, priority
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (camera_id, endpoint_type, url, verified,
                         datetime.now() if verified else None, 0))
                
                self._db_connection.commit()
                
                self.logger.info(f"Endpoint {endpoint_type} guardado para {camera_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error guardando endpoint: {e}")
            return False
    
    async def update_connection_stats(self, camera_id: str, success: bool, 
                                    duration_ms: int = 0) -> bool:
        """
        Actualiza las estadísticas de conexión de una cámara.
        
        Args:
            camera_id: ID de la cámara
            success: Si la conexión fue exitosa
            duration_ms: Duración de la conexión en ms
            
        Returns:
            bool: True si se actualizó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                
                # Actualizar estadísticas
                if success:
                    cursor.execute("""
                        UPDATE camera_statistics 
                        SET total_connections = total_connections + 1,
                            successful_connections = successful_connections + 1,
                            last_connection_at = ?
                        WHERE camera_id = ?
                    """, (datetime.now(), camera_id))
                else:
                    cursor.execute("""
                        UPDATE camera_statistics 
                        SET total_connections = total_connections + 1,
                            failed_connections = failed_connections + 1,
                            last_error_at = ?
                        WHERE camera_id = ?
                    """, (datetime.now(), camera_id))
                
                # Insertar log de conexión
                import uuid
                cursor.execute("""
                    INSERT INTO connection_logs (
                        camera_id, session_id, status, duration_seconds, started_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (camera_id, str(uuid.uuid4()), 
                     'connected' if success else 'failed', 
                     int(duration_ms / 1000) if duration_ms > 0 else 0, 
                     datetime.now()))
                
                self._db_connection.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas: {e}")
            return False
    
    def _get_port_for_protocol(self, camera: CameraModel, protocol: str) -> int:
        """Obtiene el puerto para un protocolo específico considerando la marca."""
        protocol_lower = protocol.lower()
        brand_lower = camera.brand.lower() if hasattr(camera, 'brand') else ''
        
        # Verificar si la cámara tiene puertos específicos definidos
        if hasattr(camera, 'connection_config') and camera.connection_config:
            config = camera.connection_config
            if protocol_lower == 'rtsp' and hasattr(config, 'rtsp_port'):
                return config.rtsp_port
            elif protocol_lower == 'onvif' and hasattr(config, 'onvif_port'):
                return config.onvif_port
            elif protocol_lower == 'http' and hasattr(config, 'http_port'):
                return config.http_port
        
        # Puertos específicos por marca según documentación
        brand_ports = {
            'dahua': {
                'rtsp': 554,
                'onvif': 80,
                'http': 80
            },
            'tplink': {
                'rtsp': 554,
                'onvif': 2020,  # Puerto ONVIF específico de TP-Link
                'http': 80
            },
            'steren': {
                'rtsp': 5543,   # Puerto RTSP específico de Steren
                'onvif': 8000,  # Puerto ONVIF específico de Steren
                'http': 80
            },
            'hikvision': {
                'rtsp': 554,
                'onvif': 80,
                'http': 80
            },
            'reolink': {
                'rtsp': 554,
                'onvif': 8000,  # Puerto ONVIF específico de Reolink
                'http': 80
            }
        }
        
        # Buscar puerto específico por marca
        if brand_lower in brand_ports:
            return brand_ports[brand_lower].get(protocol_lower, 80)
        
        # Puertos por defecto genéricos
        default_ports = {
            'rtsp': 554,
            'onvif': 80,
            'http': 80,
            'https': 443
        }
        return default_ports.get(protocol_lower, 80)
    
    async def get_all_camera_ids(self) -> List[str]:
        """
        Obtiene todos los IDs de cámaras activas.
        
        Returns:
            Lista de camera_ids
        """
        if not self._db_connection:
            return []
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT camera_id FROM cameras WHERE is_active = 1
                """)
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error obteniendo IDs de cámaras: {e}")
            return []
    
    # === Métodos de Gestión de Credenciales ===
    
    async def get_camera_credentials(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las credenciales de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Lista de credenciales con todos los campos
        """
        if not self._db_connection:
            return []
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT 
                        credential_id,
                        credential_name,
                        username,
                        password_encrypted,
                        auth_type,
                        is_active,
                        is_default,
                        last_used,
                        created_at,
                        updated_at
                    FROM camera_credentials
                    WHERE camera_id = ?
                    ORDER BY is_default DESC, credential_name
                """, (camera_id,))
                
                credentials = []
                for row in cursor.fetchall():
                    credentials.append({
                        'credential_id': row[0],
                        'credential_name': row[1],
                        'username': row[2],
                        'password_encrypted': row[3],
                        'auth_type': row[4],
                        'is_active': bool(row[5]),
                        'is_default': bool(row[6]),
                        'last_used': row[7],
                        'created_at': row[8],
                        'updated_at': row[9]
                    })
                
                return credentials
                
        except Exception as e:
            self.logger.error(f"Error obteniendo credenciales de {camera_id}: {e}")
            return []
    
    async def get_credential_by_id(self, camera_id: str, credential_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene una credencial específica.
        
        Args:
            camera_id: ID de la cámara
            credential_id: ID de la credencial
            
        Returns:
            Credencial o None si no existe
        """
        if not self._db_connection:
            return None
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT 
                        credential_id,
                        credential_name,
                        username,
                        password_encrypted,
                        auth_type,
                        is_active,
                        is_default,
                        last_used,
                        created_at,
                        updated_at
                    FROM camera_credentials
                    WHERE camera_id = ? AND credential_id = ?
                """, (camera_id, credential_id))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'credential_id': row[0],
                        'credential_name': row[1],
                        'username': row[2],
                        'password_encrypted': row[3],
                        'auth_type': row[4],
                        'is_active': bool(row[5]),
                        'is_default': bool(row[6]),
                        'last_used': row[7],
                        'created_at': row[8],
                        'updated_at': row[9]
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error obteniendo credencial {credential_id}: {e}")
            return None
    
    async def add_camera_credential(self, camera_id: str, credential_data: Dict[str, Any]) -> int:
        """
        Agrega una nueva credencial a una cámara.
        
        La contraseña se encripta automáticamente antes de almacenar.
        
        Args:
            camera_id: ID de la cámara
            credential_data: Datos de la credencial con campos:
                - credential_name: Nombre único de la credencial
                - username: Nombre de usuario
                - password: Contraseña sin encriptar
                - auth_type: Tipo de autenticación (default: 'basic')
                - is_default: Si es la credencial predeterminada (default: False)
            
        Returns:
            ID de la credencial creada
            
        Raises:
            Exception: Si la base de datos no está inicializada
            sqlite3.IntegrityError: Si viola restricciones únicas
            Exception: Error al encriptar o insertar datos
        """
        if not self._db_connection:
            raise Exception("Base de datos no inicializada")
            
        credential_id = None
        try:
            # Encriptar contraseña
            password_encrypted = self._encryption_service.encrypt(
                credential_data['password']
            )
            
            with self._db_lock:
                cursor = self._db_connection.cursor()
                
                # Verificar si ya existe una credencial con el mismo nombre
                cursor.execute("""
                    SELECT COUNT(*) FROM camera_credentials 
                    WHERE camera_id = ? AND credential_name = ?
                """, (camera_id, credential_data['credential_name']))
                
                if cursor.fetchone()[0] > 0:
                    raise ValueError(f"Ya existe una credencial con el nombre '{credential_data['credential_name']}'")
                
                # Insertar nueva credencial
                cursor.execute("""
                    INSERT INTO camera_credentials (
                        camera_id, credential_name, username, 
                        password_encrypted, auth_type, is_default
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    camera_id,
                    credential_data['credential_name'],
                    credential_data['username'],
                    password_encrypted,
                    credential_data.get('auth_type', 'basic'),
                    credential_data.get('is_default', False)
                ))
                
                credential_id = cursor.lastrowid
                self._db_connection.commit()
                
                self.logger.info(f"Credencial {credential_id} creada para cámara {camera_id}")
                return credential_id
                
        except ValueError:
            # Re-lanzar errores de validación
            raise
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Error de integridad al agregar credencial: {e}")
            if self._db_connection:
                self._db_connection.rollback()
            raise ValueError("Error de integridad: posible duplicado de credencial")
        except Exception as e:
            self.logger.error(f"Error agregando credencial: {e}", exc_info=True)
            if self._db_connection:
                self._db_connection.rollback()
            raise Exception(f"Error al agregar credencial: {str(e)}")
    
    async def update_credential(self, camera_id: str, credential_id: int, updates: Dict[str, Any]) -> bool:
        """
        Actualiza una credencial existente.
        
        Args:
            camera_id: ID de la cámara
            credential_id: ID de la credencial
            updates: Campos a actualizar
            
        Returns:
            True si se actualizó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            # Construir query dinámicamente
            set_clauses = []
            params = []
            
            if 'credential_name' in updates:
                set_clauses.append("credential_name = ?")
                params.append(updates['credential_name'])
            
            if 'username' in updates:
                set_clauses.append("username = ?")
                params.append(updates['username'])
                
            if 'password' in updates:
                set_clauses.append("password_encrypted = ?")
                params.append(self._encryption_service.encrypt(updates['password']))
                
            if 'auth_type' in updates:
                set_clauses.append("auth_type = ?")
                params.append(updates['auth_type'])
                
            if 'is_default' in updates:
                set_clauses.append("is_default = ?")
                params.append(updates['is_default'])
            
            if not set_clauses:
                return True  # Nada que actualizar
            
            # Agregar updated_at
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            
            # Agregar condiciones WHERE
            params.extend([camera_id, credential_id])
            
            query = f"""
                UPDATE camera_credentials 
                SET {', '.join(set_clauses)}
                WHERE camera_id = ? AND credential_id = ?
            """
            
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute(query, params)
                self._db_connection.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error actualizando credencial: {e}")
            return False
    
    async def delete_credential(self, camera_id: str, credential_id: int) -> bool:
        """
        Elimina una credencial.
        
        Args:
            camera_id: ID de la cámara
            credential_id: ID de la credencial
            
        Returns:
            True si se eliminó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    DELETE FROM camera_credentials
                    WHERE camera_id = ? AND credential_id = ?
                """, (camera_id, credential_id))
                
                self._db_connection.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error eliminando credencial: {e}")
            return False
    
    async def clear_default_credentials(self, camera_id: str) -> bool:
        """
        Quita el flag de default de todas las credenciales de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se actualizó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    UPDATE camera_credentials
                    SET is_default = 0
                    WHERE camera_id = ?
                """, (camera_id,))
                
                self._db_connection.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error limpiando credenciales default: {e}")
            return False
    
    async def set_credential_as_default(self, camera_id: str, credential_id: int) -> bool:
        """
        Establece una credencial como predeterminada.
        
        Args:
            camera_id: ID de la cámara
            credential_id: ID de la credencial
            
        Returns:
            True si se estableció correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                # Primero quitar default de todas
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    UPDATE camera_credentials
                    SET is_default = 0
                    WHERE camera_id = ?
                """, (camera_id,))
                
                # Luego establecer la nueva como default
                cursor.execute("""
                    UPDATE camera_credentials
                    SET is_default = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE camera_id = ? AND credential_id = ?
                """, (camera_id, credential_id))
                
                self._db_connection.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error estableciendo credencial default: {e}")
            return False
    
    # === Métodos de Gestión de Stream Profiles ===
    
    async def get_stream_profiles(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los perfiles de streaming de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Lista de perfiles con todos los campos
        """
        if not self._db_connection:
            return []
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT 
                        profile_id,
                        profile_name,
                        profile_token,
                        stream_type,
                        encoding,
                        resolution,
                        framerate,
                        bitrate,
                        quality,
                        gop_interval,
                        channel,
                        subtype,
                        is_default,
                        is_active,
                        endpoint_id,
                        created_at,
                        updated_at
                    FROM camera_stream_profiles
                    WHERE camera_id = ?
                    ORDER BY is_default DESC, stream_type, profile_name
                """, (camera_id,))
                
                profiles = []
                for row in cursor.fetchall():
                    profiles.append({
                        'profile_id': row[0],
                        'profile_name': row[1],
                        'profile_token': row[2],
                        'stream_type': row[3],
                        'encoding': row[4],
                        'resolution': row[5],
                        'framerate': row[6],
                        'bitrate': row[7],
                        'quality': row[8],
                        'gop_interval': row[9],
                        'channel': row[10],
                        'subtype': row[11],
                        'is_default': bool(row[12]),
                        'is_active': bool(row[13]),
                        'endpoint_id': row[14],
                        'created_at': row[15],
                        'updated_at': row[16]
                    })
                
                return profiles
                
        except Exception as e:
            self.logger.error(f"Error obteniendo perfiles de streaming de {camera_id}: {e}")
            return []
    
    async def get_stream_profile_by_id(self, camera_id: str, profile_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un perfil de streaming específico.
        
        Args:
            camera_id: ID de la cámara
            profile_id: ID del perfil
            
        Returns:
            Perfil o None si no existe
        """
        if not self._db_connection:
            return None
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT 
                        profile_id,
                        profile_name,
                        profile_token,
                        stream_type,
                        encoding,
                        resolution,
                        framerate,
                        bitrate,
                        quality,
                        gop_interval,
                        channel,
                        subtype,
                        is_default,
                        is_active,
                        endpoint_id,
                        created_at,
                        updated_at
                    FROM camera_stream_profiles
                    WHERE camera_id = ? AND profile_id = ?
                """, (camera_id, profile_id))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'profile_id': row[0],
                        'profile_name': row[1],
                        'profile_token': row[2],
                        'stream_type': row[3],
                        'encoding': row[4],
                        'resolution': row[5],
                        'framerate': row[6],
                        'bitrate': row[7],
                        'quality': row[8],
                        'gop_interval': row[9],
                        'channel': row[10],
                        'subtype': row[11],
                        'is_default': bool(row[12]),
                        'is_active': bool(row[13]),
                        'endpoint_id': row[14],
                        'created_at': row[15],
                        'updated_at': row[16]
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Error obteniendo perfil {profile_id}: {e}")
            return None
    
    async def add_stream_profile(self, camera_id: str, profile_data: Dict[str, Any]) -> int:
        """
        Agrega un nuevo perfil de streaming.
        
        Maneja automáticamente la asignación de perfil default si es el primero
        de su tipo o si se especifica explícitamente. Solo puede haber un perfil
        default por tipo de stream (main, sub, third, mobile).
        
        Args:
            camera_id: ID de la cámara (UUID)
            profile_data: Datos del perfil con campos:
                - profile_name (str): Nombre único del perfil
                - stream_type (str): Tipo de stream (main/sub/third/mobile)
                - resolution (str): Resolución en formato WIDTHxHEIGHT
                - framerate (int): FPS del stream
                - bitrate (int): Bitrate en kbps
                - encoding (str, opcional): Codec de video, default 'H264'
                - quality (str, opcional): Nivel de calidad, default 'high'
                - gop_interval (int, opcional): Intervalo GOP
                - channel (int, opcional): Canal de la cámara, default 1
                - subtype (int, opcional): Subtipo del stream, default 0
                - is_default (bool, opcional): Si debe ser el perfil default
            
        Returns:
            ID del perfil creado
            
        Raises:
            ValueError: Si hay errores de validación o nombre duplicado
            sqlite3.IntegrityError: Si viola constraints de unicidad en BD
        """
        if not self._db_connection:
            raise ValueError("Sin conexión a base de datos")
            
        try:
            # Verificar si ya existe un perfil con el mismo nombre
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM camera_stream_profiles
                    WHERE camera_id = ? AND profile_name = ?
                """, (camera_id, profile_data['profile_name']))
                
                if cursor.fetchone()[0] > 0:
                    raise ValueError(f"Ya existe un perfil con el nombre '{profile_data['profile_name']}'")
                
                # Si es default, quitar default de otros perfiles del mismo tipo
                if profile_data.get('is_default', False):
                    cursor.execute("""
                        UPDATE camera_stream_profiles
                        SET is_default = 0
                        WHERE camera_id = ? AND stream_type = ?
                    """, (camera_id, profile_data['stream_type']))
                    self.logger.debug(
                        f"Quitando flag default de perfiles tipo {profile_data['stream_type']} "
                        f"para cámara {camera_id}"
                    )
                
                # Insertar el nuevo perfil
                cursor.execute("""
                    INSERT INTO camera_stream_profiles (
                        camera_id, profile_name, stream_type, encoding,
                        resolution, framerate, bitrate, quality,
                        gop_interval, channel, subtype, is_default
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    camera_id,
                    profile_data['profile_name'],
                    profile_data['stream_type'],
                    profile_data.get('encoding', 'H264'),
                    profile_data['resolution'],
                    profile_data['framerate'],
                    profile_data['bitrate'],
                    profile_data.get('quality', 'high'),
                    profile_data.get('gop_interval'),
                    profile_data.get('channel', 1),
                    profile_data.get('subtype', 0),
                    1 if profile_data.get('is_default', False) else 0
                ))
                
                profile_id = cursor.lastrowid
                self._db_connection.commit()
                
                self.logger.info(f"Perfil de streaming {profile_id} creado para cámara {camera_id}")
                return profile_id
                
        except sqlite3.IntegrityError as e:
            self._db_connection.rollback()
            self.logger.error(f"Error de integridad al crear perfil: {e}")
            raise ValueError("Violación de constraint de unicidad")
        except Exception as e:
            self._db_connection.rollback()
            self.logger.error(f"Error creando perfil de streaming: {e}")
            raise
    
    async def update_stream_profile(self, camera_id: str, profile_id: int, updates: Dict[str, Any]) -> bool:
        """
        Actualiza un perfil de streaming existente.
        
        Args:
            camera_id: ID de la cámara
            profile_id: ID del perfil
            updates: Campos a actualizar
            
        Returns:
            True si se actualizó correctamente
            
        Raises:
            ValueError: Si el perfil no existe o hay errores de validación
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                # Verificar que el perfil existe
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT stream_type FROM camera_stream_profiles
                    WHERE camera_id = ? AND profile_id = ?
                """, (camera_id, profile_id))
                
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Perfil {profile_id} no encontrado")
                
                stream_type = result[0]
                
                # Si cambia el nombre, verificar que no exista
                if 'profile_name' in updates:
                    cursor.execute("""
                        SELECT COUNT(*) FROM camera_stream_profiles
                        WHERE camera_id = ? AND profile_name = ? AND profile_id != ?
                    """, (camera_id, updates['profile_name'], profile_id))
                    
                    if cursor.fetchone()[0] > 0:
                        raise ValueError(f"Ya existe otro perfil con el nombre '{updates['profile_name']}'")
                
                # Si se marca como default, quitar default de otros
                if updates.get('is_default', False):
                    cursor.execute("""
                        UPDATE camera_stream_profiles
                        SET is_default = 0
                        WHERE camera_id = ? AND stream_type = ? AND profile_id != ?
                    """, (camera_id, stream_type, profile_id))
                
                # Construir query de actualización
                set_clauses = []
                params = []
                for field, value in updates.items():
                    if field in ['profile_name', 'resolution', 'framerate', 'bitrate', 
                               'encoding', 'quality', 'gop_interval', 'is_default']:
                        set_clauses.append(f"{field} = ?")
                        params.append(value)
                
                if not set_clauses:
                    return True  # Nada que actualizar
                
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                params.extend([camera_id, profile_id])
                
                query = f"""
                    UPDATE camera_stream_profiles
                    SET {', '.join(set_clauses)}
                    WHERE camera_id = ? AND profile_id = ?
                """
                
                cursor.execute(query, params)
                self._db_connection.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self._db_connection.rollback()
            self.logger.error(f"Error actualizando perfil {profile_id}: {e}")
            raise
    
    async def delete_stream_profile(self, camera_id: str, profile_id: int) -> bool:
        """
        Elimina un perfil de streaming.
        
        Args:
            camera_id: ID de la cámara
            profile_id: ID del perfil
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            ValueError: Si no se puede eliminar (ej: único perfil activo)
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                
                # Verificar que el perfil existe y obtener info
                cursor.execute("""
                    SELECT stream_type, is_default, is_active
                    FROM camera_stream_profiles
                    WHERE camera_id = ? AND profile_id = ?
                """, (camera_id, profile_id))
                
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Perfil {profile_id} no encontrado")
                
                stream_type, is_default, is_active = result
                
                # Verificar si es el único perfil activo
                if is_active:
                    cursor.execute("""
                        SELECT COUNT(*) FROM camera_stream_profiles
                        WHERE camera_id = ? AND is_active = 1
                    """, (camera_id,))
                    
                    active_count = cursor.fetchone()[0]
                    if active_count == 1:
                        raise ValueError(
                            "No se puede eliminar el único perfil activo. "
                            "Desactive el perfil o agregue otro antes de eliminarlo."
                        )
                    
                    self.logger.debug(
                        f"Verificado: hay {active_count} perfiles activos, se puede eliminar"
                    )
                
                # Eliminar el perfil
                cursor.execute("""
                    DELETE FROM camera_stream_profiles
                    WHERE camera_id = ? AND profile_id = ?
                """, (camera_id, profile_id))
                
                # Si era default, asignar otro como default
                if is_default:
                    cursor.execute("""
                        UPDATE camera_stream_profiles
                        SET is_default = 1
                        WHERE camera_id = ? AND stream_type = ? AND is_active = 1
                        AND profile_id = (
                            SELECT profile_id FROM camera_stream_profiles
                            WHERE camera_id = ? AND stream_type = ? AND is_active = 1
                            ORDER BY created_at ASC
                            LIMIT 1
                        )
                    """, (camera_id, stream_type, camera_id, stream_type))
                
                self._db_connection.commit()
                return True
                
        except Exception as e:
            self._db_connection.rollback()
            self.logger.error(f"Error eliminando perfil {profile_id}: {e}")
            raise
    
    async def clear_default_profiles(self, camera_id: str, stream_type: str) -> bool:
        """
        Quita el flag de default de todos los perfiles de un tipo específico.
        
        Args:
            camera_id: ID de la cámara
            stream_type: Tipo de stream
            
        Returns:
            True si se actualizó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    UPDATE camera_stream_profiles
                    SET is_default = 0
                    WHERE camera_id = ? AND stream_type = ?
                """, (camera_id, stream_type))
                
                self._db_connection.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error limpiando perfiles default: {e}")
            return False
    
    async def set_stream_profile_as_default(self, camera_id: str, profile_id: int) -> bool:
        """
        Establece un perfil como predeterminado.
        
        Args:
            camera_id: ID de la cámara
            profile_id: ID del perfil
            
        Returns:
            True si se estableció correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                # Obtener el tipo de stream del perfil
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT stream_type, is_active
                    FROM camera_stream_profiles
                    WHERE camera_id = ? AND profile_id = ?
                """, (camera_id, profile_id))
                
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Perfil {profile_id} no encontrado")
                
                stream_type, is_active = result
                
                if not is_active:
                    raise ValueError("No se puede establecer como default un perfil inactivo")
                
                # Quitar default de todos los perfiles del mismo tipo
                cursor.execute("""
                    UPDATE camera_stream_profiles
                    SET is_default = 0
                    WHERE camera_id = ? AND stream_type = ?
                """, (camera_id, stream_type))
                
                # Establecer el nuevo como default
                cursor.execute("""
                    UPDATE camera_stream_profiles
                    SET is_default = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE camera_id = ? AND profile_id = ?
                """, (camera_id, profile_id))
                
                self._db_connection.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error estableciendo perfil default: {e}")
            raise
    
    # === Métodos de Gestión de Protocolos ===
    
    async def get_camera_protocols(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los protocolos configurados de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Lista de protocolos con todos los campos
        """
        if not self._db_connection:
            return []
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    SELECT 
                        p.protocol_id,
                        p.protocol_type,
                        p.port,
                        p.is_enabled,
                        p.is_primary,
                        p.is_verified,
                        p.version,
                        p.path,
                        p.last_tested,
                        p.last_error,
                        p.response_time_ms,
                        p.created_at,
                        p.updated_at
                    FROM camera_protocols p
                    WHERE p.camera_id = ?
                    ORDER BY p.is_primary DESC, p.protocol_type
                """, (camera_id,))
                
                protocols = []
                for row in cursor.fetchall():
                    # Obtener capacidades si existen
                    cursor.execute("""
                        SELECT capability_name, capability_value
                        FROM protocol_capabilities
                        WHERE protocol_id = ?
                    """, (row[0],))
                    
                    capabilities = {}
                    for cap in cursor.fetchall():
                        capabilities[cap[0]] = cap[1]
                    
                    protocols.append({
                        'protocol_id': row[0],
                        'protocol_type': row[1],
                        'port': row[2],
                        'is_enabled': bool(row[3]),
                        'is_primary': bool(row[4]),
                        'is_verified': bool(row[5]),
                        'version': row[6],
                        'path': row[7],
                        'last_tested': row[8],
                        'last_error': row[9],
                        'response_time_ms': row[10],
                        'created_at': row[11],
                        'updated_at': row[12],
                        'status': self._determine_protocol_status(row),
                        'capabilities': capabilities if capabilities else None
                    })
                
                return protocols
                
        except Exception as e:
            self.logger.error(f"Error obteniendo protocolos de {camera_id}: {e}")
            return []
    
    def _determine_protocol_status(self, row) -> str:
        """
        Determina el estado del protocolo basado en sus campos.
        
        Args:
            row: Tupla con datos del protocolo (is_enabled en pos 3, 
                 is_verified en pos 5, last_error en pos 9)
                 
        Returns:
            Estado del protocolo: 'disabled', 'active', 'failed' o 'unknown'
        """
        is_enabled, is_verified, last_error = row[3], row[5], row[9]
        
        if not is_enabled:
            return 'disabled'
        elif is_verified and not last_error:
            return 'active'
        elif last_error:
            return 'failed'
        else:
            return 'unknown'
    
    async def get_protocol_by_type(self, camera_id: str, protocol_type: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un protocolo específico por tipo.
        
        Args:
            camera_id: ID de la cámara
            protocol_type: Tipo de protocolo
            
        Returns:
            Protocolo o None si no existe
        """
        if not self._db_connection:
            return None
            
        try:
            protocols = await self.get_camera_protocols(camera_id)
            return next((p for p in protocols if p['protocol_type'] == protocol_type), None)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo protocolo {protocol_type}: {e}")
            return None
    
    async def add_camera_protocol(self, camera_id: str, protocol_data: Dict[str, Any]) -> int:
        """
        Agrega un nuevo protocolo a una cámara.
        
        Solo puede existir un protocolo de cada tipo por cámara.
        Si se marca como primario, automáticamente quita el flag 
        primario de otros protocolos.
        
        Args:
            camera_id: ID de la cámara (UUID)
            protocol_data: Datos del protocolo con campos:
                - protocol_type (str): Tipo de protocolo (onvif, rtsp, etc)
                - port (int): Puerto del protocolo
                - is_enabled (bool, opcional): Si está habilitado, default True
                - is_primary (bool, opcional): Si es primario, default False
                - is_verified (bool, opcional): Si está verificado, default False
                - version (str, opcional): Versión del protocolo
                - path (str, opcional): Path específico
            
        Returns:
            ID del protocolo creado
            
        Raises:
            ValueError: Si ya existe el protocolo o falta conexión BD
        """
        if not self._db_connection:
            raise ValueError("Sin conexión a base de datos")
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                
                # Verificar que no exista
                cursor.execute("""
                    SELECT COUNT(*) FROM camera_protocols
                    WHERE camera_id = ? AND protocol_type = ?
                """, (camera_id, protocol_data['protocol_type']))
                
                if cursor.fetchone()[0] > 0:
                    raise ValueError(f"Ya existe el protocolo {protocol_data['protocol_type']}")
                
                # Si es primary, quitar primary de otros
                if protocol_data.get('is_primary', False):
                    cursor.execute("""
                        UPDATE camera_protocols
                        SET is_primary = 0
                        WHERE camera_id = ?
                    """, (camera_id,))
                
                # Insertar protocolo
                cursor.execute("""
                    INSERT INTO camera_protocols (
                        camera_id, protocol_type, port, is_enabled,
                        is_primary, is_verified, version, path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    camera_id,
                    protocol_data['protocol_type'],
                    protocol_data['port'],
                    1 if protocol_data.get('is_enabled', True) else 0,
                    1 if protocol_data.get('is_primary', False) else 0,
                    1 if protocol_data.get('is_verified', False) else 0,
                    protocol_data.get('version'),
                    protocol_data.get('path')
                ))
                
                protocol_id = cursor.lastrowid
                self._db_connection.commit()
                
                self.logger.info(f"Protocolo {protocol_data['protocol_type']} agregado para {camera_id}")
                return protocol_id
                
        except Exception as e:
            self._db_connection.rollback()
            self.logger.error(f"Error agregando protocolo: {e}")
            raise
    
    async def update_protocol_config(self, camera_id: str, protocol_id: int, updates: Dict[str, Any]) -> bool:
        """
        Actualiza la configuración de un protocolo.
        
        Args:
            camera_id: ID de la cámara
            protocol_id: ID del protocolo
            updates: Campos a actualizar
            
        Returns:
            True si se actualizó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                # Si se marca como primary, quitar primary de otros
                if updates.get('is_primary', False):
                    cursor = self._db_connection.cursor()
                    cursor.execute("""
                        UPDATE camera_protocols
                        SET is_primary = 0
                        WHERE camera_id = ? AND protocol_id != ?
                    """, (camera_id, protocol_id))
                
                # Construir query de actualización
                set_clauses = []
                params = []
                for field, value in updates.items():
                    if field in ['port', 'is_enabled', 'is_primary', 'version', 'path']:
                        set_clauses.append(f"{field} = ?")
                        if field.startswith('is_'):
                            params.append(1 if value else 0)
                        else:
                            params.append(value)
                
                if not set_clauses:
                    return True
                
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                params.extend([camera_id, protocol_id])
                
                query = f"""
                    UPDATE camera_protocols
                    SET {', '.join(set_clauses)}
                    WHERE camera_id = ? AND protocol_id = ?
                """
                
                cursor.execute(query, params)
                self._db_connection.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self._db_connection.rollback()
            self.logger.error(f"Error actualizando protocolo: {e}")
            return False
    
    async def clear_primary_protocols(self, camera_id: str) -> bool:
        """
        Quita el flag de primary de todos los protocolos.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se actualizó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    UPDATE camera_protocols
                    SET is_primary = 0
                    WHERE camera_id = ?
                """, (camera_id,))
                
                self._db_connection.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error limpiando protocolos primary: {e}")
            return False
    
    async def update_protocol_test_result(self, camera_id: str, protocol_id: int,
                                        success: bool, response_time_ms: int = None,
                                        version: str = None, error: str = None) -> bool:
        """
        Actualiza el resultado de una prueba de protocolo.
        
        Args:
            camera_id: ID de la cámara
            protocol_id: ID del protocolo
            success: Si la prueba fue exitosa
            response_time_ms: Tiempo de respuesta
            version: Versión detectada
            error: Mensaje de error si falló
            
        Returns:
            True si se actualizó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    UPDATE camera_protocols
                    SET last_tested = CURRENT_TIMESTAMP,
                        is_verified = ?,
                        response_time_ms = ?,
                        version = ?,
                        last_error = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE camera_id = ? AND protocol_id = ?
                """, (
                    1 if success else 0,
                    response_time_ms,
                    version,
                    error,
                    camera_id,
                    protocol_id
                ))
                
                self._db_connection.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error actualizando resultado de test: {e}")
            return False
    
    async def update_camera_discovery_status(self, camera_id: str, status: str, message: str) -> bool:
        """
        Actualiza el estado del discovery de protocolos.
        
        Args:
            camera_id: ID de la cámara
            status: Estado del discovery (discovering, completed, failed)
            message: Mensaje descriptivo
            
        Returns:
            True si se actualizó correctamente
        """
        if not self._db_connection:
            return False
            
        try:
            with self._db_lock:
                cursor = self._db_connection.cursor()
                cursor.execute("""
                    UPDATE cameras
                    SET discovery_status = ?,
                        discovery_message = ?,
                        discovery_timestamp = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE camera_id = ?
                """, (status, message, camera_id))
                
                self._db_connection.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado de discovery: {e}")
            return False
    
    # === Métodos de Solo Lectura (Fase 4) ===
    
    async def get_camera_capabilities_detail(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene las capacidades detalladas de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Dict con capacidades o None si no existen
        """
        query = """
            SELECT 
                c.camera_id,
                cap.last_discovered,
                cap.discovery_method,
                cap.capabilities_json
            FROM cameras c
            LEFT JOIN camera_capabilities cap ON c.id = cap.camera_id
            WHERE c.camera_id = ?
        """
        
        result = await self.execute_query(query, (camera_id,), fetch_one=True)
        
        if not result or not result['capabilities_json']:
            return None
        
        import json
        capabilities = json.loads(result['capabilities_json'])
        
        # Estructurar por categorías
        return {
            'camera_id': camera_id,
            'last_updated': result['last_discovered'],
            'discovery_method': result['discovery_method'] or 'manual',
            'categories': self._categorize_capabilities(capabilities),
            'raw_capabilities': capabilities
        }
    
    def _categorize_capabilities(self, capabilities: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Categoriza las capacidades en grupos."""
        categories = {
            'video': [],
            'audio': [],
            'ptz': [],
            'analytics': [],
            'events': [],
            'network': [],
            'storage': []
        }
        
        # Mapear capacidades a categorías (ejemplo básico)
        if capabilities.get('has_video'):
            categories['video'].append({
                'name': 'video_streaming',
                'supported': True,
                'details': capabilities.get('video_details')
            })
        
        if capabilities.get('has_audio'):
            categories['audio'].append({
                'name': 'audio_streaming',
                'supported': True,
                'details': capabilities.get('audio_details')
            })
        
        if capabilities.get('has_ptz'):
            categories['ptz'].append({
                'name': 'pan_tilt_zoom',
                'supported': True,
                'details': capabilities.get('ptz_details')
            })
        
        return categories
    
    async def get_camera_events(
        self,
        camera_id: str,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Obtiene eventos paginados de una cámara.
        
        Args:
            camera_id: ID de la cámara
            event_type: Tipo de evento
            severity: Severidad
            start_date: Fecha inicial
            end_date: Fecha final
            page: Página
            page_size: Tamaño de página
            
        Returns:
            Dict con eventos paginados
        """
        # Construir query base
        query_count = """
            SELECT COUNT(*) as total
            FROM camera_events ce
            JOIN cameras c ON ce.camera_id = c.id
            WHERE c.camera_id = ?
        """
        
        query = """
            SELECT 
                ce.id as event_id,
                ce.event_type,
                ce.severity,
                ce.timestamp,
                ce.message,
                ce.details_json,
                ce.user,
                ce.ip_address
            FROM camera_events ce
            JOIN cameras c ON ce.camera_id = c.id
            WHERE c.camera_id = ?
        """
        
        params = [camera_id]
        
        # Aplicar filtros
        if event_type:
            query_count += " AND ce.event_type = ?"
            query += " AND ce.event_type = ?"
            params.append(event_type)
        
        if severity:
            query_count += " AND ce.severity = ?"
            query += " AND ce.severity = ?"
            params.append(severity)
        
        if start_date:
            query_count += " AND ce.timestamp >= ?"
            query += " AND ce.timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query_count += " AND ce.timestamp <= ?"
            query += " AND ce.timestamp <= ?"
            params.append(end_date)
        
        # Obtener total
        count_result = await self.execute_query(query_count, params, fetch_one=True)
        total = count_result['total'] if count_result else 0
        
        # Aplicar paginación
        offset = (page - 1) * page_size
        query += " ORDER BY ce.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        # Obtener eventos
        results = await self.execute_query(query, params, fetch_all=True)
        
        events = []
        for row in results:
            event = {
                'event_id': row['event_id'],
                'event_type': row['event_type'],
                'severity': row['severity'],
                'timestamp': row['timestamp'],
                'message': row['message'],
                'user': row['user'],
                'ip_address': row['ip_address']
            }
            
            if row['details_json']:
                import json
                event['details'] = json.loads(row['details_json'])
            else:
                event['details'] = None
            
            events.append(event)
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'events': events
        }
    
    async def get_camera_logs(
        self,
        camera_id: str,
        level: Optional[str] = None,
        component: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Obtiene logs paginados de una cámara.
        
        Args:
            camera_id: ID de la cámara
            level: Nivel de log
            component: Componente
            start_date: Fecha inicial
            end_date: Fecha final
            page: Página
            page_size: Tamaño de página
            
        Returns:
            Dict con logs paginados
        """
        # Construir query base
        query_count = """
            SELECT COUNT(*) as total
            FROM camera_logs cl
            JOIN cameras c ON cl.camera_id = c.id
            WHERE c.camera_id = ?
        """
        
        query = """
            SELECT 
                cl.id as log_id,
                cl.timestamp,
                cl.level,
                cl.component,
                cl.message,
                cl.context_json,
                cl.duration_ms
            FROM camera_logs cl
            JOIN cameras c ON cl.camera_id = c.id
            WHERE c.camera_id = ?
        """
        
        params = [camera_id]
        
        # Aplicar filtros
        if level:
            query_count += " AND cl.level = ?"
            query += " AND cl.level = ?"
            params.append(level)
        
        if component:
            query_count += " AND cl.component = ?"
            query += " AND cl.component = ?"
            params.append(component)
        
        if start_date:
            query_count += " AND cl.timestamp >= ?"
            query += " AND cl.timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query_count += " AND cl.timestamp <= ?"
            query += " AND cl.timestamp <= ?"
            params.append(end_date)
        
        # Obtener total
        count_result = await self.execute_query(query_count, params, fetch_one=True)
        total = count_result['total'] if count_result else 0
        
        # Aplicar paginación
        offset = (page - 1) * page_size
        query += " ORDER BY cl.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        # Obtener logs
        results = await self.execute_query(query, params, fetch_all=True)
        
        logs = []
        for row in results:
            log_entry = {
                'log_id': row['log_id'],
                'timestamp': row['timestamp'],
                'level': row['level'],
                'component': row['component'],
                'message': row['message'],
                'duration_ms': row['duration_ms']
            }
            
            if row['context_json']:
                import json
                log_entry['context'] = json.loads(row['context_json'])
            else:
                log_entry['context'] = None
            
            logs.append(log_entry)
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'logs': logs
        }
    
    async def get_camera_snapshots(
        self,
        camera_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        trigger: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Obtiene snapshots paginados de una cámara.
        
        Args:
            camera_id: ID de la cámara
            start_date: Fecha inicial
            end_date: Fecha final
            trigger: Tipo de trigger
            page: Página
            page_size: Tamaño de página
            
        Returns:
            Dict con snapshots paginados
        """
        # Construir query base
        query_count = """
            SELECT COUNT(*) as total
            FROM camera_snapshots cs
            JOIN cameras c ON cs.camera_id = c.id
            WHERE c.camera_id = ?
        """
        
        query = """
            SELECT 
                cs.id as snapshot_id,
                cs.filename,
                cs.timestamp,
                cs.file_size,
                cs.width,
                cs.height,
                cs.format,
                cs.stream_profile,
                cs.trigger_type as trigger,
                cs.storage_path,
                cs.thumbnail_path
            FROM camera_snapshots cs
            JOIN cameras c ON cs.camera_id = c.id
            WHERE c.camera_id = ?
        """
        
        params = [camera_id]
        
        # Aplicar filtros
        if trigger:
            query_count += " AND cs.trigger_type = ?"
            query += " AND cs.trigger_type = ?"
            params.append(trigger)
        
        if start_date:
            query_count += " AND cs.timestamp >= ?"
            query += " AND cs.timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query_count += " AND cs.timestamp <= ?"
            query += " AND cs.timestamp <= ?"
            params.append(end_date)
        
        # Obtener total
        count_result = await self.execute_query(query_count, params, fetch_one=True)
        total = count_result['total'] if count_result else 0
        
        # Aplicar paginación
        offset = (page - 1) * page_size
        query += " ORDER BY cs.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        # Obtener snapshots
        results = await self.execute_query(query, params, fetch_all=True)
        
        snapshots = []
        for row in results:
            snapshot = {
                'snapshot_id': row['snapshot_id'],
                'filename': row['filename'],
                'timestamp': row['timestamp'],
                'file_size': row['file_size'],
                'width': row['width'],
                'height': row['height'],
                'format': row['format'],
                'stream_profile': row['stream_profile'],
                'trigger': row['trigger'],
                'storage_path': row['storage_path'],
                'thumbnail_path': row['thumbnail_path']
            }
            snapshots.append(snapshot)
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'snapshots': snapshots
        }
    
    async def _close_database(self) -> None:
        """Cierra la conexión a la base de datos."""
        if self._db_connection:
            with self._db_lock:
                self._db_connection.close()
                self._db_connection = None
    
    async def cleanup(self) -> None:
        """
        Limpia y cierra todos los recursos del servicio.
        """
        self.logger.info("Limpiando DataService...")
        
        # Detener tareas de fondo
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        
        # Esperar a que terminen
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Cerrar base de datos
        await self._close_database()
        
        # Limpiar cache
        with self._cache_lock:
            self._camera_cache.clear()
            self._scan_cache.clear()
            self._cache_timestamps.clear()
        
        self.logger.info("DataService limpiado correctamente")


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