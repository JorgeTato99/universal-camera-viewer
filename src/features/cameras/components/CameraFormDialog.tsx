/**
 * Camera Form Dialog Component
 * Form for creating/editing cameras with new 3FN structure
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  InputAdornment,
  Alert,
  Chip,
  FormControlLabel,
  Switch,
  Tabs,
  Tab,
} from '@mui/material';
import {
  ExpandMore,
  Camera as CameraIcon,
  Add,
  Delete,
  TestConnection,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import {
  CameraFormData,
  CreateCameraRequest,
  ProtocolType,
  AuthType,
  DEFAULT_CAMERA_FORM,
  TestConnectionRequest,
} from '../../../types/camera.types.v2';
import { cameraServiceV2 } from '../../../services/python/cameraService.v2';
import { notificationStore } from '../../../stores/notificationStore';

interface CameraFormDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: CameraFormData) => Promise<void>;
  initialData?: Partial<CameraFormData>;
  mode: 'create' | 'edit';
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
      {...other}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
}

const CAMERA_BRANDS = [
  { value: 'dahua', label: 'Dahua' },
  { value: 'hikvision', label: 'Hikvision' },
  { value: 'tplink', label: 'TP-Link' },
  { value: 'steren', label: 'Steren' },
  { value: 'reolink', label: 'Reolink' },
  { value: 'xiaomi', label: 'Xiaomi' },
  { value: 'generic', label: 'Generic' },
];

export const CameraFormDialog: React.FC<CameraFormDialogProps> = ({
  open,
  onClose,
  onSubmit,
  initialData,
  mode,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState<CameraFormData>({
    ...DEFAULT_CAMERA_FORM,
    ...initialData,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (open) {
      setFormData({
        ...DEFAULT_CAMERA_FORM,
        ...initialData,
      });
      setTestResult(null);
      setErrors({});
      setActiveTab(0);
    }
  }, [open, initialData]);

  const handleChange = (field: keyof CameraFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.display_name?.trim()) {
      newErrors.display_name = 'Display name is required';
    }

    if (!formData.ip?.trim()) {
      newErrors.ip = 'IP address is required';
    } else {
      // Basic IP validation
      const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
      if (!ipRegex.test(formData.ip)) {
        newErrors.ip = 'Invalid IP address format';
      }
    }

    if (!formData.username?.trim()) {
      newErrors.username = 'Username is required';
    }

    if (mode === 'create' && !formData.password?.trim()) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleTestConnection = async () => {
    if (!validateForm()) {
      notificationStore.addNotification({
        type: 'error',
        message: 'Please fill in all required fields',
      });
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const testRequest: TestConnectionRequest = {
        ip: formData.ip!,
        username: formData.username!,
        password: formData.password!,
        brand: formData.brand,
        protocol: ProtocolType.ONVIF,
        port: formData.onvif_port,
      };

      const result = await cameraServiceV2.testConnection(testRequest);
      
      setTestResult({
        success: result.success,
        message: result.message,
      });

      if (result.discovered_endpoints && result.discovered_endpoints.length > 0) {
        notificationStore.addNotification({
          type: 'success',
          message: `Found ${result.discovered_endpoints.length} endpoints`,
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: String(error),
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      setActiveTab(0); // Go to basic tab if validation fails
      return;
    }

    try {
      await onSubmit(formData as CameraFormData);
      onClose();
    } catch (error) {
      notificationStore.addNotification({
        type: 'error',
        message: `Error ${mode === 'create' ? 'creating' : 'updating'} camera: ${error}`,
      });
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <CameraIcon />
          {mode === 'create' ? 'Add New Camera' : 'Edit Camera'}
        </Box>
      </DialogTitle>

      <DialogContent>
        <Tabs
          value={activeTab}
          onChange={(_, value) => setActiveTab(value)}
          sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
        >
          <Tab label="Basic Info" />
          <Tab label="Connection" />
          <Tab label="Advanced" />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          {/* Basic Information */}
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Display Name"
                value={formData.display_name || ''}
                onChange={(e) => handleChange('display_name', e.target.value)}
                error={!!errors.display_name}
                helperText={errors.display_name}
                required
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Brand</InputLabel>
                <Select
                  value={formData.brand || 'generic'}
                  onChange={(e) => handleChange('brand', e.target.value)}
                  label="Brand"
                >
                  {CAMERA_BRANDS.map(brand => (
                    <MenuItem key={brand.value} value={brand.value}>
                      {brand.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Model"
                value={formData.model || ''}
                onChange={(e) => handleChange('model', e.target.value)}
                placeholder="e.g., DH-IPC-HFW2431S"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Location"
                value={formData.location || ''}
                onChange={(e) => handleChange('location', e.target.value)}
                placeholder="e.g., Main Entrance"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="IP Address"
                value={formData.ip || ''}
                onChange={(e) => handleChange('ip', e.target.value)}
                error={!!errors.ip}
                helperText={errors.ip}
                required
                placeholder="192.168.1.100"
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Description"
                value={formData.description || ''}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="Additional notes about this camera..."
              />
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* Connection Settings */}
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Authentication
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Username"
                value={formData.username || ''}
                onChange={(e) => handleChange('username', e.target.value)}
                error={!!errors.username}
                helperText={errors.username}
                required
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password || ''}
                onChange={(e) => handleChange('password', e.target.value)}
                error={!!errors.password}
                helperText={errors.password || (mode === 'edit' ? 'Leave empty to keep current' : '')}
                required={mode === 'create'}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Auth Type</InputLabel>
                <Select
                  value={formData.auth_type || AuthType.BASIC}
                  onChange={(e) => handleChange('auth_type', e.target.value)}
                  label="Auth Type"
                >
                  <MenuItem value={AuthType.BASIC}>Basic</MenuItem>
                  <MenuItem value={AuthType.DIGEST}>Digest</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography>Protocol Ports (Optional)</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        label="ONVIF Port"
                        type="number"
                        value={formData.onvif_port || 80}
                        onChange={(e) => handleChange('onvif_port', parseInt(e.target.value))}
                        InputProps={{ inputProps: { min: 1, max: 65535 } }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        label="RTSP Port"
                        type="number"
                        value={formData.rtsp_port || 554}
                        onChange={(e) => handleChange('rtsp_port', parseInt(e.target.value))}
                        InputProps={{ inputProps: { min: 1, max: 65535 } }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        label="HTTP Port"
                        type="number"
                        value={formData.http_port || 80}
                        onChange={(e) => handleChange('http_port', parseInt(e.target.value))}
                        InputProps={{ inputProps: { min: 1, max: 65535 } }}
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>

            <Grid item xs={12}>
              <Box display="flex" justifyContent="center" mt={2}>
                <Button
                  variant="outlined"
                  startIcon={<TestConnection />}
                  onClick={handleTestConnection}
                  disabled={testing}
                >
                  {testing ? 'Testing...' : 'Test Connection'}
                </Button>
              </Box>

              {testResult && (
                <Alert
                  severity={testResult.success ? 'success' : 'error'}
                  sx={{ mt: 2 }}
                >
                  {testResult.message}
                </Alert>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {/* Advanced Settings */}
          <Alert severity="info" sx={{ mb: 2 }}>
            Advanced settings can be configured after the camera is created.
            The system will automatically discover endpoints and capabilities.
          </Alert>

          <Typography variant="body2" color="text.secondary">
            After creating the camera, you can:
          </Typography>
          <Box component="ul" sx={{ mt: 1 }}>
            <Typography component="li" variant="body2" color="text.secondary">
              Configure multiple stream profiles
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Add custom RTSP endpoints
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Set up recording schedules
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Configure motion detection zones
            </Typography>
          </Box>
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={testing}
        >
          {mode === 'create' ? 'Add Camera' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};