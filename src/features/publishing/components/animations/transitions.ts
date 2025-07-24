/**
 * 🎯 Transiciones y animaciones reutilizables
 * Usando Framer Motion para consistencia visual
 */

import { Variants } from 'framer-motion';

// Animación de fade in/out básica
export const fadeInOut: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

// Animación de slide desde la derecha
export const slideFromRight: Variants = {
  initial: { x: 100, opacity: 0 },
  animate: { x: 0, opacity: 1 },
  exit: { x: -100, opacity: 0 },
};

// Animación de scale up
export const scaleUp: Variants = {
  initial: { scale: 0.9, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  exit: { scale: 0.9, opacity: 0 },
};

// Animación stagger para listas
export const staggerContainer: Variants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const staggerItem: Variants = {
  initial: { y: 20, opacity: 0 },
  animate: { y: 0, opacity: 1 },
};

// Configuración de transición por defecto
export const defaultTransition = {
  duration: 0.3,
  ease: 'easeInOut',
};

// Animación para botones
export const buttonHover = {
  scale: 1.02,
  transition: { duration: 0.2 },
};

export const buttonTap = {
  scale: 0.98,
  transition: { duration: 0.1 },
};

// Animación para cards
export const cardHover = {
  y: -4,
  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
  transition: { duration: 0.2 },
};

// Animación de éxito
export const successAnimation: Variants = {
  initial: { scale: 0, opacity: 0 },
  animate: {
    scale: 1,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 200,
      damping: 15,
    },
  },
};

// Animación de pulso para indicadores
export const pulseAnimation = {
  scale: [1, 1.05, 1],
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};