/**
 * Camera Details Card Component
 * Shows comprehensive camera information with new 3FN structure
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Typography,
  Box,
  Chip,
  Button,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Collapse,
  Alert,
  Tab,
  Tabs,
  LinearProgress,
} from '@mui/material';
import {
  Camera as CameraIcon,
  NetworkCheck,
  Security,
  Settings,
  LocationOn,
  Info,
  Speed,
  Storage,
  Edit,
  ExpandMore,
  ExpandLess,
  CheckCircle,
  Error as ErrorIcon,
  VpnKey,
} from '@mui/icons-material';
import { 
  CameraResponse,
  ConnectionStatus,
  isConnected,
  hasCredentials,
  getPrimaryProtocol,
  getVerifiedEndpoint,
} from '../../../types/camera.types.v2';
import { useCameraStoreV2 } from '../../../stores/cameraStore.v2';

interface CameraDetailsCardProps {
  camera: CameraResponse;
  onEdit?: () => void;
  onDelete?: () => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`camera-tabpanel-${index}`}
      aria-labelledby={`camera-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
}

export const CameraDetailsCard: React.FC<CameraDetailsCardProps> = ({
  camera,
  onEdit,
  onDelete,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [credentialsDialogOpen, setCredentialsDialogOpen] = useState(false);
  const [username, setUsername] = useState(camera.credentials?.username || '');
  const [password, setPassword] = useState('');
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  const { 
    isConnecting,
    isSaving,
    connectCamera, 
    disconnectCamera,
    updateCredentials,
  } = useCameraStoreV2();

  const connecting = isConnecting.get(camera.camera_id) || false;
  const saving = isSaving.get(camera.camera_id) || false;
  const connected = isConnected(camera);
  const hasAuth = hasCredentials(camera);
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleConnect = async () => {
    if (connected) {
      await disconnectCamera(camera.camera_id);
    } else {
      await connectCamera(camera.camera_id);
    }
  };

  const handleSaveCredentials = async () => {
    await updateCredentials(camera.camera_id, username, password);
    setCredentialsDialogOpen(false);
    setPassword('');
  };

  const getStatusColor = () => {
    switch (camera.status) {
      case ConnectionStatus.CONNECTED:
      case ConnectionStatus.STREAMING:
        return 'success';
      case ConnectionStatus.CONNECTING:
        return 'info';
      case ConnectionStatus.ERROR:
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardHeader
          avatar={<CameraIcon />}
          title={
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="h6">{camera.display_name}</Typography>
              <Chip
                label={camera.status}
                size="small"
                color={getStatusColor()}
              />
            </Box>
          }
          subheader={`${camera.brand} ${camera.model} • ${camera.ip_address}`}
          action={
            <Box>
              {onEdit && (
                <IconButton onClick={onEdit}>
                  <Edit />
                </IconButton>
              )}
              <IconButton onClick={() => setCredentialsDialogOpen(true)}>
                <VpnKey color={hasAuth ? 'primary' : 'disabled'} />
              </IconButton>
            </Box>
          }
        />

        <CardContent sx={{ flexGrow: 1, pt: 0 }}>
          <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 2 }}>
            <Tab label="General" />
            <Tab label="Connection" />
            <Tab label="Statistics" />
            <Tab label="Advanced" />
          </Tabs>

          <TabPanel value={activeTab} index={0}>
            {/* General Information */}
            <List dense>
              {camera.location && (
                <ListItem>
                  <ListItemIcon>
                    <LocationOn />
                  </ListItemIcon>
                  <ListItemText
                    primary="Location"
                    secondary={camera.location}
                  />
                </ListItem>
              )}
              
              {camera.description && (
                <ListItem>
                  <ListItemIcon>
                    <Info />
                  </ListItemIcon>
                  <ListItemText
                    primary="Description"
                    secondary={camera.description}
                  />
                </ListItem>
              )}

              <ListItem>
                <ListItemIcon>
                  <Storage />
                </ListItemIcon>
                <ListItemText
                  primary="Camera ID"
                  secondary={camera.camera_id}
                />
              </ListItem>

              {camera.mac_address && (
                <ListItem>
                  <ListItemIcon>
                    <NetworkCheck />
                  </ListItemIcon>
                  <ListItemText
                    primary="MAC Address"
                    secondary={camera.mac_address}
                  />
                </ListItem>
              )}

              {camera.firmware_version && (
                <ListItem>
                  <ListItemIcon>
                    <Settings />
                  </ListItemIcon>
                  <ListItemText
                    primary="Firmware"
                    secondary={camera.firmware_version}
                  />
                </ListItem>
              )}
            </List>
          </TabPanel>

          <TabPanel value={activeTab} index={1}>
            {/* Connection Information */}
            <Box mb={2}>
              <Typography variant="subtitle2" gutterBottom>
                Protocols
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                {camera.protocols.map(protocol => (
                  <Chip
                    key={protocol.protocol_type}
                    label={`${protocol.protocol_type.toUpperCase()} :${protocol.port}`}
                    color={protocol.is_primary ? 'primary' : 'default'}
                    variant={protocol.is_enabled ? 'filled' : 'outlined'}
                    icon={protocol.is_primary ? <CheckCircle /> : undefined}
                  />
                ))}
              </Box>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box>
              <Box 
                display="flex" 
                alignItems="center" 
                justifyContent="space-between"
                sx={{ cursor: 'pointer' }}
                onClick={() => toggleSection('endpoints')}
              >
                <Typography variant="subtitle2">
                  Discovered Endpoints ({camera.endpoints.length})
                </Typography>
                <IconButton size="small">
                  {expandedSections.endpoints ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Box>

              <Collapse in={expandedSections.endpoints}>
                <List dense>
                  {camera.endpoints.map((endpoint, idx) => (
                    <ListItem key={idx}>
                      <ListItemIcon>
                        {endpoint.is_verified ? (
                          <CheckCircle color="success" />
                        ) : (
                          <ErrorIcon color="disabled" />
                        )}
                      </ListItemIcon>
                      <ListItemText
                        primary={endpoint.type}
                        secondary={
                          <Box>
                            <Typography variant="caption" component="div">
                              {endpoint.url}
                            </Typography>
                            {endpoint.response_time_ms && (
                              <Typography variant="caption" color="text.secondary">
                                Response: {endpoint.response_time_ms}ms
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            </Box>
          </TabPanel>

          <TabPanel value={activeTab} index={2}>
            {/* Statistics */}
            {camera.statistics && (
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Connection Success Rate"
                    secondary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <LinearProgress
                          variant="determinate"
                          value={camera.statistics.success_rate}
                          sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="body2">
                          {camera.statistics.success_rate.toFixed(1)}%
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>

                <ListItem>
                  <ListItemText
                    primary="Total Connections"
                    secondary={camera.statistics.total_connections}
                  />
                </ListItem>

                <ListItem>
                  <ListItemText
                    primary="Uptime"
                    secondary={`${camera.statistics.total_uptime_minutes} minutes`}
                  />
                </ListItem>

                {camera.statistics.average_fps && (
                  <ListItem>
                    <ListItemIcon>
                      <Speed />
                    </ListItemIcon>
                    <ListItemText
                      primary="Average FPS"
                      secondary={camera.statistics.average_fps.toFixed(1)}
                    />
                  </ListItem>
                )}

                {camera.statistics.last_error_message && (
                  <ListItem>
                    <Alert severity="error" sx={{ width: '100%' }}>
                      <Typography variant="caption">
                        Last error: {camera.statistics.last_error_message}
                      </Typography>
                    </Alert>
                  </ListItem>
                )}
              </List>
            )}
          </TabPanel>

          <TabPanel value={activeTab} index={3}>
            {/* Advanced Settings */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Stream Profiles
              </Typography>
              <List dense>
                {camera.stream_profiles.map((profile, idx) => (
                  <ListItem key={idx}>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          {profile.profile_name}
                          {profile.is_default && (
                            <Chip label="Default" size="small" color="primary" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Typography variant="caption">
                          {profile.resolution} • {profile.fps}fps • {profile.codec}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Capabilities
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                {camera.capabilities.has_ptz && (
                  <Chip label="PTZ" size="small" />
                )}
                {camera.capabilities.has_audio && (
                  <Chip label="Audio" size="small" />
                )}
                {camera.capabilities.has_ir && (
                  <Chip label="IR" size="small" />
                )}
                {camera.capabilities.has_motion_detection && (
                  <Chip label="Motion" size="small" />
                )}
              </Box>
            </Box>
          </TabPanel>
        </CardContent>

        <CardActions>
          <Button
            onClick={handleConnect}
            disabled={connecting || !hasAuth}
            startIcon={connecting ? <LinearProgress sx={{ width: 20 }} /> : null}
            color={connected ? 'error' : 'primary'}
          >
            {connecting ? 'Processing...' : connected ? 'Disconnect' : 'Connect'}
          </Button>
          
          {onDelete && (
            <Button color="error" onClick={onDelete}>
              Delete
            </Button>
          )}
        </CardActions>
      </Card>

      {/* Credentials Dialog */}
      <Dialog
        open={credentialsDialogOpen}
        onClose={() => setCredentialsDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Security />
            Update Credentials
          </Box>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            helperText="Leave empty to keep current password"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCredentialsDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSaveCredentials}
            disabled={saving || !username}
            variant="contained"
          >
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};