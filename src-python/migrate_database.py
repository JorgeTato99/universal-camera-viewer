#!/usr/bin/env python3
"""
Script para migrar o reconstruir la base de datos.

Este script permite:
1. Crear una nueva base de datos con la estructura correcta
2. Hacer backup de la base de datos existente
3. Limpiar y reinsertar datos seed
"""
import os
import sys
import shutil
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Agregar directorio src-python al path
sys.path.append(str(Path(__file__).parent))

from services.create_database import DatabaseCreator
from seed_database import DatabaseSeeder


def setup_logging(verbose: bool = False):
    """Configura el sistema de logging."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('migration.log')
        ]
    )


def backup_database(db_path: Path) -> Path:
    """
    Crea un backup de la base de datos actual.
    
    Args:
        db_path: Ruta de la base de datos
        
    Returns:
        Ruta del backup creado o None si no existe la BD
    """
    if not db_path.exists():
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    backup_path = backup_dir / f"{db_path.stem}_backup_{timestamp}.db"
    
    logging.info(f"Creando backup en: {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    return backup_path


def run_migration(db_path: str, force: bool = False, no_backup: bool = False) -> bool:
    """
    Ejecuta la migración o reconstrucción de la base de datos.
    
    Args:
        db_path: Ruta a la base de datos
        force: Forzar migración sin confirmación
        no_backup: No crear backup antes de migrar
        
    Returns:
        True si la migración fue exitosa
    """
    logger = logging.getLogger(__name__)
    db_path = Path(db_path)
    
    try:
        # 1. Verificar si existe la base de datos
        if db_path.exists():
            logger.info(f"Base de datos existente encontrada: {db_path}")
            
            # Crear backup si no se deshabilitó
            if not no_backup:
                backup_path = backup_database(db_path)
                if backup_path:
                    logger.info(f"✅ Backup creado: {backup_path}")
                else:
                    logger.warning("No se pudo crear backup")
                    if not force:
                        return False
            
            # Si existe, preguntar si reconstruir
            if not force:
                logger.warning("La base de datos será reconstruida completamente")
                response = input("\n¿Desea continuar? (s/n): ")
                if response.lower() != 's':
                    logger.info("Migración cancelada por el usuario")
                    return False
            
            # Eliminar base de datos existente
            logger.info("Eliminando base de datos existente...")
            os.remove(db_path)
            
        # 2. Crear nueva base de datos
        logger.info("Creando nueva base de datos con estructura 3FN...")
        creator = DatabaseCreator(str(db_path))
        
        if not creator.create_database():
            logger.error("Error creando la base de datos")
            return False
            
        logger.info("✅ Base de datos creada exitosamente")
        
        # 3. Insertar datos seed
        logger.info("Insertando datos iniciales (SEED)...")
        seeder = DatabaseSeeder(str(db_path))
        seeder.seed_cameras()
        seeder.close()
        
        logger.info("✅ Datos iniciales insertados")
        
        # 4. Verificar estructura
        logger.info("Verificando estructura de la base de datos...")
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        expected_tables = [
            'camera_capabilities', 'camera_credentials', 'camera_endpoints',
            'camera_events', 'camera_protocols', 'camera_statistics',
            'cameras', 'config_templates', 'connection_logs', 'network_scans',
            'recordings', 'scan_results', 'snapshots', 'stream_profiles',
            'system_config'
        ]
        
        actual_tables = [t[0] for t in tables if not t[0].startswith('sqlite_')]
        missing_tables = set(expected_tables) - set(actual_tables)
        
        if missing_tables:
            logger.error(f"Tablas faltantes: {missing_tables}")
            return False
            
        # Verificar cantidad de cámaras
        cursor.execute("SELECT COUNT(*) FROM cameras")
        camera_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"✅ Estructura verificada: {len(actual_tables)} tablas, {camera_count} cámaras")
        
        return True
        
    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        logger.exception("Stacktrace completo:")
        return False


def main():
    """Función principal del script de migración."""
    parser = argparse.ArgumentParser(
        description='Migra o reconstruye la base de datos con estructura normalizada 3FN'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/camera_data.db',
        help='Ruta a la base de datos SQLite (default: data/camera_data.db)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Forzar migración sin confirmación'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='No crear backup antes de migrar (NO RECOMENDADO)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar información detallada de debug'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular migración sin hacer cambios'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Convertir ruta relativa a absoluta
    db_path = Path(args.db_path)
    if not db_path.is_absolute():
        db_path = Path(__file__).parent / db_path
    
    logger.info("=" * 60)
    logger.info("MIGRACIÓN DE BASE DE DATOS")
    logger.info("=" * 60)
    logger.info(f"Base de datos: {db_path}")
    logger.info(f"Backup: {'Deshabilitado' if args.no_backup else 'Habilitado'}")
    logger.info(f"Modo: {'Simulación' if args.dry_run else 'Real'}")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("MODO SIMULACIÓN - No se realizarán cambios")
        
        # Verificar qué existe
        if db_path.exists():
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Contar registros
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            logger.info(f"Base de datos existente con {len(tables)} tablas")
            
            for table in tables:
                if not table[0].startswith('sqlite_'):
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    logger.info(f"  - {table[0]}: {count} registros")
            
            conn.close()
        else:
            logger.info("No existe base de datos. Se creará una nueva.")
        
        return 0
    
    # Ejecutar migración
    logger.info("Iniciando proceso de migración...")
    
    success = run_migration(
        str(db_path),
        force=args.force,
        no_backup=args.no_backup
    )
    
    if success:
        logger.info("✅ Migración completada exitosamente")
        logger.info("\nPróximos pasos:")
        logger.info("1. Verifique que la aplicación funciona correctamente")
        logger.info("2. Los backups se encuentran en data/backups/")
        logger.info("3. Puede eliminar los backups después de verificar que todo funciona")
        return 0
    else:
        logger.error("❌ Error durante la migración")
        logger.error("Revise el archivo migration.log para más detalles")
        return 1


if __name__ == "__main__":
    sys.exit(main())