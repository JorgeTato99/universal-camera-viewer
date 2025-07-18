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
} from "@mui/material";
import {
  NetworkCheck as NetworkIcon,
  Videocam as CameraIcon,
  Person as UserIcon,
  Router as ProtocolIcon,
  Backup as BackupIcon,
} from "@mui/icons-material";

// Preparado para lazy loading de secciones de configuración
// const NetworkSettings = lazy(() => import("./components/NetworkSettings"));
// const CameraSettings = lazy(() => import("./components/CameraSettings"));
// const UserPreferences = lazy(() => import("./components/UserPreferences"));
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
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
});

TabPanel.displayName = 'TabPanel';

/**
 * Componente de contenido de configuración placeholder
 */
const SettingsContent = memo<{ tab: SettingsTab }>(({ tab }) => (
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
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
      <Box sx={{ mr: 2, color: 'primary.main' }}>
        {tab.icon}
      </Box>
      <Typography variant="h6">
        Configuración de {tab.label}
      </Typography>
    </Box>
    <Typography variant="body2" color="text.secondary" paragraph>
      {tab.description}
    </Typography>
    
    {/* Placeholder para futuras opciones */}
    <List>
      {[1, 2, 3].map((item) => (
        <React.Fragment key={item}>
          <ListItem>
            <ListItemText
              primary={<Skeleton width="60%" />}
              secondary={<Skeleton width="80%" />}
            />
          </ListItem>
          {item < 3 && <Divider />}
        </React.Fragment>
      ))}
    </List>
  </Paper>
));

SettingsContent.displayName = 'SettingsContent';

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
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Configuración
        </Typography>
        
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
            {/* Suspense para futuros componentes lazy loaded */}
            <Suspense fallback={<Skeleton variant="rectangular" height={300} />}>
              {SETTINGS_TABS.map((tab, index) => (
                <TabPanel key={tab.id} value={activeTab} index={index}>
                  <SettingsContent tab={tab} />
                </TabPanel>
              ))}
            </Suspense>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
});

// Añadir displayName para debugging
SettingsPage.displayName = 'SettingsPage';

export default SettingsPage;
