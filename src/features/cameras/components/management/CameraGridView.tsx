/**
 * 🎯 Camera Grid View Component
 * Vista de cuadrícula para mostrar cámaras con cards grandes y preview
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  Typography,
  Chip,
  IconButton,
  Checkbox,
  Skeleton,
  Tooltip,
  Menu,
  MenuItem,
  Grid,
  alpha,
  useTheme,
} from '@mui/material';
import {
  MoreVert as MoreIcon,
  Videocam as VideocamIcon,
  Circle as StatusIcon,
  LocationOn as LocationIcon,
  Router as RouterIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PowerSettingsNew as ConnectIcon,
  Settings as SettingsIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { CameraResponse, ConnectionStatus } from '../../../../types/camera.types.v2';
import { useNavigate } from 'react-router-dom';
import { useCameraStoreV2 } from '../../../../stores/cameraStore.v2';
import { VideoStream } from '../VideoStream';

interface CameraGridViewProps {
  cameras: CameraResponse[];
  isLoading: boolean;
  selectedCameras: Set<string>;
  onSelectCamera: (cameraId: string, selected: boolean) => void;
  gridColumns?: number;
}

interface CameraCardProps {
  camera: CameraResponse;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
}

const CameraCard: React.FC<CameraCardProps> = ({ camera, isSelected, onSelect }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { connectCamera, disconnectCamera } = useCameraStoreV2();
  const [menuAnchor, setMenuAnchor] = React.useState<null | HTMLElement>(null);

  const getStatusColor = () => {
    switch (camera.status) {
      case ConnectionStatus.CONNECTED:
        return theme.palette.success.main;
      case ConnectionStatus.CONNECTING:
        return theme.palette.warning.main;
      case ConnectionStatus.ERROR:
        return theme.palette.error.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getStatusLabel = () => {
    switch (camera.status) {
      case ConnectionStatus.CONNECTED:
        return 'Conectada';
      case ConnectionStatus.CONNECTING:
        return 'Conectando...';
      case ConnectionStatus.ERROR:
        return 'Error';
      default:
        return 'Desconectada';
    }
  };

  const handleMenuClose = () => setMenuAnchor(null);

  const handleConnect = async () => {
    if (camera.status === ConnectionStatus.CONNECTED) {
      await disconnectCamera(camera.camera_id);
    } else {
      await connectCamera(camera.camera_id);
    }
  };

  const handleView = () => {
    navigate(`/cameras/${camera.camera_id}/view`);
  };

  const handleEdit = () => {
    navigate(`/cameras/${camera.camera_id}/edit`);
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        transition: 'all 0.2s ease-in-out',
        cursor: 'pointer',
        ...(isSelected && {
          borderColor: 'primary.main',
          borderWidth: 2,
          borderStyle: 'solid',
          transform: 'translateY(-2px)',
          boxShadow: theme.shadows[8],
        }),
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[12],
          '& .camera-actions': {
            opacity: 1,
          },
        },
      }}
      onClick={handleView}
    >
      {/* Checkbox de selección */}
      <Box
        sx={{
          position: 'absolute',
          top: 8,
          left: 8,
          zIndex: 1,
          bgcolor: alpha(theme.palette.background.paper, 0.8),
          borderRadius: 1,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <Checkbox
          checked={isSelected}
          onChange={(e) => onSelect(e.target.checked)}
          size="small"
        />
      </Box>

      {/* Menú de acciones */}
      <Box
        sx={{
          position: 'absolute',
          top: 8,
          right: 8,
          zIndex: 1,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            setMenuAnchor(e.currentTarget);
          }}
          sx={{
            bgcolor: alpha(theme.palette.background.paper, 0.8),
            '&:hover': {
              bgcolor: alpha(theme.palette.background.paper, 0.95),
            },
          }}
        >
          <MoreIcon />
        </IconButton>
      </Box>

      {/* Preview de la cámara */}
      <CardMedia
        sx={{
          height: 200,
          bgcolor: 'grey.900',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}
      >
        {camera.is_connected ? (
          <VideoStream
            cameraId={camera.camera_id}
            isConnected={camera.is_connected}
            aspectRatio="16/9"
            height="100%"
          />
        ) : (
          <VideocamIcon sx={{ fontSize: 60, color: 'grey.700' }} />
        )}

        {/* Estado overlay */}
        <Chip
          icon={<StatusIcon sx={{ fontSize: 12 }} />}
          label={getStatusLabel()}
          size="small"
          sx={{
            position: 'absolute',
            bottom: 8,
            right: 8,
            bgcolor: alpha(theme.palette.background.paper, 0.9),
            color: getStatusColor(),
            fontWeight: 600,
          }}
        />
      </CardMedia>

      {/* Información de la cámara */}
      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        <Typography variant="h6" gutterBottom noWrap>
          {camera.display_name}
        </Typography>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <RouterIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="body2" color="text.secondary">
              {camera.ip_address}
            </Typography>
          </Box>

          {camera.location && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LocationIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary" noWrap>
                {camera.location}
              </Typography>
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: 0.5, mt: 1 }}>
            <Chip
              label={camera.brand}
              size="small"
              variant="outlined"
            />
            <Chip
              label={camera.model}
              size="small"
              variant="outlined"
            />
          </Box>
        </Box>
      </CardContent>

      {/* Acciones rápidas */}
      <CardActions
        className="camera-actions"
        sx={{
          opacity: 0,
          transition: 'opacity 0.2s',
          justifyContent: 'space-between',
          px: 2,
        }}
      >
        <Tooltip title={camera.is_connected ? 'Desconectar' : 'Conectar'}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleConnect();
            }}
            color={camera.is_connected ? 'error' : 'success'}
          >
            <ConnectIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Configuración">
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleEdit();
            }}
          >
            <SettingsIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Ver detalles">
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleView();
            }}
          >
            <InfoIcon />
          </IconButton>
        </Tooltip>
      </CardActions>

      {/* Menú contextual */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        onClick={(e) => e.stopPropagation()}
      >
        <MenuItem onClick={handleView}>
          <InfoIcon fontSize="small" sx={{ mr: 1 }} />
          Ver detalles
        </MenuItem>
        <MenuItem onClick={handleEdit}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Editar
        </MenuItem>
        <MenuItem onClick={handleConnect}>
          <ConnectIcon fontSize="small" sx={{ mr: 1 }} />
          {camera.is_connected ? 'Desconectar' : 'Conectar'}
        </MenuItem>
        <MenuItem>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Eliminar
        </MenuItem>
      </Menu>
    </Card>
  );
};

export const CameraGridView: React.FC<CameraGridViewProps> = ({
  cameras,
  isLoading,
  selectedCameras,
  onSelectCamera,
  gridColumns = 3,
}) => {
  if (isLoading) {
    return (
      <Grid container spacing={3}>
        {[...Array(6)].map((_, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 4, lg: 4 / gridColumns * 12 }} key={index}>
            <Card>
              <Skeleton variant="rectangular" height={200} />
              <CardContent>
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="40%" />
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Skeleton variant="rectangular" width={60} height={24} />
                  <Skeleton variant="rectangular" width={80} height={24} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  }

  return (
    <Grid container spacing={3}>
      {cameras.map((camera) => (
        <Grid 
          size={{ 
            xs: 12, 
            sm: 6, 
            md: 4, 
            lg: 4 / gridColumns * 12 
          }} 
          key={camera.camera_id}
        >
          <CameraCard
            camera={camera}
            isSelected={selectedCameras.has(camera.camera_id)}
            onSelect={(selected) => onSelectCamera(camera.camera_id, selected)}
          />
        </Grid>
      ))}
    </Grid>
  );
};