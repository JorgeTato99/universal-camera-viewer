/**
 * 🎯 Loading Overlay - Overlay de carga con backdrop
 * Para operaciones que bloquean la interfaz
 */

import React from 'react';
import { Backdrop, CircularProgress, Box, Typography } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

interface LoadingOverlayProps {
  open: boolean;
  message?: string;
  progress?: number;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  open,
  message,
  progress,
}) => {
  return (
    <AnimatePresence>
      {open && (
        <Backdrop
          open={open}
          sx={{
            zIndex: (theme) => theme.zIndex.drawer + 1,
            color: '#fff',
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.2 }}
          >
            <Box sx={{ textAlign: 'center' }}>
              <CircularProgress
                color="inherit"
                size={60}
                variant={progress !== undefined ? 'determinate' : 'indeterminate'}
                value={progress}
                sx={{ mb: 2 }}
              />
              {message && (
                <Typography variant="h6" component="div">
                  {message}
                </Typography>
              )}
              {progress !== undefined && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {Math.round(progress)}%
                </Typography>
              )}
            </Box>
          </motion.div>
        </Backdrop>
      )}
    </AnimatePresence>
  );
};