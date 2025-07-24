/**
 * 🎯 Animated Loader - Loader animado personalizado
 * Spinner con animaciones suaves y personalizable
 */

import React from 'react';
import { Box, useTheme } from '@mui/material';
import { motion } from 'framer-motion';

interface AnimatedLoaderProps {
  size?: number;
  color?: string;
  message?: string;
}

export const AnimatedLoader: React.FC<AnimatedLoaderProps> = ({
  size = 40,
  color,
  message,
}) => {
  const theme = useTheme();
  const loaderColor = color || theme.palette.primary.main;

  const spinTransition = {
    repeat: Infinity,
    ease: "linear" as const,
    duration: 1.5,
  };

  return (
    <Box sx={{ textAlign: 'center' }}>
      <motion.div
        style={{
          width: size,
          height: size,
          margin: '0 auto',
        }}
        animate={{ rotate: 360 }}
        transition={spinTransition}
      >
        <svg
          width={size}
          height={size}
          viewBox="0 0 50 50"
          style={{ display: 'block' }}
        >
          <motion.circle
            cx="25"
            cy="25"
            r="20"
            stroke={loaderColor}
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
            initial={{ pathLength: 0.2 }}
            animate={{ pathLength: [0.2, 1, 0.2] }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            style={{
              transformOrigin: 'center',
              strokeDasharray: '1',
              strokeDashoffset: '0',
            }}
          />
        </svg>
      </motion.div>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Box sx={{ mt: 2, color: 'text.secondary' }}>
            {message}
          </Box>
        </motion.div>
      )}
    </Box>
  );
};