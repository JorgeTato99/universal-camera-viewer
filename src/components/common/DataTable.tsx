/**
 * 🗃️ DataTable Component - Universal Camera Viewer
 * Tabla de datos genérica con Material-UI
 */

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Typography,
} from '@mui/material';

interface Column<T> {
  field: string;
  headerName: string;
  width?: number;
  flex?: number;
  sortable?: boolean;
  renderCell?: (row: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  getRowId: (row: T) => string;
  emptyMessage?: string;
  emptyAction?: React.ReactNode;
}

export function DataTable<T>({
  columns,
  data,
  getRowId,
  emptyMessage = 'No hay datos disponibles',
  emptyAction,
}: DataTableProps<T>) {
  if (data.length === 0) {
    return (
      <Paper>
        <Box sx={{ p: 6, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            {emptyMessage}
          </Typography>
          {emptyAction && <Box sx={{ mt: 2 }}>{emptyAction}</Box>}
        </Box>
      </Paper>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell
                key={column.field}
                sx={{ 
                  width: column.width,
                  flex: column.flex,
                  fontWeight: 600 
                }}
              >
                {column.headerName}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((row) => (
            <TableRow key={getRowId(row)}>
              {columns.map((column) => (
                <TableCell key={column.field}>
                  {column.renderCell ? column.renderCell(row) : (row as any)[column.field]}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}