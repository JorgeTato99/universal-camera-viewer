/**
 * 🎯 Skeleton Card - Estado de carga para tarjetas
 * Componente reutilizable para mostrar placeholders durante la carga
 */

import React from 'react';
import { Card, CardContent, Skeleton, Box } from '@mui/material';

interface SkeletonCardProps {
  height?: number;
  hasActions?: boolean;
  hasImage?: boolean;
  lines?: number;
}

export const SkeletonCard: React.FC<SkeletonCardProps> = ({
  height = 200,
  hasActions = false,
  hasImage = false,
  lines = 3,
}) => {
  return (
    <Card sx={{ height, display: 'flex', flexDirection: 'column' }}>
      {hasImage && (
        <Skeleton 
          variant="rectangular" 
          height={140} 
          sx={{ flexShrink: 0 }}
        />
      )}
      
      <CardContent sx={{ flex: 1 }}>
        <Skeleton variant="text" sx={{ fontSize: '1.5rem', mb: 1 }} />
        
        {[...Array(lines)].map((_, index) => (
          <Skeleton 
            key={index} 
            variant="text" 
            sx={{ 
              fontSize: '0.875rem',
              width: index === lines - 1 ? '60%' : '100%' 
            }} 
          />
        ))}
      </CardContent>
      
      {hasActions && (
        <Box sx={{ p: 2, pt: 0, display: 'flex', gap: 1 }}>
          <Skeleton variant="rounded" width={80} height={36} />
          <Skeleton variant="rounded" width={80} height={36} />
        </Box>
      )}
    </Card>
  );
};