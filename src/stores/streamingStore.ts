import { create } from "zustand";
import {
  StreamingSession,
  StreamModel,
  StreamMetrics,
  FrameData,
} from "../types/streaming.types";

interface StreamingState {
  // Active streaming sessions
  activeSessions: Map<string, StreamingSession>;

  // Selected stream for detailed view
  selectedStream: string | null;

  // Global streaming settings
  globalSettings: {
    maxConcurrentStreams: number;
    defaultQuality: string;
    autoReconnect: boolean;
    bufferSize: number;
  };

  // Actions
  startStream: (cameraId: string, config?: any) => void;
  stopStream: (cameraId: string) => void;
  updateStreamMetrics: (cameraId: string, metrics: StreamMetrics) => void;
  updateFrame: (cameraId: string, frameData: FrameData) => void;
  setSelectedStream: (cameraId: string | null) => void;
  stopAllStreams: () => void;

  // Computed
  getActiveStreamCount: () => number;
  getStreamHealth: (cameraId: string) => number;
}

export const useStreamingStore = create<StreamingState>((set, get) => ({
  activeSessions: new Map(),
  selectedStream: null,

  globalSettings: {
    maxConcurrentStreams: 6,
    defaultQuality: "medium",
    autoReconnect: true,
    bufferSize: 5,
  },

  startStream: (cameraId, config) =>
    set((state) => {
      const newSessions = new Map(state.activeSessions);

      // Create new streaming session
      const session: StreamingSession = {
        camera_id: cameraId,
        stream: {
          stream_id: `stream_${cameraId}_${Date.now()}`,
          camera_id: cameraId,
          protocol: "rtsp" as any,
          target_fps: 30,
          buffer_size: state.globalSettings.bufferSize,
          status: "connecting" as any,
          fps: 0,
          frame_count: 0,
          dropped_frames: 0,
          reconnect_attempts: 0,
          metadata: config || {},
        },
        metrics: {
          stream_id: `stream_${cameraId}`,
          current_fps: 0,
          average_fps: 0,
          current_latency_ms: 0,
          average_latency_ms: 0,
          bandwidth_kbps: 0,
          average_bandwidth_kbps: 0,
          total_frames: 0,
          dropped_frames: 0,
          drop_rate_percent: 0,
          error_count: 0,
          reconnect_count: 0,
          total_bytes: 0,
          uptime_seconds: 0,
          health_score: 100,
          last_update: new Date().toISOString(),
        },
        player_state: {
          isPlaying: false,
          isFullscreen: false,
          volume: 100,
          muted: false,
          currentTime: 0,
          duration: 0,
          buffered: 0,
        },
        last_activity: new Date().toISOString(),
      };

      newSessions.set(cameraId, session);
      return { activeSessions: newSessions };
    }),

  stopStream: (cameraId) =>
    set((state) => {
      const newSessions = new Map(state.activeSessions);
      newSessions.delete(cameraId);

      return {
        activeSessions: newSessions,
        selectedStream:
          state.selectedStream === cameraId ? null : state.selectedStream,
      };
    }),

  updateStreamMetrics: (cameraId, metrics) =>
    set((state) => {
      const newSessions = new Map(state.activeSessions);
      const session = newSessions.get(cameraId);

      if (session) {
        newSessions.set(cameraId, {
          ...session,
          metrics,
          last_activity: new Date().toISOString(),
        });
      }

      return { activeSessions: newSessions };
    }),

  updateFrame: (cameraId, frameData) =>
    set((state) => {
      const newSessions = new Map(state.activeSessions);
      const session = newSessions.get(cameraId);

      if (session) {
        newSessions.set(cameraId, {
          ...session,
          current_frame: frameData,
          last_activity: new Date().toISOString(),
        });
      }

      return { activeSessions: newSessions };
    }),

  setSelectedStream: (cameraId) => set({ selectedStream: cameraId }),

  stopAllStreams: () =>
    set({ activeSessions: new Map(), selectedStream: null }),

  getActiveStreamCount: () => {
    const { activeSessions } = get();
    return activeSessions.size;
  },

  getStreamHealth: (cameraId) => {
    const { activeSessions } = get();
    const session = activeSessions.get(cameraId);
    return session?.metrics.health_score || 0;
  },
}));
