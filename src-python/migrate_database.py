#!/usr/bin/env python3
"""
Script para ejecutar la migración de base de datos.

Migra la estructura antigua de SQLite a la nueva estructura normalizada 3FN.
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# Agregar directorio src-python al path
sys.path.append(str(Path(__file__).parent))

from services.database_migration import run_migration
from services.data_service import DataService, DataServiceConfig


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


def main():
    """Función principal del script de migración."""
    parser = argparse.ArgumentParser(
        description='Migra la base de datos a la nueva estructura normalizada 3FN'
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
        help='Forzar migración incluso si ya está migrada'
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
    
    # Verificar que existe la base de datos
    db_path = Path(args.db_path)
    if not db_path.exists():
        logger.error(f"No se encontró la base de datos en: {db_path}")
        logger.info("Si es una instalación nueva, simplemente ejecute la aplicación")
        return 1
    
    logger.info("=" * 60)
    logger.info("MIGRACIÓN DE BASE DE DATOS")
    logger.info("=" * 60)
    logger.info(f"Base de datos: {db_path}")
    logger.info(f"Backup: {'Deshabilitado' if args.no_backup else 'Habilitado'}")
    logger.info(f"Modo: {'Simulación' if args.dry_run else 'Real'}")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("MODO SIMULACIÓN - No se realizarán cambios")
        # TODO: Implementar análisis de qué se migraría
        return 0
    
    # Preguntar confirmación
    if not args.force:
        print("\n⚠️  ADVERTENCIA: Este proceso modificará la estructura de la base de datos.")
        print("Se recomienda hacer un backup manual adicional antes de continuar.")
        response = input("\n¿Desea continuar? (s/N): ")
        
        if response.lower() != 's':
            logger.info("Migración cancelada por el usuario")
            return 0
    
    try:
        # Ejecutar migración
        logger.info("Iniciando proceso de migración...")
        
        success = run_migration(str(db_path))
        
        if success:
            logger.info("✅ Migración completada exitosamente")
            logger.info("\nPróximos pasos:")
            logger.info("1. Verifique que la aplicación funciona correctamente")
            logger.info("2. Los backups se encuentran en el mismo directorio que la DB")
            logger.info("3. Puede eliminar los backups después de verificar que todo funciona")
            
            # Verificar nueva estructura
            logger.info("\nVerificando nueva estructura...")
            try:
                from services.data_service import DataService
                config = DataServiceConfig(database_path=str(db_path))
                data_service = DataService(config)
                
                # Intentar una operación simple
                asyncio.run(data_service.initialize())
                logger.info("✅ Nueva estructura verificada correctamente")
                
            except Exception as e:
                logger.error(f"⚠️  Error verificando nueva estructura: {e}")
                logger.error("Puede restaurar desde el backup si es necesario")
            
            return 0
        else:
            logger.error("❌ Error durante la migración")
            logger.error("La base de datos no fue modificada o fue revertida")
            logger.error("Revise el archivo migration.log para más detalles")
            return 1
            
    except KeyboardInterrupt:
        logger.warning("\nMigración interrumpida por el usuario")
        return 1
        
    except Exception as e:
        logger.error(f"Error inesperado durante la migración: {e}")
        logger.exception("Stacktrace completo:")
        return 1


if __name__ == "__main__":
    import asyncio
    sys.exit(main())