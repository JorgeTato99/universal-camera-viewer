#!/usr/bin/env python3
"""
Script para crear la base de datos desde cero.

Este script elimina la base de datos existente y crea una nueva
con la estructura 3FN siguiendo las mejores prácticas.

NOTA: Esta es la versión modular que utiliza los módulos de schema
para mejor organización y mantenibilidad.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import sys
import os

# Agregar el directorio actual al path para importar los módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Importar definiciones de esquema
from services.database.schema import (
    core_tables,
    operation_tables,
    scanning_tables,
    storage_tables,
    mediamtx_tables,
    config_tables,
    indexes,
    triggers,
    views
)
from services.database.data import initial_data
from services.logging_service import get_secure_logger

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = get_secure_logger("services.create_database")


class DatabaseCreator:
    """Crea la base de datos con estructura modular 3FN optimizada."""
    
    def __init__(self, db_path: str = "data/camera_data.db"):
        """
        Inicializa el creador de base de datos.
        
        Args:
            db_path: Ruta donde crear la base de datos
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def drop_existing_database(self) -> None:
        """Elimina la base de datos existente si existe."""
        if self.db_path.exists():
            logger.warning(f"Eliminando base de datos existente: {self.db_path}")
            try:
                self.db_path.unlink()
                logger.info("Base de datos eliminada")
            except PermissionError:
                # Intentar cerrar cualquier conexión existente
                import gc
                gc.collect()  # Forzar recolección de basura
                
                # Intentar renombrar en lugar de eliminar
                backup_name = f"{self.db_path}.old_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                try:
                    self.db_path.rename(backup_name)
                    logger.warning(f"No se pudo eliminar, se renombró a: {backup_name}")
                except Exception as e:
                    logger.error(f"No se pudo eliminar ni renombrar la base de datos: {e}")
                    logger.error("Por favor cierre todos los procesos que usen la base de datos:")
                    logger.error("1. Detenga el servidor FastAPI (Ctrl+C)")
                    logger.error("2. Cierre SQLite Browser o herramientas similares")
                    logger.error("3. Verifique que no haya scripts Python ejecutándose")
                    raise RuntimeError(f"Base de datos en uso: {self.db_path}")
        
    def create_database(self) -> bool:
        """
        Crea la base de datos con todas las tablas.
        
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            # Eliminar DB existente
            self.drop_existing_database()
            
            # Crear nueva conexión
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Habilitar claves foráneas
            cursor.execute("PRAGMA foreign_keys = ON")
            
            logger.info("Creando nueva base de datos...")
            
            # ================== CREAR TABLAS ==================
            
            # Crear tablas principales
            self._create_tables(cursor, "principales", core_tables.get_core_tables())
            
            # Crear tablas de operación
            self._create_tables(cursor, "operación", operation_tables.get_operation_tables())
            
            # Crear tablas de escaneo
            self._create_tables(cursor, "escaneo", scanning_tables.get_scanning_tables())
            
            # Crear tablas de almacenamiento
            self._create_tables(cursor, "almacenamiento", storage_tables.get_storage_tables())
            
            # Crear tablas de MediaMTX
            self._create_tables(cursor, "MediaMTX", mediamtx_tables.get_mediamtx_tables())
            
            # Crear tablas de configuración
            self._create_tables(cursor, "configuración", config_tables.get_config_tables())
            
            # ================== CREAR ÍNDICES ==================
            
            logger.info("Creando índices...")
            all_indexes = indexes.get_all_indexes()
            for index_sql in all_indexes:
                cursor.execute(index_sql)
            logger.info(f"  ✓ {len(all_indexes)} índices creados")
            
            # ================== CREAR TRIGGERS ==================
            
            logger.info("Creando triggers...")
            all_triggers = triggers.get_all_triggers()
            for trigger_sql in all_triggers:
                cursor.execute(trigger_sql)
            logger.info(f"  ✓ {len(all_triggers)} triggers creados")
            
            # ================== CREAR VISTAS ==================
            
            logger.info("Creando vistas...")
            all_views = views.get_all_views()
            for view_sql in all_views:
                cursor.execute(view_sql)
            logger.info(f"  ✓ {len(all_views)} vistas creadas")
            
            # ================== INSERTAR DATOS INICIALES ==================
            
            logger.info("Insertando datos iniciales...")
            initial_data.insert_initial_data(cursor)
            data_summary = initial_data.get_initial_data_summary()
            logger.info(f"  ✓ {data_summary['system_config']} configuraciones del sistema")
            logger.info(f"  ✓ {data_summary['config_templates']} plantillas de configuración")
            
            # Confirmar cambios
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Base de datos creada exitosamente en: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando base de datos: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_tables(self, cursor, category: str, tables: list):
        """
        Crea un grupo de tablas.
        
        Args:
            cursor: Cursor de SQLite
            category: Categoría de las tablas (para logging)
            tables: Lista de tuplas (nombre_tabla, sql_create)
        """
        logger.info(f"Creando tablas de {category}...")
        for table_name, create_sql in tables:
            cursor.execute(create_sql)
            logger.debug(f"  ✓ Tabla '{table_name}' creada")
        logger.info(f"  ✓ {len(tables)} tablas de {category} creadas")
    
    def verify_database(self) -> bool:
        """
        Verifica que la base de datos se creó correctamente.
        
        Returns:
            bool: True si la verificación es exitosa
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Obtener lista de todas las tablas esperadas
            expected_tables = []
            expected_tables.extend(core_tables.get_table_names())
            expected_tables.extend(operation_tables.get_table_names())
            expected_tables.extend(scanning_tables.get_table_names())
            expected_tables.extend(storage_tables.get_table_names())
            expected_tables.extend(mediamtx_tables.get_table_names())
            expected_tables.extend(config_tables.get_table_names())
            
            # Verificar que existen las tablas
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            missing = set(expected_tables) - set(tables)
            if missing:
                logger.error(f"Tablas faltantes: {missing}")
                return False
            
            logger.info(f"✅ Verificación exitosa: {len(tables)} tablas encontradas")
            
            # Verificar integridad de claves foráneas
            cursor.execute("PRAGMA foreign_key_check")
            fk_errors = cursor.fetchall()
            if fk_errors:
                logger.error(f"Errores de claves foráneas: {fk_errors}")
                return False
            
            # Verificar vistas
            expected_views = views.get_view_names()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='view' 
                ORDER BY name
            """)
            
            created_views = [row[0] for row in cursor.fetchall()]
            missing_views = set(expected_views) - set(created_views)
            if missing_views:
                logger.error(f"Vistas faltantes: {missing_views}")
                return False
            
            logger.info(f"✅ {len(created_views)} vistas verificadas")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error verificando base de datos: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """
        Obtiene información estadística de la base de datos.
        
        Returns:
            dict: Información sobre tablas, índices, etc.
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Contar tablas
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # Contar índices
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            index_count = cursor.fetchone()[0]
            
            # Contar triggers
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'")
            trigger_count = cursor.fetchone()[0]
            
            # Contar vistas
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'")
            view_count = cursor.fetchone()[0]
            
            # Tamaño del archivo
            db_size = self.db_path.stat().st_size / 1024 / 1024  # MB
            
            conn.close()
            
            return {
                'tables': table_count,
                'indexes': index_count,
                'triggers': trigger_count,
                'views': view_count,
                'size_mb': round(db_size, 2)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información de la base de datos: {e}")
            return {}


def main():
    """Función principal para ejecutar el script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crear base de datos para Universal Camera Viewer')
    parser.add_argument('--path', default='data/camera_data.db', help='Ruta de la base de datos')
    parser.add_argument('--force', action='store_true', help='Forzar recreación sin confirmar')
    parser.add_argument('--info', action='store_true', help='Mostrar información de la base de datos existente')
    
    args = parser.parse_args()
    
    creator = DatabaseCreator(args.path)
    
    # Si solo se pide información
    if args.info:
        if Path(args.path).exists():
            info = creator.get_database_info()
            print("\n📊 Información de la base de datos:")
            print(f"  - Tablas: {info.get('tables', 0)}")
            print(f"  - Índices: {info.get('indexes', 0)}")
            print(f"  - Triggers: {info.get('triggers', 0)}")
            print(f"  - Vistas: {info.get('views', 0)}")
            print(f"  - Tamaño: {info.get('size_mb', 0)} MB")
        else:
            print(f"❌ La base de datos {args.path} no existe")
        return
    
    # Verificar si existe y pedir confirmación
    if Path(args.path).exists() and not args.force:
        response = input(f"⚠️  La base de datos {args.path} existe. ¿Eliminar y recrear? (s/n): ")
        if response.lower() != 's':
            print("Operación cancelada")
            return
    
    # Crear base de datos
    if creator.create_database():
        # Verificar creación
        if creator.verify_database():
            print("✅ Base de datos creada y verificada exitosamente")
            
            # Mostrar información
            info = creator.get_database_info()
            print("\n📊 Resumen de la base de datos creada:")
            print(f"  - Tablas: {info.get('tables', 0)}")
            print(f"  - Índices: {info.get('indexes', 0)}")
            print(f"  - Triggers: {info.get('triggers', 0)}")
            print(f"  - Vistas: {info.get('views', 0)}")
            print(f"  - Tamaño: {info.get('size_mb', 0)} MB")
        else:
            print("❌ La base de datos se creó pero falló la verificación")
            sys.exit(1)
    else:
        print("❌ Error al crear la base de datos")
        sys.exit(1)


if __name__ == "__main__":
    main()