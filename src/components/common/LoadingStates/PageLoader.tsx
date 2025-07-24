/**
 * 🎯 Page Loader - Loader de página completa
 * Muestra un estado de carga elegante mientras se inicializa la aplicación
 */

import React from 'react';
import { Box, Typography, LinearProgress } from '@mui/material';
import { motion } from 'framer-motion';
import { AnimatedLoader } from './AnimatedLoader';

interface PageLoaderProps {
  title?: string;
  subtitle?: string;
  progress?: number;
  showProgress?: boolean;
}

export const PageLoader: React.FC<PageLoaderProps> = ({
  title = 'Cargando...',
  subtitle,
  progress,
  showProgress = false,
}) => {
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        zIndex: 9999,
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <AnimatedLoader size={60} />
          
          <Typography
            variant="h5"
            sx={{ mt: 3, mb: 1, fontWeight: 500 }}
          >
            {title}
          </Typography>
          
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        
        {(showProgress || progress !== undefined) && (
          <Box sx={{ width: 300 }}>
            <LinearProgress
              variant={progress !== undefined ? 'determinate' : 'indeterminate'}
              value={progress}
              sx={{
                height: 4,
                borderRadius: 2,
                '& .MuiLinearProgress-bar': {
                  borderRadius: 2,
                },
              }}
            />
            {progress !== undefined && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', textAlign: 'center', mt: 1 }}
              >
                {Math.round(progress)}%
              </Typography>
            )}
          </Box>
        )}
      </motion.div>
    </Box>
  );
};