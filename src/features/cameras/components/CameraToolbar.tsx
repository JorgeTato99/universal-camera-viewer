/**
 * 🎯 Camera Toolbar Component - Universal Camera Viewer
 * Barra de herramientas superior para gestión de cámaras
 */

import React from "react";
import {
  Box,
  Typography,
  Button,
  FormControl,
  Select,
  MenuItem,
  SelectChangeEvent,
} from "@mui/material";
import {
  PowerSettingsNew as ConnectIcon,
  PowerOff as DisconnectIcon,
  ViewModule as GridIcon,
} from "@mui/icons-material";
import { buttonStyles } from "../../../design-system/components";
import { colorTokens } from "../../../design-system/tokens";

interface CameraToolbarProps {
  connectedCameras: number;
  totalCameras: number;
  gridColumns: 2 | 3 | 4 | 5;
  onGridColumnsChange: (columns: 2 | 3 | 4 | 5) => void;
  onConnectAll: () => void;
  onDisconnectAll: () => void;
}

export const CameraToolbar: React.FC<CameraToolbarProps> = ({
  connectedCameras,
  totalCameras,
  gridColumns,
  onGridColumnsChange,
  onConnectAll,
  onDisconnectAll,
}) => {
  const handleGridChange = (event: SelectChangeEvent<number>) => {
    onGridColumnsChange(event.target.value as 2 | 3 | 4 | 5);
  };

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        p: 1.5, // Reducido de 3 a 1.5 para optimizar espacio
        borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
        backgroundColor: (theme) => theme.palette.background.paper,
        flexWrap: { xs: "wrap", md: "nowrap" },
        gap: 2,
      }}
    >
      {/* Sección izquierda - Controles de visualización */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <GridIcon sx={{ color: (theme) => theme.palette.text.secondary }} />
          <Typography
            variant="body2"
            sx={{ color: (theme) => theme.palette.text.secondary }}
          >
            Columnas:
          </Typography>
          <FormControl size="small" sx={{ minWidth: 80 }}>
            <Select
              value={gridColumns}
              onChange={handleGridChange}
              sx={{
                // Transición suave para el selector
                transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                "& .MuiOutlinedInput-notchedOutline": {
                  borderColor: (theme) => theme.palette.divider,
                  transition: "border-color 0.2s ease-in-out",
                },
                "&:hover .MuiOutlinedInput-notchedOutline": {
                  borderColor: (theme) => theme.palette.primary.main,
                },
                "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                  borderColor: (theme) => theme.palette.primary.main,
                  borderWidth: "2px",
                },
                // Efecto hover suave
                "&:hover": {
                  backgroundColor: (theme) => theme.palette.action.hover,
                },
              }}
            >
              <MenuItem
                value={2}
                sx={{
                  transition: "background-color 0.2s ease-in-out",
                  "&:hover": {
                    backgroundColor: (theme) => theme.palette.action.hover,
                  },
                }}
              >
                2
              </MenuItem>
              <MenuItem
                value={3}
                sx={{
                  transition: "background-color 0.2s ease-in-out",
                  "&:hover": {
                    backgroundColor: (theme) => theme.palette.action.hover,
                  },
                }}
              >
                3
              </MenuItem>
              <MenuItem
                value={4}
                sx={{
                  transition: "background-color 0.2s ease-in-out",
                  "&:hover": {
                    backgroundColor: (theme) => theme.palette.action.hover,
                  },
                }}
              >
                4
              </MenuItem>
              <MenuItem
                value={5}
                sx={{
                  transition: "background-color 0.2s ease-in-out",
                  "&:hover": {
                    backgroundColor: (theme) => theme.palette.action.hover,
                  },
                }}
              >
                5
              </MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {/* Sección central - Estado de cámaras */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <Typography
          variant="body1"
          sx={{
            color: (theme) => theme.palette.text.primary,
            fontWeight: 500,
          }}
        >
          Cámaras Conectadas:
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color:
              connectedCameras > 0
                ? colorTokens.status.connected
                : (theme) => theme.palette.text.secondary,
            fontWeight: 600,
          }}
        >
          {connectedCameras}
        </Typography>
        <Typography
          variant="body2"
          sx={{ color: (theme) => theme.palette.text.secondary }}
        >
          / {totalCameras}
        </Typography>
      </Box>

      {/* Sección derecha - Botones de acción */}
      <Box sx={{ display: "flex", gap: 1 }}>
        <Button
          variant="outlined"
          startIcon={<ConnectIcon />}
          onClick={onConnectAll}
          disabled={connectedCameras === totalCameras || totalCameras === 0}
          sx={{
            ...buttonStyles.outlined,
            "&.Mui-disabled": {
              backgroundColor: "transparent",
              color: (theme) => theme.palette.text.disabled,
              borderColor: (theme) => theme.palette.divider,
            },
          }}
        >
          Conectar Todas
        </Button>
        <Button
          variant="outlined"
          startIcon={<DisconnectIcon />}
          onClick={onDisconnectAll}
          disabled={connectedCameras === 0}
          sx={{
            ...buttonStyles.outlined,
            "&:hover": {
              backgroundColor: colorTokens.alert.error,
              borderColor: colorTokens.alert.error,
              color: "#ffffff",
            },
            "&.Mui-disabled": {
              backgroundColor: "transparent",
              color: (theme) => theme.palette.text.disabled,
              borderColor: (theme) => theme.palette.divider,
            },
          }}
        >
          Desconectar Todas
        </Button>
      </Box>
    </Box>
  );
};
