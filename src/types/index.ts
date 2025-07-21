// Re-export all types from individual files
export * from "./camera.types";
export * from "./scanner.types";
export * from "./streaming.types";
export * from "./common.types";
export * from "./api.types";

// Re-export publishing types separately to handle type-only exports
export type {
  // Configuration types
  PublishConfiguration,
  CreateConfigurationRequest,
  
  // Status types
  PublishStatus,
  PublishingStatus,
  
  // Metrics types
  PublishMetrics,
  PublishingStatistics,
  
  // History types
  PublishingHistorySession,
  HistoryFilters,
  
  // Health & Alert types
  PublishingHealth,
  PublishingAlert,
  
  // MediaMTX types
  MediaMTXPath,
  CreatePathRequest,
  
  // Request/Response types
  StartPublishingRequest,
  StopPublishingRequest
} from "./publishing.types";
