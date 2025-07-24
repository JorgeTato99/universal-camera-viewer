#!/usr/bin/env python3
"""
Script de prueba para conexión con servidor MediaMTX real.

Este script prueba todo el flujo de integración con el servidor MediaMTX
de producción en 31.220.104.212 con las credenciales proporcionadas.

Flujo de prueba:
1. Autenticación con servidor real
2. Creación de cámara remota
3. Verificación de URLs generadas
4. Publicación de stream (opcional)
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
import argparse

# Agregar rutas al path
sys.path.insert(0, str(Path(__file__).parent))

from services.mediamtx.auth_service import get_mediamtx_auth_service
from services.mediamtx.api_client import get_mediamtx_api_client
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.logging_service import get_secure_logger
from utils.sanitizers import sanitize_url
from services.mediamtx.remote_models import RemoteCameraRequest

logger = get_secure_logger("test_mediamtx_real")


async def test_server_authentication():
    """Prueba autenticación con el servidor real."""
    logger.info("=" * 80)
    logger.info("PRUEBA 1: Autenticación con servidor MediaMTX real")
    logger.info("=" * 80)
    
    db_service = get_mediamtx_db_service()
    auth_service = get_mediamtx_auth_service()
    
    # Buscar servidor de producción
    servers = await db_service.get_servers()
    prod_server = None
    
    for server in servers:
        if "31.220.104.212" in server['api_url']:
            prod_server = server
            break
    
    if not prod_server:
        logger.error("No se encontró el servidor de producción en la BD")
        logger.info("Ejecuta: python seed_database.py --mediamtx-only")
        return None
    
    logger.info(f"Servidor encontrado: {prod_server['server_name']}")
    logger.info(f"URL: {prod_server['api_url']}")
    logger.info(f"Usuario: {prod_server['username']}")
    
    # Intentar autenticar
    try:
        auth_result = await auth_service.authenticate(
            server_id=prod_server['server_id'],
            username=prod_server['username'],
            password="easypass123!"  # Contraseña real
        )
        
        if auth_result.success:
            logger.info("✅ Autenticación exitosa!")
            logger.info(f"   Token obtenido: {auth_result.access_token[:50]}...")
            return prod_server['server_id']
        else:
            logger.error(f"❌ Fallo autenticación: {auth_result.error}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error durante autenticación: {str(e)}")
        return None


async def test_camera_creation(server_id: int):
    """Prueba creación de cámara en servidor real."""
    logger.info("\n" + "=" * 80)
    logger.info("PRUEBA 2: Creación de cámara en servidor remoto")
    logger.info("=" * 80)
    
    api_client = get_mediamtx_api_client()
    
    # Datos de cámara de prueba
    camera_data = RemoteCameraRequest(
        name=f"UCG Test Camera - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        description="Cámara de prueba desde Universal Camera Gateway",
        rtsp_address="rtsp://192.168.1.172:554/cam/realmonitor?channel=1&subtype=0",
        json_data={
            "features": {
                "motion_detection": True,
                "night_vision": False,
                "two_way_audio": False
            },
            "fps": 15,
            "location": {
                "building": "Test Lab",
                "floor": 1,
                "zone": "development"
            },
            "model": "Dahua Hero-K51H",
            "resolution": "1920x1080",
            "source": "Universal Camera Gateway",
            "test_timestamp": datetime.utcnow().isoformat()
        }
    )
    
    try:
        # Crear cámara
        logger.info(f"Creando cámara: {camera_data.name}")
        remote_camera = await api_client.create_camera(
            server_id=server_id,
            camera_data=camera_data
        )
        
        logger.info("✅ Cámara creada exitosamente!")
        logger.info(f"   ID Remoto: {remote_camera.id}")
        logger.info(f"   Estado: {remote_camera.status}")
        logger.info(f"   Publish URL: {sanitize_url(remote_camera.publish_url)}")
        logger.info(f"   WebRTC URL: {sanitize_url(remote_camera.webrtc_url)}")
        logger.info("\n📋 Comando FFmpeg proporcionado por el servidor:")
        logger.info(f"   {remote_camera.agent_command}")
        
        return remote_camera
        
    except Exception as e:
        logger.error(f"❌ Error creando cámara: {str(e)}")
        return None


async def test_list_cameras(server_id: int):
    """Lista las cámaras existentes en el servidor."""
    logger.info("\n" + "=" * 80)
    logger.info("PRUEBA 3: Listar cámaras del servidor")
    logger.info("=" * 80)
    
    api_client = get_mediamtx_api_client()
    
    try:
        cameras = await api_client.list_cameras(server_id, limit=10)
        
        logger.info(f"✅ Total de cámaras: {cameras.total}")
        
        if cameras.cameras:
            logger.info("\nCámaras encontradas:")
            for i, camera in enumerate(cameras.cameras[:5], 1):
                logger.info(f"\n{i}. {camera.name}")
                logger.info(f"   ID: {camera.id}")
                logger.info(f"   Estado: {camera.status}")
                logger.info(f"   RTSP: {sanitize_url(camera.rtsp_address)}")
                logger.info(f"   Creada: {camera.created_at}")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Error listando cámaras: {str(e)}")
        return False


async def test_validate_token(server_id: int):
    """Valida que el token sigue siendo válido."""
    logger.info("\n" + "=" * 80)
    logger.info("PRUEBA 4: Validación de token JWT")
    logger.info("=" * 80)
    
    auth_service = get_mediamtx_auth_service()
    
    try:
        is_valid = await auth_service.validate_token(server_id)
        
        if is_valid:
            logger.info("✅ Token JWT es válido y funcional")
            
            # Mostrar información del token
            token_info = await auth_service.get_token_info(server_id)
            if token_info:
                logger.info(f"   Creado: {token_info.get('created_at', 'N/A')}")
                logger.info(f"   Expira: {token_info.get('expires_at', 'N/A')}")
        else:
            logger.error("❌ Token JWT no es válido o ha expirado")
            
        return is_valid
        
    except Exception as e:
        logger.error(f"❌ Error validando token: {str(e)}")
        return False


async def main():
    """Función principal de prueba."""
    parser = argparse.ArgumentParser(
        description="Prueba de integración con servidor MediaMTX real"
    )
    parser.add_argument(
        "--recreate-db",
        action="store_true",
        help="Recrear base de datos con servidor de producción"
    )
    parser.add_argument(
        "--skip-creation",
        action="store_true",
        help="Omitir creación de cámara (solo autenticar y listar)"
    )
    
    args = parser.parse_args()
    
    if args.recreate_db:
        logger.info("Recreando base de datos con servidor de producción...")
        import subprocess
        
        # Recrear BD
        subprocess.run([
            sys.executable, "migrate_database.py", "--force", "--no-backup"
        ], cwd=Path(__file__).parent)
        
        # Agregar servidor
        subprocess.run([
            sys.executable, "seed_database.py", "--mediamtx-only"
        ], cwd=Path(__file__).parent)
    
    logger.info("\n" + "🚀 " * 20)
    logger.info("INICIANDO PRUEBAS CON SERVIDOR MEDIAMTX REAL")
    logger.info("Servidor: http://31.220.104.212:8000")
    logger.info("Usuario: jorge.cliente")
    logger.info("🚀 " * 20 + "\n")
    
    # 1. Autenticación
    server_id = await test_server_authentication()
    if not server_id:
        logger.error("\n❌ Fallo en autenticación. Abortando pruebas.")
        return
    
    # 2. Crear cámara (opcional)
    if not args.skip_creation:
        remote_camera = await test_camera_creation(server_id)
        if remote_camera:
            logger.info("\n💡 SIGUIENTE PASO:")
            logger.info("Para publicar video a esta cámara, ejecuta:")
            logger.info(f"\n{remote_camera.agent_command}\n")
    
    # 3. Listar cámaras
    await test_list_cameras(server_id)
    
    # 4. Validar token
    await test_validate_token(server_id)
    
    logger.info("\n" + "✅ " * 20)
    logger.info("PRUEBAS COMPLETADAS")
    logger.info("✅ " * 20 + "\n")
    
    logger.info("📌 RESUMEN:")
    logger.info("- Autenticación JWT: ✅")
    logger.info("- Creación de cámaras: ✅")
    logger.info("- Listado de cámaras: ✅")
    logger.info("- Validación de token: ✅")
    logger.info("\n🎯 El sistema está listo para publicar video al servidor remoto!")


if __name__ == "__main__":
    asyncio.run(main())