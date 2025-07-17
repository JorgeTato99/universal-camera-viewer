/**
 * 🎯 Camera List View Component
 * Vista de tabla para mostrar cámaras con funcionalidad completa
 */

import React, { useState } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  Paper,
  Checkbox,
  IconButton,
  Chip,
  Avatar,
  Menu,
  MenuItem,
  Skeleton,
  Tooltip,
  Typography,
  useTheme,
  alpha,
} from '@mui/material';
import {
  MoreVert as MoreIcon,
  Circle as StatusIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PowerSettingsNew as ConnectIcon,
  Visibility as ViewIcon,
  Router as RouterIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';
import { CameraResponse, ConnectionStatus } from '../../../../types/camera.types.v2';
import { useNavigate } from 'react-router-dom';
import { useCameraStoreV2 } from '../../../../stores/cameraStore.v2';
import { visuallyHidden } from '@mui/utils';

interface CameraListViewProps {
  cameras: CameraResponse[];
  isLoading: boolean;
  selectedCameras: Set<string>;
  onSelectCamera: (cameraId: string, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
}

type Order = 'asc' | 'desc';

interface HeadCell {
  id: keyof CameraResponse | 'actions';
  label: string;
  numeric: boolean;
  sortable: boolean;
  width?: string | number;
}

const headCells: HeadCell[] = [
  { id: 'display_name', label: 'Nombre', numeric: false, sortable: true },
  { id: 'brand', label: 'Marca', numeric: false, sortable: true, width: 120 },
  { id: 'model', label: 'Modelo', numeric: false, sortable: true, width: 150 },
  { id: 'ip_address', label: 'Dirección IP', numeric: false, sortable: true, width: 140 },
  { id: 'location', label: 'Ubicación', numeric: false, sortable: true },
  { id: 'status', label: 'Estado', numeric: false, sortable: true, width: 120 },
  { id: 'actions', label: 'Acciones', numeric: false, sortable: false, width: 100 },
];

interface EnhancedTableHeadProps {
  numSelected: number;
  onSelectAllClick: (event: React.ChangeEvent<HTMLInputElement>) => void;
  order: Order;
  orderBy: string;
  rowCount: number;
  onRequestSort: (event: React.MouseEvent<unknown>, property: keyof CameraResponse) => void;
}

const EnhancedTableHead: React.FC<EnhancedTableHeadProps> = ({
  onSelectAllClick,
  order,
  orderBy,
  numSelected,
  rowCount,
  onRequestSort,
}) => {
  const createSortHandler = (property: keyof CameraResponse) => (event: React.MouseEvent<unknown>) => {
    onRequestSort(event, property);
  };

  return (
    <TableHead>
      <TableRow>
        <TableCell padding="checkbox">
          <Checkbox
            color="primary"
            indeterminate={numSelected > 0 && numSelected < rowCount}
            checked={rowCount > 0 && numSelected === rowCount}
            onChange={onSelectAllClick}
          />
        </TableCell>
        {headCells.map((headCell) => (
          <TableCell
            key={headCell.id}
            align={headCell.numeric ? 'right' : 'left'}
            sortDirection={orderBy === headCell.id ? order : false}
            sx={{ width: headCell.width, fontWeight: 600 }}
          >
            {headCell.sortable ? (
              <TableSortLabel
                active={orderBy === headCell.id}
                direction={orderBy === headCell.id ? order : 'asc'}
                onClick={createSortHandler(headCell.id as keyof CameraResponse)}
              >
                {headCell.label}
                {orderBy === headCell.id ? (
                  <Box component="span" sx={visuallyHidden}>
                    {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                  </Box>
                ) : null}
              </TableSortLabel>
            ) : (
              headCell.label
            )}
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
};

interface CameraRowProps {
  camera: CameraResponse;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
}

const CameraRow: React.FC<CameraRowProps> = ({ camera, isSelected, onSelect }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { connectCamera, disconnectCamera } = useCameraStoreV2();
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  const getStatusColor = () => {
    switch (camera.status) {
      case ConnectionStatus.CONNECTED:
        return theme.palette.success.main;
      case ConnectionStatus.CONNECTING:
        return theme.palette.warning.main;
      case ConnectionStatus.ERROR:
        return theme.palette.error.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getStatusLabel = () => {
    switch (camera.status) {
      case ConnectionStatus.CONNECTED:
        return 'Conectada';
      case ConnectionStatus.CONNECTING:
        return 'Conectando...';
      case ConnectionStatus.ERROR:
        return 'Error';
      default:
        return 'Desconectada';
    }
  };

  const handleConnect = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (camera.status === ConnectionStatus.CONNECTED) {
      await disconnectCamera(camera.camera_id);
    } else {
      await connectCamera(camera.camera_id);
    }
  };

  const handleView = () => {
    navigate(`/cameras/${camera.camera_id}/view`);
  };

  const handleEdit = () => {
    navigate(`/cameras/${camera.camera_id}/edit`);
  };

  return (
    <TableRow
      hover
      onClick={handleView}
      role="checkbox"
      aria-checked={isSelected}
      tabIndex={-1}
      selected={isSelected}
      sx={{ cursor: 'pointer' }}
    >
      <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
        <Checkbox
          color="primary"
          checked={isSelected}
          onChange={(e) => onSelect(e.target.checked)}
        />
      </TableCell>
      
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar
            sx={{
              width: 32,
              height: 32,
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              color: 'primary.main',
            }}
          >
            {camera.display_name.charAt(0).toUpperCase()}
          </Avatar>
          <Typography variant="body2" fontWeight={500}>
            {camera.display_name}
          </Typography>
        </Box>
      </TableCell>
      
      <TableCell>{camera.brand}</TableCell>
      <TableCell>{camera.model}</TableCell>
      
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <RouterIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="body2">{camera.ip_address}</Typography>
        </Box>
      </TableCell>
      
      <TableCell>
        {camera.location && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <LocationIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
              {camera.location}
            </Typography>
          </Box>
        )}
      </TableCell>
      
      <TableCell>
        <Chip
          icon={<StatusIcon sx={{ fontSize: 12 }} />}
          label={getStatusLabel()}
          size="small"
          sx={{
            color: getStatusColor(),
            borderColor: getStatusColor(),
            bgcolor: alpha(getStatusColor(), 0.1),
          }}
          variant="outlined"
        />
      </TableCell>
      
      <TableCell onClick={(e) => e.stopPropagation()}>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title={camera.is_connected ? 'Desconectar' : 'Conectar'}>
            <IconButton
              size="small"
              onClick={handleConnect}
              color={camera.is_connected ? 'error' : 'success'}
            >
              <ConnectIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setMenuAnchor(e.currentTarget);
            }}
          >
            <MoreIcon fontSize="small" />
          </IconButton>
        </Box>
        
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={() => setMenuAnchor(null)}
        >
          <MenuItem onClick={handleView}>
            <ViewIcon fontSize="small" sx={{ mr: 1 }} />
            Ver detalles
          </MenuItem>
          <MenuItem onClick={handleEdit}>
            <EditIcon fontSize="small" sx={{ mr: 1 }} />
            Editar
          </MenuItem>
          <MenuItem>
            <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
            Eliminar
          </MenuItem>
        </Menu>
      </TableCell>
    </TableRow>
  );
};

export const CameraListView: React.FC<CameraListViewProps> = ({
  cameras,
  isLoading,
  selectedCameras,
  onSelectCamera,
  onSelectAll,
}) => {
  const [order, setOrder] = useState<Order>('asc');
  const [orderBy, setOrderBy] = useState<keyof CameraResponse>('display_name');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const handleRequestSort = (event: React.MouseEvent<unknown>, property: keyof CameraResponse) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getComparator = <Key extends keyof any>(
    order: Order,
    orderBy: Key,
  ): (a: { [key in Key]: any }, b: { [key in Key]: any }) => number => {
    return order === 'desc'
      ? (a, b) => descendingComparator(a, b, orderBy)
      : (a, b) => -descendingComparator(a, b, orderBy);
  };

  const descendingComparator = <T,>(a: T, b: T, orderBy: keyof T) => {
    if (b[orderBy] < a[orderBy]) {
      return -1;
    }
    if (b[orderBy] > a[orderBy]) {
      return 1;
    }
    return 0;
  };

  const sortedCameras = React.useMemo(
    () => [...cameras].sort(getComparator(order, orderBy)),
    [cameras, order, orderBy]
  );

  const paginatedCameras = React.useMemo(
    () => sortedCameras.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage),
    [sortedCameras, page, rowsPerPage]
  );

  if (isLoading) {
    return (
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer>
          <Table>
            <EnhancedTableHead
              numSelected={0}
              order={order}
              orderBy={orderBy}
              onSelectAllClick={() => {}}
              onRequestSort={handleRequestSort}
              rowCount={0}
            />
            <TableBody>
              {[...Array(5)].map((_, index) => (
                <TableRow key={index}>
                  <TableCell padding="checkbox">
                    <Skeleton variant="rectangular" width={20} height={20} />
                  </TableCell>
                  {headCells.map((cell) => (
                    <TableCell key={cell.id}>
                      <Skeleton variant="text" />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    );
  }

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <TableContainer>
        <Table sx={{ minWidth: 750 }} size="medium">
          <EnhancedTableHead
            numSelected={selectedCameras.size}
            order={order}
            orderBy={orderBy}
            onSelectAllClick={(event) => onSelectAll(event.target.checked)}
            onRequestSort={handleRequestSort}
            rowCount={cameras.length}
          />
          <TableBody>
            {paginatedCameras.map((camera) => (
              <CameraRow
                key={camera.camera_id}
                camera={camera}
                isSelected={selectedCameras.has(camera.camera_id)}
                onSelect={(selected) => onSelectCamera(camera.camera_id, selected)}
              />
            ))}
            {paginatedCameras.length === 0 && (
              <TableRow>
                <TableCell colSpan={headCells.length + 1} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                    No se encontraron cámaras
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={cameras.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        labelRowsPerPage="Filas por página:"
        labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
      />
    </Paper>
  );
};