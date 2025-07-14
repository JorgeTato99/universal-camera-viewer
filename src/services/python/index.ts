/**
 * Exportación de servicios Python
 */

export { cameraService, CameraService } from './cameraService';
export type { 
  ConnectCameraRequest, 
  CameraSnapshot, 
  StreamStatus 
} from './cameraService';

export { streamingService, StreamingService } from './streamingService';
export type { 
  StreamConfig, 
  FrameData, 
  StreamMessage,
  StreamEventCallback,
  StatusEventCallback,
  ErrorEventCallback
} from './streamingService';

export { scannerService, ScannerService } from './scannerService';
export type { 
  ScanRange, 
  ScanRequest, 
  ScanProgress, 
  ScanResult 
} from './scannerService';