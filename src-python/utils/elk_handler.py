"""
Handler personalizado para envío de logs a ELK Stack.

Este módulo proporciona handlers para exportar logs a Elasticsearch
o escribir en formato compatible con Filebeat/Logstash.
"""
import logging
import json
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from queue import Queue, Empty
import threading
import time

from utils.json_formatter import StructuredJSONFormatter, ElasticCommonSchema
from services.base_service import BaseService


class FilebasedELKHandler(logging.Handler):
    """
    Handler que escribe logs en formato JSON para ser recogidos por Filebeat.
    
    Esta es la aproximación recomendada para producción:
    - La aplicación escribe logs JSON a archivos
    - Filebeat los recoge y envía a Logstash/Elasticsearch
    - Menor acoplamiento y mayor resiliencia
    """
    
    def __init__(self, 
                 log_dir: str = "logs/elk",
                 index_prefix: str = "ucv",
                 max_file_size: int = 100 * 1024 * 1024,  # 100MB
                 backup_count: int = 10,
                 buffer_size: int = 1000,
                 flush_interval: float = 5.0):
        """
        Inicializa el handler basado en archivos.
        
        Args:
            log_dir: Directorio para logs JSON
            index_prefix: Prefijo para índices de Elasticsearch
            max_file_size: Tamaño máximo por archivo
            backup_count: Número de archivos de respaldo
            buffer_size: Tamaño del buffer interno
            flush_interval: Intervalo de flush en segundos
        """
        super().__init__()
        
        # Configuración
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.index_prefix = index_prefix
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # Buffer para mejorar rendimiento
        self.buffer = []
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.last_flush = time.time()
        
        # Archivos por tipo de log
        self.log_files: Dict[str, logging.handlers.RotatingFileHandler] = {}
        self._setup_log_files()
        
        # Thread para flush periódico
        self.flush_thread = threading.Thread(target=self._periodic_flush, daemon=True)
        self.flush_thread.start()
        
        # Formateador JSON
        self.setFormatter(ElasticCommonSchema(
            include_hostname=True,
            sanitize=True
        ))
        
    def _setup_log_files(self) -> None:
        """Configura archivos de log por categoría."""
        categories = ['app', 'audit', 'error', 'metrics', 'streaming']
        
        for category in categories:
            file_path = self.log_dir / f"{self.index_prefix}-{category}.json"
            handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            self.log_files[category] = handler
            
    def _get_category(self, record: logging.LogRecord) -> str:
        """
        Determina la categoría del log.
        
        Args:
            record: Registro de logging
            
        Returns:
            Categoría del log
        """
        # Por nivel
        if record.levelname in ['ERROR', 'CRITICAL']:
            return 'error'
        elif record.levelname == 'AUDIT':
            return 'audit'
            
        # Por logger name
        if 'metrics' in record.name:
            return 'metrics'
        elif 'stream' in record.name or 'video' in record.name:
            return 'streaming'
            
        # Default
        return 'app'
        
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emite el registro de log.
        
        Args:
            record: Registro a emitir
        """
        try:
            # Formatear registro
            msg = self.format(record)
            
            # Agregar metadatos para Filebeat
            log_entry = json.loads(msg)
            log_entry['_index'] = f"{self.index_prefix}-{self._get_category(record)}"
            log_entry['_type'] = '_doc'
            
            # Agregar al buffer
            self.buffer.append(json.dumps(log_entry) + '\n')
            
            # Flush si el buffer está lleno
            if len(self.buffer) >= self.buffer_size:
                self.flush()
                
        except Exception:
            self.handleError(record)
            
    def flush(self) -> None:
        """Escribe el buffer a los archivos."""
        if not self.buffer:
            return
            
        try:
            # Agrupar por categoría
            categorized_logs: Dict[str, List[str]] = {}
            
            for log_line in self.buffer:
                try:
                    log_data = json.loads(log_line.strip())
                    category = log_data['_index'].split('-')[-1]
                    
                    if category not in categorized_logs:
                        categorized_logs[category] = []
                    categorized_logs[category].append(log_line)
                except:
                    # Si falla, escribir en app por defecto
                    if 'app' not in categorized_logs:
                        categorized_logs['app'] = []
                    categorized_logs['app'].append(log_line)
                    
            # Escribir a archivos correspondientes
            for category, logs in categorized_logs.items():
                if category in self.log_files:
                    handler = self.log_files[category]
                    for log in logs:
                        handler.stream.write(log)
                    handler.stream.flush()
                    
            # Limpiar buffer
            self.buffer.clear()
            self.last_flush = time.time()
            
        except Exception as e:
            # Log error to stderr to avoid recursion
            import sys
            print(f"Error flushing ELK logs: {e}", file=sys.stderr)
            
    def _periodic_flush(self) -> None:
        """Thread que hace flush periódico del buffer."""
        while True:
            time.sleep(self.flush_interval)
            if time.time() - self.last_flush >= self.flush_interval:
                self.flush()
                
    def close(self) -> None:
        """Cierra el handler y sus recursos."""
        self.flush()
        for handler in self.log_files.values():
            handler.close()
        super().close()


class AsyncElasticsearchHandler(logging.Handler):
    """
    Handler asíncrono para envío directo a Elasticsearch.
    
    NOTA: Esta implementación es para desarrollo/testing.
    En producción se recomienda usar FilebasedELKHandler + Filebeat.
    
    TODO: Requiere instalación de elasticsearch-py:
    pip install elasticsearch[async]
    """
    
    def __init__(self,
                 es_host: str = "localhost",
                 es_port: int = 9200,
                 index_prefix: str = "ucv",
                 use_ssl: bool = False,
                 verify_certs: bool = True,
                 es_user: Optional[str] = None,
                 es_password: Optional[str] = None,
                 batch_size: int = 100,
                 flush_interval: float = 10.0):
        """
        Inicializa el handler de Elasticsearch.
        
        Args:
            es_host: Host de Elasticsearch
            es_port: Puerto de Elasticsearch
            index_prefix: Prefijo para índices
            use_ssl: Si usar SSL
            verify_certs: Si verificar certificados SSL
            es_user: Usuario de Elasticsearch
            es_password: Contraseña de Elasticsearch
            batch_size: Tamaño del batch para bulk insert
            flush_interval: Intervalo de flush en segundos
        """
        super().__init__()
        
        # Configuración
        self.es_host = es_host
        self.es_port = es_port
        self.index_prefix = index_prefix
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Queue para logs
        self.log_queue: Queue = Queue(maxsize=10000)
        
        # Formateador
        self.setFormatter(ElasticCommonSchema(
            include_hostname=True,
            sanitize=True
        ))
        
        # TODO: Implementar conexión real a Elasticsearch
        # Por ahora es un placeholder que simula el comportamiento
        self.es_client = None  # AsyncElasticsearch en implementación real
        
        # Thread para procesamiento asíncrono
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
    def emit(self, record: logging.LogRecord) -> None:
        """
        Agrega el registro a la cola para procesamiento asíncrono.
        
        Args:
            record: Registro de logging
        """
        try:
            # Formatear mensaje
            msg = self.format(record)
            log_data = json.loads(msg)
            
            # Agregar índice
            index_name = self._get_index_name(record)
            
            # Agregar a la cola (non-blocking)
            self.log_queue.put_nowait({
                'index': index_name,
                'document': log_data
            })
            
        except Exception:
            self.handleError(record)
            
    def _get_index_name(self, record: logging.LogRecord) -> str:
        """
        Genera el nombre del índice basado en la fecha y categoría.
        
        Args:
            record: Registro de logging
            
        Returns:
            Nombre del índice
        """
        date_suffix = datetime.utcnow().strftime('%Y.%m.%d')
        
        # Categorizar
        if record.levelname in ['ERROR', 'CRITICAL']:
            category = 'errors'
        elif record.levelname == 'AUDIT':
            category = 'audit'
        elif 'metrics' in record.name:
            category = 'metrics'
        elif 'stream' in record.name:
            category = 'streaming'
        else:
            category = 'app'
            
        return f"{self.index_prefix}-{category}-{date_suffix}"
        
    def _worker(self) -> None:
        """Worker thread que procesa la cola de logs."""
        batch = []
        last_flush = time.time()
        
        while True:
            try:
                # Timeout para permitir flush periódico
                timeout = max(0.1, self.flush_interval - (time.time() - last_flush))
                
                try:
                    item = self.log_queue.get(timeout=timeout)
                    batch.append(item)
                except Empty:
                    pass
                    
                # Flush si es necesario
                should_flush = (
                    len(batch) >= self.batch_size or
                    time.time() - last_flush >= self.flush_interval
                )
                
                if should_flush and batch:
                    # TODO: Implementar bulk insert real
                    # asyncio.run(self._bulk_insert(batch))
                    self._simulate_bulk_insert(batch)
                    batch.clear()
                    last_flush = time.time()
                    
            except Exception as e:
                import sys
                print(f"Error in ELK worker: {e}", file=sys.stderr)
                
    def _simulate_bulk_insert(self, batch: List[Dict[str, Any]]) -> None:
        """
        Simula bulk insert para desarrollo.
        
        TODO: Reemplazar con implementación real de Elasticsearch.
        
        Args:
            batch: Batch de documentos a insertar
        """
        # Por ahora solo log a archivo para debugging
        debug_file = Path("logs/elk_debug.jsonl")
        debug_file.parent.mkdir(exist_ok=True)
        
        with open(debug_file, 'a', encoding='utf-8') as f:
            for item in batch:
                f.write(json.dumps({
                    'index': item['index'],
                    'document': item['document']
                }) + '\n')
                
    def close(self) -> None:
        """Cierra el handler."""
        # TODO: Cerrar conexión de Elasticsearch
        super().close()


def create_elk_handler(handler_type: str = "file", **kwargs) -> logging.Handler:
    """
    Factory para crear handlers ELK.
    
    Args:
        handler_type: Tipo de handler ('file' o 'elasticsearch')
        kwargs: Argumentos para el handler
        
    Returns:
        Handler configurado
    """
    if handler_type == "file":
        return FilebasedELKHandler(**kwargs)
    elif handler_type == "elasticsearch":
        return AsyncElasticsearchHandler(**kwargs)
    else:
        raise ValueError(f"Tipo de handler no soportado: {handler_type}")