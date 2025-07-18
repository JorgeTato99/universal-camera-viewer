/**
 * 🪝 useScanner Hook - Universal Camera Viewer
 * Hook personalizado para compartir lógica de escaneo entre páginas
 */

import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useScannerStore } from "../../../stores/scannerStore";
import { useNotificationStore } from "../../../stores/notificationStore";
import { ScanStatus, DeviceScanResult } from "../../../types/scanner.types";

export interface UseScannerOptions {
  autoSelectFirst?: boolean;
  onScanComplete?: (results: DeviceScanResult[]) => void;
}

export interface UseScannerReturn {
  // Estado
  isScanning: boolean;
  scanProgress: number;
  scanResults: DeviceScanResult[];
  selectedDevice: DeviceScanResult | null;
  selectedIP: string;
  
  // Acciones
  startNetworkScan: (config?: any) => Promise<void>;
  startPortScan: (ip: string, config?: any) => Promise<void>;
  testAccess: (ip: string, port: number, credentials: any) => Promise<boolean>;
  selectDevice: (device: DeviceScanResult) => void;
  selectIP: (ip: string) => void;
  clearResults: () => void;
  
  // Navegación
  navigateToNetwork: () => void;
  navigateToPorts: (ip?: string) => void;
  navigateToAccess: (ip?: string, ports?: number[]) => void;
}

export function useScanner(options: UseScannerOptions = {}): UseScannerReturn {
  const navigate = useNavigate();
  const { addNotification } = useNotificationStore();
  
  // Estado del store
  const currentScan = useScannerStore((state) => state.currentScan);
  const scanResults = useScannerStore((state) => state.results) || [];
  const selectedDevice = useScannerStore((state) => state.selectedDevice);
  
  // Estado local
  const [selectedIP, setSelectedIP] = useState<string>("");
  
  // Estados derivados
  const isScanning = currentScan?.status === ScanStatus.SCANNING;
  const scanProgress = currentScan?.progress?.scanned_ips 
    ? Math.round((currentScan.progress.scanned_ips / currentScan.progress.total_ips) * 100)
    : 0;
  
  // Auto-seleccionar el primer resultado si está habilitado
  useEffect(() => {
    if (options.autoSelectFirst && scanResults.length > 0 && !selectedDevice) {
      const firstCamera = scanResults.find((r: any) => r.probability > 0.7) || scanResults[0];
      selectDevice(firstCamera);
    }
  }, [scanResults, selectedDevice, options.autoSelectFirst]);
  
  // Acciones de escaneo
  const startNetworkScan = useCallback(async (config?: any) => {
    try {
      // TODO: Implementar llamada al servicio de escaneo
      addNotification({
        type: 'info',
        message: 'Iniciando escaneo de red...',
      });
      
      // Simular escaneo por ahora
      setTimeout(() => {
        if (options.onScanComplete) {
          options.onScanComplete(scanResults);
        }
      }, 3000);
      
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Error al iniciar escaneo de red',
      });
    }
  }, [addNotification, scanResults, options]);
  
  const startPortScan = useCallback(async (ip: string, config?: any) => {
    if (!ip) {
      addNotification({
        type: 'warning',
        message: 'Debe seleccionar una IP para escanear puertos',
      });
      return;
    }
    
    try {
      // TODO: Implementar llamada al servicio de escaneo de puertos
      addNotification({
        type: 'info',
        message: `Escaneando puertos en ${ip}...`,
      });
      
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Error al escanear puertos',
      });
    }
  }, [addNotification]);
  
  const testAccess = useCallback(async (ip: string, port: number, credentials: any): Promise<boolean> => {
    try {
      // TODO: Implementar prueba de acceso real
      addNotification({
        type: 'info',
        message: `Probando acceso en ${ip}:${port}...`,
      });
      
      // Simular resultado
      return true;
      
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Error al probar acceso',
      });
      return false;
    }
  }, [addNotification]);
  
  // Acciones de selección
  const selectDevice = useCallback((device: DeviceScanResult) => {
    // TODO: Actualizar en el store
    setSelectedIP(device.ip);
    addNotification({
      type: 'info',
      message: `Dispositivo seleccionado: ${device.ip}`,
    });
  }, [addNotification]);
  
  const selectIP = useCallback((ip: string) => {
    setSelectedIP(ip);
  }, []);
  
  const clearResults = useCallback(() => {
    // TODO: Limpiar resultados en el store
    setSelectedIP("");
  }, []);
  
  // Navegación
  const navigateToNetwork = useCallback(() => {
    navigate("/scanner/network");
  }, [navigate]);
  
  const navigateToPorts = useCallback((ip?: string) => {
    const targetIP = ip || selectedIP;
    if (targetIP) {
      navigate(`/scanner/ports?ip=${targetIP}`);
    } else {
      navigate("/scanner/ports");
    }
  }, [navigate, selectedIP]);
  
  const navigateToAccess = useCallback((ip?: string, ports?: number[]) => {
    const targetIP = ip || selectedIP;
    const params = new URLSearchParams();
    
    if (targetIP) {
      params.append('ip', targetIP);
    }
    
    if (ports && ports.length > 0) {
      params.append('ports', ports.join(','));
    }
    
    const queryString = params.toString();
    navigate(`/scanner/access${queryString ? `?${queryString}` : ''}`);
  }, [navigate, selectedIP]);
  
  return {
    // Estado
    isScanning,
    scanProgress,
    scanResults,
    selectedDevice,
    selectedIP,
    
    // Acciones
    startNetworkScan,
    startPortScan,
    testAccess,
    selectDevice,
    selectIP,
    clearResults,
    
    // Navegación
    navigateToNetwork,
    navigateToPorts,
    navigateToAccess,
  };
}