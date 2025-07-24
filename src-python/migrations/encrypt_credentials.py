#!/usr/bin/env python3
"""
Script de migración para encriptar credenciales existentes.

Este script:
1. Hace backup de la base de datos
2. Migra del servicio de encriptación v1 al v2
3. Re-encripta todas las credenciales con el nuevo sistema
4. Verifica la integridad de los datos
5. Genera reporte de migración
"""
import asyncio
import sqlite3
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys
import argparse

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.encryption_service import encryption_service as encryption_v1
from services.encryption_service_v2 import encryption_service_v2
from services.logging_service import get_secure_logger, log_audit
from utils.sanitizers import sanitize_config


logger = get_secure_logger(__name__)


class CredentialsMigration:
    """Gestiona la migración de credenciales al nuevo sistema de encriptación."""
    
    def __init__(self, db_path: str, backup_dir: Optional[str] = None):
        """
        Inicializa la migración.
        
        Args:
            db_path: Ruta a la base de datos
            backup_dir: Directorio para backups (opcional)
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir) if backup_dir else self.db_path.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Estadísticas
        self.stats = {
            'total_credentials': 0,
            'migrated': 0,
            'failed': 0,
            'already_v2': 0,
            'errors': []
        }
        
    def create_backup(self) -> Path:
        """
        Crea un backup de la base de datos.
        
        Returns:
            Path al archivo de backup
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"cameras_backup_{timestamp}.db"
        
        logger.info(f"Creando backup en: {backup_path}")
        shutil.copy2(self.db_path, backup_path)
        
        # Verificar backup
        if backup_path.exists() and backup_path.stat().st_size > 0:
            logger.info("Backup creado exitosamente")
            return backup_path
        else:
            raise RuntimeError("Error creando backup")
            
    def analyze_credentials(self) -> Dict[str, List[Dict]]:
        """
        Analiza las credenciales actuales en la base de datos.
        
        Returns:
            Diccionario con análisis de credenciales
        """
        analysis = {
            'plain_text': [],      # Credenciales en texto plano
            'encrypted_v1': [],    # Encriptadas con v1
            'encrypted_v2': [],    # Ya migradas a v2
            'invalid': []          # Credenciales inválidas
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Obtener todas las credenciales
            cursor.execute("""
                SELECT 
                    credential_id,
                    camera_id,
                    credential_name,
                    username,
                    password_encrypted
                FROM camera_credentials
                ORDER BY camera_id, credential_id
            """)
            
            for row in cursor.fetchall():
                cred_info = {
                    'credential_id': row[0],
                    'camera_id': row[1],
                    'credential_name': row[2],
                    'username': row[3],
                    'has_password': bool(row[4])
                }
                
                password_encrypted = row[4]
                
                if not password_encrypted:
                    analysis['invalid'].append(cred_info)
                elif password_encrypted.startswith('v') and ':' in password_encrypted:
                    # Ya está en formato v2
                    analysis['encrypted_v2'].append(cred_info)
                else:
                    # Verificar si es v1 válido
                    try:
                        # Intentar desencriptar con v1
                        decrypted = encryption_v1.decrypt(password_encrypted)
                        if decrypted:
                            analysis['encrypted_v1'].append(cred_info)
                        else:
                            analysis['invalid'].append(cred_info)
                    except:
                        # Podría ser texto plano
                        if len(password_encrypted) < 100:  # Las encriptadas son más largas
                            analysis['plain_text'].append(cred_info)
                        else:
                            analysis['invalid'].append(cred_info)
                            
        finally:
            conn.close()
            
        # Log del análisis (sin información sensible)
        logger.info(f"Análisis de credenciales:")
        logger.info(f"  - Texto plano: {len(analysis['plain_text'])}")
        logger.info(f"  - Encriptadas v1: {len(analysis['encrypted_v1'])}")
        logger.info(f"  - Encriptadas v2: {len(analysis['encrypted_v2'])}")
        logger.info(f"  - Inválidas: {len(analysis['invalid'])}")
        
        return analysis
        
    async def migrate_credential(self, conn: sqlite3.Connection, 
                               cred_id: int, 
                               current_password: str,
                               is_plain_text: bool = False) -> bool:
        """
        Migra una credencial individual.
        
        Args:
            conn: Conexión a la base de datos
            cred_id: ID de la credencial
            current_password: Password actual (encriptado o plano)
            is_plain_text: Si el password está en texto plano
            
        Returns:
            True si la migración fue exitosa
        """
        try:
            # Desencriptar o usar directamente
            if is_plain_text:
                plain_password = current_password
            else:
                # Desencriptar con v1
                plain_password = encryption_v1.decrypt(current_password)
                
            # Re-encriptar con v2
            encrypted_v2 = encryption_service_v2.encrypt(plain_password)
            
            # Actualizar en la base de datos
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE camera_credentials
                SET password_encrypted = ?,
                    updated_at = datetime('now')
                WHERE credential_id = ?
            """, (encrypted_v2, cred_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error migrando credencial {cred_id}: {e}")
            self.stats['errors'].append({
                'credential_id': cred_id,
                'error': str(e)
            })
            return False
            
    async def migrate_all(self, dry_run: bool = False) -> Dict[str, any]:
        """
        Ejecuta la migración completa.
        
        Args:
            dry_run: Si True, solo simula sin hacer cambios
            
        Returns:
            Diccionario con resultados de la migración
        """
        logger.info(f"Iniciando migración {'(DRY RUN)' if dry_run else ''}")
        
        # Crear backup si no es dry run
        backup_path = None
        if not dry_run:
            backup_path = self.create_backup()
            
        # Analizar credenciales actuales
        analysis = self.analyze_credentials()
        
        # Calcular total a migrar
        to_migrate = len(analysis['plain_text']) + len(analysis['encrypted_v1'])
        self.stats['total_credentials'] = sum(len(v) for v in analysis.values())
        self.stats['already_v2'] = len(analysis['encrypted_v2'])
        
        if to_migrate == 0:
            logger.info("No hay credenciales para migrar")
            return self.stats
            
        logger.info(f"Credenciales a migrar: {to_migrate}")
        
        if dry_run:
            logger.info("Modo DRY RUN - No se realizarán cambios")
            self.stats['migrated'] = to_migrate
            return self.stats
            
        # Conectar a la base de datos
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Iniciar transacción
            conn.execute("BEGIN TRANSACTION")
            
            # Migrar credenciales en texto plano
            for cred in analysis['plain_text']:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT password_encrypted FROM camera_credentials WHERE credential_id = ?",
                    (cred['credential_id'],)
                )
                row = cursor.fetchone()
                
                if row and await self.migrate_credential(conn, cred['credential_id'], row[0], True):
                    self.stats['migrated'] += 1
                else:
                    self.stats['failed'] += 1
                    
            # Migrar credenciales v1
            for cred in analysis['encrypted_v1']:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT password_encrypted FROM camera_credentials WHERE credential_id = ?",
                    (cred['credential_id'],)
                )
                row = cursor.fetchone()
                
                if row and await self.migrate_credential(conn, cred['credential_id'], row[0], False):
                    self.stats['migrated'] += 1
                else:
                    self.stats['failed'] += 1
                    
            # Confirmar transacción
            conn.commit()
            logger.info("Migración completada exitosamente")
            
            # Registrar evento de auditoría
            log_audit('credentials_migration', {
                'total_migrated': self.stats['migrated'],
                'failed': self.stats['failed'],
                'backup_path': str(backup_path) if backup_path else None
            })
            
        except Exception as e:
            logger.error(f"Error durante la migración: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
        return self.stats
        
    def verify_migration(self) -> bool:
        """
        Verifica que la migración fue exitosa.
        
        Returns:
            True si todas las credenciales son válidas
        """
        logger.info("Verificando migración...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Verificar que todas las credenciales están en formato v2
            cursor.execute("""
                SELECT COUNT(*) 
                FROM camera_credentials 
                WHERE password_encrypted IS NOT NULL
                AND password_encrypted != ''
                AND NOT (password_encrypted LIKE 'v%:%')
            """)
            
            non_v2_count = cursor.fetchone()[0]
            
            if non_v2_count > 0:
                logger.warning(f"Encontradas {non_v2_count} credenciales no migradas")
                return False
                
            # Verificar que se pueden desencriptar
            cursor.execute("""
                SELECT credential_id, password_encrypted
                FROM camera_credentials
                WHERE password_encrypted IS NOT NULL
                LIMIT 10
            """)
            
            for row in cursor.fetchall():
                try:
                    decrypted = encryption_service_v2.decrypt(row[1])
                    if not decrypted:
                        logger.error(f"No se pudo desencriptar credencial {row[0]}")
                        return False
                except Exception as e:
                    logger.error(f"Error verificando credencial {row[0]}: {e}")
                    return False
                    
            logger.info("Verificación completada exitosamente")
            return True
            
        finally:
            conn.close()
            
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Genera un reporte de la migración.
        
        Args:
            output_path: Ruta para guardar el reporte (opcional)
            
        Returns:
            Contenido del reporte
        """
        report = {
            'migration_date': datetime.now().isoformat(),
            'database': str(self.db_path),
            'statistics': self.stats,
            'encryption_info': encryption_service_v2.get_key_info()
        }
        
        # Sanitizar errores en el reporte
        if self.stats['errors']:
            report['statistics']['errors'] = [
                sanitize_config(error) for error in self.stats['errors']
            ]
            
        report_json = json.dumps(report, indent=2, ensure_ascii=False)
        
        if output_path:
            output_file = Path(output_path)
            output_file.write_text(report_json, encoding='utf-8')
            logger.info(f"Reporte guardado en: {output_file}")
            
        return report_json


async def main():
    """Función principal del script de migración."""
    parser = argparse.ArgumentParser(
        description='Migra credenciales al nuevo sistema de encriptación'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        help='Ruta a la base de datos SQLite',
        default=str(Path(__file__).parent.parent / "data" / "camera_data.db")
    )
    parser.add_argument(
        '--backup-dir',
        type=str,
        help='Directorio para guardar backups',
        default=None
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula la migración sin hacer cambios'
    )
    parser.add_argument(
        '--report',
        type=str,
        help='Archivo para guardar el reporte de migración',
        default=None
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Solo verificar el estado actual sin migrar'
    )
    
    args = parser.parse_args()
    
    # Verificar que la base de datos existe
    if not Path(args.db_path).exists():
        logger.error(f"Base de datos no encontrada: {args.db_path}")
        return 1
        
    # Crear instancia de migración
    migration = CredentialsMigration(args.db_path, args.backup_dir)
    
    try:
        if args.verify_only:
            # Solo verificar
            analysis = migration.analyze_credentials()
            is_valid = migration.verify_migration()
            
            print("\n=== Estado actual de credenciales ===")
            print(f"Total: {sum(len(v) for v in analysis.values())}")
            print(f"Texto plano: {len(analysis['plain_text'])}")
            print(f"Encriptadas v1: {len(analysis['encrypted_v1'])}")
            print(f"Encriptadas v2: {len(analysis['encrypted_v2'])}")
            print(f"Inválidas: {len(analysis['invalid'])}")
            print(f"\nEstado de migración: {'✓ Completa' if is_valid else '✗ Incompleta'}")
            
        else:
            # Ejecutar migración
            stats = await migration.migrate_all(dry_run=args.dry_run)
            
            # Generar reporte
            report = migration.generate_report(args.report)
            
            # Mostrar resumen
            print("\n=== Resumen de migración ===")
            print(f"Total de credenciales: {stats['total_credentials']}")
            print(f"Ya migradas (v2): {stats['already_v2']}")
            print(f"Migradas ahora: {stats['migrated']}")
            print(f"Fallidas: {stats['failed']}")
            
            if not args.dry_run and stats['migrated'] > 0:
                # Verificar migración
                is_valid = migration.verify_migration()
                print(f"\nVerificación: {'✓ Exitosa' if is_valid else '✗ Falló'}")
                
        return 0
        
    except Exception as e:
        logger.error(f"Error en la migración: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Ejecutar migración
    exit_code = asyncio.run(main())
    sys.exit(exit_code)