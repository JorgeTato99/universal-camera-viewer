#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de publicación remota MediaMTX.

Este script prueba el flujo completo:
1. Autenticación con servidor MediaMTX
2. Crear/registrar cámara remota
3. Iniciar publicación FFmpeg
4. Verificar estado
5. Detener publicación
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Agregar src-python al path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from services.logging_service import get_secure_logger
from presenters.mediamtx_remote_publishing_presenter import (
    get_mediamtx_remote_publishing_presenter
)
from presenters.mediamtx_auth_presenter import get_mediamtx_auth_presenter
from services.database import get_database_service


logger = get_secure_logger("test_remote_publishing")


async def test_remote_publishing(recreate_db: bool = False):
    """
    Prueba el flujo completo de publicación remota.
    
    Args:
        recreate_db: Si True, recrea la base de datos con datos de prueba
    """
    try:
        # Inicializar base de datos si es necesario
        if recreate_db:
            logger.info("Recreando base de datos con servidor de prueba...")
            
            # Ejecutar migrate_database
            import subprocess
            result = subprocess.run(
                [sys.executable, "migrate_database.py", "--force", "--no-backup"],
                cwd=src_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"Error migrando BD: {result.stderr}")
                return
            
            # Ejecutar seed_database
            result = subprocess.run(
                [sys.executable, "seed_database.py", "--mediamtx-only"],
                cwd=src_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"Error sembrando BD: {result.stderr}")
                return
            
            logger.info("Base de datos recreada exitosamente")
        
        # Inicializar servicios
        db_service = get_database_service()
        await db_service.initialize()
        
        # Obtener presenters
        auth_presenter = get_mediamtx_auth_presenter()
        await auth_presenter.initialize()
        
        remote_presenter = get_mediamtx_remote_publishing_presenter()
        await remote_presenter.initialize()
        
        # Paso 1: Verificar servidor MediaMTX disponible
        logger.info("\n=== Paso 1: Verificando servidor MediaMTX ===")
        servers = await db_service.get_mediamtx_servers()
        
        if not servers:
            logger.error("No hay servidores MediaMTX configurados")
            return
        
        server = servers[0]
        server_id = server['server_id']
        logger.info(f"Servidor encontrado: {server['server_name']} (ID: {server_id})")
        
        # Paso 2: Autenticar con servidor
        logger.info("\n=== Paso 2: Autenticando con servidor ===")
        auth_result = await auth_presenter.authenticate_with_server(
            server_id=server_id,
            username="jorge.cliente",
            password="easypass123!"
        )
        
        if not auth_result.get('success'):
            logger.error(f"Error autenticando: {auth_result.get('error')}")
            return
        
        logger.info("Autenticación exitosa")
        
        # Paso 3: Verificar cámaras disponibles
        logger.info("\n=== Paso 3: Verificando cámaras locales ===")
        cameras = await db_service.get_all_cameras()
        
        if not cameras:
            logger.error("No hay cámaras configuradas")
            return
        
        camera = cameras[0]
        camera_id = camera['camera_id']
        logger.info(f"Usando cámara: {camera.get('display_name', camera_id)}")
        
        # Paso 4: Iniciar publicación remota
        logger.info("\n=== Paso 4: Iniciando publicación remota ===")
        start_result = await remote_presenter.start_remote_stream(
            camera_id=camera_id,
            server_id=server_id,
            custom_name="Test Remote Camera",
            custom_description="Cámara de prueba para publicación remota"
        )
        
        if not start_result.get('success'):
            logger.error(f"Error iniciando stream: {start_result.get('error')}")
            return
        
        logger.info("Stream remoto iniciado exitosamente")
        logger.info(f"URL de publicación: {start_result.get('publish_url')}")
        logger.info(f"URL WebRTC: {start_result.get('webrtc_url')}")
        
        # Paso 5: Verificar estado
        logger.info("\n=== Paso 5: Verificando estado del stream ===")
        await asyncio.sleep(2)  # Esperar un momento para que se estabilice
        
        status = await remote_presenter.get_remote_stream_status(camera_id)
        if status.get('is_streaming'):
            logger.info("Stream activo y funcionando")
            stream_info = status.get('stream_info', {})
            logger.info(f"Duración: {stream_info.get('duration', 0)} segundos")
        else:
            logger.warning("Stream no está activo")
        
        # Paso 6: Listar streams activos
        logger.info("\n=== Paso 6: Listando streams activos ===")
        streams = await remote_presenter.list_remote_streams()
        logger.info(f"Streams activos: {len(streams)}")
        for stream in streams:
            logger.info(f"  - Cámara {stream['camera_id']} -> {stream.get('publish_url')}")
        
        # Esperar un poco antes de detener
        logger.info("\n⏳ Esperando 5 segundos antes de detener...")
        await asyncio.sleep(5)
        
        # Paso 7: Detener publicación
        logger.info("\n=== Paso 7: Deteniendo publicación ===")
        stop_result = await remote_presenter.stop_remote_stream(camera_id)
        
        if stop_result.get('success'):
            logger.info("Stream detenido correctamente")
        else:
            logger.error(f"Error deteniendo stream: {stop_result.get('error')}")
        
        # Verificar que se detuvo
        status = await remote_presenter.get_remote_stream_status(camera_id)
        if not status.get('is_streaming'):
            logger.info("✅ Stream confirmado como detenido")
        else:
            logger.warning("⚠️ Stream aún aparece como activo")
        
        logger.info("\n=== Prueba completada exitosamente ===")
        
    except Exception as e:
        logger.error(f"Error durante la prueba: {str(e)}", exc_info=True)
        
    finally:
        # Cleanup
        try:
            if 'auth_presenter' in locals():
                await auth_presenter.cleanup()
            if 'remote_presenter' in locals():
                await remote_presenter.cleanup()
            if 'db_service' in locals():
                await db_service.cleanup()
        except:
            pass


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Prueba la funcionalidad de publicación remota MediaMTX"
    )
    parser.add_argument(
        "--recreate-db",
        action="store_true",
        help="Recrear base de datos con datos de prueba"
    )
    
    args = parser.parse_args()
    
    # Ejecutar prueba
    asyncio.run(test_remote_publishing(args.recreate_db))


if __name__ == "__main__":
    main()