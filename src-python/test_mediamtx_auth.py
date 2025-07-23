#!/usr/bin/env python3
"""
Script de prueba para autenticación con servidor MediaMTX remoto.

Uso:
    python test_mediamtx_auth.py [--recreate-db]
    
Opciones:
    --recreate-db: Recrea la base de datos y agrega servidor de prueba
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent))

from services.logging_service import get_secure_logger
from services.mediamtx.auth_service import get_auth_service
from services.database.mediamtx_db_service import get_mediamtx_db_service
import subprocess


logger = get_secure_logger("test_mediamtx_auth")


async def test_authentication():
    """Prueba completa del flujo de autenticación."""
    
    print("\n" + "="*60)
    print("TEST DE AUTENTICACIÓN MEDIAMTX")
    print("="*60 + "\n")
    
    # Inicializar servicios
    auth_service = get_auth_service()
    db_service = get_mediamtx_db_service()
    
    try:
        # 1. Buscar servidor de prueba
        print("1. Buscando servidor MediaMTX de prueba...")
        servers = await db_service.get_all_servers()
        
        test_server = None
        for server in servers:
            if "Prueba" in server['server_name']:
                test_server = server
                break
        
        if not test_server:
            print("   ❌ No se encontró servidor de prueba")
            print("   💡 Ejecuta: python seed_database.py --mediamtx-only")
            return
        
        print(f"   ✅ Servidor encontrado: {test_server['server_name']}")
        print(f"      - ID: {test_server['server_id']}")
        print(f"      - API URL: {test_server['api_url']}")
        print(f"      - Usuario: {test_server['username']}")
        
        # 2. Verificar si ya hay token
        print("\n2. Verificando token existente...")
        existing_token = await auth_service.get_valid_token(test_server['server_id'])
        
        if existing_token:
            print("   ✅ Ya existe un token válido")
            print(f"      - Token: {existing_token[:20]}...")
            
            # Validar token
            print("\n3. Validando token con la API...")
            is_valid, error_msg = await auth_service.validate_token(
                test_server['server_id'],
                test_server['api_url']
            )
            
            if is_valid:
                print("   ✅ Token validado correctamente")
            else:
                print(f"   ❌ Token inválido: {error_msg}")
                print("   🔄 Procediendo con nuevo login...")
                existing_token = None
        else:
            print("   ℹ️  No hay token existente")
        
        # 3. Login si no hay token válido
        if not existing_token:
            print("\n3. Realizando login...")
            
            # Obtener contraseña desencriptada
            from services.encryption_service_v2 import EncryptionServiceV2
            encryption = EncryptionServiceV2()
            
            if test_server['password_encrypted']:
                password = encryption.decrypt(test_server['password_encrypted'])
            else:
                password = "easypass123!"  # Contraseña por defecto de prueba
            
            success, error = await auth_service.login(
                server_id=test_server['server_id'],
                username=test_server['username'],
                password=password,
                api_url=test_server['api_url']
            )
            
            if success:
                print("   ✅ Login exitoso")
                
                # Obtener token
                token = await auth_service.get_valid_token(test_server['server_id'])
                if token:
                    print(f"      - Token obtenido: {token[:20]}...")
                
                # Validar inmediatamente
                print("\n4. Validando token recién obtenido...")
                is_valid, error_msg = await auth_service.validate_token(
                    test_server['server_id'],
                    test_server['api_url']
                )
                
                if is_valid:
                    print("   ✅ Token validado correctamente")
                else:
                    print(f"   ❌ Error validando token: {error_msg}")
            else:
                print(f"   ❌ Error en login: {error}")
                return
        
        # 4. Probar headers de autenticación
        print("\n5. Obteniendo headers de autenticación...")
        headers = await auth_service.get_auth_headers(test_server['server_id'])
        
        if headers:
            print("   ✅ Headers generados:")
            for key, value in headers.items():
                if key == "Authorization":
                    print(f"      - {key}: {value[:30]}...")
                else:
                    print(f"      - {key}: {value}")
        else:
            print("   ❌ No se pudieron generar headers")
        
        # 5. Hacer petición de prueba directa
        print("\n6. Haciendo petición de prueba a la API...")
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            cameras_url = f"{test_server['api_url']}/api/v1/cameras"
            
            try:
                async with session.get(cameras_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("   ✅ Petición exitosa")
                        print(f"      - Cámaras en el servidor: {len(data.get('cameras', []))}")
                        
                        # Mostrar primeras 3 cámaras si hay
                        cameras = data.get('cameras', [])
                        if cameras:
                            print("\n   Primeras cámaras encontradas:")
                            for i, cam in enumerate(cameras[:3]):
                                print(f"      {i+1}. {cam.get('name', 'Sin nombre')} - {cam.get('source', 'Sin fuente')}")
                            if len(cameras) > 3:
                                print(f"      ... y {len(cameras) - 3} más")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Error en petición: {response.status}")
                        print(f"      - Respuesta: {error_text[:200]}")
                        
            except Exception as e:
                print(f"   ❌ Error de conexión: {str(e)}")
        
        print("\n" + "="*60)
        print("TEST COMPLETADO")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error en test: {str(e)}", exc_info=True)
        print(f"\n❌ ERROR FATAL: {str(e)}")
        
    finally:
        # Limpiar recursos
        await auth_service.cleanup()


async def recreate_database():
    """Recrea la base de datos con datos de prueba."""
    print("\n📦 Recreando base de datos...")
    
    try:
        # Ejecutar migrate_database.py
        result = subprocess.run(
            [sys.executable, "migrate_database.py", "--force", "--no-backup"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print(f"   ❌ Error migrando base de datos: {result.stderr}")
            return False
        
        print("   ✅ Base de datos migrada")
        
        # Ejecutar seed_database.py
        result = subprocess.run(
            [sys.executable, "seed_database.py", "--mediamtx-only"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print(f"   ❌ Error agregando datos de prueba: {result.stderr}")
            return False
        
        print("   ✅ Servidor MediaMTX de prueba agregado")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error recreando base de datos: {str(e)}")
        return False


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Test de autenticación MediaMTX"
    )
    parser.add_argument(
        "--recreate-db",
        action="store_true",
        help="Recrea la base de datos con servidor de prueba"
    )
    
    args = parser.parse_args()
    
    # Recrear base de datos si se solicita
    if args.recreate_db:
        if not asyncio.run(recreate_database()):
            sys.exit(1)
    
    # Ejecutar test
    try:
        asyncio.run(test_authentication())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error ejecutando test: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()