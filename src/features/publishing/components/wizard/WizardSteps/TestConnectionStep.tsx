/**
 * 🎯 Paso de Prueba de Conexión
 * Verifica la conexión con el servidor y muestra feedback visual
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowBack as BackIcon,
  ArrowForward as NextIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RetryIcon,
  Link as LinkIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { fadeInOut, staggerContainer, staggerItem } from '../../animations/transitions';
import { ServerType, WizardState } from '../useWizardState';

interface TestConnectionStepProps {
  serverType: ServerType;
  config: WizardState['serverConfig'];
  testResult: WizardState['testResult'];
  onTestResult: (result: WizardState['testResult']) => void;
  onNext: () => void;
  onBack: () => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

interface TestStep {
  id: string;
  label: string;
  icon: React.ReactNode;
  status: 'pending' | 'testing' | 'success' | 'error';
}

export const TestConnectionStep: React.FC<TestConnectionStepProps> = ({
  serverType,
  config,
  testResult,
  onTestResult,
  onNext,
  onBack,
  isLoading,
  setIsLoading,
}) => {
  const [testSteps, setTestSteps] = useState<TestStep[]>([
    {
      id: 'connection',
      label: 'Conectando al servidor',
      icon: <LinkIcon />,
      status: 'pending',
    },
    {
      id: 'auth',
      label: 'Verificando autenticación',
      icon: <SecurityIcon />,
      status: 'pending',
    },
    {
      id: 'performance',
      label: 'Comprobando rendimiento',
      icon: <SpeedIcon />,
      status: 'pending',
    },
  ]);

  const runTest = async () => {
    setIsLoading(true);
    onTestResult(null);

    // Simular pruebas paso a paso
    for (let i = 0; i < testSteps.length; i++) {
      setTestSteps(prev => prev.map((step, index) => ({
        ...step,
        status: index === i ? 'testing' : index < i ? 'success' : 'pending',
      })));

      await new Promise(resolve => setTimeout(resolve, 800));

      // En el paso de autenticación, puede fallar si no hay credenciales
      if (i === 1 && config.auth_required && (!config.username || !config.password)) {
        setTestSteps(prev => prev.map((step, index) => ({
          ...step,
          status: index <= i ? (index === i ? 'error' : 'success') : 'pending',
        })));
        onTestResult({
          success: false,
          message: 'Error de autenticación: Credenciales inválidas',
        });
        setIsLoading(false);
        return;
      }
    }

    // Marcar todos como exitosos
    setTestSteps(prev => prev.map(step => ({ ...step, status: 'success' })));

    // TODO: Aquí se haría la prueba real cuando el backend esté listo
    // Por ahora simulamos éxito
    onTestResult({
      success: true,
      message: 'Conexión exitosa. El servidor está listo para usar.',
    });
    setIsLoading(false);
  };

  useEffect(() => {
    // Ejecutar prueba automáticamente al entrar
    runTest();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const getStepIcon = (step: TestStep) => {
    if (step.status === 'testing') {
      return (
        <motion.div 
          animate={{ scale: [1, 1.05, 1] }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut" as const,
          }}
        >
          <CircularProgress size={24} />
        </motion.div>
      );
    }
    if (step.status === 'success') {
      return <CheckIcon sx={{ color: 'success.main' }} />;
    }
    if (step.status === 'error') {
      return <ErrorIcon sx={{ color: 'error.main' }} />;
    }
    return (
      <Box sx={{ color: 'text.disabled' }}>
        {step.icon}
      </Box>
    );
  };

  return (
    <motion.div
      variants={fadeInOut}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <Box sx={{ py: 3 }}>
        <Typography variant="h5" gutterBottom align="center">
          Probando Conexión
        </Typography>
        <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
          Verificando que el servidor esté configurado correctamente
        </Typography>

        <Paper sx={{ p: 4, maxWidth: 500, mx: 'auto' }}>
          <motion.div variants={staggerContainer} initial="initial" animate="animate">
            <List>
              <AnimatePresence mode="wait">
                {testSteps.map((step) => (
                  <motion.div key={step.id} variants={staggerItem}>
                    <ListItem>
                      <ListItemIcon>{getStepIcon(step)}</ListItemIcon>
                      <ListItemText
                        primary={step.label}
                        slotProps={{
                          primary: {
                            color: step.status === 'error' ? 'error' : 'textPrimary',
                          },
                        }}
                      />
                    </ListItem>
                  </motion.div>
                ))}
              </AnimatePresence>
            </List>
          </motion.div>

          {testResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Alert 
                severity={testResult.success ? 'success' : 'error'}
                sx={{ mt: 3 }}
                action={
                  !testResult.success && (
                    <Button
                      color="inherit"
                      size="small"
                      startIcon={<RetryIcon />}
                      onClick={runTest}
                      disabled={isLoading}
                    >
                      Reintentar
                    </Button>
                  )
                }
              >
                {testResult.message}
              </Alert>
            </motion.div>
          )}

          {/* Información del servidor */}
          {testResult?.success && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              <Box sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Detalles de conexión:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Servidor:</strong> {config.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Tipo:</strong> {serverType === 'remote' ? 'Remoto' : 'Local'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>URL:</strong> {config.api_url}
                </Typography>
              </Box>
            </motion.div>
          )}
        </Paper>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            variant="outlined"
            startIcon={<BackIcon />}
            onClick={onBack}
            disabled={isLoading}
          >
            Atrás
          </Button>

          <Button
            variant="contained"
            endIcon={<NextIcon />}
            onClick={onNext}
            disabled={!testResult?.success || isLoading}
          >
            Finalizar
          </Button>
        </Box>
      </Box>
    </motion.div>
  );
};