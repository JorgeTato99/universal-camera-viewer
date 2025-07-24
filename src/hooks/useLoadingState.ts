/**
 * 🎯 Hook de Estado de Carga
 * Maneja estados de carga con timeout y mensajes
 */

import { useState, useCallback, useRef, useEffect } from 'react';

interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

interface UseLoadingStateOptions {
  timeout?: number;
  onTimeout?: () => void;
}

export const useLoadingState = (options?: UseLoadingStateOptions) => {
  const [state, setState] = useState<LoadingState>({ isLoading: false });
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // Limpiar timeout al desmontar
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const startLoading = useCallback((message?: string) => {
    setState({ isLoading: true, message, progress: undefined });

    // Configurar timeout si se especifica
    if (options?.timeout) {
      timeoutRef.current = setTimeout(() => {
        if (options.onTimeout) {
          options.onTimeout();
        }
        setState({ isLoading: false });
      }, options.timeout);
    }
  }, [options]);

  const stopLoading = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setState({ isLoading: false });
  }, []);

  const updateProgress = useCallback((progress: number, message?: string) => {
    setState(prev => ({
      ...prev,
      progress: Math.min(100, Math.max(0, progress)),
      message: message || prev.message,
    }));
  }, []);

  const updateMessage = useCallback((message: string) => {
    setState(prev => ({ ...prev, message }));
  }, []);

  return {
    isLoading: state.isLoading,
    message: state.message,
    progress: state.progress,
    startLoading,
    stopLoading,
    updateProgress,
    updateMessage,
  };
};