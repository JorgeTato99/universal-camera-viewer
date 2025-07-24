#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos SEED de cámaras.

Incluye las 6 cámaras de prueba definidas en el proyecto.
"""
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Agregar el directorio src-python al path
sys.path.insert(0, str(Path(__file__).parent))

from services.encryption_service_v2 import EncryptionServiceV2
from utils.id_generator import generate_camera_id

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

    def clear_existing_data(self) -> None:
        """Limpia todos los datos existentes en orden correcto."""
        try:
            # Deshabilitar temporalmente las claves foráneas
            self.cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Orden de eliminación (respetando dependencias)
            tables_to_clear = [
                # Tablas de MediaMTX (dependientes primero)
                "publication_viewers",
                "publication_metrics",
                "publication_history",
                "camera_publications",
                "mediamtx_auth_tokens",
                "mediamtx_paths",
                "mediamtx_servers",
                # Tablas de cámaras
                "camera_events",
                "recordings",
                "snapshots",
                "scan_results",
                "network_scans",
                "connection_logs",
                "camera_statistics",
                "stream_profiles",
                "camera_capabilities",
                "camera_endpoints",
                "camera_protocols",
                "camera_credentials",
                "cameras"
            ]
            
            for table in tables_to_clear:
                self.cursor.execute(f"DELETE FROM {table}")
                logger.info(f"Tabla {table} limpiada")
            
            # Resetear secuencias
            self.cursor.execute("DELETE FROM sqlite_sequence")
            
            # Re-habilitar claves foráneas
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            self.conn.commit()
            logger.info("[OK] Todas las tablas han sido limpiadas")
            
        except Exception as e:
            logger.error(f"Error limpiando tablas: {e}")
            raise
    
    def seed_cameras(self, clear_first: bool = False) -> None:
        """Inserta las cámaras SEED en la base de datos.
        
        Args:
            clear_first: Si True, limpia todos los datos antes de insertar
        """
        if clear_first:
            logger.info("Limpiando datos existentes...")
            self.clear_existing_data()

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
                "password": "3gfwb3ToWfeWNqm22223DGbzcH-4si",  # Contraseña de ejemplo
                "protocols": [
                    {"type": "ONVIF", "port": 80, "is_primary": True},
                    {"type": "RTSP", "port": 554},
                ],
                "capabilities": ["ptz", "onvif", "rtsp", "audio", "motion_detection"],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal",
                        "url": "rtsp://192.168.1.172:554/cam/realmonitor?channel=1&subtype=0",
                    },
                    {
                        "type": "rtsp_sub",
                        "name": "Stream Secundario",
                        "url": "rtsp://192.168.1.172:554/cam/realmonitor?channel=1&subtype=1",
                    },
                    {
                        "type": "snapshot",
                        "name": "Captura de Imagen",
                        "url": "http://192.168.1.172/cgi-bin/snapshot.cgi",
                    },
                ],
            },
            {
                "camera_id": generate_camera_id(),
                "code": "CAM-TPLINK-TAPO-C520WS-77",
                "brand": "tplink",
                "model": "Tapo C520WS",
                "display_name": "Cámara TP-Link C520WS Exterior 2K",
                "ip_address": "192.168.1.77",
                "mac_address": "F0:A7:31:D8:64:E8",
                "location": "Exterior",
                "description": "Cámara TP-Link Tapo C520WS 2K con 3 perfiles ONVIF, visión nocturna y WiFi",
                "username": "admin-tato",
                "password": "mUidGT87gMxg8ce!Wxso3Guu8t.3*Q",
                "protocols": [
                    {"type": "ONVIF", "port": 2020, "is_primary": True},
                    {"type": "RTSP", "port": 554},
                    {"type": "HTTPS", "port": 443},
                ],
                "capabilities": [
                    "onvif",
                    "rtsp", 
                    "https", 
                    "motion_detection", 
                    "night_vision", 
                    "wifi",
                    "h264",
                    "mjpeg",
                    "2k_resolution"
                ],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "mainStream - 2K HD (2560x1440)",
                        "url": "rtsp://192.168.1.77:554/stream1",
                    },
                    {
                        "type": "rtsp_sub",
                        "name": "minorStream - SD (640x360)",
                        "url": "rtsp://192.168.1.77:554/stream2",
                    },
                    {
                        "type": "rtsp_jpeg",
                        "name": "jpegStream - MJPEG (640x360)",
                        "url": "rtsp://192.168.1.77:554/stream8",
                    },
                    {
                        "type": "onvif_media",
                        "name": "ONVIF Media Service",
                        "url": "http://192.168.1.77:2020/onvif/device_service",
                    },
                    {
                        "type": "https_api",
                        "name": "API HTTPS",
                        "url": "https://192.168.1.77:443/",
                    },
                ],
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
                    {"type": "HTTP", "port": 80},
                ],
                "capabilities": ["rtsp", "http_api"],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal",
                        "url": "rtsp://192.168.1.102:5543/live/ch00_0",
                    },
                    {
                        "type": "snapshot",
                        "name": "Captura HTTP",
                        "url": "http://192.168.1.102/snapshot.jpg",
                    },
                ],
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
                    {"type": "RTSP", "port": 554},
                ],
                "capabilities": [
                    "onvif",
                    "rtsp",
                    "ptz",
                    "face_detection",
                    "motion_detection",
                    "ir",
                ],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal H.265",
                        "url": "rtsp://192.168.1.103:554/Streaming/Channels/101",
                    },
                    {
                        "type": "rtsp_sub",
                        "name": "Stream Secundario",
                        "url": "rtsp://192.168.1.103:554/Streaming/Channels/102",
                    },
                    {
                        "type": "snapshot",
                        "name": "Captura ISAPI",
                        "url": "http://192.168.1.103/ISAPI/Streaming/channels/101/picture",
                    },
                ],
            },
            {
                "camera_id": generate_camera_id(),
                "code": "CAM-TPLINK-C200-248",
                "brand": "tplink",
                "model": "C200",
                "display_name": "Cámara TP-Link C200 Interior",
                "ip_address": "192.168.100.248",
                "mac_address": "",  # Por completar si lo conoces
                "firmware_version": "",  # Por completar si lo conoces
                "location": "Interior",
                "description": "Cámara TP-Link C200 HD con PTZ, visión nocturna y audio bidireccional",
                "username": "superadmin",
                "password": "superadmin",
                "protocols": [
                    {"type": "RTSP", "port": 554, "is_primary": True},
                    {"type": "ONVIF", "port": 2020},  # Puerto típico ONVIF para TP-Link
                    {"type": "HTTP", "port": 80},
                ],
                "capabilities": [
                    "rtsp", 
                    "onvif",
                    "http_api", 
                    "ptz",  # La C200 tiene PTZ
                    "audio",  # Confirmado por FFmpeg output
                    "motion_detection",  # Típicamente incluida
                    "night_vision",  # Típicamente incluida
                    "h264",  # Confirmado por FFmpeg output
                    "two_way_audio"  # Típico en C200
                ],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal HD (1280x720)",
                        "url": "rtsp://192.168.100.248:554/stream1",
                    },
                    {
                        "type": "rtsp_sub",
                        "name": "Stream Secundario SD (640x360)",
                        "url": "rtsp://192.168.100.248:554/stream2",
                    },
                    {
                        "type": "onvif_device",
                        "name": "ONVIF Device Service",
                        "url": "http://192.168.100.248:2020/onvif/device_service",
                    },
                    {
                        "type": "snapshot",
                        "name": "Captura HTTP",
                        "url": "http://192.168.100.248/capture",  # URL típica, verificar
                    },
                ],
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
                    {"type": "RTSP", "port": 554},
                ],
                "capabilities": [
                    "onvif",
                    "rtsp",
                    "face_detection",
                    "motion_detection",
                    "h265",
                ],
                "endpoints": [
                    {
                        "type": "rtsp_main",
                        "name": "Stream Principal 4K",
                        "url": "rtsp://192.168.1.105:554/h264Preview_01_main",
                    },
                    {
                        "type": "rtsp_sub",
                        "name": "Stream Secundario",
                        "url": "rtsp://192.168.1.105:554/h264Preview_01_sub",
                    },
                    {
                        "type": "snapshot",
                        "name": "Captura API",
                        "url": "http://192.168.1.105/cgi-bin/api.cgi?cmd=Snap&channel=0",
                    },
                ],
            },
        ]

        # Insertar cada cámara
        for idx, camera_data in enumerate(cameras, 1):
            try:
                logger.info(f"Insertando cámara {idx}/6: {camera_data['display_name']}")

                # 1. Insertar cámara principal
                self.cursor.execute(
                    """
                    INSERT INTO cameras (
                        camera_id, code, brand, model, display_name,
                        ip_address, mac_address, firmware_version, location, 
                        description, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                    (
                        camera_data["camera_id"],
                        camera_data["code"],
                        camera_data["brand"],
                        camera_data["model"],
                        camera_data["display_name"],
                        camera_data["ip_address"],
                        camera_data.get("mac_address") or None,
                        camera_data.get("firmware_version") or None,
                        camera_data["location"],
                        camera_data["description"],
                    ),
                )

                # 2. Insertar credenciales
                encryption_service = EncryptionServiceV2()
                encrypted_password = encryption_service.encrypt(camera_data["password"])
                self.cursor.execute(
                    """
                    INSERT INTO camera_credentials (
                        camera_id, credential_name, username, password_encrypted,
                        auth_type, is_default, is_active
                    ) VALUES (?, ?, ?, ?, 'basic', 1, 1)
                """,
                    (
                        camera_data["camera_id"],
                        "Credencial Principal",
                        camera_data["username"],
                        encrypted_password,
                    ),
                )
                credential_id = self.cursor.lastrowid

                # 3. Insertar protocolos
                for protocol in camera_data["protocols"]:
                    self.cursor.execute(
                        """
                        INSERT INTO camera_protocols (
                            camera_id, protocol_type, port, is_enabled, is_primary
                        ) VALUES (?, ?, ?, 1, ?)
                    """,
                        (
                            camera_data["camera_id"],
                            protocol["type"],
                            protocol["port"],
                            protocol.get("is_primary", False),
                        ),
                    )

                    if protocol.get("is_primary"):
                        primary_protocol_id = self.cursor.lastrowid

                # 4. Insertar capacidades
                for capability in camera_data["capabilities"]:
                    self.cursor.execute(
                        """
                        INSERT INTO camera_capabilities (
                            camera_id, capability_type, capability_name, is_supported
                        ) VALUES (?, ?, ?, 1)
                    """,
                        (
                            camera_data["camera_id"],
                            capability,
                            capability.replace("_", " ").title(),
                        ),
                    )

                # 5. Insertar endpoints
                for endpoint in camera_data["endpoints"]:
                    self.cursor.execute(
                        """
                        INSERT INTO camera_endpoints (
                            camera_id, endpoint_type, endpoint_name, url,
                            protocol_id, credential_id, is_verified, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 1)
                    """,
                        (
                            camera_data["camera_id"],
                            endpoint["type"],
                            endpoint["name"],
                            endpoint["url"],
                            primary_protocol_id if "rtsp" in endpoint["type"] else None,
                            credential_id,
                        ),
                    )

                # 6. Crear perfil de streaming por defecto
                self.cursor.execute(
                    """
                    INSERT INTO stream_profiles (
                        camera_id, profile_name, stream_type, encoding,
                        resolution, framerate, bitrate, quality, is_default
                    ) VALUES (?, ?, 'main', 'H264', '1920x1080', 25, 4096, 'high', 1)
                """,
                    (camera_data["camera_id"], "Perfil Principal"),
                )

                logger.info(
                    f"[OK] Camara {camera_data['display_name']} insertada exitosamente"
                )

            except Exception as e:
                logger.error(
                    f"Error insertando cámara {camera_data['display_name']}: {e}"
                )
                self.conn.rollback()
                raise

        # Confirmar cambios
        self.conn.commit()
        logger.info("[OK] Todas las camaras SEED insertadas exitosamente")

    def seed_mediamtx_server(self) -> None:
        """Inserta un servidor MediaMTX de prueba en la base de datos."""
        try:
            logger.info("Insertando servidor MediaMTX de producción...")
            
            # Datos del servidor MediaMTX real proporcionado por el equipo
            server_data = {
                "server_name": "MediaMTX Production Server",
                "rtsp_url": "rtsp://31.220.104.212",
                "rtsp_port": 8554,
                "api_url": "http://31.220.104.212:8000",
                "api_port": 8000,
                "api_enabled": True,
                "username": "jorge.cliente",
                "password": "easypass123!",
                "auth_enabled": True,
                "use_tcp": True,
                "max_reconnects": 3,
                "reconnect_delay": 5.0,
                "publish_path_template": "ucv_{camera_code}",
                "is_active": True,
                "is_default": True,
                "health_check_interval": 30,
                "last_health_status": "unknown",
                "metadata": json.dumps({
                    "description": "Servidor MediaMTX de producción - Integración real",
                    "location": "Cloud Server (31.220.104.212)",
                    "environment": "production",
                    "capabilities": ["rtsp", "rtmp", "webrtc", "api", "auth"],
                    "api_version": "v1",
                    "notes": "Servidor real con autenticación JWT y generación automática de comandos FFmpeg"
                })
            }
            
            # Encriptar contraseña
            if server_data["password"]:
                encryption_service = EncryptionServiceV2()
                encrypted_password = encryption_service.encrypt(server_data["password"])
            else:
                encrypted_password = None
            
            # Insertar servidor
            self.cursor.execute(
                """
                INSERT INTO mediamtx_servers (
                    server_name, rtsp_url, rtsp_port, api_url, api_port,
                    api_enabled, username, password_encrypted, auth_enabled,
                    use_tcp, max_reconnects, reconnect_delay, publish_path_template,
                    is_active, is_default, health_check_interval, last_health_status,
                    metadata, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    server_data["server_name"],
                    server_data["rtsp_url"],
                    server_data["rtsp_port"],
                    server_data["api_url"],
                    server_data["api_port"],
                    server_data["api_enabled"],
                    server_data["username"],
                    encrypted_password,
                    server_data["auth_enabled"],
                    server_data["use_tcp"],
                    server_data["max_reconnects"],
                    server_data["reconnect_delay"],
                    server_data["publish_path_template"],
                    server_data["is_active"],
                    server_data["is_default"],
                    server_data["health_check_interval"],
                    server_data["last_health_status"],
                    server_data["metadata"],
                    "seed_database.py"
                ),
            )
            
            self.conn.commit()
            logger.info("[OK] Servidor MediaMTX de prueba insertado exitosamente")
            
            # Verificar inserción
            self.cursor.execute("SELECT server_id, server_name FROM mediamtx_servers WHERE server_name = ?", (server_data["server_name"],))
            server = self.cursor.fetchone()
            if server:
                logger.info(f"   - ID: {server[0]}")
                logger.info(f"   - Nombre: {server[1]}")
                logger.info(f"   - API URL: {server_data['api_url']}")
                logger.info(f"   - Usuario: {server_data['username']}")
            
        except Exception as e:
            logger.error(f"Error insertando servidor MediaMTX: {e}")
            self.conn.rollback()
            raise

    def verify_seed_data(self) -> None:
        """Verifica que los datos se insertaron correctamente."""

        # Contar cámaras
        self.cursor.execute("SELECT COUNT(*) FROM cameras")
        camera_count = self.cursor.fetchone()[0]

        # Obtener lista de cámaras
        self.cursor.execute(
            """
            SELECT c.camera_id, c.code, c.brand, c.model, c.display_name, c.ip_address,
                   COUNT(DISTINCT cr.credential_id) as cred_count,
                   COUNT(DISTINCT cp.protocol_id) as proto_count,
                   COUNT(DISTINCT ce.endpoint_id) as endpoint_count
            FROM cameras c
            LEFT JOIN camera_credentials cr ON c.camera_id = cr.camera_id
            LEFT JOIN camera_protocols cp ON c.camera_id = cp.camera_id
            LEFT JOIN camera_endpoints ce ON c.camera_id = ce.camera_id
            GROUP BY c.camera_id
        """
        )

        cameras = self.cursor.fetchall()

        logger.info(f"\n{'='*80}")
        logger.info(f"VERIFICACIÓN DE DATOS SEED")
        logger.info(f"{'='*80}")
        logger.info(f"Total de cámaras: {camera_count}")
        logger.info(f"\nDetalle de cámaras:")

        for camera in cameras:
            logger.info(f"\n[CAMARA] {camera[4]} ({camera[2].upper()} {camera[3]})")
            logger.info(f"   - Código: {camera[1]}")
            logger.info(f"   - IP: {camera[5]}")
            logger.info(f"   - Credenciales: {camera[6]}")
            logger.info(f"   - Protocolos: {camera[7]}")
            logger.info(f"   - Endpoints: {camera[8]}")

        # Verificar servidores MediaMTX
        self.cursor.execute("SELECT COUNT(*) FROM mediamtx_servers")
        server_count = self.cursor.fetchone()[0]
        
        if server_count > 0:
            logger.info(f"\nServidores MediaMTX: {server_count}")
            
            self.cursor.execute(
                """
                SELECT server_id, server_name, api_url, is_active, is_default
                FROM mediamtx_servers
                """
            )
            servers = self.cursor.fetchall()
            
            for server in servers:
                logger.info(f"\n[SERVIDOR] {server[1]}")
                logger.info(f"   - ID: {server[0]}")
                logger.info(f"   - API URL: {server[2]}")
                logger.info(f"   - Activo: {'Sí' if server[3] else 'No'}")
                logger.info(f"   - Por defecto: {'Sí' if server[4] else 'No'}")

        logger.info(f"\n{'='*80}")

    def close(self) -> None:
        """Cierra la conexión a la base de datos."""
        self.conn.close()


def main():
    """Función principal del script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Poblar base de datos con cámaras SEED"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Solo verificar datos existentes sin insertar",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Limpiar todos los datos antes de insertar (CUIDADO: Elimina todo)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="No pedir confirmacion para operaciones peligrosas",
    )
    parser.add_argument(
        "--path", default="data/camera_data.db", help="Ruta de la base de datos"
    )
    parser.add_argument(
        "--mediamtx-only",
        action="store_true",
        help="Solo agregar servidor MediaMTX de prueba sin tocar las cámaras",
    )

    args = parser.parse_args()

    try:
        seeder = DatabaseSeeder(args.path)

        if args.verify_only:
            seeder.verify_seed_data()
        elif args.mediamtx_only:
            # Solo agregar servidor MediaMTX
            seeder.cursor.execute("SELECT COUNT(*) FROM mediamtx_servers WHERE server_name = ?", ("MediaMTX Remoto - Prueba",))
            if seeder.cursor.fetchone()[0] > 0:
                print("El servidor MediaMTX de prueba ya existe")
            else:
                print("Agregando servidor MediaMTX de prueba...")
                seeder.seed_mediamtx_server()
                print("Servidor MediaMTX agregado exitosamente")
            seeder.verify_seed_data()
        else:
            # Si se especifica --clear, limpiar primero
            if args.clear:
                if not args.force:
                    print("ADVERTENCIA: Esto eliminara TODOS los datos de la base de datos")
                    response = input("¿Esta seguro? (s/n): ")
                    if response.lower() != "s":
                        print("Operacion cancelada")
                        return
                seeder.seed_cameras(clear_first=True)
                seeder.seed_mediamtx_server()
            else:
                # Verificar si ya hay datos
                seeder.cursor.execute("SELECT COUNT(*) FROM cameras")
                if seeder.cursor.fetchone()[0] > 0:
                    print("ADVERTENCIA: Ya hay camaras en la base de datos.")
                    print("   Use --clear para limpiar primero, o responda 's' para agregar más cámaras")
                    response = input("¿Continuar agregando? (s/n): ")
                    if response.lower() != "s":
                        print("Operación cancelada")
                        print("Tip: Use 'python seed_database.py --clear' para limpiar y reinsertar")
                        return
                
                # Insertar datos SEED
                seeder.seed_cameras(clear_first=False)
            
            # Insertar servidor MediaMTX si no existe
            seeder.cursor.execute("SELECT COUNT(*) FROM mediamtx_servers")
            if seeder.cursor.fetchone()[0] == 0:
                logger.info("\nNo hay servidores MediaMTX, agregando servidor de prueba...")
                seeder.seed_mediamtx_server()

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
