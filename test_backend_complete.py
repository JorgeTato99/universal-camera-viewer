#!/usr/bin/env python3
"""
Script completo para probar el backend con la nueva estructura de base de datos.

Prueba:
1. Servidor FastAPI
2. Endpoints de cámaras
3. WebSocket streaming
4. Base de datos 3FN
"""
import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Configurar colores para Windows
import os
os.system('color')

# Colores ANSI
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


async def test_api_endpoints():
    """Prueba los endpoints principales de la API."""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print(f"\n{BLUE}=== Probando Endpoints API ==={RESET}")
        
        # 1. Verificar que el servidor está corriendo
        print(f"\n1. Verificando servidor en {base_url}...")
        try:
            async with session.get(f"{base_url}/") as resp:
                if resp.status == 200:
                    print(f"   {GREEN}✓ Servidor respondiendo correctamente{RESET}")
                else:
                    print(f"   {RED}✗ Servidor respondió con código {resp.status}{RESET}")
                    return False
        except aiohttp.ClientConnectorError:
            print(f"   {RED}✗ No se puede conectar al servidor{RESET}")
            print(f"   {YELLOW}Asegúrese de ejecutar: python run_api.py{RESET}")
            return False
        
        # 2. Probar endpoint de documentación
        print(f"\n2. Verificando documentación API...")
        async with session.get(f"{base_url}/docs") as resp:
            if resp.status == 200:
                print(f"   {GREEN}✓ Documentación Swagger disponible en {base_url}/docs{RESET}")
            else:
                print(f"   {RED}✗ Documentación no disponible{RESET}")
        
        # 3. Listar cámaras
        print(f"\n3. Listando cámaras desde /api/cameras...")
        async with session.get(f"{base_url}/api/cameras") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get('success'):
                    cameras = data.get('data', [])
                    print(f"   {GREEN}✓ Encontradas {len(cameras)} cámaras{RESET}")
                    for i, cam in enumerate(cameras[:3]):
                        print(f"     - {cam.get('name', 'Sin nombre')} ({cam.get('brand', 'N/A')}) - {cam.get('ip_address', 'N/A')}")
                    if len(cameras) > 3:
                        print(f"     ... y {len(cameras) - 3} más")
                else:
                    print(f"   {YELLOW}⚠ Respuesta sin éxito{RESET}")
            else:
                print(f"   {RED}✗ Error al listar cámaras: {resp.status}{RESET}")
        
        # 4. Obtener cámara específica
        print(f"\n4. Obteniendo detalle de cámara...")
        if cameras:
            camera_id = cameras[0].get('id')
            if camera_id:
                async with session.get(f"{base_url}/api/cameras/{camera_id}") as resp:
                    if resp.status == 200:
                        cam = await resp.json()
                        print(f"   {GREEN}✓ Cámara obtenida: {cam.get('name')}{RESET}")
                        print(f"     - Estado: {cam.get('status', 'N/A')}")
                        print(f"     - Protocolo: {cam.get('protocol', 'N/A')}")
                    else:
                        print(f"   {RED}✗ Error obteniendo cámara: {resp.status}{RESET}")
        
        # 5. Probar API v2 (nueva estructura)
        print(f"\n5. Probando API v2 con nueva estructura 3FN...")
        async with session.get(f"{base_url}/api/v2/cameras") as resp:
            if resp.status == 200:
                v2_data = await resp.json()
                v2_cameras = v2_data.get('data', [])
                print(f"   {GREEN}✓ API v2: {len(v2_cameras)} cámaras desde DB{RESET}")
            else:
                print(f"   {YELLOW}⚠ API v2 no disponible o sin datos{RESET}")
        
        # 6. Probar scanner
        print(f"\n6. Verificando endpoint de scanner...")
        async with session.get(f"{base_url}/api/scanner/status") as resp:
            if resp.status == 200:
                scanner_data = await resp.json()
                print(f"   {GREEN}✓ Scanner status: {scanner_data.get('status', 'N/A')}{RESET}")
            else:
                print(f"   {YELLOW}⚠ Scanner no disponible{RESET}")
        
        return True


