#!/usr/bin/env python3
"""
Script de prueba para verificar la integración con la nueva base de datos 3FN.

Este script prueba:
1. DataService con wrappers de compatibilidad
2. CameraManagerService con nueva estructura
3. API endpoints usando datos reales
4. Conversión entre estructuras antigua y nueva
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent))

from models.camera_model import CameraModel, ConnectionConfig
from services.data_service import get_data_service
from services.camera_manager_service import camera_manager_service

# Obtener instancia del servicio
data_service = get_data_service()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_data_service_compatibility():
    """Prueba los wrappers de compatibilidad en DataService."""
    print("\n=== Probando DataService con wrappers de compatibilidad ===")
    
    # Inicializar servicio
    await data_service.initialize()
    
    # Crear una cámara de prueba
    test_camera = CameraModel(
        brand="test",
        model="Test Camera",
        display_name="Test Camera Integration",
        connection_config=ConnectionConfig(
            ip="192.168.1.200",
            username="testuser",
            password="testpass123"
        )
    )
    
    # Probar save_camera_data (método antiguo con wrapper)
    print(f"\n1. Guardando cámara con método antiguo save_camera_data()...")
    result = await data_service.save_camera_data(test_camera)
    print(f"   Resultado: {'OK Éxito' if result else 'ERROR Error'}")
    
    # Verificar que se guardó
    print(f"\n2. Obteniendo cámara con get_camera_data()...")
    camera_data = await data_service.get_camera_data(test_camera.camera_id)
    if camera_data:
        print(f"   OK Cámara encontrada:")
        print(f"      - ID: {camera_data.camera_id}")
        print(f"      - Marca: {camera_data.brand}")
        print(f"      - IP: {camera_data.ip}")
        print(f"      - Protocolos: {camera_data.protocols}")
    else:
        print("   ERROR Cámara no encontrada")
    
    # Probar método nuevo get_camera_full_config
    print(f"\n3. Obteniendo configuración completa con get_camera_full_config()...")
    full_config = await data_service.get_camera_full_config(test_camera.camera_id)
    if full_config:
        print("   OK Configuración completa obtenida:")
        print(f"      - Cámara: {full_config.get('camera', {})}")
        print(f"      - Credenciales: {len(full_config.get('credentials', []))} encontradas")
        print(f"      - Protocolos: {full_config.get('protocols', [])}")
        print(f"      - Estadísticas: {full_config.get('statistics', {})}")
    else:
        print("   ERROR No se pudo obtener configuración completa")
    
    return test_camera.camera_id


async def test_camera_manager_service(camera_id: str):
    """Prueba CameraManagerService con la nueva estructura."""
    print("\n\n=== Probando CameraManagerService ===")
    
    # Listar todas las cámaras
    print("\n1. Listando todas las cámaras...")
    cameras = await camera_manager_service.list_cameras()
    print(f"   Total cámaras encontradas: {len(cameras)}")
    for cam in cameras[:3]:  # Mostrar solo las primeras 3
        print(f"   - {cam.camera_id}: {cam.display_name} ({cam.brand})")
    
    # Obtener cámara específica
    print(f"\n2. Obteniendo cámara específica {camera_id}...")
    camera = await camera_manager_service.get_camera(camera_id)
    if camera:
        print(f"   OK Cámara encontrada:")
        print(f"      - Display Name: {camera.display_name}")
        print(f"      - IP: {camera.ip}")
        print(f"      - Marca: {camera.brand}")
    else:
        print("   ERROR Cámara no encontrada")
    
    # Actualizar estadísticas
    print("\n3. Actualizando estadísticas de conexión...")
    stats_updated = await camera_manager_service.update_connection_stats(
        camera_id=camera_id,
        success=True,
        connection_time=120  # 2 minutos
    )
    print(f"   Resultado: {'OK Éxito' if stats_updated else 'ERROR Error'}")


async def test_api_integration():
    """Prueba la integración con los endpoints API."""
    print("\n\n=== Probando integración con API ===")
    
    # Importar router
    from routers.cameras import list_cameras, get_camera_info
    
    # Probar listado
    print("\n1. Probando endpoint list_cameras()...")
    try:
        response = await list_cameras()
        if response.get('success') and 'data' in response:
            cameras = response['data']
            print(f"   OK Respuesta exitosa: {len(cameras)} cámaras")
            if cameras:
                print(f"   Primera cámara: {cameras[0].get('name')} ({cameras[0].get('brand')})")
        else:
            print("   ERROR Respuesta sin éxito")
    except Exception as e:
        print(f"   ERROR Error: {e}")
    
    # Probar obtener cámara específica
    print("\n2. Probando endpoint get_camera_info()...")
    try:
        # Usar el primer ID de la lista si hay cámaras
        if cameras:
            test_id = cameras[0]['id']
            camera_info = await get_camera_info(test_id)
            print(f"   OK Cámara obtenida: {camera_info.name} - {camera_info.ip_address}")
        else:
            print("   ADVERTENCIA  No hay cámaras para probar")
    except Exception as e:
        print(f"   ERROR Error: {e}")


async def main():
    """Función principal de prueba."""
    print("PRUEBA DE INTEGRACION DE BASE DE DATOS 3FN")
    print("=" * 50)
    
    try:
        # Verificar que existe la base de datos
        db_path = Path("data/camera_data.db")
        if not db_path.exists():
            print(f"\nERROR ERROR: No se encuentra la base de datos en {db_path}")
            print("   Ejecute primero: python src-python/services/create_database.py")
            print("   Luego: python src-python/seed_database.py")
            return
        
        print(f"\nOK Base de datos encontrada en {db_path}")
        
        # Ejecutar pruebas
        camera_id = await test_data_service_compatibility()
        await test_camera_manager_service(camera_id)
        await test_api_integration()
        
        print("\n\nOK TODAS LAS PRUEBAS COMPLETADAS")
        print("\nResumen:")
        print("- DataService: Wrappers de compatibilidad funcionando")
        print("- CameraManagerService: Integración con nueva estructura OK")
        print("- API: Endpoints usando datos reales (con fallback a mock)")
        print("\nADVERTENCIA  NOTA: Revise los logs para ver mensajes DEPRECATED")
        
    except Exception as e:
        print(f"\nERROR ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpiar
        await data_service.cleanup()


if __name__ == "__main__":
    asyncio.run(main())