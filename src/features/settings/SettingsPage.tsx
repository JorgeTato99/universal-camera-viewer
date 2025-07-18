/**
 * ⚙️ Settings Page - Universal Camera Viewer
 * Página de configuración del sistema
 * Optimizada con memo, lazy loading y estructura modular
 */

import React, { memo, useState, useCallback, Suspense, lazy } from "react";
import { 
  Box, 
  Typography, 
  Paper,
  Container,
  Tab,
  Tabs,
  Skeleton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Fade,
  Slide,
  Grow,
  CircularProgress,
} from "@mui/material";
import {
  NetworkCheck as NetworkIcon,
  Videocam as CameraIcon,
  Person as UserIcon,
  Router as ProtocolIcon,
  Backup as BackupIcon,
} from "@mui/icons-material";

// Lazy loading de componentes de configuración
const NetworkSettings = lazy(() => import("./components/NetworkSettings"));
const CameraSettings = lazy(() => import("./components/CameraSettings"));
const UserPreferences = lazy(() => import("./components/UserPreferences"));
// TODO: Implementar estos componentes cuando se necesiten
// const ProtocolSettings = lazy(() => import("./components/ProtocolSettings"));
// const BackupSettings = lazy(() => import("./components/BackupSettings"));

/**
 * Interface para los tabs de configuración
 */
interface SettingsTab {
  id: string;
  label: string;
  icon: React.ReactNode;
  description: string;
}

/**
 * Configuración de tabs disponibles
 */
const SETTINGS_TABS: SettingsTab[] = [
  {
    id: 'network',
    label: 'Red',
    icon: <NetworkIcon />,
    description: 'Configuración de red y conectividad',
  },
  {
    id: 'cameras',
    label: 'Cámaras',
    icon: <CameraIcon />,
    description: 'Configuración global de cámaras',
  },
  {
    id: 'user',
    label: 'Usuario',
    icon: <UserIcon />,
    description: 'Preferencias de usuario e interfaz',
  },
  {
    id: 'protocols',
    label: 'Protocolos',
    icon: <ProtocolIcon />,
    description: 'Configuración de protocolos ONVIF/RTSP',
  },
  {
    id: 'backup',
    label: 'Respaldo',
    icon: <BackupIcon />,
    description: 'Respaldos y restauración del sistema',
  },
];

/**
 * Componente de panel de tabs memoizado
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = memo<TabPanelProps>(({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
    >
      {value === index && (
        <Fade in timeout={600}>
          <Box sx={{ py: 3 }}>
            {children}
          </Box>
        </Fade>
      )}
    </div>
  );
});

TabPanel.displayName = 'TabPanel';

/**
 * Componente de carga para Suspense con animación mejorada
 */
const LoadingFallback = memo(() => (
  <Fade in timeout={300}>
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center', 
      minHeight: 400,
      gap: 2
    }}>
      <CircularProgress size={40} thickness={4} />
      <Typography variant="body2" color="text.secondary">
        Cargando configuración...
      </Typography>
    </Box>
  </Fade>
));

LoadingFallback.displayName = 'LoadingFallback';

/**
 * Componente de contenido de configuración placeholder para tabs sin implementar
 */
const PlaceholderContent = memo<{ tab: SettingsTab }>(({ tab }) => (
  <Grow in timeout={800} style={{ transformOrigin: '0 0 0' }}>
    <Paper 
      sx={{ 
        p: 3,
        // Optimización de animaciones
        willChange: 'transform',
        transition: 'all 0.2s ease',
        '&:hover': {
          transform: 'scale(1.01)',
          boxShadow: 2,
        }
      }}
    >
      <Fade in timeout={600} style={{ transitionDelay: '100ms' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ mr: 2, color: 'primary.main' }}>
            {tab.icon}
          </Box>
          <Typography variant="h6">
            Configuración de {tab.label}
          </Typography>
        </Box>
      </Fade>
      <Fade in timeout={600} style={{ transitionDelay: '200ms' }}>
        <Typography variant="body2" color="text.secondary" paragraph>
          {tab.description}
        </Typography>
      </Fade>
      
      {/* Placeholder para futuras opciones con animación */}
      <List>
        {[1, 2, 3].map((item, index) => (
          <Slide
            key={item}
            direction="right"
            in
            timeout={500}
            style={{ transitionDelay: `${300 + index * 100}ms` }}
          >
            <Box>
              <ListItem>
                <ListItemText
                  primary={
                    <Skeleton 
                      width="60%" 
                      animation="pulse"
                      sx={{
                        animationDelay: `${index * 0.2}s`
                      }}
                    />
                  }
                  secondary={
                    <Skeleton 
                      width="80%" 
                      animation="pulse"
                      sx={{
                        animationDelay: `${index * 0.2 + 0.1}s`
                      }}
                    />
                  }
                />
              </ListItem>
              {item < 3 && <Divider />}
            </Box>
          </Slide>
        ))}
      </List>
    </Paper>
  </Grow>
));

PlaceholderContent.displayName = 'PlaceholderContent';

/**
 * Página de Settings optimizada
 */
const SettingsPage = memo(() => {
  const [activeTab, setActiveTab] = useState(0);

  /**
   * Maneja el cambio de tab con callback memoizado
   */
  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  }, []);

  return (
    <Fade in timeout={600}>
      <Container maxWidth="xl">
        <Box sx={{ py: 3 }}>
          <Fade in timeout={500} style={{ transitionDelay: '100ms' }}>
            <Typography variant="h4" component="h1" gutterBottom>
              Configuración
            </Typography>
          </Fade>
          
          <Grow in timeout={800} style={{ transitionDelay: '200ms', transformOrigin: '0 0 0' }}>
            <Paper sx={{ width: '100%', mt: 2 }}>
              <Tabs
            value={activeTab}
            onChange={handleTabChange}
            aria-label="settings tabs"
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              '& .MuiTab-root': {
                minHeight: 64,
                textTransform: 'none',
              }
            }}
          >
            {SETTINGS_TABS.map((tab, index) => (
              <Tab
                key={tab.id}
                label={tab.label}
                icon={tab.icon}
                id={`settings-tab-${index}`}
                aria-controls={`settings-tabpanel-${index}`}
              />
            ))}
          </Tabs>
          
          <Box sx={{ p: 3 }}>
            {/* Suspense para componentes lazy loaded */}
            <Suspense fallback={<LoadingFallback />}>
              {SETTINGS_TABS.map((tab, index) => (
                <TabPanel key={tab.id} value={activeTab} index={index}>
                  {/* Renderizar componente real según el tab activo */}
                  {tab.id === 'network' && <NetworkSettings />}
                  {tab.id === 'cameras' && <CameraSettings />}
                  {tab.id === 'user' && <UserPreferences />}
                  {/* TODO: Implementar estos componentes cuando se completen en el backend */}
                  {tab.id === 'protocols' && <PlaceholderContent tab={tab} />}
                  {tab.id === 'backup' && <PlaceholderContent tab={tab} />}
                </TabPanel>
              ))}
            </Suspense>
          </Box>
            </Paper>
          </Grow>
        </Box>
      </Container>
    </Fade>
  );
});

// Añadir displayName para debugging
SettingsPage.displayName = 'SettingsPage';

export default SettingsPage;
