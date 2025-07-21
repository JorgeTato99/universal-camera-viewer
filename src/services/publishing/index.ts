/**
 * 🎯 Publishing Services Index - Universal Camera Viewer
 * Exporta todos los servicios relacionados con publicación MediaMTX
 */

export { publishingService, default as PublishingService } from './publishingService';

// Re-exportar tipos comunes para conveniencia
export type {
  PublishConfiguration,
  PublishStatus,
  PublishingHealth,
  PublishMetrics,
  PublishingHistorySession,
  MediaMTXPath
} from '../../features/publishing/types';