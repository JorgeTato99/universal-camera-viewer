/**
 * 🎨 ThemeToggle Component - Universal Camera Viewer
 * Componente para cambiar entre temas light/dark/system
 */

import React, { useState } from "react";
import {
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  alpha,
  useTheme as useMuiTheme,
} from "@mui/material";
import {
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  SettingsBrightness as SystemIcon,
  Check as CheckIcon,
} from "@mui/icons-material";
import { useTheme } from "../../hooks/useTheme";
import { colorTokens } from "../../design-system/tokens";
import type { ThemeMode } from "../../stores/appStore";

interface ThemeOption {
  mode: ThemeMode;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const themeOptions: ThemeOption[] = [
  {
    mode: "light",
    label: "Claro",
    icon: <LightModeIcon fontSize="small" />,
    description: "Tema claro",
  },
  {
    mode: "dark",
    label: "Oscuro",
    icon: <DarkModeIcon fontSize="small" />,
    description: "Tema oscuro",
  },
  {
    mode: "system",
    label: "Sistema",
    icon: <SystemIcon fontSize="small" />,
    description: "Seguir preferencia del sistema",
  },
];

interface ThemeToggleProps {
  size?: "small" | "medium" | "large";
  showLabel?: boolean;
  variant?: "icon" | "button";
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  size = "medium",
  showLabel = false,
  variant = "icon",
}) => {
  const muiTheme = useMuiTheme();
  const { themeMode, effectiveTheme, setThemeMode } = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleThemeChange = (mode: ThemeMode) => {
    setThemeMode(mode);
    handleClose();
  };

  // Obtener el icono actual
  const getCurrentIcon = () => {
    if (themeMode === "system") {
      return <SystemIcon fontSize={size} />;
    }
    return effectiveTheme === "dark" ? (
      <DarkModeIcon fontSize={size} />
    ) : (
      <LightModeIcon fontSize={size} />
    );
  };

  return (
    <>
      <Tooltip title="Cambiar tema" arrow>
        <IconButton
          onClick={handleClick}
          size={size}
          sx={{
            color: (theme) => theme.palette.text.secondary,
            "&:hover": {
              backgroundColor: (theme) => theme.palette.action.hover,
              color: (theme) => theme.palette.text.primary,
            },
            transition: "all 0.2s ease",
          }}
        >
          {getCurrentIcon()}
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        transformOrigin={{ horizontal: "right", vertical: "top" }}
        anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
        slotProps={{
          paper: {
            sx: {
              minWidth: 200,
              backgroundColor: (theme) => theme.palette.background.paper,
              border: (theme) => `1px solid ${theme.palette.divider}`,
              boxShadow:
                effectiveTheme === "dark"
                  ? "0 8px 32px rgba(0, 0, 0, 0.32)"
                  : "0 8px 32px rgba(0, 0, 0, 0.12)",
            },
          },
        }}
      >
        {themeOptions.map((option) => (
          <MenuItem
            key={option.mode}
            onClick={() => handleThemeChange(option.mode)}
            selected={themeMode === option.mode}
            sx={{
              py: 1.5,
              px: 2,
              gap: 1.5,
              color: (theme) => theme.palette.text.primary,
              "&:hover": {
                backgroundColor: (theme) => theme.palette.action.hover,
              },
              "&.Mui-selected": {
                backgroundColor: alpha(colorTokens.primary[500], 0.1),
                color:
                  effectiveTheme === "dark"
                    ? colorTokens.primary[300]
                    : colorTokens.primary[700],
                "&:hover": {
                  backgroundColor: alpha(colorTokens.primary[500], 0.15),
                },
              },
            }}
          >
            <ListItemIcon
              sx={{
                color: "inherit",
                minWidth: 36,
              }}
            >
              {option.icon}
            </ListItemIcon>

            <ListItemText
              primary={option.label}
              secondary={option.description}
              sx={{
                "& .MuiListItemText-primary": {
                  fontSize: "0.875rem",
                  fontWeight: themeMode === option.mode ? 500 : 400,
                },
                "& .MuiListItemText-secondary": {
                  fontSize: "0.75rem",
                  color:
                    effectiveTheme === "dark"
                      ? colorTokens.neutral[400]
                      : colorTokens.neutral[500],
                },
              }}
            />

            {themeMode === option.mode && (
              <CheckIcon
                fontSize="small"
                sx={{
                  color: colorTokens.primary[500],
                  ml: 1,
                }}
              />
            )}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
};
