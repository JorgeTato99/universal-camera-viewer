/**
 * 📊 Remote Publishing Dashboard - Universal Camera Viewer
 * Dashboard principal para gestión de publicaciones a servidores MediaMTX remotos
 * 
 * Características:
 * - Vista general de servidores y publicaciones
 * - Grid de cámaras con capacidad de publicación remota
 * - Filtros y búsqueda
 * - Acciones masivas
 * - Métricas agregadas
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert,
  Skeleton,
  Tooltip,
  Badge,
  ToggleButton,
  ToggleButtonGroup,
  Fab
} from '@mui/material';
import {
  Search,
  FilterList,
  Add,
  CloudUpload,
  PlayArrow,
  Stop,
  Refresh,
  ViewModule,
  ViewList,
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  CloudQueue,
  Speed,
  People,
  MoreVert,
  Settings
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { RemotePublishingCard } from '../remote/RemotePublishingCard';
import { RemoteServerSelector } from '../remote/RemoteServerSelector';
import { MediaMTXAuthDialog } from '../auth/MediaMTXAuthDialog';
import { ServerConnectionStatus } from '../auth/ServerConnectionStatus';
import { useMediaMTXAuth } from '../../hooks/useMediaMTXAuth';
import { useCameraStoreV2 } from '../../../../stores/cameraStore.v2';
import { MediaMTXServer } from '../../../../services/publishing/mediamtxRemoteService';
import { PublishingStatus } from '../../types';

// === STYLED COMPONENTS ===

const DashboardContainer = styled(Box)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(3),
  padding: theme.spacing(3)
}));

const HeaderPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)',
  color: 'white'
}));

const StatCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  textAlign: 'center',
  height: '100%',
  transition: 'all 0.3s ease',
  cursor: 'pointer',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4]
  }
}));

const FilterChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5)
}));

// === INTERFACES ===

interface RemotePublishingDashboardProps {
  onConfigureServer?: () => void;
  onViewMetrics?: () => void;
}

// === COMPONENTE PRINCIPAL ===

export const RemotePublishingDashboard: React.FC<RemotePublishingDashboardProps> = ({
  onConfigureServer,
  onViewMetrics
}) => {
  // Estado local
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedServerId, setSelectedServerId] = useState<number | undefined>();
  const [filterStatus, setFilterStatus] = useState<PublishingStatus | 'all'>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [authDialogOpen, setAuthDialogOpen] = useState(false);
  const [authDialogServer, setAuthDialogServer] = useState<MediaMTXServer | null>(null);
  const [filterMenuAnchor, setFilterMenuAnchor] = useState<null | HTMLElement>(null);
  
  // Hooks
  const {
    servers,
    authStatuses,
    isLoading,
    authenticate,
    logout,
    validateConnection,
    getAuthenticatedServers,
    isAuthenticated
  } = useMediaMTXAuth();
  
  // Estado de cámaras
  const { cameras } = useCameraStoreV2();
  const cameraList = Array.from(cameras.values());
  
  // TODO: Obtener publicaciones remotas reales
  const remotePublications = new Map(); // Mock por ahora
  
  // Filtrar cámaras
  const filteredCameras = useMemo(() => {
    return cameraList.filter(camera => {
      // Filtrar por búsqueda
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (!camera.name.toLowerCase().includes(query) &&
            !camera.ip.toLowerCase().includes(query)) {
          return false;
        }
      }
      
      // Filtrar por estado
      if (filterStatus !== 'all') {
        const publication = remotePublications.get(camera.camera_id);
        if (!publication || publication.status !== filterStatus) {
          return false;
        }
      }
      
      return true;
    });
  }, [cameraList, searchQuery, filterStatus, remotePublications]);
  
  // Calcular estadísticas
  const stats = useMemo(() => {
    const authenticatedServers = getAuthenticatedServers();
    let publishing = 0;
    let error = 0;
    let viewers = 0;
    
    remotePublications.forEach(pub => {
      if (pub.status === PublishingStatus.PUBLISHING) {
        publishing++;
        viewers += pub.metrics?.viewers || 0;
      } else if (pub.status === PublishingStatus.ERROR) {
        error++;
      }
    });
    
    return {
      servers: {
        total: servers.length,
        authenticated: authenticatedServers.length
      },
      publications: {
        total: remotePublications.size,
        publishing,
        error
      },
      viewers
    };
  }, [servers, getAuthenticatedServers, remotePublications]);
  
  // Manejadores
  const handleServerAuth = useCallback((server: MediaMTXServer) => {
    setAuthDialogServer(server);
    setAuthDialogOpen(true);
  }, []);
  
  const handleAuthSuccess = useCallback((server: MediaMTXServer) => {
    setAuthDialogOpen(false);
    setAuthDialogServer(null);
    // Seleccionar el servidor autenticado
    setSelectedServerId(server.id);
  }, []);
  
  const handleStartPublishing = useCallback(async (cameraId: string, serverId: number) => {
    // TODO: Implementar publicación real
    console.log('Iniciar publicación:', cameraId, serverId);
  }, []);
  
  const handleStopPublishing = useCallback(async (cameraId: string) => {
    // TODO: Implementar detener publicación
    console.log('Detener publicación:', cameraId);
  }, []);
  
  const handleRestartPublishing = useCallback(async (cameraId: string) => {
    // TODO: Implementar reiniciar publicación
    console.log('Reiniciar publicación:', cameraId);
  }, []);
  
  const handleBulkAction = useCallback((action: 'start' | 'stop') => {
    if (!selectedServerId) return;
    
    filteredCameras.forEach(camera => {
      if (action === 'start') {
        handleStartPublishing(camera.camera_id, selectedServerId);
      } else {
        handleStopPublishing(camera.camera_id);
      }
    });
  }, [filteredCameras, selectedServerId, handleStartPublishing, handleStopPublishing]);
  
  // Renderizar contenido principal
  const renderContent = () => {
    if (isLoading) {
      return (
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map(i => (
            <Grid item key={i} xs={12} sm={6} md={4} lg={3}>
              <Skeleton variant="rectangular" height={200} />
            </Grid>
          ))}
        </Grid>
      );
    }
    
    if (servers.length === 0) {
      return (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <CloudQueue sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No hay servidores configurados
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Configure un servidor MediaMTX remoto para comenzar a publicar
          </Typography>
          {onConfigureServer && (
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={onConfigureServer}
            >
              Configurar servidor
            </Button>
          )}
        </Paper>
      );
    }
    
    if (filteredCameras.length === 0) {
      return (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Search sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No se encontraron cámaras
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Ajuste los filtros de búsqueda o agregue nuevas cámaras
          </Typography>
        </Paper>
      );
    }
    
    return (
      <Grid container spacing={3}>
        {filteredCameras.map(camera => (
          <Grid 
            item 
            key={camera.camera_id} 
            xs={12} 
            sm={viewMode === 'list' ? 12 : 6} 
            md={viewMode === 'list' ? 12 : 4}
            lg={viewMode === 'list' ? 12 : 3}
          >
            <RemotePublishingCard
              cameraId={camera.camera_id}
              cameraName={camera.name}
              remotePublication={remotePublications.get(camera.camera_id)}
              availableServers={getAuthenticatedServers()}
              selectedServerId={selectedServerId}
              onServerSelect={setSelectedServerId}
              onStart={handleStartPublishing}
              onStop={handleStopPublishing}
              onRestart={handleRestartPublishing}
              isLoading={false}
            />
          </Grid>
        ))}
      </Grid>
    );
  };
  
  return (
    <DashboardContainer>
      {/* Header con estadísticas */}
      <HeaderPaper elevation={3}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h4" gutterBottom>
              Publicación Remota
            </Typography>
            <Typography variant="body1">
              Gestione la publicación de cámaras a servidores MediaMTX remotos
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <StatCard elevation={0} sx={{ bgcolor: 'rgba(255,255,255,0.1)' }}>
                  <CloudQueue sx={{ fontSize: 32, mb: 1 }} />
                  <Typography variant="h6">
                    {stats.servers.authenticated}/{stats.servers.total}
                  </Typography>
                  <Typography variant="caption">
                    Servidores activos
                  </Typography>
                </StatCard>
              </Grid>
              <Grid item xs={4}>
                <StatCard elevation={0} sx={{ bgcolor: 'rgba(255,255,255,0.1)' }}>
                  <Speed sx={{ fontSize: 32, mb: 1 }} />
                  <Typography variant="h6">
                    {stats.publications.publishing}
                  </Typography>
                  <Typography variant="caption">
                    Publicando
                  </Typography>
                </StatCard>
              </Grid>
              <Grid item xs={4}>
                <StatCard elevation={0} sx={{ bgcolor: 'rgba(255,255,255,0.1)' }}>
                  <People sx={{ fontSize: 32, mb: 1 }} />
                  <Typography variant="h6">
                    {stats.viewers}
                  </Typography>
                  <Typography variant="caption">
                    Espectadores
                  </Typography>
                </StatCard>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </HeaderPaper>
      
      {/* Barra de herramientas */}
      <Paper sx={{ p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              size="small"
              placeholder="Buscar cámaras..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            <RemoteServerSelector
              servers={servers}
              authStatuses={authStatuses}
              selectedServerId={selectedServerId}
              onChange={setSelectedServerId}
              onAuthServer={handleServerAuth}
              onRefreshStatus={validateConnection}
              showOnlyAuthenticated={true}
              fullWidth
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(_, value) => value && setViewMode(value)}
                size="small"
              >
                <ToggleButton value="grid">
                  <ViewModule />
                </ToggleButton>
                <ToggleButton value="list">
                  <ViewList />
                </ToggleButton>
              </ToggleButtonGroup>
              
              <IconButton
                onClick={(e) => setFilterMenuAnchor(e.currentTarget)}
                color={filterStatus !== 'all' ? 'primary' : 'default'}
              >
                <Badge 
                  badgeContent={filterStatus !== 'all' ? 1 : 0} 
                  color="primary"
                >
                  <FilterList />
                </Badge>
              </IconButton>
              
              <IconButton onClick={() => window.location.reload()}>
                <Refresh />
              </IconButton>
            </Box>
          </Grid>
        </Grid>
        
        {/* Chips de filtros activos */}
        {(filterStatus !== 'all' || selectedServerId) && (
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {filterStatus !== 'all' && (
              <FilterChip
                label={`Estado: ${filterStatus}`}
                onDelete={() => setFilterStatus('all')}
                color="primary"
              />
            )}
            {selectedServerId && (
              <FilterChip
                label={`Servidor: ${servers.find(s => s.id === selectedServerId)?.name}`}
                onDelete={() => setSelectedServerId(undefined)}
                color="primary"
              />
            )}
          </Box>
        )}
      </Paper>
      
      {/* Alertas */}
      {stats.publications.error > 0 && (
        <Alert severity="warning" action={
          <Button color="inherit" size="small" onClick={onViewMetrics}>
            Ver detalles
          </Button>
        }>
          Hay {stats.publications.error} publicación(es) con errores
        </Alert>
      )}
      
      {/* Contenido principal */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {renderContent()}
      </Box>
      
      {/* FAB para acciones masivas */}
      {selectedServerId && filteredCameras.length > 0 && (
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 24, right: 24 }}
          onClick={() => handleBulkAction('start')}
        >
          <PlayArrow />
        </Fab>
      )}
      
      {/* Menú de filtros */}
      <Menu
        anchorEl={filterMenuAnchor}
        open={Boolean(filterMenuAnchor)}
        onClose={() => setFilterMenuAnchor(null)}
      >
        <MenuItem onClick={() => { setFilterStatus('all'); setFilterMenuAnchor(null); }}>
          <ListItemText>Todos los estados</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => { setFilterStatus(PublishingStatus.PUBLISHING); setFilterMenuAnchor(null); }}>
          <ListItemIcon>
            <CheckCircle color="success" />
          </ListItemIcon>
          <ListItemText>Publicando</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { setFilterStatus(PublishingStatus.ERROR); setFilterMenuAnchor(null); }}>
          <ListItemIcon>
            <ErrorIcon color="error" />
          </ListItemIcon>
          <ListItemText>Con errores</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { setFilterStatus(PublishingStatus.IDLE); setFilterMenuAnchor(null); }}>
          <ListItemIcon>
            <Stop />
          </ListItemIcon>
          <ListItemText>Detenidos</ListItemText>
        </MenuItem>
      </Menu>
      
      {/* Diálogo de autenticación */}
      {authDialogServer && (
        <MediaMTXAuthDialog
          open={authDialogOpen}
          onClose={() => setAuthDialogOpen(false)}
          server={authDialogServer}
          onAuthSuccess={handleAuthSuccess}
        />
      )}
    </DashboardContainer>
  );
};

export default RemotePublishingDashboard;