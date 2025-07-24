/**
 * 🎯 Hook para detectar usuarios nuevos
 * Maneja la lógica de detección y persistencia del estado de onboarding
 */

import { useState, useEffect } from 'react';
import { usePublishingStore } from '../../../stores/publishingStore';

const ONBOARDING_KEY = 'publishing_onboarding_completed';
const SKIP_WIZARD_KEY = 'publishing_wizard_skipped';

interface UseFirstTimeUserReturn {
  isFirstTime: boolean;
  hasNoServers: boolean;
  shouldShowWizard: boolean;
  markOnboardingComplete: () => void;
  skipWizard: () => void;
  resetOnboarding: () => void; // Para testing o reset manual
}

export const useFirstTimeUser = (): UseFirstTimeUserReturn => {
  const { remote } = usePublishingStore();
  const [isFirstTime, setIsFirstTime] = useState(false);
  const [wizardSkipped, setWizardSkipped] = useState(false);

  useEffect(() => {
    // Verificar si el usuario ya completó el onboarding
    const onboardingCompleted = localStorage.getItem(ONBOARDING_KEY) === 'true';
    const wasSkipped = localStorage.getItem(SKIP_WIZARD_KEY) === 'true';
    
    setIsFirstTime(!onboardingCompleted);
    setWizardSkipped(wasSkipped);
  }, []);

  // Detectar si no hay servidores configurados
  const hasNoServers = remote.servers.length === 0;
  const isLoading = remote.isLoadingServers;

  // Mostrar wizard si no está cargando, es primera vez Y no hay servidores Y no fue saltado
  const shouldShowWizard = !isLoading && isFirstTime && hasNoServers && !wizardSkipped;

  const markOnboardingComplete = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
    setIsFirstTime(false);
  };

  const skipWizard = () => {
    localStorage.setItem(SKIP_WIZARD_KEY, 'true');
    setWizardSkipped(true);
  };

  const resetOnboarding = () => {
    localStorage.removeItem(ONBOARDING_KEY);
    localStorage.removeItem(SKIP_WIZARD_KEY);
    setIsFirstTime(true);
    setWizardSkipped(false);
  };

  return {
    isFirstTime,
    hasNoServers,
    shouldShowWizard,
    markOnboardingComplete,
    skipWizard,
    resetOnboarding,
  };
};