/**
 * 🎯 Skeleton Table - Estado de carga para tablas
 * Muestra filas de skeleton mientras se cargan los datos
 */

import React from 'react';
import { 
  Box, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Skeleton,
  Paper,
} from '@mui/material';

interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  hasActions?: boolean;
}

export const SkeletonTable: React.FC<SkeletonTableProps> = ({
  rows = 5,
  columns = 4,
  hasActions = true,
}) => {
  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            {[...Array(columns)].map((_, index) => (
              <TableCell key={index}>
                <Skeleton variant="text" width={index === 0 ? 150 : 100} />
              </TableCell>
            ))}
            {hasActions && (
              <TableCell align="right">
                <Skeleton variant="text" width={80} />
              </TableCell>
            )}
          </TableRow>
        </TableHead>
        <TableBody>
          {[...Array(rows)].map((_, rowIndex) => (
            <TableRow key={rowIndex}>
              {[...Array(columns)].map((_, colIndex) => (
                <TableCell key={colIndex}>
                  {colIndex === 0 ? (
                    <Box>
                      <Skeleton variant="text" width={120} sx={{ mb: 0.5 }} />
                      <Skeleton variant="text" width={80} height={16} />
                    </Box>
                  ) : (
                    <Skeleton 
                      variant="text" 
                      width={colIndex === columns - 1 ? 60 : 100} 
                    />
                  )}
                </TableCell>
              ))}
              {hasActions && (
                <TableCell align="right">
                  <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="circular" width={32} height={32} />
                  </Box>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};