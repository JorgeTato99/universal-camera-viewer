/**
 * 🎯 Camera Management Dashboard - Universal Camera Viewer
 * Dashboard principal para gestión de cámaras con vista híbrida
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { useCameraStoreV2 } from '../../../../stores/cameraStore.v2';
import { ManagementToolbar } from '../../components/management/ManagementToolbar';
import { CameraDataTable } from '../../components/management/CameraDataTable';
import { ManagementStatusBar } from '../../components/management/ManagementStatusBar';
import { CameraCreationWizard } from '../../components/management/CameraCreationWizard';
import { ConnectionErrorState } from '../../../../components/feedback/ConnectionErrorState';
import { useConnectionError } from '../../../../hooks/useConnectionError';

export const CameraManagementPage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Estado global de cámaras
  const {
    cameras,
    isLoading,
    loadCameras,
    getCameraStats,
    setSearchQuery,
    setFilterStatus,
    setFilterBrand,
    setFilterLocation,
    getFilteredCameras,
    connectionError,
    clearConnectionError,
  } = useCameraStoreV2();

  // Estado local del componente
  const [selectedCameras, setSelectedCameras] = useState<Set<string>>(new Set());
  const [showCreationWizard, setShowCreationWizard] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Hook para manejar errores de conexión con reintentos
  const connectionErrorHandler = useConnectionError(
    async () => {
      await loadCameras();
    },
    {
      maxRetries: 3,
      baseRetryDelay: 2000,
      enableAutoRetry: true,
    }
  );

  // Cargar cámaras al montar
  useEffect(() => {
    loadCameras();
  }, [loadCameras]);

  // Obtener cámaras filtradas y estadísticas
  // No usar useMemo aquí porque necesitamos que se actualice cuando cambie el estado interno del store
  const filteredCameras = getFilteredCameras();
  const stats = getCameraStats();

  // Handlers

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadCameras();
    setTimeout(() => setIsRefreshing(false), 500);
  }, [loadCameras]);

  const handleSelectCamera = useCallback((cameraId: string, selected: boolean) => {
    setSelectedCameras(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(cameraId);
      } else {
        newSet.delete(cameraId);
      }
      return newSet;
    });
  }, []);

  const handleSelectAll = useCallback((selected: boolean) => {
    if (selected) {
      setSelectedCameras(new Set(filteredCameras.map(cam => cam.camera_id)));
    } else {
      setSelectedCameras(new Set());
    }
  }, [filteredCameras]);

  const handleBulkAction = useCallback((action: string) => {
    console.log(`Bulk action: ${action} on ${selectedCameras.size} cameras`);
    // TODO: Implementar acciones masivas
  }, [selectedCameras]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        bgcolor: 'background.default',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Container maxWidth={false}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h4" component="h1">
              Registro de Cámaras
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Gestión completa de cámaras: configuración, credenciales y protocolos
            </Typography>
          </Box>

          {/* Toolbar */}
          <ManagementToolbar
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
            onCreateNew={() => setShowCreationWizard(true)}
            selectedCount={selectedCameras.size}
            onBulkAction={handleBulkAction}
            onSearch={setSearchQuery}
            onFilterStatus={setFilterStatus}
            onFilterBrand={setFilterBrand}
            onFilterLocation={setFilterLocation}
          />
        </Container>
      </Box>

      {/* Main Content */}
      <Box sx={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <Container 
          maxWidth={false} 
          sx={{ 
            height: '100%', 
            py: 2,
            overflow: 'auto',
          }}
        >
          {/* Mostrar error de conexión si existe */}
          {connectionError?.hasError ? (
            <ConnectionErrorState
              errorType={connectionError.errorType}
              customMessage={connectionError.errorMessage}
              errorDetails={connectionError.errorDetails}
              onRetry={() => {
                clearConnectionError();
                connectionErrorHandler.retry();
              }}
              isRetrying={connectionErrorHandler.isRetrying}
              showDebugInfo={true}
            />
          ) : (
            <>
              {/* Tabla de datos principal */}
              <CameraDataTable
                cameras={filteredCameras}
                selectedCameras={selectedCameras}
                onSelectCamera={handleSelectCamera}
                onSelectAll={handleSelectAll}
              />

              {/* Empty State */}
              {!isLoading && filteredCameras.length === 0 && (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '60vh',
                    gap: 2,
                  }}
                >
                  <Typography variant="h6" color="text.secondary">
                    No se encontraron cámaras
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Intenta ajustar los filtros o crear una nueva cámara
                  </Typography>
                </Box>
              )}
            </>
          )}
        </Container>
      </Box>

      {/* Status Bar */}
      <ManagementStatusBar
        totalCameras={stats.total}
        connectedCameras={stats.connected}
        activeCameras={stats.active}
        alerts={0} // TODO: Implementar sistema de alertas
      />

      {/* Creation Wizard */}
      <CameraCreationWizard
        open={showCreationWizard}
        onClose={() => setShowCreationWizard(false)}
        onSuccess={() => {
          setShowCreationWizard(false);
          loadCameras();
        }}
      />
    </Box>
  );
};

export default CameraManagementPage;