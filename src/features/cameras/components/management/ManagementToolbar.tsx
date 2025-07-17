/**
 * 🎯 Management Toolbar Component
 * Barra de herramientas con filtros y acciones para gestión de cámaras
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Button,
  TextField,
  IconButton,
  InputAdornment,
  Menu,
  MenuItem,
  Chip,
  Divider,
  Badge,
  Tooltip,
  Fade,
  FormControl,
  Select,
  SelectChangeEvent,
  Typography,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Delete as DeleteIcon,
  PowerSettingsNew as ConnectIcon,
  PowerOff as DisconnectIcon,
  Edit as EditIcon,
  Clear as ClearIcon,
  Upload as ImportIcon,
  Download as ExportIcon,
  ContentCopy as CloneIcon,
} from '@mui/icons-material';
import { ConnectionStatus } from '../../../../types/camera.types.v2';
import { useCameraStoreV2 } from '../../../../stores/cameraStore.v2';

interface ManagementToolbarProps {
  onRefresh: () => void;
  isRefreshing: boolean;
  onCreateNew: () => void;
  selectedCount: number;
  onBulkAction: (action: string) => void;
  onSearch: (query: string) => void;
  onFilterStatus: (status: ConnectionStatus | 'all') => void;
  onFilterBrand: (brand: string | 'all') => void;
  onFilterLocation: (location: string | 'all') => void;
}

export const ManagementToolbar: React.FC<ManagementToolbarProps> = ({
  onRefresh,
  isRefreshing,
  onCreateNew,
  selectedCount,
  onBulkAction,
  onSearch,
  onFilterStatus,
  onFilterBrand,
  onFilterLocation,
}) => {
  const theme = useTheme();
  const { getUniqueBrands, getUniqueLocations, filterStatus, filterBrand, filterLocation } = useCameraStoreV2();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [filterMenuAnchor, setFilterMenuAnchor] = useState<null | HTMLElement>(null);
  const [bulkMenuAnchor, setBulkMenuAnchor] = useState<null | HTMLElement>(null);
  
  const brands = getUniqueBrands();
  const locations = getUniqueLocations();
  
  // Contar filtros activos
  const activeFiltersCount = [
    filterStatus !== 'all',
    filterBrand !== 'all',
    filterLocation !== 'all',
  ].filter(Boolean).length;

  // Handlers
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    onSearch(value);
  }, [onSearch]);

  const handleClearSearch = useCallback(() => {
    setSearchQuery('');
    onSearch('');
  }, [onSearch]);

  const handleStatusChange = useCallback((e: SelectChangeEvent<string>) => {
    onFilterStatus(e.target.value as ConnectionStatus | 'all');
  }, [onFilterStatus]);

  const handleBrandChange = useCallback((e: SelectChangeEvent<string>) => {
    onFilterBrand(e.target.value);
  }, [onFilterBrand]);

  const handleLocationChange = useCallback((e: SelectChangeEvent<string>) => {
    onFilterLocation(e.target.value);
  }, [onFilterLocation]);

  const handleClearFilters = useCallback(() => {
    onFilterStatus('all');
    onFilterBrand('all');
    onFilterLocation('all');
    setFilterMenuAnchor(null);
  }, [onFilterStatus, onFilterBrand, onFilterLocation]);

  return (
    <Box
      sx={{
        display: 'flex',
        gap: 2,
        alignItems: 'center',
        flexWrap: 'wrap',
      }}
    >
      {/* Acciones principales */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={onCreateNew}
          sx={{
            textTransform: 'none',
            fontWeight: 600,
          }}
        >
          Nueva Cámara
        </Button>

        <Tooltip title="Importar configuración">
          <IconButton onClick={() => console.log('Import')}>
            <ImportIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Exportar configuración">
          <IconButton onClick={() => console.log('Export')}>
            <ExportIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Actualizar lista">
          <IconButton 
            onClick={onRefresh} 
            disabled={isRefreshing}
            sx={{
              animation: isRefreshing ? 'spin 1s linear infinite' : 'none',
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' },
              },
            }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Divider orientation="vertical" flexItem />

      {/* Búsqueda */}
      <TextField
        placeholder="Buscar cámaras..."
        size="small"
        value={searchQuery}
        onChange={handleSearchChange}
        sx={{ minWidth: 250 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon fontSize="small" />
            </InputAdornment>
          ),
          endAdornment: searchQuery && (
            <InputAdornment position="end">
              <IconButton size="small" onClick={handleClearSearch}>
                <ClearIcon fontSize="small" />
              </IconButton>
            </InputAdornment>
          ),
        }}
      />

      {/* Filtros */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <Badge badgeContent={activeFiltersCount} color="primary">
          <IconButton
            onClick={(e) => setFilterMenuAnchor(e.currentTarget)}
            sx={{
              bgcolor: activeFiltersCount > 0 ? alpha(theme.palette.primary.main, 0.1) : 'transparent',
              color: activeFiltersCount > 0 ? 'primary.main' : 'inherit',
            }}
          >
            <FilterIcon />
          </IconButton>
        </Badge>

        {/* Chips de filtros activos */}
        {filterStatus !== 'all' && (
          <Chip
            label={`Estado: ${filterStatus}`}
            size="small"
            onDelete={() => onFilterStatus('all')}
          />
        )}
        {filterBrand !== 'all' && (
          <Chip
            label={`Marca: ${filterBrand}`}
            size="small"
            onDelete={() => onFilterBrand('all')}
          />
        )}
        {filterLocation !== 'all' && (
          <Chip
            label={`Ubicación: ${filterLocation}`}
            size="small"
            onDelete={() => onFilterLocation('all')}
          />
        )}
      </Box>

      {/* Espaciador flexible */}
      <Box sx={{ flexGrow: 1 }} />

      {/* Acciones masivas */}
      {selectedCount > 0 && (
        <Fade in>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              label={`${selectedCount} seleccionadas`}
              color="primary"
              variant="outlined"
            />
            <Button
              size="small"
              startIcon={<ConnectIcon />}
              onClick={() => onBulkAction('connect')}
            >
              Conectar
            </Button>
            <Button
              size="small"
              startIcon={<DisconnectIcon />}
              onClick={() => onBulkAction('disconnect')}
            >
              Desconectar
            </Button>
            <IconButton
              onClick={(e) => setBulkMenuAnchor(e.currentTarget)}
            >
              <MoreIcon />
            </IconButton>
          </Box>
        </Fade>
      )}

      {/* Menú de filtros */}
      <Menu
        anchorEl={filterMenuAnchor}
        open={Boolean(filterMenuAnchor)}
        onClose={() => setFilterMenuAnchor(null)}
        PaperProps={{
          sx: { width: 300, p: 2 },
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Typography variant="subtitle2" fontWeight={600}>
            Filtros
          </Typography>

          {/* Filtro por estado */}
          <FormControl size="small" fullWidth>
            <Select
              value={filterStatus}
              onChange={handleStatusChange}
              displayEmpty
            >
              <MenuItem value="all">Todos los estados</MenuItem>
              <MenuItem value={ConnectionStatus.CONNECTED}>Conectadas</MenuItem>
              <MenuItem value={ConnectionStatus.DISCONNECTED}>Desconectadas</MenuItem>
              <MenuItem value={ConnectionStatus.CONNECTING}>Conectando</MenuItem>
              <MenuItem value={ConnectionStatus.ERROR}>Error</MenuItem>
            </Select>
          </FormControl>

          {/* Filtro por marca */}
          {brands.length > 0 && (
            <FormControl size="small" fullWidth>
              <Select
                value={filterBrand}
                onChange={handleBrandChange}
                displayEmpty
              >
                <MenuItem value="all">Todas las marcas</MenuItem>
                {brands.map(brand => (
                  <MenuItem key={brand} value={brand}>{brand}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          {/* Filtro por ubicación */}
          {locations.length > 0 && (
            <FormControl size="small" fullWidth>
              <Select
                value={filterLocation}
                onChange={handleLocationChange}
                displayEmpty
              >
                <MenuItem value="all">Todas las ubicaciones</MenuItem>
                {locations.map(location => (
                  <MenuItem key={location} value={location}>{location}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          <Divider />

          <Button
            size="small"
            onClick={handleClearFilters}
            disabled={activeFiltersCount === 0}
          >
            Limpiar filtros
          </Button>
        </Box>
      </Menu>

      {/* Menú de acciones masivas */}
      <Menu
        anchorEl={bulkMenuAnchor}
        open={Boolean(bulkMenuAnchor)}
        onClose={() => setBulkMenuAnchor(null)}
      >
        <MenuItem onClick={() => { onBulkAction('edit'); setBulkMenuAnchor(null); }}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Editar seleccionadas
        </MenuItem>
        <MenuItem onClick={() => { onBulkAction('clone'); setBulkMenuAnchor(null); }}>
          <CloneIcon fontSize="small" sx={{ mr: 1 }} />
          Clonar configuración
        </MenuItem>
        <MenuItem onClick={() => { onBulkAction('delete'); setBulkMenuAnchor(null); }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Eliminar seleccionadas
        </MenuItem>
      </Menu>
    </Box>
  );
};