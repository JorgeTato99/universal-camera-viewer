/**
 * 🔌 Server Connection Status - Universal Camera Viewer
 * Indicador visual del estado de conexión con servidores MediaMTX
 * 
 * Muestra:
 * - Estado de autenticación
 * - Último chequeo de conexión
 * - Acciones rápidas (reconectar, cerrar sesión)
 */

import React, { memo } from 'react';
import {
  Box,
  Chip,
  Typography,
  IconButton,
  Tooltip,
  CircularProgress,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  Warning as WarningIcon,
  CloudOff,
  MoreVert,
  Refresh,
  Logout,
  VpnKey,
  Info as InfoIcon,
  Schedule as TimeIcon
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { MediaMTXServer, AuthStatus } from '../../../../services/publishing/mediamtxRemoteService';

interface ServerConnectionStatusProps {
  server: MediaMTXServer;
  authStatus?: AuthStatus;
  isChecking?: boolean;
  onRefresh?: () => void;
  onAuthenticate?: () => void;
  onLogout?: () => void;
  variant?: 'compact' | 'detailed';
}

/**
 * Componente para mostrar el estado de conexión del servidor
 */
export const ServerConnectionStatus = memo<ServerConnectionStatusProps>(({
  server,
  authStatus,
  isChecking = false,
  onRefresh,
  onAuthenticate,
  onLogout,
  variant = 'compact'
}) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // Determinar estado de conexión
  const getConnectionStatus = () => {
    if (isChecking) {
      return {
        status: 'checking',
        label: 'Verificando...',
        color: 'info' as const,
        icon: <CircularProgress size={16} />
      };
    }

    if (!authStatus) {
      return {
        status: 'unknown',
        label: 'No verificado',
        color: 'default' as const,
        icon: <WarningIcon />
      };
    }

    if (authStatus.is_authenticated) {
      return {
        status: 'authenticated',
        label: 'Autenticado',
        color: 'success' as const,
        icon: <CheckCircle />
      };
    }

    if (authStatus.error) {
      return {
        status: 'error',
        label: 'Error',
        color: 'error' as const,
        icon: <ErrorIcon />
      };
    }

    return {
      status: 'disconnected',
      label: 'Desconectado',
      color: 'warning' as const,
      icon: <CloudOff />
    };
  };

  const connectionStatus = getConnectionStatus();

  // Formatear tiempo desde último chequeo
  const formatLastCheck = () => {
    if (!authStatus?.last_check) return 'Nunca';
    
    try {
      return formatDistanceToNow(new Date(authStatus.last_check), {
        addSuffix: true,
        locale: es
      });
    } catch {
      return 'Desconocido';
    }
  };

  // Renderizar versión compacta
  if (variant === 'compact') {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Tooltip
          title={
            <Box>
              <Typography variant="body2">{server.name}</Typography>
              <Typography variant="caption">
                Estado: {connectionStatus.label}
              </Typography>
              {authStatus?.last_check && (
                <Typography variant="caption" sx={{ display: 'block' }}>
                  Verificado: {formatLastCheck()}
                </Typography>
              )}
            </Box>
          }
        >
          <Chip
            label={connectionStatus.label}
            color={connectionStatus.color}
            size="small"
            icon={connectionStatus.icon}
            sx={{ cursor: 'pointer' }}
            onClick={onRefresh}
          />
        </Tooltip>

        {(onRefresh || onAuthenticate || onLogout) && (
          <>
            <IconButton size="small" onClick={handleMenuOpen}>
              <MoreVert fontSize="small" />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={menuOpen}
              onClose={handleMenuClose}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
            >
              {onRefresh && (
                <MenuItem onClick={() => { handleMenuClose(); onRefresh(); }}>
                  <ListItemIcon>
                    <Refresh fontSize="small" />
                  </ListItemIcon>
                  <ListItemText>Verificar conexión</ListItemText>
                </MenuItem>
              )}
              
              {onAuthenticate && !authStatus?.is_authenticated && (
                <MenuItem onClick={() => { handleMenuClose(); onAuthenticate(); }}>
                  <ListItemIcon>
                    <VpnKey fontSize="small" />
                  </ListItemIcon>
                  <ListItemText>Autenticar</ListItemText>
                </MenuItem>
              )}
              
              {onLogout && authStatus?.is_authenticated && (
                <>
                  <Divider />
                  <MenuItem onClick={() => { handleMenuClose(); onLogout(); }}>
                    <ListItemIcon>
                      <Logout fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>Cerrar sesión</ListItemText>
                  </MenuItem>
                </>
              )}
            </Menu>
          </>
        )}
      </Box>
    );
  }

  // Renderizar versión detallada
  return (
    <Box
      sx={{
        p: 2,
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        bgcolor: 'background.paper'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            {server.name}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Chip
              label={connectionStatus.label}
              color={connectionStatus.color}
              size="small"
              icon={connectionStatus.icon}
            />
            
            {authStatus?.last_check && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <TimeIcon sx={{ fontSize: 14 }} />
                {formatLastCheck()}
              </Typography>
            )}
          </Box>

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
            {server.url}
          </Typography>
          
          {authStatus?.error && (
            <Typography variant="caption" color="error" sx={{ display: 'block', mt: 0.5 }}>
              {authStatus.error}
            </Typography>
          )}
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {onRefresh && (
            <Tooltip title="Verificar conexión">
              <IconButton
                size="small"
                onClick={onRefresh}
                disabled={isChecking}
              >
                {isChecking ? <CircularProgress size={20} /> : <Refresh />}
              </IconButton>
            </Tooltip>
          )}
          
          {onAuthenticate && !authStatus?.is_authenticated && (
            <Tooltip title="Autenticar">
              <IconButton
                size="small"
                onClick={onAuthenticate}
                color="primary"
              >
                <VpnKey />
              </IconButton>
            </Tooltip>
          )}
          
          {onLogout && authStatus?.is_authenticated && (
            <Tooltip title="Cerrar sesión">
              <IconButton
                size="small"
                onClick={onLogout}
                color="error"
              >
                <Logout />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Información adicional para versión detallada */}
      {authStatus?.is_authenticated && authStatus.token_expires_at && (
        <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <InfoIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              Token expira: {new Date(authStatus.token_expires_at).toLocaleString('es-ES')}
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
});

ServerConnectionStatus.displayName = 'ServerConnectionStatus';