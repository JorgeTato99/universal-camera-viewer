#!/usr/bin/env python3
"""
Python Sidecar para Tauri - Comunicación via stdin/stdout
Este script se ejecuta como proceso sidecar y se comunica con Tauri
mediante mensajes JSON a través de stdin/stdout.
"""

import sys
import json
import asyncio
from pathlib import Path
import logging

# Configurar path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent / "src-python"))

# Importar componentes necesarios
from presenters.streaming.video_stream_presenter import VideoStreamPresenter
from presenters.camera_presenter import CameraPresenter
from services.scan_service import ScanService
from services.connection_service import ConnectionService
from services.video.video_stream_service import VideoStreamService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='python_sidecar.log'
)
logger = logging.getLogger(__name__)


class PythonSidecar:
    """Maneja la comunicación entre Python y Tauri."""
    
    def __init__(self):
        # Inicializar servicios
        self.scan_service = ScanService()
        self.connection_service = ConnectionService()
        self.video_service = VideoStreamService()
        
        # Inicializar presenters
        self.camera_presenter = CameraPresenter(
            self.scan_service, 
            self.connection_service
        )
        self.video_presenter = VideoStreamPresenter(self.video_service)
        
        # Configurar comunicación con Tauri
        self._setup_tauri_communication()
    
    def _setup_tauri_communication(self):
        """Configura la comunicación bidireccional con Tauri."""
        # Los eventos se envían a stdout como JSON
        self.send_to_tauri = lambda event, data: print(
            json.dumps({"event": event, "data": data}), 
            flush=True
        )
    
    async def handle_command(self, command: dict):
        """
        Procesa comandos recibidos desde Tauri.
        
        Args:
            command: Diccionario con 'action' y 'params'
        """
        action = command.get("action")
        params = command.get("params", {})
        
        try:
            if action == "scan_network":
                await self._handle_scan_network(params)
            elif action == "connect_camera":
                await self._handle_connect_camera(params)
            elif action == "start_stream":
                await self._handle_start_stream(params)
            elif action == "stop_stream":
                await self._handle_stop_stream(params)
            else:
                logger.warning(f"Acción desconocida: {action}")
                self.send_to_tauri("error", {"message": f"Unknown action: {action}"})
        
        except Exception as e:
            logger.error(f"Error procesando comando {action}: {e}")
            self.send_to_tauri("error", {
                "action": action,
                "message": str(e)
            })
    
    async def _handle_scan_network(self, params: dict):
        """Maneja escaneo de red."""
        ip_range = params.get("ip_range", "192.168.1.0/24")
        
        # Callback para actualizaciones
        def on_update(event_type: str, data: dict):
            self.send_to_tauri(f"scan_{event_type}", data)
        
        # Configurar callback en presenter
        self.camera_presenter.on_update = on_update
        
        # Iniciar escaneo
        await self.camera_presenter._handle_view_action("scan_network", {
            "ip_range": ip_range
        })
    
    async def _handle_connect_camera(self, params: dict):
        """Maneja conexión a cámara."""
        camera_id = params.get("camera_id")
        
        # Callback para actualizaciones
        def on_update(event_type: str, data: dict):
            self.send_to_tauri(f"camera_{event_type}", data)
        
        self.camera_presenter.on_update = on_update
        
        # Conectar cámara
        await self.camera_presenter._handle_view_action("connect_camera", {
            "camera_id": camera_id
        })
    
    async def _handle_start_stream(self, params: dict):
        """Inicia streaming de video."""
        camera_id = params.get("camera_id")
        
        # Callback para frames
        async def on_frame(camera_id: str, frame_base64: str):
            self.send_to_tauri("video_frame", {
                "camera_id": camera_id,
                "frame": frame_base64
            })
        
        # Configurar callback en video presenter
        self.video_presenter._event_emitter.emit_frame_update = on_frame
        
        # Iniciar streaming
        await self.video_presenter.start_streaming(camera_id)
    
    async def _handle_stop_stream(self, params: dict):
        """Detiene streaming de video."""
        camera_id = params.get("camera_id")
        await self.video_presenter.stop_streaming(camera_id)
    
    async def run(self):
        """Loop principal del sidecar."""
        logger.info("Python sidecar iniciado")
        
        # Enviar evento de inicio
        self.send_to_tauri("ready", {"version": "1.0.0"})
        
        # Leer comandos desde stdin
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            try:
                # Leer línea desde stdin
                line = await reader.readline()
                if not line:
                    break
                
                # Parsear comando JSON
                command = json.loads(line.decode().strip())
                
                # Procesar comando
                await self.handle_command(command)
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON: {e}")
            except Exception as e:
                logger.error(f"Error en loop principal: {e}")


async def main():
    """Función principal."""
    sidecar = PythonSidecar()
    await sidecar.run()


if __name__ == "__main__":
    # Ejecutar sidecar
    asyncio.run(main())