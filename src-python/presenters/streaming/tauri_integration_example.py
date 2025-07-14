"""
Ejemplo de integración con Tauri.

Este archivo muestra cómo el backend Python se comunicaría
con el frontend Tauri para streaming de video.
"""

import asyncio
import json
from typing import Dict, Any

from .video_stream_presenter import VideoStreamPresenter
from .tauri_event_emitter import TauriEventEmitter
from ...models.connection_model import ConnectionConfig
from ...models.streaming import StreamProtocol


class TauriIntegration:
    """
    Ejemplo de cómo integrar el VideoStreamPresenter con Tauri.
    
    En producción, esto sería parte del backend que Tauri ejecuta.
    """
    
    def __init__(self):
        """Inicializa la integración."""
        self.event_emitter = TauriEventEmitter()
        self.video_presenter = VideoStreamPresenter(event_emitter=self.event_emitter)
        self.is_running = False
    
    async def initialize(self) -> None:
        """Inicializa el sistema."""
        await self.video_presenter.activate()
        self.is_running = True
        
        # Registrar handlers para comandos desde Tauri
        self._setup_command_handlers()
    
    def _setup_command_handlers(self) -> None:
        """
        Configura los handlers para comandos Tauri.
        
        En producción, estos serían endpoints que Tauri puede invocar.
        """
        # Los comandos vendrían desde Tauri invoke()
        pass
    
    async def handle_tauri_command(self, cmd: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja comandos desde el frontend Tauri.
        
        Args:
            cmd: Nombre del comando
            args: Argumentos del comando
            
        Returns:
            Respuesta para el frontend
        """
        try:
            if cmd == "start_camera_stream":
                return await self._start_camera_stream(args)
            elif cmd == "stop_camera_stream":
                return await self._stop_camera_stream(args)
            elif cmd == "get_active_streams":
                return await self._get_active_streams()
            elif cmd == "get_stream_metrics":
                return await self._get_stream_metrics(args)
            else:
                return {"success": False, "error": f"Unknown command: {cmd}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _start_camera_stream(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Inicia un stream de cámara."""
        camera_id = args.get("cameraId")
        if not camera_id:
            return {"success": False, "error": "cameraId is required"}
        
        # Crear configuración desde args
        config = ConnectionConfig(
            ip=args.get("ip", ""),
            port=args.get("port"),
            username=args.get("username", ""),
            password=args.get("password", "")
        )
        
        # Protocolo
        protocol = StreamProtocol(args.get("protocol", "rtsp").lower())
        
        # Opciones
        options = {
            "targetFps": args.get("targetFps", 30),
            "quality": args.get("quality", 85),
            "bufferSize": args.get("bufferSize", 5)
        }
        
        # Iniciar stream
        success = await self.video_presenter.start_camera_stream(
            camera_id=camera_id,
            connection_config=config,
            protocol=protocol,
            options=options
        )
        
        return {
            "success": success,
            "cameraId": camera_id,
            "message": "Stream started" if success else "Failed to start stream"
        }
    
    async def _stop_camera_stream(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Detiene un stream de cámara."""
        camera_id = args.get("cameraId")
        if not camera_id:
            return {"success": False, "error": "cameraId is required"}
        
        success = await self.video_presenter.stop_camera_stream(camera_id)
        
        return {
            "success": success,
            "cameraId": camera_id,
            "message": "Stream stopped" if success else "Failed to stop stream"
        }
    
    async def _get_active_streams(self) -> Dict[str, Any]:
        """Obtiene información de streams activos."""
        streams = self.video_presenter.get_active_streams()
        
        return {
            "success": True,
            "streams": streams,
            "count": len(streams)
        }
    
    async def _get_stream_metrics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene métricas de un stream específico."""
        camera_id = args.get("cameraId")
        if not camera_id:
            return {"success": False, "error": "cameraId is required"}
        
        metrics = self.video_presenter._video_service.get_stream_metrics(camera_id)
        
        if metrics:
            return {
                "success": True,
                "cameraId": camera_id,
                "metrics": metrics
            }
        else:
            return {
                "success": False,
                "error": f"No active stream for camera {camera_id}"
            }
    
    async def cleanup(self) -> None:
        """Limpia recursos."""
        if self.is_running:
            await self.video_presenter.deactivate()
            self.is_running = False


# Ejemplo de cómo se usaría desde Tauri
async def example_usage():
    """
    Ejemplo de uso que muestra el flujo completo.
    
    En producción, Tauri llamaría a estos métodos via IPC.
    """
    # Crear integración
    integration = TauriIntegration()
    await integration.initialize()
    
    # Simular comando desde frontend para iniciar stream
    start_result = await integration.handle_tauri_command("start_camera_stream", {
        "cameraId": "camera_001",
        "ip": "192.168.1.100",
        "port": 554,
        "username": "admin",
        "password": "password",
        "protocol": "rtsp",
        "targetFps": 30,
        "quality": 85
    })
    
    print(f"Start result: {json.dumps(start_result, indent=2)}")
    
    # El frontend recibiría eventos via Tauri:
    # - 'stream-status' con estado 'connecting'
    # - 'stream-status' con estado 'connected'
    # - 'frame-update' con frames en base64 (30 veces por segundo)
    # - 'stream-metrics' con FPS, latencia, etc.
    
    # Simular espera mientras se reciben frames
    await asyncio.sleep(5)
    
    # Obtener métricas
    metrics_result = await integration.handle_tauri_command("get_stream_metrics", {
        "cameraId": "camera_001"
    })
    
    print(f"Metrics: {json.dumps(metrics_result, indent=2)}")
    
    # Detener stream
    stop_result = await integration.handle_tauri_command("stop_camera_stream", {
        "cameraId": "camera_001"
    })
    
    print(f"Stop result: {json.dumps(stop_result, indent=2)}")
    
    # Limpiar
    await integration.cleanup()


# Documentación para el frontend Tauri
TAURI_FRONTEND_EXAMPLE = """
// En el frontend de Tauri (React/Vue/etc)

import { invoke, listen } from '@tauri-apps/api';

// Iniciar stream de cámara
async function startCameraStream(cameraId, config) {
    const result = await invoke('start_camera_stream', {
        cameraId,
        ip: config.ip,
        port: config.port,
        username: config.username,
        password: config.password,
        protocol: 'rtsp',
        targetFps: 30,
        quality: 85
    });
    
    if (result.success) {
        console.log('Stream started:', cameraId);
    }
}

// Escuchar actualizaciones de frames
const unlistenFrame = await listen('frame-update', (event) => {
    const { cameraId, frameData, dataUri } = event.payload;
    
    // Actualizar imagen en UI
    const img = document.getElementById(`camera-${cameraId}`);
    if (img) {
        img.src = dataUri; // data:image/jpeg;base64,...
    }
});

// Escuchar cambios de estado
const unlistenStatus = await listen('stream-status', (event) => {
    const { cameraId, status } = event.payload;
    console.log(`Camera ${cameraId} status: ${status}`);
});

// Escuchar métricas
const unlistenMetrics = await listen('stream-metrics', (event) => {
    const { cameraId, metrics } = event.payload;
    console.log(`Camera ${cameraId} FPS:`, metrics.fps);
});

// Detener stream
async function stopCameraStream(cameraId) {
    await invoke('stop_camera_stream', { cameraId });
}

// Limpiar listeners cuando el componente se desmonte
function cleanup() {
    unlistenFrame();
    unlistenStatus();
    unlistenMetrics();
}
"""