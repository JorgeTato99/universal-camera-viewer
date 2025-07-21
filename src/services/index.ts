/**
 * Exportación principal de servicios
 */

// API Client
export * from './api';

// Python Services
export * from './python';

// Tauri Service (si existe)
// export * from "./tauri/tauriService";

// Publishing Service
export * from './publishing';

// Config Service (si existe)
// export * from "./api/configService";

// Instancias singleton para uso directo
export { apiClient } from './api/apiClient';
export { cameraService } from './python/cameraService';
export { streamingService } from './python/streamingService';
export { scannerService } from './python/scannerService';
export { publishingService } from './publishing/publishingService';
