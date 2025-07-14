import { invoke } from "@tauri-apps/api/tauri";
import { listen, UnlistenFn } from "@tauri-apps/api/event";
import {
  TauriCommands,
  TauriEvents,
  TauriCommandResult,
  ApiResponse,
} from "../../types/api.types";

/**
 * Tauri Service - Main interface for communicating with Python backend
 */
class TauriService {
  private eventListeners: Map<string, UnlistenFn> = new Map();
  private isInitialized: boolean = false;

  /**
   * Initialize the Tauri service and set up event listeners
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Test connection to Python backend
      await this.invoke(TauriCommands.GET_SYSTEM_INFO);
      this.isInitialized = true;
      console.log("✅ Tauri service initialized successfully");
    } catch (error) {
      console.error("❌ Failed to initialize Tauri service:", error);
      throw new Error("Tauri service initialization failed");
    }
  }

  /**
   * Generic method to invoke Tauri commands
   */
  async invoke<T = any>(
    command: TauriCommands,
    payload?: any
  ): Promise<TauriCommandResult<T>> {
    try {
      const result = await invoke(command, payload);
      return {
        success: true,
        data: result,
      };
    } catch (error) {
      console.error(`Error invoking command ${command}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Listen to Tauri events
   */
  async addEventListener<T = any>(
    event: TauriEvents,
    handler: (payload: T) => void
  ): Promise<void> {
    try {
      // Remove existing listener if present
      const existingListener = this.eventListeners.get(event);
      if (existingListener) {
        existingListener();
      }

      // Add new listener
      const unlisten = await listen(event, (eventPayload) => {
        handler(eventPayload.payload as T);
      });

      this.eventListeners.set(event, unlisten);
      console.log(`✅ Event listener added for: ${event}`);
    } catch (error) {
      console.error(`Error adding event listener for ${event}:`, error);
      throw error;
    }
  }

  /**
   * Remove event listener
   */
  removeEventListener(event: TauriEvents): void {
    const listener = this.eventListeners.get(event);
    if (listener) {
      listener();
      this.eventListeners.delete(event);
      console.log(`✅ Event listener removed for: ${event}`);
    }
  }

  /**
   * Remove all event listeners
   */
  removeAllEventListeners(): void {
    this.eventListeners.forEach((unlisten, event) => {
      unlisten();
      console.log(`✅ Event listener removed for: ${event}`);
    });
    this.eventListeners.clear();
  }

  /**
   * Check if service is initialized
   */
  get initialized(): boolean {
    return this.isInitialized;
  }

  /**
   * Cleanup and shutdown the service
   */
  async shutdown(): Promise<void> {
    this.removeAllEventListeners();
    this.isInitialized = false;
    console.log("✅ Tauri service shut down");
  }

  // === Camera Commands ===

  async scanCameras(networkRange?: string): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.SCAN_CAMERAS, {
      network_range: networkRange,
    });
  }

  async connectCamera(
    cameraId: string,
    connectionConfig: any
  ): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.CONNECT_CAMERA, {
      camera_id: cameraId,
      connection_config: connectionConfig,
    });
  }

  async disconnectCamera(cameraId: string): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.DISCONNECT_CAMERA, {
      camera_id: cameraId,
    });
  }

  async getCameraInfo(cameraId: string): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.GET_CAMERA_INFO, { camera_id: cameraId });
  }

  async captureSnapshot(cameraId: string): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.CAPTURE_SNAPSHOT, { camera_id: cameraId });
  }

  // === Streaming Commands ===

  async startStream(
    cameraId: string,
    quality?: string,
    fps?: number
  ): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.START_STREAM, {
      camera_id: cameraId,
      quality,
      fps,
    });
  }

  async stopStream(cameraId: string): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.STOP_STREAM, { camera_id: cameraId });
  }

  async getStreamStatus(cameraId: string): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.GET_STREAM_STATUS, {
      camera_id: cameraId,
    });
  }

  async getStreamMetrics(cameraId: string): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.GET_STREAM_METRICS, {
      camera_id: cameraId,
    });
  }

  // === Network Scanning Commands ===

  async startNetworkScan(scanConfig: any): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.START_NETWORK_SCAN, scanConfig);
  }

  async stopNetworkScan(): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.STOP_NETWORK_SCAN);
  }

  async getScanProgress(): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.GET_SCAN_PROGRESS);
  }

  async getScanResults(): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.GET_SCAN_RESULTS);
  }

  // === Configuration Commands ===

  async getConfig(key?: string): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.GET_CONFIG, { key });
  }

  async setConfig(
    key: string,
    value: any,
    category?: string
  ): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.SET_CONFIG, { key, value, category });
  }

  async saveConfig(): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.SAVE_CONFIG);
  }

  // === System Commands ===

  async getSystemInfo(): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.GET_SYSTEM_INFO);
  }

  async getPerformanceMetrics(): Promise<TauriCommandResult> {
    return this.invoke(TauriCommands.GET_PERFORMANCE_METRICS);
  }
}

// Export singleton instance
export const tauriService = new TauriService();
export default tauriService;