async def test_websocket_connection():
    """Prueba la conexión WebSocket para streaming."""
    print(f"\n{BLUE}=== Probando WebSocket Streaming ==={RESET}")
    
    ws_url = "ws://localhost:8000/ws/stream/test_camera"
    
    try:
        import websockets
    except ImportError:
        print(f"   {YELLOW}⚠ Instalando websockets...{RESET}")
        os.system(f"{sys.executable} -m pip install websockets")
        import websockets
    
    print(f"\n1. Conectando a WebSocket en {ws_url}...")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"   {GREEN}✓ Conectado exitosamente{RESET}")
            
            # Enviar mensaje de inicio
            start_msg = {
                "action": "start_stream",
                "params": {
                    "quality": "medium",
                    "fps": 30,
                    "format": "jpeg"
                }
            }
            await websocket.send(json.dumps(start_msg))
            print(f"   {GREEN}✓ Mensaje de inicio enviado{RESET}")
            
            # Recibir algunos frames
            print("\n2. Recibiendo frames...")
            frames_received = 0
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'frame':
                        frames_received += 1
                        if frames_received <= 3:
                            print(f"   {GREEN}✓ Frame {frames_received} recibido - {len(data.get('data', ''))} bytes{RESET}")
                        if frames_received >= 5:
                            break
                except json.JSONDecodeError:
                    pass
            
            print(f"   {GREEN}✓ Total frames recibidos: {frames_received}{RESET}")
            
    except Exception as e:
        print(f"   {RED}✗ Error en WebSocket: {e}{RESET}")
        print(f"   {YELLOW}Nota: El streaming WebSocket requiere que el servidor esté ejecutándose{RESET}")


async def test_database_operations():
    """Prueba operaciones directas con la base de datos."""
    print(f"\n{BLUE}=== Probando Base de Datos 3FN ==={RESET}")
    
    # Agregar el path de src-python
    sys.path.insert(0, str(Path(__file__).parent / "src-python"))
    
    try:
        from services.data_service import get_data_service
        from services.camera_manager_service import camera_manager_service
        
        data_service = get_data_service()
        await data_service.initialize()
        
        print("\n1. Verificando cámaras en base de datos...")
        camera_ids = await data_service.get_all_camera_ids()
        print(f"   {GREEN}✓ Encontradas {len(camera_ids)} cámaras en DB{RESET}")
        
        print("\n2. Obteniendo configuración completa de una cámara...")
        if camera_ids:
            config = await data_service.get_camera_full_config(camera_ids[0])
            if config:
                print(f"   {GREEN}✓ Configuración obtenida exitosamente{RESET}")
                print(f"     - Cámara: {config.get('camera', {}).get('display_name', 'N/A')}")
                print(f"     - Protocolos: {len(config.get('protocols', []))}")
                print(f"     - Endpoints: {len(config.get('endpoints', []))}")
                print(f"     - Credenciales: {len(config.get('credentials', []))}")
        
        print("\n3. Verificando estadísticas...")
        stats = data_service.get_statistics()
        print(f"   {GREEN}✓ Estadísticas del servicio:{RESET}")
        print(f"     - Cámaras rastreadas: {stats.get('cameras_tracked', 0)}")
        print(f"     - Cache hits: {stats.get('cache_hits', 0)}")
        print(f"     - Cache misses: {stats.get('cache_misses', 0)}")
        
        await data_service.cleanup()
        
    except Exception as e:
        print(f"   {RED}✗ Error accediendo a base de datos: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def main():
    """Función principal de pruebas."""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}PRUEBA COMPLETA DEL BACKEND - UNIVERSAL CAMERA VIEWER{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Verificar que existe la base de datos
    db_path = Path("data/camera_data.db")
    if not db_path.exists():
        print(f"\n{RED}✗ ERROR: No se encuentra la base de datos{RESET}")
        print(f"{YELLOW}Ejecute los siguientes comandos:{RESET}")
        print("  1. python src-python/services/create_database.py")
        print("  2. python src-python/seed_database.py")
        return
    
    print(f"\n{GREEN}✓ Base de datos encontrada en {db_path}{RESET}")
    
    # Ejecutar pruebas
    tests_passed = 0
    total_tests = 3
    
    # 1. Probar endpoints API
    if await test_api_endpoints():
        tests_passed += 1
    
    # 2. Probar WebSocket
    try:
        await test_websocket_connection()
        tests_passed += 1
    except Exception as e:
        print(f"{RED}✗ Error en prueba WebSocket: {e}{RESET}")
    
    # 3. Probar base de datos
    try:
        await test_database_operations()
        tests_passed += 1
    except Exception as e:
        print(f"{RED}✗ Error en prueba de base de datos: {e}{RESET}")
    
    # Resumen
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}RESUMEN DE PRUEBAS{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    if tests_passed == total_tests:
        print(f"\n{GREEN}✓ TODAS LAS PRUEBAS PASARON ({tests_passed}/{total_tests}){RESET}")
    else:
        print(f"\n{YELLOW}⚠ Pruebas completadas: {tests_passed}/{total_tests}{RESET}")
    
    print(f"\n{BLUE}Próximos pasos:{RESET}")
    print("1. Si el servidor no está corriendo, ejecute: python run_api.py")
    print("2. Abra el navegador en http://localhost:8000/docs para ver la documentación")
    print("3. Para el frontend React, ejecute: yarn dev")
    print("4. Para streaming real, configure las credenciales de las cámaras")


if __name__ == "__main__":
    # Para Windows, habilitar colores ANSI
    if sys.platform == "win32":
        os.system("")
    
    asyncio.run(main())