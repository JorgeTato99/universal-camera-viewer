import { create } from "zustand";
import {
  ScanStatus,
  NetworkDiscovery,
  ScanConfig,
} from "../types/scanner.types";

interface ScannerState {
  // Current scan
  currentScan: NetworkDiscovery | null;
  scanHistory: NetworkDiscovery[];

  // Configuration
  scanConfig: ScanConfig;

  // Actions
  startScan: (config?: Partial<ScanConfig>) => void;
  stopScan: () => void;
  updateScanProgress: (scan: NetworkDiscovery) => void;
  completeScan: (scan: NetworkDiscovery) => void;
  setScanConfig: (config: Partial<ScanConfig>) => void;
  clearHistory: () => void;
}

export const useScannerStore = create<ScannerState>((set, get) => ({
  currentScan: null,
  scanHistory: [],

  scanConfig: {
    network_ranges: ["192.168.1.0/24"],
    ports: [80, 554, 8080],
    timeout: 5.0,
    max_threads: 50,
    include_onvif: true,
    include_rtsp: true,
    include_http: true,
    include_amcrest: true,
    test_authentication: true,
    auto_detect_protocols: true,
  },

  startScan: (config) => {
    const { scanConfig } = get();
    const updatedConfig = { ...scanConfig, ...config };

    const newScan: NetworkDiscovery = {
      scan_id: `scan_${Date.now()}`,
      status: ScanStatus.PREPARING,
      progress: {
        total_ips: 0,
        scanned_ips: 0,
        total_ports: 0,
        scanned_ports: 0,
        cameras_found: 0,
        elapsed_time: 0,
        estimated_remaining: 0,
      },
      results: [],
      cameras_found: [],
      scan_range: {
        start_ip: updatedConfig.network_ranges[0].split("/")[0],
        end_ip: updatedConfig.network_ranges[0].split("/")[0],
        ports: updatedConfig.ports,
        protocols: [],
        timeout: updatedConfig.timeout,
      },
      methods: [],
      duration_seconds: 0,
    };

    set({ currentScan: newScan, scanConfig: updatedConfig });
  },

  stopScan: () =>
    set((state) => {
      if (state.currentScan) {
        const updatedScan = {
          ...state.currentScan,
          status: ScanStatus.CANCELLED,
        };
        return { currentScan: updatedScan };
      }
      return state;
    }),

  updateScanProgress: (scan) => set({ currentScan: scan }),

  completeScan: (scan) =>
    set((state) => ({
      currentScan: null,
      scanHistory: [scan, ...state.scanHistory.slice(0, 9)], // Keep last 10 scans
    })),

  setScanConfig: (config) =>
    set((state) => ({
      scanConfig: { ...state.scanConfig, ...config },
    })),

  clearHistory: () => set({ scanHistory: [] }),
}));
