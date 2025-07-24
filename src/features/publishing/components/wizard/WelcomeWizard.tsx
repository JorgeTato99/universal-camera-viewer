/**
 * 🎯 Wizard Principal de Bienvenida
 * Orquesta todos los pasos del proceso de configuración inicial
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  Box,
  Stepper,
  Step,
  StepLabel,
  StepIconProps,
  useTheme,
  useMediaQuery,
  IconButton,
} from '@mui/material';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Home as WelcomeIcon,
  CloudQueue as ServerTypeIcon,
  Settings as ConfigIcon,
  CheckCircle as TestIcon,
  Celebration as SuccessIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useWizardState } from './useWizardState';
import { WelcomeStep } from './WizardSteps/WelcomeStep';
import { ServerTypeStep } from './WizardSteps/ServerTypeStep';
import { ConfigurationStep } from './WizardSteps/ConfigurationStep';
import { TestConnectionStep } from './WizardSteps/TestConnectionStep';
import { SuccessStep } from './WizardSteps/SuccessStep';
import { useNavigate } from 'react-router-dom';

interface WelcomeWizardProps {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}

// Iconos personalizados para cada paso
const stepIcons: Record<number, React.ReactNode> = {
  0: <WelcomeIcon />,
  1: <ServerTypeIcon />,
  2: <ConfigIcon />,
  3: <TestIcon />,
  4: <SuccessIcon />,
};

// Componente de ícono personalizado para el Stepper
const CustomStepIcon: React.FC<StepIconProps> = ({ active, completed, icon }) => {
  const stepNumber = Number(icon) - 1;
  const Icon = stepIcons[stepNumber];

  return (
    <motion.div
      initial={{ scale: 0.8 }}
      animate={{ 
        scale: active ? 1.1 : 1,
      }}
      transition={{ duration: 0.3 }}
    >
      <Box
        sx={{
          width: 40,
          height: 40,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: completed 
            ? 'success.main' 
            : active 
              ? 'primary.main' 
              : 'action.disabledBackground',
          color: 'white',
        }}
      >
        {Icon}
      </Box>
    </motion.div>
  );
};

export const WelcomeWizard: React.FC<WelcomeWizardProps> = ({
  open,
  onClose,
  onComplete,
}) => {
  const navigate = useNavigate();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const [isLoading, setIsLoading] = useState(false);
  
  const {
    state,
    updateServerType,
    updateServerConfig,
    nextStep,
    prevStep,
    setTestResult,
    reset,
  } = useWizardState();
  
  const { currentStep, serverType, serverConfig, testResult } = state;

  const steps = [
    'Bienvenida',
    'Tipo de Servidor',
    'Configuración',
    'Prueba de Conexión',
    'Finalizado',
  ];

  const handleSkip = () => {
    onClose();
    onComplete();
  };

  const handleFinish = () => {
    // TODO: Guardar el servidor cuando el backend esté listo
    onComplete();
    navigate('/cameras');
    reset();
  };

  const handleViewServers = () => {
    onComplete();
    navigate('/publishing/servers');
    reset();
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <WelcomeStep
            onNext={nextStep}
            onSkip={handleSkip}
          />
        );
      
      case 1:
        return (
          <ServerTypeStep
            selectedType={serverType}
            onSelectType={updateServerType}
            onNext={nextStep}
            onBack={prevStep}
          />
        );
      
      case 2:
        return (
          <ConfigurationStep
            serverType={serverType!}
            config={serverConfig}
            onUpdateConfig={updateServerConfig}
            onNext={nextStep}
            onBack={prevStep}
          />
        );
      
      case 3:
        return (
          <TestConnectionStep
            serverType={serverType!}
            config={serverConfig}
            testResult={testResult}
            onTestResult={setTestResult}
            onNext={nextStep}
            onBack={prevStep}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        );
      
      case 4:
        return (
          <SuccessStep
            serverType={serverType!}
            serverName={serverConfig.name}
            onFinish={handleFinish}
            onViewServers={handleViewServers}
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={isLoading ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="md"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            borderRadius: fullScreen ? 0 : 2,
            overflow: 'hidden',
          },
        },
      }}
    >
      {/* Botón de cerrar */}
      {!isLoading && currentStep < 4 && (
        <IconButton
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            zIndex: 1,
          }}
        >
          <CloseIcon />
        </IconButton>
      )}

      {/* Stepper */}
      {currentStep > 0 && currentStep < 4 && (
        <Box sx={{ px: 3, pt: 3, pb: 0 }}>
          <Stepper activeStep={currentStep - 1} alternativeLabel>
            {steps.slice(1, 4).map((label, index) => (
              <Step key={label}>
                <StepLabel
                  slots={{
                    stepIcon: CustomStepIcon,
                  }}
                  sx={{
                    '& .MuiStepLabel-label': {
                      mt: 1,
                      color: index + 1 <= currentStep ? 'text.primary' : 'text.disabled',
                    },
                  }}
                >
                  {label}
                </StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>
      )}

      <DialogContent sx={{ px: { xs: 2, sm: 3 }, pb: 3 }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            {renderStep()}
          </motion.div>
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
};