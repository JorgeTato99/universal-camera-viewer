/**
 * 🚨 Alerts List Component - Universal Camera Viewer
 * Lista de alertas con funciones de dismiss y snooze
 */

import React, { memo, useState } from "react";
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  Typography,
  Collapse,
} from "@mui/material";
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  MoreVert as MoreIcon,
  Close as DismissIcon,
  Snooze as SnoozeIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
} from "@mui/icons-material";
import { PublishingAlert } from "../../types";

interface AlertsListProps {
  alerts: PublishingAlert[];
  onDismiss?: (alertId: string) => void;
  onSnooze?: (alertId: string, minutes: number) => void;
  maxVisible?: number;
  showActions?: boolean;
}

/**
 * Componente de lista de alertas
 */
export const AlertsList = memo<AlertsListProps>(
  ({ alerts, onDismiss, onSnooze, maxVisible = 5, showActions = true }) => {
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [selectedAlert, setSelectedAlert] = useState<string | null>(null);
    const [expanded, setExpanded] = useState(false);
    const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(
      new Set()
    );

    const visibleAlerts = expanded ? alerts : alerts.slice(0, maxVisible);
    const hasMore = alerts.length > maxVisible;

    const handleMenuOpen = (
      event: React.MouseEvent<HTMLElement>,
      alertId: string
    ) => {
      setAnchorEl(event.currentTarget);
      setSelectedAlert(alertId);
    };

    const handleMenuClose = () => {
      setAnchorEl(null);
      setSelectedAlert(null);
    };

    const handleDismiss = (alertId: string) => {
      setDismissedAlerts((prev) => new Set(prev).add(alertId));
      onDismiss?.(alertId);
      handleMenuClose();
    };

    const handleSnooze = (minutes: number) => {
      if (selectedAlert) {
        onSnooze?.(selectedAlert, minutes);
        handleMenuClose();
      }
    };

    const getAlertIcon = (severity: string) => {
      switch (severity) {
        case "critical":
        case "error":
          return <ErrorIcon sx={{ color: "#f44336" }} />;
        case "warning":
          return <WarningIcon sx={{ color: "#ff9800" }} />;
        default:
          return <InfoIcon sx={{ color: "#2196f3" }} />;
      }
    };

    const getSeverityColor = (severity: string) => {
      switch (severity) {
        case "critical":
        case "error":
          return "error";
        case "warning":
          return "warning";
        default:
          return "info";
      }
    };

    if (alerts.length === 0) {
      return (
        <Box sx={{ py: 3, textAlign: "center" }}>
          <Typography variant="body2" color="text.secondary">
            No hay alertas activas
          </Typography>
        </Box>
      );
    }

    return (
      <Box>
        <List sx={{ py: 0 }}>
          {visibleAlerts.map((alert) => (
            <Collapse
              key={alert.id}
              in={!dismissedAlerts.has(alert.id)}
              timeout={300}
            >
              <ListItem sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {getAlertIcon(alert.severity)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Typography variant="body2">{alert.message}</Typography>
                      <Chip
                        label={alert.alert_type}
                        size="small"
                        color={getSeverityColor(alert.severity)}
                        sx={{ height: 20 }}
                      />
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {new Date(alert.timestamp).toLocaleString("es-ES")}
                      {alert.camera_id && ` • Cámara: ${alert.camera_id}`}
                    </Typography>
                  }
                />
                {showActions && (
                  <ListItemSecondaryAction>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, alert.id)}
                    >
                      <MoreIcon fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                )}
              </ListItem>
            </Collapse>
          ))}
        </List>

        {hasMore && (
          <Box sx={{ textAlign: "center", mt: 1 }}>
            <IconButton
              size="small"
              onClick={() => setExpanded(!expanded)}
              sx={{
                "&:hover": {
                  backgroundColor: "action.hover",
                },
              }}
            >
              {expanded ? <CollapseIcon /> : <ExpandIcon />}
            </IconButton>
            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
              {expanded ? "Ver menos" : `Ver ${alerts.length - maxVisible} más`}
            </Typography>
          </Box>
        )}

        {/* Menú de acciones */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
          transformOrigin={{ vertical: "top", horizontal: "right" }}
        >
          <MenuItem
            onClick={() => selectedAlert && handleDismiss(selectedAlert)}
          >
            <ListItemIcon>
              <DismissIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Descartar</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => handleSnooze(15)}>
            <ListItemIcon>
              <SnoozeIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Posponer 15 min</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => handleSnooze(60)}>
            <ListItemIcon>
              <SnoozeIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Posponer 1 hora</ListItemText>
          </MenuItem>
        </Menu>
      </Box>
    );
  }
);

AlertsList.displayName = "AlertsList";
