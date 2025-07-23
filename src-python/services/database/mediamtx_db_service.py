"""
Servicio extendido de base de datos para integración completa con MediaMTX.

Extiende PublishingDatabaseService para trabajar con todas las tablas
del esquema MediaMTX definido en mediamtx_tables.py.
"""

import sqlite3
import json

from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
import asyncio
from pathlib import Path

from services.database.publishing_db_service import PublishingDatabaseService
from api.schemas.requests.mediamtx_requests import (
    PublicationStatus, TerminationReason, ViewerProtocol, PathSourceType,
    GetMetricsRequest, GetHistoryRequest, GetViewersRequest
)
from utils.exceptions import ServiceError
from services.logging_service import get_secure_logger


logger = get_secure_logger("services.database.mediamtx_db_service")


class MediaMTXDatabaseService(PublishingDatabaseService):
    """
    Servicio completo de base de datos para MediaMTX.
    
    Extiende el servicio base para incluir:
    - Gestión de métricas en tiempo real
    - Historial de publicaciones
    - Tracking de viewers
    - Configuración de paths MediaMTX
    - Health checks y alertas
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa el servicio extendido.
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        if db_path is None:
            # Usar ruta absoluta basada en src-python
            db_path = str(Path(__file__).parent.parent.parent / "data" / "camera_data.db")
        super().__init__(db_path)
        self.logger = logger
        
    # === Métodos de Métricas ===
    
    async def get_publication_metrics(
        self,
        camera_id: str,
        request: GetMetricsRequest
    ) -> Dict[str, Any]:
        """
        Obtiene métricas de publicación para una cámara.
        
        Args:
            camera_id: ID de la cámara
            request: Parámetros de la consulta
            
        Returns:
            Dict con métricas y resumen estadístico
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Determinar rango de tiempo
                end_time = datetime.utcnow()
                start_time = self._calculate_start_time(request.time_range, request.start_time, end_time)
                
                # Obtener publication_id activa
                cursor.execute("""
                    SELECT publication_id FROM camera_publications
                    WHERE camera_id = ? AND is_active = 1
                    LIMIT 1
                """, (camera_id,))
                
                pub_row = cursor.fetchone()
                if not pub_row:
                    return {
                        'camera_id': camera_id,
                        'publication_id': None,
                        'time_range': request.time_range.value,
                        'data_points': [],
                        'summary': self._empty_metrics_summary()
                    }
                
                publication_id = pub_row['publication_id']
                
                # Consultar métricas
                query = """
                    SELECT 
                        metric_time as timestamp,
                        fps, bitrate_kbps, frames, dropped_frames,
                        quality_score, viewer_count, cpu_usage_percent,
                        memory_usage_mb
                    FROM publication_metrics
                    WHERE publication_id = ? 
                    AND metric_time BETWEEN ? AND ?
                    ORDER BY metric_time ASC
                """
                
                cursor.execute(query, (publication_id, start_time, end_time))
                
                data_points = []
                for row in cursor.fetchall():
                    data_points.append(dict(row))
                
                # Calcular resumen
                summary = self._calculate_metrics_summary(data_points)
                
                # Obtener estadísticas de viewers si se solicita
                viewer_stats = None
                if request.include_viewers:
                    viewer_stats = self._get_viewer_stats(conn, publication_id, start_time, end_time)
                
                return {
                    'camera_id': camera_id,
                    'publication_id': publication_id,
                    'time_range': request.time_range.value,
                    'data_points': data_points,
                    'summary': summary,
                    'viewer_stats': viewer_stats
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    async def get_latest_publication_metric(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la métrica más reciente de una cámara.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            Dict con la métrica más reciente o None si no hay
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener publication_id activa
                cursor.execute("""
                    SELECT publication_id FROM camera_publications
                    WHERE camera_id = ? AND is_active = 1
                    LIMIT 1
                """, (camera_id,))
                
                pub_row = cursor.fetchone()
                if not pub_row:
                    return None
                
                publication_id = pub_row['publication_id']
                
                # Obtener la métrica más reciente
                cursor.execute("""
                    SELECT 
                        metric_time as timestamp,
                        fps, bitrate_kbps, frames, dropped_frames,
                        quality_score, viewer_count, cpu_usage_percent,
                        memory_usage_mb, size_kb
                    FROM publication_metrics
                    WHERE publication_id = ?
                    ORDER BY metric_time DESC
                    LIMIT 1
                """, (publication_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                return dict(row)
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    async def save_publication_metrics(
        self,
        publication_id: int,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Guarda métricas de una publicación activa.
        
        Args:
            publication_id: ID de la publicación
            metrics: Diccionario con métricas
        """
        def _save():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO publication_metrics (
                        publication_id, metric_time, fps, bitrate_kbps,
                        frames, speed, quality_score, size_kb, time_seconds,
                        dropped_frames, viewer_count, cpu_usage_percent,
                        memory_usage_mb
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    publication_id,
                    datetime.utcnow(),
                    metrics.get('fps'),
                    metrics.get('bitrate_kbps'),
                    metrics.get('frames'),
                    metrics.get('speed'),
                    metrics.get('quality_score'),
                    metrics.get('size_kb'),
                    metrics.get('time_seconds'),
                    metrics.get('dropped_frames', 0),
                    metrics.get('viewer_count', 0),
                    metrics.get('cpu_usage_percent'),
                    metrics.get('memory_usage_mb')
                ))
                
        await asyncio.get_event_loop().run_in_executor(None, _save)
        
    async def get_global_metrics_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen global de métricas del sistema.
        
        Returns:
            Dict con estadísticas globales
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Publicaciones activas
                cursor.execute("""
                    SELECT COUNT(DISTINCT camera_id) as total_cameras
                    FROM camera_publications
                    WHERE status = 'PUBLISHING' AND is_active = 1
                """)
                total_cameras = cursor.fetchone()['total_cameras']
                
                # Viewers activos
                cursor.execute("""
                    SELECT COUNT(*) as total_viewers
                    FROM publication_viewers
                    WHERE end_time IS NULL
                """)
                total_viewers = cursor.fetchone()['total_viewers']
                
                # Métricas agregadas recientes (últimos 5 minutos)
                cursor.execute("""
                    SELECT 
                        AVG(bitrate_kbps) as avg_bitrate,
                        AVG(quality_score) as avg_quality,
                        AVG(cpu_usage_percent) as avg_cpu,
                        AVG(memory_usage_mb) as avg_memory
                    FROM publication_metrics
                    WHERE metric_time > datetime('now', '-5 minutes')
                """)
                
                metrics_row = cursor.fetchone()
                
                # Top cámaras por viewers
                cursor.execute("""
                    SELECT 
                        c.display_name as camera_name,
                        cp.camera_id,
                        COUNT(pv.viewer_id) as viewer_count
                    FROM camera_publications cp
                    JOIN cameras c ON cp.camera_id = c.camera_id
                    LEFT JOIN publication_viewers pv ON cp.publication_id = pv.publication_id
                    WHERE cp.is_active = 1 AND pv.end_time IS NULL
                    GROUP BY cp.camera_id, c.display_name
                    ORDER BY viewer_count DESC
                    LIMIT 5
                """)
                
                top_cameras = []
                for row in cursor.fetchall():
                    top_cameras.append({
                        'camera_id': row['camera_id'],
                        'camera_name': row['camera_name'],
                        'viewer_count': row['viewer_count']
                    })
                
                # Calcular ancho de banda total
                total_bandwidth_mbps = 0
                if metrics_row['avg_bitrate']:
                    total_bandwidth_mbps = (metrics_row['avg_bitrate'] * total_cameras) / 1000
                
                return {
                    'total_cameras_publishing': total_cameras,
                    'total_active_viewers': total_viewers,
                    'total_bandwidth_mbps': round(total_bandwidth_mbps, 2),
                    'avg_quality_score': round(metrics_row['avg_quality'] or 0, 2),
                    'system_cpu_percent': round(metrics_row['avg_cpu'] or 0, 2),
                    'system_memory_percent': round(
                        (metrics_row['avg_memory'] or 0) / 1024 * 100, 2  # Asumiendo 1GB total
                    ),
                    'top_cameras': top_cameras,
                    'alerts_count': 0  # TODO: Implementar sistema de alertas
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    # === Métodos de Historial ===
    
    async def get_publication_history(
        self,
        request: GetHistoryRequest
    ) -> Dict[str, Any]:
        """
        Obtiene historial de publicaciones con filtros.
        
        Args:
            request: Parámetros de búsqueda y paginación
            
        Returns:
            Dict con resultados paginados
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Construir query con filtros
                conditions = []
                params = []
                
                if request.camera_id:
                    conditions.append("ph.camera_id = ?")
                    params.append(request.camera_id)
                    
                if request.server_id:
                    conditions.append("ph.server_id = ?")
                    params.append(request.server_id)
                    
                if request.termination_reason:
                    conditions.append("ph.termination_reason = ?")
                    params.append(request.termination_reason.value)
                    
                if request.start_date:
                    conditions.append("ph.start_time >= ?")
                    params.append(request.start_date)
                    
                if request.end_date:
                    conditions.append("ph.start_time <= ?")
                    params.append(request.end_date)
                    
                if request.min_duration_seconds:
                    conditions.append("ph.duration_seconds >= ?")
                    params.append(request.min_duration_seconds)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Contar total
                count_query = f"""
                    SELECT COUNT(*) as total
                    FROM publication_history ph
                    WHERE {where_clause}
                """
                cursor.execute(count_query, params)
                total = cursor.fetchone()['total']
                
                # Query principal con paginación
                offset = (request.page - 1) * request.page_size
                order_dir = "DESC" if request.order_desc else "ASC"
                
                query = f"""
                    SELECT 
                        ph.*,
                        c.display_name as camera_name,
                        ms.server_name
                    FROM publication_history ph
                    JOIN cameras c ON ph.camera_id = c.camera_id
                    LEFT JOIN mediamtx_servers ms ON ph.server_id = ms.server_id
                    WHERE {where_clause}
                    ORDER BY ph.{request.order_by} {order_dir}
                    LIMIT ? OFFSET ?
                """
                params.extend([request.page_size, offset])
                
                cursor.execute(query, params)
                
                items = []
                for row in cursor.fetchall():
                    items.append({
                        'history_id': row['history_id'],
                        'camera_id': row['camera_id'],
                        'camera_name': row['camera_name'],
                        'server_id': row['server_id'],
                        'server_name': row['server_name'],
                        'session_id': row['session_id'],
                        'publish_path': row['publish_path'],
                        'start_time': row['start_time'],
                        'end_time': row['end_time'],
                        'duration_seconds': row['duration_seconds'],
                        'total_frames': row['total_frames'],
                        'average_fps': row['average_fps'],
                        'average_bitrate_kbps': row['average_bitrate_kbps'],
                        'total_data_mb': row['total_data_mb'],
                        'max_viewers': row['max_viewers'],
                        'error_count': row['error_count'],
                        'termination_reason': row['termination_reason'],
                        'last_error': row['last_error']
                    })
                
                return {
                    'total': total,
                    'page': request.page,
                    'page_size': request.page_size,
                    'items': items,
                    'filters_applied': {
                        'camera_id': request.camera_id,
                        'server_id': request.server_id,
                        'termination_reason': request.termination_reason,
                        'date_range': {
                            'start': request.start_date,
                            'end': request.end_date
                        }
                    }
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    async def get_session_detail(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el detalle completo de una sesión de publicación.
        
        Args:
            session_id: ID único de la sesión
            
        Returns:
            Dict con información detallada o None si no existe
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Información de la sesión
                cursor.execute("""
                    SELECT 
                        ph.*,
                        c.display_name as camera_name,
                        ms.server_name,
                        cp.ffmpeg_command
                    FROM publication_history ph
                    JOIN cameras c ON ph.camera_id = c.camera_id
                    LEFT JOIN mediamtx_servers ms ON ph.server_id = ms.server_id
                    LEFT JOIN camera_publications cp ON ph.session_id = cp.session_id
                    WHERE ph.session_id = ?
                """, (session_id,))
                
                session_row = cursor.fetchone()
                if not session_row:
                    return None
                
                # Timeline de errores
                error_timeline = []
                if session_row['error_count'] > 0:
                    # Buscar en logs o métricas donde se registraron errores
                    cursor.execute("""
                        SELECT 
                            created_at as timestamp,
                            'metric_anomaly' as error_type,
                            'Low FPS detected' as message
                        FROM publication_metrics
                        WHERE publication_id IN (
                            SELECT publication_id FROM camera_publications 
                            WHERE session_id = ?
                        ) AND fps < 5
                        ORDER BY created_at
                        LIMIT 10
                    """, (session_id,))
                    
                    for row in cursor.fetchall():
                        error_timeline.append(dict(row))
                
                # Resumen de viewers
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT viewer_ip) as unique_viewers,
                        COUNT(*) as total_sessions,
                        AVG(duration_seconds) as avg_duration,
                        SUM(bytes_received) as total_bytes,
                        GROUP_CONCAT(DISTINCT protocol_used) as protocols
                    FROM publication_viewers
                    WHERE publication_id IN (
                        SELECT publication_id FROM camera_publications 
                        WHERE session_id = ?
                    )
                """, (session_id,))
                
                viewer_row = cursor.fetchone()
                viewer_summary = {
                    'unique_viewers': viewer_row['unique_viewers'] or 0,
                    'total_sessions': viewer_row['total_sessions'] or 0,
                    'avg_duration_seconds': round(viewer_row['avg_duration'] or 0, 2),
                    'total_data_gb': round((viewer_row['total_bytes'] or 0) / 1024 / 1024 / 1024, 2),
                    'protocols_used': viewer_row['protocols'].split(',') if viewer_row['protocols'] else []
                }
                
                # Construir respuesta
                return {
                    'session_info': dict(session_row),
                    'metrics_summary': self._calculate_session_metrics_summary(conn, session_id),
                    'error_timeline': error_timeline,
                    'viewer_summary': viewer_summary,
                    'ffmpeg_command': session_row['ffmpeg_command'],
                    'metadata': json.loads(session_row['metadata']) if session_row['metadata'] else {}
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    async def cleanup_old_history(
        self,
        older_than_days: int,
        keep_errors: bool = True,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Limpia registros antiguos del historial con opciones avanzadas.
        
        Este método elimina de forma segura registros antiguos del historial
        junto con sus datos relacionados (métricas, viewers). Por defecto
        opera en modo dry_run para previsualizar cambios.
        
        Args:
            older_than_days: Eliminar registros más antiguos que N días
            keep_errors: Si mantener registros con errores (recomendado)
            dry_run: Si solo simular sin eliminar (default True)
            
        Returns:
            Dict con información detallada:
            - records_affected: número de registros a eliminar
            - space_freed_mb: espacio estimado a liberar
            - oldest_record_date: fecha del registro más antiguo
            - dry_run: si fue simulación
            - details: desglose por razón de terminación y cámara
        """
        def _cleanup():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
                
                # Construir condiciones
                conditions = ["ph.start_time < ?"]
                params = [cutoff_date]
                
                if keep_errors:
                    conditions.append("(ph.error_count = 0 OR ph.error_count IS NULL)")
                
                # También mantener sesiones largas (>24 horas) como casos especiales
                conditions.append("ph.duration_seconds < 86400")  # 24 horas
                
                where_clause = " AND ".join(conditions)
                
                # Contar registros a eliminar con información detallada
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_records,
                        SUM(ph.total_data_mb) as total_data_mb,
                        MIN(ph.start_time) as oldest_date,
                        AVG(ph.duration_seconds) as avg_duration
                    FROM publication_history ph
                    WHERE {where_clause}
                """, params)
                
                stats = cursor.fetchone()
                
                # Desglose por razón de terminación
                cursor.execute(f"""
                    SELECT 
                        ph.termination_reason,
                        COUNT(*) as count,
                        SUM(ph.total_data_mb) as data_mb
                    FROM publication_history ph
                    WHERE {where_clause}
                    GROUP BY ph.termination_reason
                """, params)
                
                details = {
                    'by_termination_reason': {},
                    'by_camera': {}
                }
                
                for row in cursor.fetchall():
                    reason = row['termination_reason'] or 'unknown'
                    details['by_termination_reason'][reason] = {
                        'count': row['count'],
                        'data_mb': round(row['data_mb'] or 0, 2)
                    }
                
                # Desglose por cámara (top 10)
                cursor.execute(f"""
                    SELECT 
                        ph.camera_id,
                        c.name as camera_name,
                        COUNT(*) as count,
                        SUM(ph.total_data_mb) as data_mb
                    FROM publication_history ph
                    LEFT JOIN cameras c ON ph.camera_id = c.camera_id
                    WHERE {where_clause}
                    GROUP BY ph.camera_id
                    ORDER BY count DESC
                    LIMIT 10
                """, params)
                
                for row in cursor.fetchall():
                    details['by_camera'][row['camera_id']] = {
                        'name': row['camera_name'] or row['camera_id'],
                        'count': row['count'],
                        'data_mb': round(row['data_mb'] or 0, 2)
                    }
                
                # Calcular espacio total incluyendo métricas y viewers
                if stats['total_records'] > 0:
                    # Estimar espacio de métricas (aprox 100 bytes por registro)
                    cursor.execute(f"""
                        SELECT COUNT(*) * 0.0001 as metrics_mb
                        FROM publication_metrics pm
                        WHERE pm.publication_id IN (
                            SELECT cp.publication_id 
                            FROM camera_publications cp
                            JOIN publication_history ph ON cp.session_id = ph.session_id
                            WHERE {where_clause}
                        )
                    """, params)
                    
                    metrics_space = cursor.fetchone()
                    total_space_mb = (stats['total_data_mb'] or 0) + (metrics_space['metrics_mb'] or 0)
                else:
                    total_space_mb = 0
                
                # Ejecutar eliminación si no es dry run
                if not dry_run and stats['total_records'] > 0:
                    conn.execute("BEGIN TRANSACTION")
                    try:
                        # Obtener publication_ids a eliminar
                        cursor.execute(f"""
                            SELECT cp.publication_id
                            FROM camera_publications cp
                            JOIN publication_history ph ON cp.session_id = ph.session_id
                            WHERE {where_clause}
                        """, params)
                        
                        pub_ids = [row['publication_id'] for row in cursor.fetchall()]
                        
                        if pub_ids:
                            # Eliminar métricas
                            placeholders = ','.join('?' * len(pub_ids))
                            cursor.execute(f"""
                                DELETE FROM publication_metrics
                                WHERE publication_id IN ({placeholders})
                            """, pub_ids)
                            
                            # Eliminar viewers
                            cursor.execute(f"""
                                DELETE FROM publication_viewers
                                WHERE publication_id IN ({placeholders})
                            """, pub_ids)
                        
                        # Eliminar historial
                        cursor.execute(f"""
                            DELETE FROM publication_history ph
                            WHERE {where_clause}
                        """, params)
                        
                        # Limpiar camera_publications huérfanas
                        cursor.execute("""
                            DELETE FROM camera_publications
                            WHERE is_active = 0 
                            AND session_id NOT IN (
                                SELECT session_id FROM publication_history
                            )
                        """)
                        
                        conn.commit()
                        self.logger.info(
                            f"Limpieza completada: {stats['total_records']} registros eliminados, "
                            f"{round(total_space_mb, 2)} MB liberados"
                        )
                        
                    except Exception as e:
                        conn.rollback()
                        self.logger.error(f"Error durante limpieza: {e}")
                        raise
                
                return {
                    'records_affected': stats['total_records'] or 0,
                    'space_freed_mb': round(total_space_mb, 2),
                    'oldest_record_date': stats['oldest_date'],
                    'dry_run': dry_run,
                    'details': details
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _cleanup)
    
    # === Métodos de Historial ===
    
    async def get_publication_history(
        self,
        request: GetHistoryRequest
    ) -> Dict[str, Any]:
        """
        Obtiene historial de publicaciones con filtros y paginación.
        
        Args:
            request: Parámetros de búsqueda con filtros
            
        Returns:
            Dict con:
            - total: número total de registros
            - page: página actual
            - page_size: tamaño de página
            - items: lista de PublicationHistoryItem
            - filters_applied: filtros aplicados
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Construir condiciones WHERE
                conditions = []
                params = []
                
                if request.camera_id:
                    conditions.append("ph.camera_id = ?")
                    params.append(request.camera_id)
                    
                if request.server_id is not None:
                    conditions.append("ph.server_id = ?")
                    params.append(request.server_id)
                    
                if request.termination_reason:
                    conditions.append("ph.termination_reason = ?")
                    params.append(request.termination_reason.value)
                    
                if request.start_date:
                    conditions.append("ph.start_time >= ?")
                    params.append(request.start_date)
                    
                if request.end_date:
                    conditions.append("ph.start_time <= ?")
                    params.append(request.end_date)
                    
                if request.min_duration_seconds is not None:
                    conditions.append("ph.duration_seconds >= ?")
                    params.append(request.min_duration_seconds)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Contar total de registros
                count_query = f"""
                    SELECT COUNT(*) as total
                    FROM publication_history ph
                    WHERE {where_clause}
                """
                cursor.execute(count_query, params)
                total = cursor.fetchone()['total']
                
                # Query principal con paginación
                offset = (request.page - 1) * request.page_size
                order_direction = "DESC" if request.order_desc else "ASC"
                
                query = f"""
                    SELECT 
                        ph.history_id,
                        ph.camera_id,
                        ph.server_id,
                        ph.session_id,
                        ph.publish_path,
                        ph.start_time,
                        ph.end_time,
                        ph.duration_seconds,
                        ph.total_frames,
                        ph.average_fps,
                        ph.average_bitrate_kbps,
                        ph.total_data_mb,
                        ph.max_viewers,
                        ph.error_count,
                        ph.termination_reason,
                        ph.last_error,
                        ph.metadata,
                        c.name as camera_name,
                        ms.server_name
                    FROM publication_history ph
                    LEFT JOIN cameras c ON ph.camera_id = c.camera_id
                    LEFT JOIN mediamtx_servers ms ON ph.server_id = ms.server_id
                    WHERE {where_clause}
                    ORDER BY ph.{request.order_by} {order_direction}
                    LIMIT ? OFFSET ?
                """
                
                cursor.execute(query, params + [request.page_size, offset])
                
                items = []
                for row in cursor.fetchall():
                    item = dict(row)
                    # Parsear metadata JSON si existe
                    if item.get('metadata'):
                        try:
                            item['metadata'] = json.loads(item['metadata'])
                        except:
                            item['metadata'] = None
                    items.append(item)
                
                # Construir respuesta
                return {
                    'total': total,
                    'page': request.page,
                    'page_size': request.page_size,
                    'items': items,
                    'filters_applied': {
                        'camera_id': request.camera_id,
                        'server_id': request.server_id,
                        'termination_reason': request.termination_reason.value if request.termination_reason else None,
                        'start_date': request.start_date.isoformat() if request.start_date else None,
                        'end_date': request.end_date.isoformat() if request.end_date else None,
                        'min_duration_seconds': request.min_duration_seconds
                    }
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    async def get_session_detail(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene el detalle completo de una sesión de publicación.
        
        Incluye:
        - Información básica de la sesión
        - Resumen de métricas agregadas
        - Timeline de errores
        - Estadísticas de viewers
        - Comando FFmpeg usado
        
        Args:
            session_id: ID único de la sesión
            
        Returns:
            Dict con PublicationSessionDetailResponse o None si no existe
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener información básica de la sesión
                cursor.execute("""
                    SELECT 
                        ph.*,
                        c.name as camera_name,
                        ms.server_name
                    FROM publication_history ph
                    LEFT JOIN cameras c ON ph.camera_id = c.camera_id
                    LEFT JOIN mediamtx_servers ms ON ph.server_id = ms.server_id
                    WHERE ph.session_id = ?
                """, (session_id,))
                
                session_row = cursor.fetchone()
                if not session_row:
                    return None
                
                session_info = dict(session_row)
                
                # Parsear metadata para obtener ffmpeg_command
                ffmpeg_command = None
                if session_info.get('metadata'):
                    try:
                        metadata = json.loads(session_info['metadata'])
                        ffmpeg_command = metadata.get('ffmpeg_command')
                    except:
                        pass
                
                # Obtener publication_id para consultar métricas
                cursor.execute("""
                    SELECT publication_id 
                    FROM camera_publications 
                    WHERE session_id = ?
                    LIMIT 1
                """, (session_id,))
                
                pub_row = cursor.fetchone()
                publication_id = pub_row['publication_id'] if pub_row else None
                
                # Calcular resumen de métricas si tenemos publication_id
                metrics_summary = self._empty_metrics_summary()
                if publication_id:
                    cursor.execute("""
                        SELECT 
                            AVG(fps) as avg_fps,
                            MIN(fps) as min_fps,
                            MAX(fps) as max_fps,
                            AVG(bitrate_kbps) as avg_bitrate_kbps,
                            SUM(frames) as total_frames,
                            SUM(dropped_frames) as total_dropped_frames,
                            AVG(quality_score) as avg_quality_score,
                            MAX(viewer_count) as peak_viewers,
                            AVG(viewer_count) as avg_viewers,
                            SUM(size_kb) / 1024.0 as total_data_mb,
                            COUNT(*) as metric_count
                        FROM publication_metrics
                        WHERE publication_id = ?
                    """, (publication_id,))
                    
                    metrics_row = cursor.fetchone()
                    if metrics_row and metrics_row['metric_count'] > 0:
                        metrics_summary = {
                            'avg_fps': round(metrics_row['avg_fps'] or 0, 2),
                            'min_fps': round(metrics_row['min_fps'] or 0, 2),
                            'max_fps': round(metrics_row['max_fps'] or 0, 2),
                            'avg_bitrate_kbps': round(metrics_row['avg_bitrate_kbps'] or 0, 2),
                            'total_frames': int(metrics_row['total_frames'] or 0),
                            'total_dropped_frames': int(metrics_row['total_dropped_frames'] or 0),
                            'avg_quality_score': round(metrics_row['avg_quality_score'] or 0, 2),
                            'peak_viewers': int(metrics_row['peak_viewers'] or 0),
                            'avg_viewers': round(metrics_row['avg_viewers'] or 0, 2),
                            'total_data_mb': round(metrics_row['total_data_mb'] or 0, 2),
                            'uptime_percent': 100.0  # TODO: Calcular basado en duración esperada
                        }
                
                # Obtener timeline de errores (simulado por ahora)
                error_timeline = []
                if session_info.get('error_count', 0) > 0:
                    # TODO: Implementar tabla de eventos/errores
                    error_timeline.append({
                        'timestamp': session_info.get('end_time', session_info['start_time']),
                        'error_type': 'termination',
                        'message': session_info.get('last_error', 'Unknown error'),
                        'severity': 'error'
                    })
                
                # Obtener estadísticas de viewers
                viewer_summary = {
                    'total_unique_viewers': 0,
                    'total_viewer_time_seconds': session_info.get('total_viewer_time_seconds', 0),
                    'peak_concurrent': session_info.get('max_viewers', 0),
                    'protocol_breakdown': {}
                }
                
                if publication_id:
                    # Contar viewers únicos
                    cursor.execute("""
                        SELECT 
                            COUNT(DISTINCT viewer_ip) as unique_viewers,
                            protocol_used,
                            COUNT(*) as count
                        FROM publication_viewers
                        WHERE publication_id = ?
                        GROUP BY protocol_used
                    """, (publication_id,))
                    
                    for row in cursor.fetchall():
                        if row['unique_viewers'] > viewer_summary['total_unique_viewers']:
                            viewer_summary['total_unique_viewers'] = row['unique_viewers']
                        if row['protocol_used']:
                            viewer_summary['protocol_breakdown'][row['protocol_used']] = row['count']
                
                # Construir respuesta completa
                return {
                    'session_info': session_info,
                    'metrics_summary': metrics_summary,
                    'error_timeline': error_timeline,
                    'viewer_summary': viewer_summary,
                    'ffmpeg_command': ffmpeg_command,
                    'metadata': session_info.get('metadata')
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    async def move_publication_to_history(
        self,
        camera_id: str,
        termination_reason: TerminationReason = TerminationReason.COMPLETED
    ) -> bool:
        """
        Mueve una publicación activa al historial.
        
        Este método se llama cuando se detiene una publicación para:
        1. Calcular métricas agregadas finales
        2. Mover datos de camera_publications a publication_history
        3. Limpiar registros temporales
        
        Args:
            camera_id: ID de la cámara
            termination_reason: Razón de terminación
            
        Returns:
            True si se movió exitosamente, False si no había publicación activa
        """
        def _move():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener publicación activa
                cursor.execute("""
                    SELECT * FROM camera_publications
                    WHERE camera_id = ? AND is_active = 1
                    LIMIT 1
                """, (camera_id,))
                
                pub_row = cursor.fetchone()
                if not pub_row:
                    return False
                
                publication_id = pub_row['publication_id']
                
                # Calcular métricas agregadas
                cursor.execute("""
                    SELECT 
                        COUNT(*) as metric_count,
                        AVG(fps) as avg_fps,
                        AVG(bitrate_kbps) as avg_bitrate,
                        SUM(frames) as total_frames,
                        SUM(size_kb) / 1024.0 as total_data_mb,
                        MAX(viewer_count) as max_viewers
                    FROM publication_metrics
                    WHERE publication_id = ?
                """, (publication_id,))
                
                metrics = cursor.fetchone()
                
                # Calcular duración
                end_time = datetime.utcnow()
                start_time = pub_row['start_time']
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                duration_seconds = int((end_time - start_time).total_seconds())
                
                # Preparar metadata
                metadata = {
                    'process_pid': pub_row.get('process_pid'),
                    'ffmpeg_command': pub_row.get('ffmpeg_command'),
                    'final_error_count': pub_row.get('error_count', 0)
                }
                
                # Insertar en historial
                cursor.execute("""
                    INSERT INTO publication_history (
                        camera_id, server_id, session_id, publish_path,
                        start_time, end_time, duration_seconds,
                        total_frames, average_fps, average_bitrate_kbps,
                        total_data_mb, max_viewers, error_count,
                        termination_reason, last_error, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pub_row['camera_id'],
                    pub_row['server_id'],
                    pub_row['session_id'],
                    pub_row['publish_path'],
                    pub_row['start_time'],
                    end_time,
                    duration_seconds,
                    int(metrics['total_frames'] or 0) if metrics else 0,
                    round(metrics['avg_fps'] or 0, 2) if metrics else 0,
                    round(metrics['avg_bitrate'] or 0, 2) if metrics else 0,
                    round(metrics['total_data_mb'] or 0, 2) if metrics else 0,
                    int(metrics['max_viewers'] or 0) if metrics else 0,
                    pub_row.get('error_count', 0),
                    termination_reason.value,
                    pub_row.get('last_error'),
                    json.dumps(metadata)
                ))
                
                # Marcar publicación como inactiva
                cursor.execute("""
                    UPDATE camera_publications
                    SET is_active = 0, stop_time = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE publication_id = ?
                """, (end_time, publication_id))
                
                conn.commit()
                
                self.logger.info(
                    f"Publicación {pub_row['session_id']} movida a historial. "
                    f"Duración: {duration_seconds}s, Frames: {metrics['total_frames'] if metrics else 0}"
                )
                
                return True
                
        return await asyncio.get_event_loop().run_in_executor(None, _move)
    
    # === Métodos de Viewers ===
    
    async def get_active_viewers(
        self,
        request: GetViewersRequest
    ) -> Dict[str, Any]:
        """
        Obtiene información de viewers activos.
        
        Args:
            request: Parámetros de búsqueda
            
        Returns:
            Dict con lista de viewers
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Construir filtros
                conditions = []
                params = []
                
                if request.active_only:
                    conditions.append("pv.end_time IS NULL")
                    
                if request.publication_id:
                    conditions.append("pv.publication_id = ?")
                    params.append(request.publication_id)
                    
                if request.protocol:
                    conditions.append("pv.protocol_used = ?")
                    params.append(request.protocol.value)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Contar total
                cursor.execute(f"""
                    SELECT COUNT(*) as total
                    FROM publication_viewers pv
                    WHERE {where_clause}
                """, params)
                total = cursor.fetchone()['total']
                
                # Contar activos
                active_params = params.copy()
                active_conditions = conditions.copy()
                if "pv.end_time IS NULL" not in active_conditions:
                    active_conditions.append("pv.end_time IS NULL")
                active_where = " AND ".join(active_conditions) if active_conditions else "1=1"
                
                cursor.execute(f"""
                    SELECT COUNT(*) as active
                    FROM publication_viewers pv
                    WHERE {active_where}
                """, active_params)
                active_count = cursor.fetchone()['active']
                
                # Query principal
                offset = (request.page - 1) * request.page_size
                query = f"""
                    SELECT 
                        pv.*,
                        cp.camera_id,
                        c.display_name as camera_name,
                        CASE 
                            WHEN pv.end_time IS NULL 
                            THEN (julianday('now') - julianday(pv.start_time)) * 86400
                            ELSE pv.duration_seconds
                        END as duration_seconds
                    FROM publication_viewers pv
                    JOIN camera_publications cp ON pv.publication_id = cp.publication_id
                    JOIN cameras c ON cp.camera_id = c.camera_id
                    WHERE {where_clause}
                    ORDER BY pv.start_time DESC
                    LIMIT ? OFFSET ?
                """
                params.extend([request.page_size, offset])
                
                cursor.execute(query, params)
                
                items = []
                for row in cursor.fetchall():
                    items.append({
                        'viewer_id': row['viewer_id'],
                        'publication_id': row['publication_id'],
                        'camera_id': row['camera_id'],
                        'camera_name': row['camera_name'],
                        'viewer_ip': row['viewer_ip'],
                        'viewer_user_agent': row['viewer_user_agent'],
                        'protocol_used': row['protocol_used'],
                        'start_time': row['start_time'],
                        'duration_seconds': int(row['duration_seconds']),
                        'bytes_received': row['bytes_received'],
                        'quality_changes': row['quality_changes'],
                        'buffer_events': row['buffer_events']
                    })
                
                # Breakdown por protocolo
                cursor.execute("""
                    SELECT 
                        protocol_used,
                        COUNT(*) as count
                    FROM publication_viewers
                    WHERE end_time IS NULL
                    GROUP BY protocol_used
                """)
                
                protocol_breakdown = {}
                for row in cursor.fetchall():
                    protocol_breakdown[row['protocol_used']] = row['count']
                
                return {
                    'total': total,
                    'active_count': active_count,
                    'page': request.page,
                    'page_size': request.page_size,
                    'items': items,
                    'protocol_breakdown': protocol_breakdown
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    async def track_viewer(
        self,
        publication_id: int,
        viewer_ip: str,
        protocol: ViewerProtocol,
        user_agent: Optional[str] = None
    ) -> int:
        """
        Registra un nuevo viewer conectado.
        
        Args:
            publication_id: ID de la publicación
            viewer_ip: IP del viewer
            protocol: Protocolo usado
            user_agent: User agent del viewer
            
        Returns:
            ID del registro de viewer
        """
        def _track():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO publication_viewers (
                        publication_id, viewer_ip, viewer_user_agent,
                        protocol_used, start_time
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    publication_id,
                    viewer_ip,
                    user_agent,
                    protocol.value,
                    datetime.utcnow()
                ))
                return cursor.lastrowid
                
        viewer_id = await asyncio.get_event_loop().run_in_executor(None, _track)
        self.logger.debug(f"Viewer {viewer_ip} registrado con ID {viewer_id}")
        return viewer_id
    
    async def update_viewer_disconnection(
        self,
        viewer_id: int,
        bytes_received: int = 0,
        quality_changes: int = 0,
        buffer_events: int = 0
    ) -> None:
        """
        Actualiza información cuando un viewer se desconecta.
        
        Args:
            viewer_id: ID del viewer
            bytes_received: Bytes totales recibidos
            quality_changes: Número de cambios de calidad
            buffer_events: Número de eventos de buffer
        """
        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE publication_viewers
                    SET 
                        end_time = ?,
                        duration_seconds = (julianday(?) - julianday(start_time)) * 86400,
                        bytes_received = ?,
                        quality_changes = ?,
                        buffer_events = ?
                    WHERE viewer_id = ?
                """, (
                    datetime.utcnow(),
                    datetime.utcnow(),
                    bytes_received,
                    quality_changes,
                    buffer_events,
                    viewer_id
                ))
                
        await asyncio.get_event_loop().run_in_executor(None, _update)
    
    # === Métodos de Paths MediaMTX ===
    
    async def get_mediamtx_paths(
        self,
        server_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los paths configurados de MediaMTX.
        
        Args:
            server_id: Filtrar por servidor específico
            active_only: Solo paths activos
            
        Returns:
            Lista de paths con su configuración
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                conditions = []
                params = []
                
                if server_id:
                    conditions.append("mp.server_id = ?")
                    params.append(server_id)
                    
                if active_only:
                    conditions.append("mp.is_active = 1")
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                cursor.execute(f"""
                    SELECT 
                        mp.*,
                        ms.server_name,
                        (
                            SELECT COUNT(*) FROM camera_publications
                            WHERE publish_path = mp.path_name AND is_active = 1
                        ) as connected_publishers,
                        (
                            SELECT COUNT(*) FROM publication_viewers pv
                            JOIN camera_publications cp ON pv.publication_id = cp.publication_id
                            WHERE cp.publish_path = mp.path_name AND pv.end_time IS NULL
                        ) as connected_readers
                    FROM mediamtx_paths mp
                    JOIN mediamtx_servers ms ON mp.server_id = ms.server_id
                    WHERE {where_clause}
                    ORDER BY mp.path_name
                """, params)
                
                paths = []
                for row in cursor.fetchall():
                    paths.append({
                        'path_id': row['path_id'],
                        'server_id': row['server_id'],
                        'server_name': row['server_name'],
                        'path_name': row['path_name'],
                        'source_type': row['source_type'],
                        'source_url': row['source_url'],
                        'is_active': bool(row['is_active']),
                        'is_running': row['connected_publishers'] > 0 or row['connected_readers'] > 0,
                        'connected_publishers': row['connected_publishers'],
                        'connected_readers': row['connected_readers'],
                        'record_enabled': bool(row['record_enabled']),
                        'record_path': row['record_path'],
                        'authentication_required': bool(row['authentication_required']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return paths
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    async def create_mediamtx_path(
        self,
        server_id: int,
        path_config: Dict[str, Any]
    ) -> int:
        """
        Crea un nuevo path en MediaMTX.
        
        Args:
            server_id: ID del servidor
            path_config: Configuración del path
            
        Returns:
            ID del path creado
        """
        def _create():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar que no exista
                cursor.execute("""
                    SELECT path_id FROM mediamtx_paths
                    WHERE server_id = ? AND path_name = ?
                """, (server_id, path_config['path_name']))
                
                if cursor.fetchone():
                    raise ServiceError(
                        f"Ya existe un path '{path_config['path_name']}' en este servidor",
                        error_code="PATH_EXISTS"
                    )
                
                # Encriptar contraseñas si existen
                publish_pass_enc = None
                read_pass_enc = None
                if path_config.get('publish_password'):
                    publish_pass_enc = self._encrypt_password(path_config['publish_password'])
                if path_config.get('read_password'):
                    read_pass_enc = self._encrypt_password(path_config['read_password'])
                
                cursor.execute("""
                    INSERT INTO mediamtx_paths (
                        server_id, path_name, source_type, source_url,
                        record_enabled, record_path, record_format,
                        record_segment_duration, playback_enabled,
                        authentication_required, allowed_ips,
                        publish_user, publish_password_encrypted,
                        read_user, read_password_encrypted,
                        run_on_init, run_on_demand, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    server_id,
                    path_config['path_name'],
                    path_config['source_type'],
                    path_config.get('source_url'),
                    path_config.get('record_enabled', False),
                    path_config.get('record_path'),
                    path_config.get('record_format', 'fmp4'),
                    path_config.get('record_segment_duration', 3600),
                    path_config.get('playback_enabled', True),
                    path_config.get('authentication_required', False),
                    json.dumps(path_config.get('allowed_ips', [])),
                    path_config.get('publish_user'),
                    publish_pass_enc,
                    path_config.get('read_user'),
                    read_pass_enc,
                    path_config.get('run_on_init'),
                    path_config.get('run_on_demand'),
                    True
                ))
                
                return cursor.lastrowid
                
        path_id = await asyncio.get_event_loop().run_in_executor(None, _create)
        self.logger.info(f"Path MediaMTX creado con ID {path_id}")
        return path_id
    
    async def update_mediamtx_path(
        self,
        path_id: int,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Actualiza un path MediaMTX existente.
        
        Args:
            path_id: ID del path
            updates: Campos a actualizar
            
        Returns:
            True si se actualizó
        """
        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Construir query dinámicamente
                set_clauses = []
                params = []
                
                # Mapeo de campos permitidos
                field_map = {
                    'path_name': 'path_name',
                    'source_type': 'source_type',
                    'source_url': 'source_url',
                    'record_enabled': 'record_enabled',
                    'record_path': 'record_path',
                    'authentication_required': 'authentication_required',
                    'is_active': 'is_active'
                }
                
                for field, db_field in field_map.items():
                    if field in updates:
                        set_clauses.append(f"{db_field} = ?")
                        params.append(updates[field])
                
                if not set_clauses:
                    return False
                
                query = f"""
                    UPDATE mediamtx_paths
                    SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                    WHERE path_id = ?
                """
                params.append(path_id)
                
                cursor.execute(query, params)
                return cursor.rowcount > 0
                
        updated = await asyncio.get_event_loop().run_in_executor(None, _update)
        if updated:
            self.logger.info(f"Path {path_id} actualizado")
        return updated
    
    async def delete_mediamtx_path(self, path_id: int) -> bool:
        """
        Elimina un path MediaMTX.
        
        Args:
            path_id: ID del path a eliminar
            
        Returns:
            True si se eliminó
        """
        def _delete():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar que no esté en uso
                cursor.execute("""
                    SELECT COUNT(*) FROM camera_publications
                    WHERE publish_path = (
                        SELECT path_name FROM mediamtx_paths WHERE path_id = ?
                    ) AND is_active = 1
                """, (path_id,))
                
                if cursor.fetchone()[0] > 0:
                    raise ServiceError(
                        "No se puede eliminar el path porque está en uso",
                        error_code="PATH_IN_USE"
                    )
                
                cursor.execute("DELETE FROM mediamtx_paths WHERE path_id = ?", (path_id,))
                return cursor.rowcount > 0
                
        deleted = await asyncio.get_event_loop().run_in_executor(None, _delete)
        if deleted:
            self.logger.info(f"Path {path_id} eliminado")
        return deleted
    
    # === Métodos de Health/Monitoreo ===
    
    async def get_server_health_status(self, server_id: int) -> Dict[str, Any]:
        """
        Obtiene el estado de salud de un servidor MediaMTX.
        
        Args:
            server_id: ID del servidor
            
        Returns:
            Dict con información de salud
        """
        def _fetch():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Información del servidor
                cursor.execute("""
                    SELECT * FROM mediamtx_servers
                    WHERE server_id = ?
                """, (server_id,))
                
                server = cursor.fetchone()
                if not server:
                    return None
                
                # Publicaciones activas
                cursor.execute("""
                    SELECT COUNT(*) as active_pubs
                    FROM camera_publications
                    WHERE server_id = ? AND status = 'PUBLISHING' AND is_active = 1
                """, (server_id,))
                active_pubs = cursor.fetchone()['active_pubs']
                
                # Errores recientes (última hora)
                cursor.execute("""
                    SELECT COUNT(*) as recent_errors
                    FROM camera_publications
                    WHERE server_id = ? AND last_error_time > datetime('now', '-1 hour')
                """, (server_id,))
                recent_errors = cursor.fetchone()['recent_errors']
                
                # Determinar estado de salud
                health_status = "healthy"
                warnings = []
                
                if server['last_health_status'] == 'unhealthy':
                    health_status = "unhealthy"
                elif recent_errors > 5:
                    health_status = "degraded"
                    warnings.append(f"{recent_errors} errores en la última hora")
                
                # Métricas del servidor (si están disponibles)
                cursor.execute("""
                    SELECT 
                        AVG(cpu_usage_percent) as avg_cpu,
                        AVG(memory_usage_mb) as avg_memory
                    FROM publication_metrics pm
                    JOIN camera_publications cp ON pm.publication_id = cp.publication_id
                    WHERE cp.server_id = ? AND pm.metric_time > datetime('now', '-5 minutes')
                """, (server_id,))
                
                metrics = cursor.fetchone()
                
                return {
                    'server_id': server_id,
                    'server_name': server['server_name'],
                    'health_status': health_status,
                    'last_check_time': server['last_health_check'] or datetime.utcnow(),
                    'rtsp_server_ok': health_status != "unhealthy",
                    'api_server_ok': server['api_enabled'] and health_status != "unhealthy",
                    'paths_ok': True,  # TODO: Implementar verificación real
                    'active_connections': active_pubs,
                    'cpu_usage_percent': metrics['avg_cpu'],
                    'memory_usage_mb': metrics['avg_memory'],
                    'uptime_seconds': None,  # TODO: Calcular desde logs
                    'error_count': recent_errors,
                    'last_error': None,  # TODO: Obtener último error
                    'warnings': warnings
                }
                
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    
    async def update_server_health_check(
        self,
        server_id: int,
        health_status: str,
        error: Optional[str] = None
    ) -> None:
        """
        Actualiza el resultado de un health check.
        
        Args:
            server_id: ID del servidor
            health_status: Estado de salud (healthy, unhealthy, unknown)
            error: Mensaje de error si aplica
        """
        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE mediamtx_servers
                    SET 
                        last_health_check = ?,
                        last_health_status = ?
                    WHERE server_id = ?
                """, (
                    datetime.utcnow(),
                    health_status,
                    server_id
                ))
                
        await asyncio.get_event_loop().run_in_executor(None, _update)
    
    # === Métodos auxiliares privados ===
    
    def _calculate_start_time(
        self,
        time_range: str,
        custom_start: Optional[datetime],
        end_time: datetime
    ) -> datetime:
        """Calcula el tiempo de inicio basado en el rango."""
        if time_range == "custom" and custom_start:
            return custom_start
            
        range_map = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        delta = range_map.get(time_range, timedelta(hours=1))
        return end_time - delta
    
    def _calculate_metrics_summary(self, data_points: List[Dict]) -> Dict[str, Any]:
        """Calcula resumen estadístico de métricas."""
        if not data_points:
            return self._empty_metrics_summary()
            
        fps_values = [p['fps'] for p in data_points if p.get('fps')]
        bitrate_values = [p['bitrate_kbps'] for p in data_points if p.get('bitrate_kbps')]
        quality_values = [p['quality_score'] for p in data_points if p.get('quality_score')]
        viewer_counts = [p['viewer_count'] for p in data_points if p.get('viewer_count') is not None]
        
        return {
            'avg_fps': sum(fps_values) / len(fps_values) if fps_values else 0,
            'min_fps': min(fps_values) if fps_values else 0,
            'max_fps': max(fps_values) if fps_values else 0,
            'avg_bitrate_kbps': sum(bitrate_values) / len(bitrate_values) if bitrate_values else 0,
            'total_frames': sum(p.get('frames', 0) for p in data_points),
            'total_dropped_frames': sum(p.get('dropped_frames', 0) for p in data_points),
            'avg_quality_score': sum(quality_values) / len(quality_values) if quality_values else 0,
            'peak_viewers': max(viewer_counts) if viewer_counts else 0,
            'avg_viewers': sum(viewer_counts) / len(viewer_counts) if viewer_counts else 0,
            'total_data_mb': sum(p.get('size_kb', 0) for p in data_points) / 1024,
            'uptime_percent': self._calculate_uptime_percent(data_points)
        }
    
    def _calculate_uptime_percent(self, data_points: List[Dict]) -> float:
        """Calcula el porcentaje de uptime basado en métricas."""
        if not data_points:
            return 0.0
            
        # Contar puntos con FPS > 0 como "activos"
        active_points = sum(1 for p in data_points if p.get('fps', 0) > 0)
        return (active_points / len(data_points)) * 100 if data_points else 0.0
    
    def _empty_metrics_summary(self) -> Dict[str, Any]:
        """Retorna un resumen de métricas vacío."""
        return {
            'avg_fps': 0,
            'min_fps': 0,
            'max_fps': 0,
            'avg_bitrate_kbps': 0,
            'total_frames': 0,
            'total_dropped_frames': 0,
            'avg_quality_score': 0,
            'peak_viewers': 0,
            'avg_viewers': 0,
            'total_data_mb': 0,
            'uptime_percent': 0
        }
    
    def _get_viewer_stats(
        self,
        conn: sqlite3.Connection,
        publication_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Obtiene estadísticas de viewers para un período."""
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT viewer_ip) as unique_viewers,
                COUNT(*) as total_sessions,
                AVG(duration_seconds) as avg_duration,
                MAX(duration_seconds) as max_duration,
                SUM(bytes_received) as total_bytes,
                AVG(buffer_events) as avg_buffer_events
            FROM publication_viewers
            WHERE publication_id = ?
            AND start_time BETWEEN ? AND ?
        """, (publication_id, start_time, end_time))
        
        row = cursor.fetchone()
        return {
            'unique_viewers': row['unique_viewers'] or 0,
            'total_sessions': row['total_sessions'] or 0,
            'avg_session_duration': round(row['avg_duration'] or 0, 2),
            'max_session_duration': row['max_duration'] or 0,
            'total_data_gb': round((row['total_bytes'] or 0) / 1024 / 1024 / 1024, 2),
            'avg_buffer_events': round(row['avg_buffer_events'] or 0, 2)
        }
    
    def _calculate_session_metrics_summary(
        self,
        conn: sqlite3.Connection,
        session_id: str
    ) -> Dict[str, Any]:
        """Calcula resumen de métricas para una sesión específica."""
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                AVG(fps) as avg_fps,
                MIN(fps) as min_fps,
                MAX(fps) as max_fps,
                AVG(bitrate_kbps) as avg_bitrate,
                SUM(frames) as total_frames,
                SUM(dropped_frames) as total_dropped,
                AVG(quality_score) as avg_quality,
                MAX(viewer_count) as peak_viewers,
                SUM(size_kb) / 1024 as total_data_mb
            FROM publication_metrics
            WHERE publication_id IN (
                SELECT publication_id FROM camera_publications 
                WHERE session_id = ?
            )
        """, (session_id,))
        
        row = cursor.fetchone()
        return {
            'avg_fps': round(row['avg_fps'] or 0, 2),
            'min_fps': row['min_fps'] or 0,
            'max_fps': row['max_fps'] or 0,
            'avg_bitrate_kbps': round(row['avg_bitrate'] or 0, 2),
            'total_frames': row['total_frames'] or 0,
            'total_dropped_frames': row['total_dropped'] or 0,
            'avg_quality_score': round(row['avg_quality'] or 0, 2),
            'peak_viewers': row['peak_viewers'] or 0,
            'avg_viewers': 0,  # Requeriría cálculo más complejo
            'total_data_mb': round(row['total_data_mb'] or 0, 2),
            'uptime_percent': 100.0  # Asumiendo que si hay métricas, estuvo activo
        }


# Instancia singleton
_mediamtx_db_service: Optional[MediaMTXDatabaseService] = None


def get_mediamtx_db_service(db_path: Optional[str] = None) -> MediaMTXDatabaseService:
    """
    Obtiene la instancia singleton del servicio MediaMTX.
    
    Args:
        db_path: Ruta a la BD (solo en primera llamada)
        
    Returns:
        MediaMTXDatabaseService singleton
    """
    global _mediamtx_db_service
    
    if _mediamtx_db_service is None:
        if db_path is None:
            db_path = "data/camera_data.db"
        _mediamtx_db_service = MediaMTXDatabaseService(db_path)
        
    return _mediamtx_db_service