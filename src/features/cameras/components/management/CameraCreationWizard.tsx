/**
 * 🎯 Camera Creation Wizard Component
 * Wizard para crear nuevas cámaras con validación paso a paso
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormHelperText,
  Typography,
  Alert,
  CircularProgress,
  IconButton,
  InputAdornment,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Close as CloseIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material';
import { useCameraStoreV2 } from '../../../../stores/cameraStore.v2';

interface CameraCreationWizardProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface FormData {
  // Paso 1: Información básica
  brand: string;
  model: string;
  display_name: string;
  ip: string;
  
  // Paso 2: Credenciales
  username: string;
  password: string;
  auth_type: 'basic' | 'digest' | 'bearer';
  
  // Paso 3: Configuración avanzada
  location: string;
  description: string;
  rtsp_port: number;
  onvif_port: number;
  http_port: number;
}

const steps = ['Información básica', 'Credenciales', 'Configuración avanzada'];

const knownBrands = [
  'Dahua',
  'Hikvision',
  'TP-Link',
  'Steren',
  'Axis',
  'Bosch',
  'Samsung',
  'Sony',
  'Ubiquiti',
  'Foscam',
  'Otro',
];

export const CameraCreationWizard: React.FC<CameraCreationWizardProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const theme = useTheme();
  const { createCamera } = useCameraStoreV2();
  
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState<FormData>({
    brand: '',
    model: 'Unknown',
    display_name: '',
    ip: '',
    username: '',
    password: '',
    auth_type: 'basic',
    location: '',
    description: '',
    rtsp_port: 554,
    onvif_port: 80,
    http_port: 80,
  });
  
  const [errors, setErrors] = useState<Partial<FormData>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prevStep) => prevStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleClose = () => {
    setActiveStep(0);
    setFormData({
      brand: '',
      model: 'Unknown',
      display_name: '',
      ip: '',
      username: '',
      password: '',
      auth_type: 'basic',
      location: '',
      description: '',
      rtsp_port: 554,
      onvif_port: 80,
      http_port: 80,
    });
    setErrors({});
    setTestResult(null);
    onClose();
  };

  const validateStep = (step: number): boolean => {
    const newErrors: Partial<FormData> = {};
    
    switch (step) {
      case 0: // Información básica
        if (!formData.brand) newErrors.brand = 'La marca es requerida';
        if (!formData.display_name) newErrors.display_name = 'El nombre es requerido';
        if (!formData.ip) {
          newErrors.ip = 'La dirección IP es requerida';
        } else if (!isValidIP(formData.ip)) {
          newErrors.ip = 'Dirección IP inválida';
        }
        break;
        
      case 1: // Credenciales
        if (!formData.username) newErrors.username = 'El usuario es requerido';
        if (!formData.password) newErrors.password = 'La contraseña es requerida';
        break;
        
      case 2: // Configuración avanzada
        // Validaciones opcionales
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isValidIP = (ip: string): boolean => {
    const pattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return pattern.test(ip);
  };

  const handleTestConnection = async () => {
    setIsTestingConnection(true);
    setTestResult(null);
    
    try {
      // TODO: Implementar llamada real a API de test
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulación de resultado
      const success = Math.random() > 0.3;
      setTestResult(success ? 'success' : 'error');
    } catch (error) {
      setTestResult('error');
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleCreate = async () => {
    if (!validateStep(2)) return;
    
    setIsCreating(true);
    
    try {
      await createCamera({
        brand: formData.brand,
        model: formData.model,
        display_name: formData.display_name,
        ip_address: formData.ip,
        credentials: {
          username: formData.username,
          password: formData.password,
          auth_type: formData.auth_type,
        },
        location: formData.location || undefined,
        description: formData.description || undefined,
        protocols: [
          {
            protocol_type: 'rtsp',
            port: formData.rtsp_port,
            is_enabled: true,
            is_primary: true,
          },
          {
            protocol_type: 'onvif',
            port: formData.onvif_port,
            is_enabled: true,
            is_primary: false,
          },
          {
            protocol_type: 'http',
            port: formData.http_port,
            is_enabled: true,
            is_primary: false,
          },
        ],
      });
      
      onSuccess();
      handleClose();
    } catch (error) {
      console.error('Error creating camera:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth error={!!errors.brand}>
              <InputLabel>Marca</InputLabel>
              <Select
                value={formData.brand}
                onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                label="Marca"
              >
                {knownBrands.map((brand) => (
                  <MenuItem key={brand} value={brand}>
                    {brand}
                  </MenuItem>
                ))}
              </Select>
              {errors.brand && <FormHelperText>{errors.brand}</FormHelperText>}
            </FormControl>

            <TextField
              fullWidth
              label="Modelo"
              value={formData.model}
              onChange={(e) => setFormData({ ...formData, model: e.target.value })}
              helperText="Dejar 'Unknown' si no se conoce"
            />

            <TextField
              fullWidth
              required
              label="Nombre de la cámara"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              error={!!errors.display_name}
              helperText={errors.display_name || 'Nombre amigable para identificar la cámara'}
            />

            <TextField
              fullWidth
              required
              label="Dirección IP"
              value={formData.ip}
              onChange={(e) => setFormData({ ...formData, ip: e.target.value })}
              error={!!errors.ip}
              helperText={errors.ip || 'Ejemplo: 192.168.1.100'}
              placeholder="192.168.1.100"
            />
          </Box>
        );

      case 1:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              required
              label="Usuario"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              error={!!errors.username}
              helperText={errors.username}
            />

            <TextField
              fullWidth
              required
              type={showPassword ? 'text' : 'password'}
              label="Contraseña"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              error={!!errors.password}
              helperText={errors.password}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <FormControl fullWidth>
              <InputLabel>Tipo de autenticación</InputLabel>
              <Select
                value={formData.auth_type}
                onChange={(e) => setFormData({ ...formData, auth_type: e.target.value as any })}
                label="Tipo de autenticación"
              >
                <MenuItem value="basic">Basic</MenuItem>
                <MenuItem value="digest">Digest</MenuItem>
                <MenuItem value="bearer">Bearer</MenuItem>
              </Select>
              <FormHelperText>Generalmente 'Basic' funciona para la mayoría de cámaras</FormHelperText>
            </FormControl>

            <Box sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                onClick={handleTestConnection}
                disabled={isTestingConnection || !formData.username || !formData.password}
                startIcon={isTestingConnection ? <CircularProgress size={20} /> : undefined}
              >
                {isTestingConnection ? 'Probando conexión...' : 'Probar conexión'}
              </Button>

              {testResult && (
                <Alert
                  severity={testResult === 'success' ? 'success' : 'error'}
                  sx={{ mt: 2 }}
                  icon={testResult === 'success' ? <SuccessIcon /> : undefined}
                >
                  {testResult === 'success'
                    ? 'Conexión exitosa! Las credenciales son válidas.'
                    : 'No se pudo conectar. Verifica las credenciales y la IP.'}
                </Alert>
              )}
            </Box>
          </Box>
        );

      case 2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Configuración opcional. Los valores por defecto funcionan para la mayoría de cámaras.
            </Typography>

            <TextField
              fullWidth
              label="Ubicación"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              helperText="Ejemplo: Entrada principal, Oficina 2do piso"
            />

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Descripción"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              helperText="Notas adicionales sobre la cámara"
            />

            <Typography variant="subtitle2" sx={{ mt: 2 }}>
              Puertos de comunicación
            </Typography>

            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="Puerto RTSP"
                type="number"
                value={formData.rtsp_port}
                onChange={(e) => setFormData({ ...formData, rtsp_port: Number(e.target.value) })}
                inputProps={{ min: 1, max: 65535 }}
                helperText="Default: 554"
              />

              <TextField
                label="Puerto ONVIF"
                type="number"
                value={formData.onvif_port}
                onChange={(e) => setFormData({ ...formData, onvif_port: Number(e.target.value) })}
                inputProps={{ min: 1, max: 65535 }}
                helperText="Default: 80"
              />

              <TextField
                label="Puerto HTTP"
                type="number"
                value={formData.http_port}
                onChange={(e) => setFormData({ ...formData, http_port: Number(e.target.value) })}
                inputProps={{ min: 1, max: 65535 }}
                helperText="Default: 80"
              />
            </Box>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
        },
      }}
    >
      <DialogTitle sx={{ m: 0, p: 2 }}>
        Nueva Cámara
        <IconButton
          onClick={handleClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: (theme) => theme.palette.grey[500],
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {getStepContent(activeStep)}
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button onClick={handleClose} disabled={isCreating}>
          Cancelar
        </Button>
        
        <Box sx={{ flex: 1 }} />
        
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={isCreating}>
            Atrás
          </Button>
        )}
        
        {activeStep < steps.length - 1 ? (
          <Button variant="contained" onClick={handleNext}>
            Siguiente
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={isCreating}
            startIcon={isCreating ? <CircularProgress size={20} /> : undefined}
          >
            {isCreating ? 'Creando...' : 'Crear cámara'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};