/**
 * 🎯 Publishing Services Index - Universal Camera Viewer
 * Exporta todos los servicios relacionados con publicación MediaMTX
 */

export { publishingService, default as PublishingService } from './publishingService';
export { mediamtxRemoteService } from './mediamtxRemoteService';

// Re-exportar tipos comunes para conveniencia
export type {
  PublishConfiguration,
  PublishStatus,
  PublishingHealth,
  PublishMetrics,
  PublishingHistorySession,
  MediaMTXPath
} from '../../features/publishing/types';

// Re-exportar tipos de servicio remoto
export type {
  MediaMTXServer,
  AuthStatus,
  AuthRequest,
  RemotePublishStatus,
  RemotePublishRequest,
  RemotePublishMetrics
} from './mediamtxRemoteService';