/**
 * 🔌 Connection Error Hook - Universal Camera Viewer
 * Hook personalizado para manejar errores de conexión con reintentos automáticos
 * Implementa estrategia de backoff exponencial y notificaciones al usuario
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useNotificationStore } from '../stores/notificationStore';

interface ConnectionErrorOptions {
  /** Número máximo de reintentos automáticos */
  maxRetries?: number;
  /** Tiempo base de espera entre reintentos (ms) */
  baseRetryDelay?: number;
  /** Factor de multiplicación para backoff exponencial */
  backoffFactor?: number;
  /** Habilitar reintentos automáticos */
  enableAutoRetry?: boolean;
  /** Callback cuando se alcanza el máximo de reintentos */
  onMaxRetriesReached?: () => void;
}

interface ConnectionErrorState {
  /** Indica si hay un error de conexión activo */
  hasError: boolean;
  /** Tipo de error detectado */
  errorType: 'connection' | 'server' | 'timeout' | 'unknown';
  /** Mensaje de error detallado */
  errorMessage: string;
  /** Detalles técnicos del error */
  errorDetails?: string;
  /** Indica si está reintentando la conexión */
  isRetrying: boolean;
  /** Número de reintentos realizados */
  retryCount: number;
  /** Tiempo hasta el próximo reintento (ms) */
  nextRetryIn: number;
}

/**
 * Hook para manejar errores de conexión con el backend
 * Proporciona reintentos automáticos con backoff exponencial
 * 
 * @param onRetry - Función a ejecutar al reintentar
 * @param options - Opciones de configuración del hook
 * @returns Estado del error y funciones de control
 */
export const useConnectionError = (
  onRetry: () => Promise<void>,
  options: ConnectionErrorOptions = {}
) => {
  const {
    maxRetries = 3,
    baseRetryDelay = 2000,
    backoffFactor = 2,
    enableAutoRetry = true,
    onMaxRetriesReached,
  } = options;

  const { addNotification } = useNotificationStore();
  const retryTimeoutRef = useRef<NodeJS.Timeout>();
  const countdownIntervalRef = useRef<NodeJS.Timeout>();

  // Estado del error de conexión
  const [errorState, setErrorState] = useState<ConnectionErrorState>({
    hasError: false,
    errorType: 'connection',
    errorMessage: '',
    isRetrying: false,
    retryCount: 0,
    nextRetryIn: 0,
  });

  /**
   * Limpia los timers activos
   */
  const clearTimers = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = undefined;
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = undefined;
    }
  }, []);

  /**
   * Detecta el tipo de error basado en el objeto de error
   */
  const detectErrorType = useCallback((error: any): ConnectionErrorState['errorType'] => {
    const errorString = error?.toString?.() || '';
    const errorMessage = error?.message || '';
    
    // Error de conexión rechazada (backend no disponible)
    if (errorString.includes('ERR_CONNECTION_REFUSED') || 
        errorMessage.includes('Network Error') ||
        errorMessage.includes('Failed to fetch')) {
      return 'connection';
    }
    
    // Error del servidor (5xx)
    if (error?.status >= 500 && error?.status < 600) {
      return 'server';
    }
    
    // Timeout
    if (errorString.includes('timeout') || errorMessage.includes('timeout')) {
      return 'timeout';
    }
    
    return 'unknown';
  }, []);

  /**
   * Maneja un nuevo error de conexión
   */
  const handleError = useCallback((error: any) => {
    console.error('[useConnectionError] Error detectado:', error);
    
    const errorType = detectErrorType(error);
    const errorMessage = error?.message || 'Error de conexión desconocido';
    const errorDetails = error?.stack || error?.toString?.() || '';
    
    setErrorState(prev => ({
      ...prev,
      hasError: true,
      errorType,
      errorMessage,
      errorDetails,
    }));

    // Mostrar notificación al usuario
    addNotification({
      type: 'error',
      message: errorType === 'connection' 
        ? 'No se puede conectar con el servidor. Verifica que esté ejecutándose.'
        : errorMessage,
      duration: 5000,
    });

    // Iniciar reintentos automáticos si está habilitado
    if (enableAutoRetry && errorState.retryCount < maxRetries) {
      const delay = baseRetryDelay * Math.pow(backoffFactor, errorState.retryCount);
      
      setErrorState(prev => ({
        ...prev,
        nextRetryIn: delay,
      }));

      // Cuenta regresiva visual
      let timeLeft = delay;
      countdownIntervalRef.current = setInterval(() => {
        timeLeft -= 100;
        setErrorState(prev => ({
          ...prev,
          nextRetryIn: Math.max(0, timeLeft),
        }));
        
        if (timeLeft <= 0) {
          clearInterval(countdownIntervalRef.current!);
        }
      }, 100);

      // Programar reintento
      retryTimeoutRef.current = setTimeout(() => {
        retry();
      }, delay);
    } else if (errorState.retryCount >= maxRetries && onMaxRetriesReached) {
      onMaxRetriesReached();
      addNotification({
        type: 'error',
        message: 'Se alcanzó el máximo de reintentos. Por favor, verifica el servidor manualmente.',
        duration: 0, // No auto-cerrar
      });
    }
  }, [
    detectErrorType,
    addNotification,
    enableAutoRetry,
    errorState.retryCount,
    maxRetries,
    baseRetryDelay,
    backoffFactor,
    onMaxRetriesReached,
  ]);

  /**
   * Ejecuta un reintento manual o automático
   */
  const retry = useCallback(async () => {
    clearTimers();
    
    setErrorState(prev => ({
      ...prev,
      isRetrying: true,
      nextRetryIn: 0,
    }));

    try {
      await onRetry();
      
      // Si el reintento fue exitoso, limpiar el estado de error
      setErrorState({
        hasError: false,
        errorType: 'connection',
        errorMessage: '',
        isRetrying: false,
        retryCount: 0,
        nextRetryIn: 0,
      });
      
      addNotification({
        type: 'success',
        message: 'Conexión reestablecida exitosamente',
      });
    } catch (error) {
      // Si el reintento falla, incrementar contador y manejar el error
      setErrorState(prev => ({
        ...prev,
        isRetrying: false,
        retryCount: prev.retryCount + 1,
      }));
      
      handleError(error);
    }
  }, [clearTimers, onRetry, addNotification, handleError]);

  /**
   * Reinicia el estado de error manualmente
   */
  const clearError = useCallback(() => {
    clearTimers();
    setErrorState({
      hasError: false,
      errorType: 'connection',
      errorMessage: '',
      isRetrying: false,
      retryCount: 0,
      nextRetryIn: 0,
    });
  }, [clearTimers]);

  /**
   * Limpieza al desmontar el componente
   */
  useEffect(() => {
    return () => {
      clearTimers();
    };
  }, [clearTimers]);

  return {
    ...errorState,
    handleError,
    retry,
    clearError,
  };
};