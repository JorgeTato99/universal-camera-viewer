/**
 * 🌐 Remote Server Selector - Universal Camera Viewer
 * Selector de servidor MediaMTX remoto con indicadores de estado
 * 
 * Características:
 * - Lista de servidores disponibles
 * - Indicador de estado de autenticación
 * - Opción para agregar nuevo servidor
 * - Filtrado por servidores autenticados
 */

import React, { memo, useState } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Chip,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  Tooltip,
  SelectChangeEvent,
  FormHelperText,
  Badge
} from '@mui/material';
import {
  CloudQueue,
  Add,
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Refresh,
  VpnKey
} from '@mui/icons-material';
import { AuthStatus } from '../../../../services/publishing/mediamtxRemoteService';
import type { MediaMTXServer } from '../../../../services/publishing/mediamtxServerService';

interface RemoteServerSelectorProps {
  servers: MediaMTXServer[];
  authStatuses?: Map<number, AuthStatus>;
  selectedServerId?: number;
  onChange: (serverId: number) => void;
  onAddServer?: () => void;
  onAuthServer?: (serverId: number) => void;
  onRefreshStatus?: (serverId: number) => void;
  label?: string;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
  showOnlyAuthenticated?: boolean;
  fullWidth?: boolean;
}

/**
 * Selector de servidor MediaMTX remoto
 */
export const RemoteServerSelector = memo<RemoteServerSelectorProps>(({
  servers,
  authStatuses = new Map(),
  selectedServerId,
  onChange,
  onAddServer,
  onAuthServer,
  onRefreshStatus,
  label = 'Servidor MediaMTX',
  helperText,
  required = false,
  disabled = false,
  showOnlyAuthenticated = false,
  fullWidth = true
}) => {
  const [isOpen, setIsOpen] = useState(false);

  // Filtrar servidores según configuración
  const filteredServers = showOnlyAuthenticated
    ? servers.filter(server => {
        const authStatus = authStatuses.get(server.id);
        return authStatus?.is_authenticated;
      })
    : servers;

  // Obtener servidor seleccionado
  const selectedServer = servers.find(s => s.id === selectedServerId);

  // Manejar cambio de selección
  const handleChange = (event: SelectChangeEvent<number>) => {
    const value = event.target.value;
    if (typeof value === 'number') {
      onChange(value);
    }
  };

  // Obtener icono y color según estado
  const getServerStatus = (server: MediaMTXServer) => {
    const authStatus = authStatuses.get(server.id);
    
    if (!authStatus) {
      return {
        icon: <Warning />,
        color: 'default' as const,
        label: 'No verificado'
      };
    }
    
    if (authStatus.is_authenticated) {
      return {
        icon: <CheckCircle />,
        color: 'success' as const,
        label: 'Autenticado'
      };
    }
    
    if (authStatus.error) {
      return {
        icon: <ErrorIcon />,
        color: 'error' as const,
        label: 'Error'
      };
    }
    
    return {
      icon: <CloudQueue />,
      color: 'default' as const,
      label: 'Desconectado'
    };
  };

  // Renderizar item de servidor
  const renderServerItem = (server: MediaMTXServer) => {
    const status = getServerStatus(server);
    const authStatus = authStatuses.get(server.id);
    
    return (
      <MenuItem key={server.id} value={server.id}>
        <ListItemIcon>
          <Badge
            badgeContent={status.icon}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            sx={{
              '& .MuiBadge-badge': {
                right: -3,
                bottom: -3,
                border: '2px solid',
                borderColor: 'background.paper',
                padding: 0,
                minWidth: 'auto',
                height: 'auto',
                backgroundColor: 'transparent'
              }
            }}
          >
            <CloudQueue />
          </Badge>
        </ListItemIcon>
        
        <ListItemText
          primary={server.name}
          secondary={
            <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                {server.url}
              </Typography>
              {authStatus?.error && (
                <Typography variant="caption" color="error">
                  • {authStatus.error}
                </Typography>
              )}
            </Box>
          }
        />
        
        <Box sx={{ display: 'flex', gap: 0.5, ml: 2 }}>
          {onRefreshStatus && (
            <Tooltip title="Verificar estado">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onRefreshStatus(server.id);
                }}
              >
                <Refresh fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          
          {onAuthServer && !authStatus?.is_authenticated && (
            <Tooltip title="Autenticar">
              <IconButton
                size="small"
                color="primary"
                onClick={(e) => {
                  e.stopPropagation();
                  onAuthServer(server.id);
                }}
              >
                <VpnKey fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </MenuItem>
    );
  };

  return (
    <FormControl 
      fullWidth={fullWidth} 
      required={required} 
      disabled={disabled}
      error={required && !selectedServerId}
    >
      <InputLabel id="remote-server-selector-label">
        {label}
      </InputLabel>
      
      <Select
        labelId="remote-server-selector-label"
        id="remote-server-selector"
        value={selectedServerId || ''}
        onChange={handleChange}
        label={label}
        open={isOpen}
        onOpen={() => setIsOpen(true)}
        onClose={() => setIsOpen(false)}
        renderValue={(value) => {
          if (!value || !selectedServer) return '';
          
          const status = getServerStatus(selectedServer);
          
          return (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CloudQueue />
              <Typography>{selectedServer.name}</Typography>
              <Chip
                label={status.label}
                size="small"
                color={status.color}
                icon={status.icon}
              />
            </Box>
          );
        }}
      >
        {/* Servidores disponibles */}
        {filteredServers.length > 0 ? (
          filteredServers.map(renderServerItem)
        ) : (
          <MenuItem disabled>
            <Typography variant="body2" color="text.secondary">
              {showOnlyAuthenticated 
                ? 'No hay servidores autenticados'
                : 'No hay servidores configurados'
              }
            </Typography>
          </MenuItem>
        )}
        
        {/* Opción para agregar servidor */}
        {onAddServer && (
          <>
            <Divider />
            <MenuItem onClick={onAddServer}>
              <ListItemIcon>
                <Add />
              </ListItemIcon>
              <ListItemText primary="Agregar servidor..." />
            </MenuItem>
          </>
        )}
      </Select>
      
      {helperText && (
        <FormHelperText>{helperText}</FormHelperText>
      )}
      
      {showOnlyAuthenticated && servers.length > filteredServers.length && (
        <FormHelperText>
          {servers.length - filteredServers.length} servidor(es) sin autenticar
        </FormHelperText>
      )}
    </FormControl>
  );
});

RemoteServerSelector.displayName = 'RemoteServerSelector';