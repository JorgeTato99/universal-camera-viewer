#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos SEED de cámaras.

Incluye las 6 cámaras de prueba definidas en el proyecto.
"""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
import sys

# Agregar el directorio src-python al path
sys.path.insert(0, str(Path(__file__).parent))

from utils.id_generator import generate_camera_id
from services.encryption_service import encryption_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Clase para poblar la base de datos con datos de prueba."""
    
    def __init__(self, db_path: str = "data/camera_data.db"):
        """
        Inicializa el seeder.
        
        Args:
            db_path: Ruta a la base de datos
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
        
        # Habilitar claves foráneas
        self.cursor.execute("PRAGMA foreign_keys = ON")
    
    def seed_cameras(self) -> None:
        """Inserta las cámaras SEED en la base de datos."""
        
        # Datos de las 6 cámaras SEED
        cameras = [
            {
                "camera_id": generate_camera_id(),
                "code": "CAM-DAHUA-REAL-172",
                "brand": "dahua",
                "model": "Dahua IP Camera",
                "display_name": "Cámara Dahua Real",
                "ip_address": "192.168.1.172",
                "location": "Entrada Principal",
                "description": "Cámara real Dahua con capacidades ONVIF, RTSP y PTZ",
                "username": "admin",
                "password": "admin123",  # Contraseña de ejemplo
                "protocols": [
                    {"type": "ONVIF", "port": 80, "is_primary": True},
                    {"type": "RTSP", "port": 554}
                ],
                "capabilities": ["ptz", "onvif", "rtsp", "audio", "motion_detection"],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal",
                        "url": "rtsp://192.168.1.172:554/cam/realmonitor?channel=1&subtype=0"
                    },
                    {
                        "type": "rtsp_sub",
                        "name": "Stream Secundario",
                        "url": "rtsp://192.168.1.172:554/cam/realmonitor?channel=1&subtype=1"
                    },
                    {
                        "type": "snapshot",
                        "name": "Captura de Imagen",
                        "url": "http://192.168.1.172/cgi-bin/snapshot.cgi"
                    }
                ]
            },
            {
                "camera_id": generate_camera_id(),
                "code": "CAM-TPLINK-PATIO-101",
                "brand": "tplink",
                "model": "Tapo C200",
                "display_name": "Cámara Patio",
                "ip_address": "192.168.1.101",
                "location": "Patio",
                "description": "Cámara TP-Link con rotación 360° y detección de movimiento",
                "username": "admin",
                "password": "admin123",
                "protocols": [
                    {"type": "ONVIF", "port": 2020, "is_primary": True},
                    {"type": "RTSP", "port": 554}
                ],
                "capabilities": ["onvif", "rtsp", "ptz", "motion_detection"],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal",
                        "url": "rtsp://192.168.1.101:554/stream1"
                    },
                    {
                        "type": "rtsp_sub",
                        "name": "Stream Secundario",
                        "url": "rtsp://192.168.1.101:554/stream2"
                    }
                ]
            },
            {
                "camera_id": generate_camera_id(),
                "code": "CAM-STEREN-GARAJE-102",
                "brand": "steren",
                "model": "CCTV-240",
                "display_name": "Cámara Garaje",
                "ip_address": "192.168.1.102",
                "location": "Garaje",
                "description": "Cámara Steren básica con streaming RTSP",
                "username": "admin",
                "password": "admin",
                "protocols": [
                    {"type": "RTSP", "port": 5543, "is_primary": True},
                    {"type": "HTTP", "port": 80}
                ],
                "capabilities": ["rtsp", "http_api"],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal",
                        "url": "rtsp://192.168.1.102:5543/live/ch00_0"
                    },
                    {
                        "type": "snapshot",
                        "name": "Captura HTTP",
                        "url": "http://192.168.1.102/snapshot.jpg"
                    }
                ]
            },
            {
                "camera_id": generate_camera_id(),
                "code": "CAM-HIKVISION-ENTRADA-103",
                "brand": "hikvision",
                "model": "DS-2CD2043G2-I",
                "display_name": "Cámara Entrada Principal",
                "ip_address": "192.168.1.103",
                "location": "Entrada Principal",
                "description": "Cámara Hikvision profesional con AI y visión nocturna",
                "username": "admin",
                "password": "admin12345",
                "protocols": [
                    {"type": "ONVIF", "port": 80, "is_primary": True},
                    {"type": "RTSP", "port": 554}
                ],
                "capabilities": ["onvif", "rtsp", "ptz", "face_detection", "motion_detection", "ir"],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal H.265",
                        "url": "rtsp://192.168.1.103:554/Streaming/Channels/101"
                    },
                    {
                        "type": "rtsp_sub",
                        "name": "Stream Secundario",
                        "url": "rtsp://192.168.1.103:554/Streaming/Channels/102"
                    },
                    {
                        "type": "snapshot",
                        "name": "Captura ISAPI",
                        "url": "http://192.168.1.103/ISAPI/Streaming/channels/101/picture"
                    }
                ]
            },
            {
                "camera_id": generate_camera_id(),
                "code": "CAM-XIAOMI-PASILLO-104",
                "brand": "xiaomi",
                "model": "Mi Home Security 360",
                "display_name": "Cámara Pasillo",
                "ip_address": "192.168.1.104",
                "location": "Pasillo",
                "description": "Cámara Xiaomi con visión 360° y app móvil",
                "username": "admin",
                "password": "admin",
                "protocols": [
                    {"type": "RTSP", "port": 554, "is_primary": True},
                    {"type": "HTTP", "port": 80}
                ],
                "capabilities": ["rtsp", "http_api", "ptz", "audio"],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal",
                        "url": "rtsp://192.168.1.104:554/live/ch0"
                    },
                    {
                        "type": "mjpeg",
                        "name": "Stream MJPEG",
                        "url": "http://192.168.1.104/mjpeg"
                    }
                ]
            },
            {
                "camera_id": generate_camera_id(),
                "code": "CAM-REOLINK-JARDIN-105",
                "brand": "reolink",
                "model": "RLC-810A",
                "display_name": "Cámara Jardín Trasero",
                "ip_address": "192.168.1.105",
                "location": "Jardín Trasero",
                "description": "Cámara Reolink 4K con PoE y detección de personas/vehículos",
                "username": "admin",
                "password": "admin123",
                "protocols": [
                    {"type": "ONVIF", "port": 8000, "is_primary": True},
                    {"type": "RTSP", "port": 554}
                ],
                "capabilities": ["onvif", "rtsp", "face_detection", "motion_detection", "h265"],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal 4K",
                        "url": "rtsp://192.168.1.105:554/h264Preview_01_main"
                    },
                    {
                        "type": "rtsp_sub",
                        "name": "Stream Secundario",
                        "url": "rtsp://192.168.1.105:554/h264Preview_01_sub"
                    },
                    {
                        "type": "snapshot",
                        "name": "Captura API",
                        "url": "http://192.168.1.105/cgi-bin/api.cgi?cmd=Snap&channel=0"
                    }
                ]
            }
        ]
        
        # Insertar cada cámara
        for idx, camera_data in enumerate(cameras, 1):
            try:
                logger.info(f"Insertando cámara {idx}/6: {camera_data['display_name']}")
                
                # 1. Insertar cámara principal
                self.cursor.execute("""
                    INSERT INTO cameras (
                        camera_id, code, brand, model, display_name,
                        ip_address, location, description, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    camera_data['camera_id'],
                    camera_data['code'],
                    camera_data['brand'],
                    camera_data['model'],
                    camera_data['display_name'],
                    camera_data['ip_address'],
                    camera_data['location'],
                    camera_data['description']
                ))
                
                # 2. Insertar credenciales
                encrypted_password = encryption_service.encrypt(camera_data['password'])
                self.cursor.execute("""
                    INSERT INTO camera_credentials (
                        camera_id, credential_name, username, password_encrypted,
                        auth_type, is_default, is_active
                    ) VALUES (?, ?, ?, ?, 'basic', 1, 1)
                """, (
                    camera_data['camera_id'],
                    'Credencial Principal',
                    camera_data['username'],
                    encrypted_password
                ))
                credential_id = self.cursor.lastrowid
                
                # 3. Insertar protocolos
                for protocol in camera_data['protocols']:
                    self.cursor.execute("""
                        INSERT INTO camera_protocols (
                            camera_id, protocol_type, port, is_enabled, is_primary
                        ) VALUES (?, ?, ?, 1, ?)
                    """, (
                        camera_data['camera_id'],
                        protocol['type'],
                        protocol['port'],
                        protocol.get('is_primary', False)
                    ))
                    
                    if protocol.get('is_primary'):
                        primary_protocol_id = self.cursor.lastrowid
                
                # 4. Insertar capacidades
                for capability in camera_data['capabilities']:
                    self.cursor.execute("""
                        INSERT INTO camera_capabilities (
                            camera_id, capability_type, capability_name, is_supported
                        ) VALUES (?, ?, ?, 1)
                    """, (
                        camera_data['camera_id'],
                        capability,
                        capability.replace('_', ' ').title()
                    ))
                
                # 5. Insertar endpoints
                for endpoint in camera_data['endpoints']:
                    self.cursor.execute("""
                        INSERT INTO camera_endpoints (
                            camera_id, endpoint_type, endpoint_name, url,
                            protocol_id, credential_id, is_verified, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 1)
                    """, (
                        camera_data['camera_id'],
                        endpoint['type'],
                        endpoint['name'],
                        endpoint['url'],
                        primary_protocol_id if 'rtsp' in endpoint['type'] else None,
                        credential_id
                    ))
                
                # 6. Crear perfil de streaming por defecto
                self.cursor.execute("""
                    INSERT INTO stream_profiles (
                        camera_id, profile_name, stream_type, encoding,
                        resolution, framerate, bitrate, quality, is_default
                    ) VALUES (?, ?, 'main', 'H264', '1920x1080', 25, 4096, 'high', 1)
                """, (
                    camera_data['camera_id'],
                    'Perfil Principal'
                ))
                
                logger.info(f"✅ Cámara {camera_data['display_name']} insertada exitosamente")
                
            except Exception as e:
                logger.error(f"Error insertando cámara {camera_data['display_name']}: {e}")
                self.conn.rollback()
                raise
        
        # Confirmar cambios
        self.conn.commit()
        logger.info("✅ Todas las cámaras SEED insertadas exitosamente")
    
    def verify_seed_data(self) -> None:
        """Verifica que los datos se insertaron correctamente."""
        
        # Contar cámaras
        self.cursor.execute("SELECT COUNT(*) FROM cameras")
        camera_count = self.cursor.fetchone()[0]
        
        # Obtener lista de cámaras
        self.cursor.execute("""
            SELECT c.camera_id, c.code, c.brand, c.model, c.display_name, c.ip_address,
                   COUNT(DISTINCT cr.credential_id) as cred_count,
                   COUNT(DISTINCT cp.protocol_id) as proto_count,
                   COUNT(DISTINCT ce.endpoint_id) as endpoint_count
            FROM cameras c
            LEFT JOIN camera_credentials cr ON c.camera_id = cr.camera_id
            LEFT JOIN camera_protocols cp ON c.camera_id = cp.camera_id
            LEFT JOIN camera_endpoints ce ON c.camera_id = ce.camera_id
            GROUP BY c.camera_id
        """)
        
        cameras = self.cursor.fetchall()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"VERIFICACIÓN DE DATOS SEED")
        logger.info(f"{'='*80}")
        logger.info(f"Total de cámaras: {camera_count}")
        logger.info(f"\nDetalle de cámaras:")
        
        for camera in cameras:
            logger.info(f"\n📷 {camera[4]} ({camera[2].upper()} {camera[3]})")
            logger.info(f"   - Código: {camera[1]}")
            logger.info(f"   - IP: {camera[5]}")
            logger.info(f"   - Credenciales: {camera[6]}")
            logger.info(f"   - Protocolos: {camera[7]}")
            logger.info(f"   - Endpoints: {camera[8]}")
        
        logger.info(f"\n{'='*80}")
    
    def close(self) -> None:
        """Cierra la conexión a la base de datos."""
        self.conn.close()


def main():
    """Función principal del script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Poblar base de datos con cámaras SEED')
    parser.add_argument('--verify-only', action='store_true', 
                       help='Solo verificar datos existentes sin insertar')
    parser.add_argument('--path', default='data/camera_data.db',
                       help='Ruta de la base de datos')
    
    args = parser.parse_args()
    
    try:
        seeder = DatabaseSeeder(args.path)
        
        if args.verify_only:
            seeder.verify_seed_data()
        else:
            # Verificar si ya hay datos
            seeder.cursor.execute("SELECT COUNT(*) FROM cameras")
            if seeder.cursor.fetchone()[0] > 0:
                response = input("⚠️  Ya hay cámaras en la base de datos. ¿Continuar? (s/n): ")
                if response.lower() != 's':
                    print("Operación cancelada")
                    return
            
            # Insertar datos SEED
            seeder.seed_cameras()
            
            # Verificar
            seeder.verify_seed_data()
        
        seeder.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()