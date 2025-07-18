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
  Fade,
  Grow,
  Slide,
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
    <Fade in timeout={600}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          bgcolor: 'background.default',
        }}
      >
        {/* Header con animación */}
        <Slide direction="down" in timeout={500}>
          <Box
            sx={{
              p: 2,
              borderBottom: 1,
              borderColor: 'divider',
              bgcolor: 'background.paper',
            }}
          >
            <Container maxWidth={false}>
              <Fade in timeout={600} style={{ transitionDelay: '100ms' }}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h4" component="h1">
                    Registro de Cámaras
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    Gestión completa de cámaras: configuración, credenciales y protocolos
                  </Typography>
                </Box>
              </Fade>

              {/* Toolbar con animación */}
              <Fade in timeout={700} style={{ transitionDelay: '200ms' }}>
                <Box>
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
                </Box>
              </Fade>
            </Container>
          </Box>
        </Slide>

        {/* Main Content con animación */}
        <Grow in timeout={800} style={{ transitionDelay: '300ms', transformOrigin: '0 0 0' }}>
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
                <Fade in timeout={400}>
                  <Box>
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
                  </Box>
                </Fade>
              ) : (
                <>
                  {/* Tabla de datos principal con animación */}
                  <Fade in timeout={600} style={{ transitionDelay: '400ms' }}>
                    <Box>
                      <CameraDataTable
                        cameras={filteredCameras}
                        selectedCameras={selectedCameras}
                        onSelectCamera={handleSelectCamera}
                        onSelectAll={handleSelectAll}
                      />
                    </Box>
                  </Fade>

                  {/* Empty State con animación */}
                  {!isLoading && filteredCameras.length === 0 && (
                    <Fade in timeout={800}>
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
                        <Grow in timeout={600} style={{ transitionDelay: '200ms' }}>
                          <Typography variant="h6" color="text.secondary">
                            No se encontraron cámaras
                          </Typography>
                        </Grow>
                        <Fade in timeout={600} style={{ transitionDelay: '400ms' }}>
                          <Typography variant="body2" color="text.secondary">
                            Intenta ajustar los filtros o crear una nueva cámara
                          </Typography>
                        </Fade>
                      </Box>
                    </Fade>
                  )}
                </>
              )}
            </Container>
          </Box>
        </Grow>

        {/* Status Bar con animación */}
        <Slide direction="up" in timeout={600} style={{ transitionDelay: '500ms' }}>
          <Box>
            <ManagementStatusBar
              totalCameras={stats.total}
              connectedCameras={stats.connected}
              activeCameras={stats.active}
              alerts={0} // TODO: Implementar sistema de alertas
            />
          </Box>
        </Slide>

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
    </Fade>
  );
};

export default CameraManagementPage;