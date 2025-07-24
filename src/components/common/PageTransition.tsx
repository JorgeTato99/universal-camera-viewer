/**
 * 🎯 Page Transition - Transiciones animadas entre páginas
 * Envuelve las páginas para proporcionar animaciones suaves
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Box } from '@mui/material';

interface PageTransitionProps {
  children: React.ReactNode;
  variant?: 'fade' | 'slideUp' | 'slideRight';
}

const variants = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  },
  slideRight: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 },
  },
};

export const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  variant = 'fade',
}) => {
  return (
    <motion.div
      initial="initial"
      animate="animate"
      exit="exit"
      variants={variants[variant]}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      style={{ width: '100%', height: '100%' }}
    >
      <Box sx={{ width: '100%', height: '100%' }}>
        {children}
      </Box>
    </motion.div>
  );
};