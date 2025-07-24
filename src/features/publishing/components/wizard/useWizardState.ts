/**
 * 🎯 Estado del Wizard de Configuración
 * Maneja la navegación y validación entre pasos
 */

import { useState, useCallback } from 'react';

export type ServerType = 'remote' | 'local';

export interface WizardState {
  currentStep: number;
  serverType: ServerType | null;
  serverConfig: {
    name: string;
    api_url: string;
    rtmp_url: string;
    rtsp_url: string;
    auth_required: boolean;
    username?: string;
    password?: string;
  };
  testResult: {
    success: boolean;
    message: string;
  } | null;
}

const initialState: WizardState = {
  currentStep: 0,
  serverType: null,
  serverConfig: {
    name: '',
    api_url: 'http://localhost:9997',
    rtmp_url: 'rtmp://localhost:1935',
    rtsp_url: 'rtsp://localhost:8554',
    auth_required: false,
    username: '',
    password: '',
  },
  testResult: null,
};

export const useWizardState = () => {
  const [state, setState] = useState<WizardState>(initialState);
  const [isLoading, setIsLoading] = useState(false);

  const updateServerType = useCallback((type: ServerType) => {
    setState(prev => ({ 
      ...prev, 
      serverType: type,
      // Ajustar URLs por defecto según el tipo
      serverConfig: {
        ...prev.serverConfig,
        api_url: type === 'remote' ? 'http://servidor.com:9997' : 'http://localhost:9997',
        rtmp_url: type === 'remote' ? 'rtmp://servidor.com:1935' : 'rtmp://localhost:1935',
        rtsp_url: type === 'remote' ? 'rtsp://servidor.com:8554' : 'rtsp://localhost:8554',
      }
    }));
  }, []);

  const updateServerConfig = useCallback((config: Partial<WizardState['serverConfig']>) => {
    setState(prev => ({
      ...prev,
      serverConfig: { ...prev.serverConfig, ...config }
    }));
  }, []);

  const nextStep = useCallback(() => {
    setState(prev => ({ ...prev, currentStep: prev.currentStep + 1 }));
  }, []);

  const prevStep = useCallback(() => {
    setState(prev => ({ ...prev, currentStep: Math.max(0, prev.currentStep - 1) }));
  }, []);

  const setTestResult = useCallback((result: WizardState['testResult']) => {
    setState(prev => ({ ...prev, testResult: result }));
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return {
    state,
    isLoading,
    setIsLoading,
    updateServerType,
    updateServerConfig,
    nextStep,
    prevStep,
    setTestResult,
    reset,
  };
};