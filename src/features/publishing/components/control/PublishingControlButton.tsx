/**
 * 🎮 Publishing Control Button - Universal Camera Viewer
 * Botón de control con estados y confirmación
 */

import React, { memo, useState } from "react";
import {
  Button,
  IconButton,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Tooltip,
} from "@mui/material";
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Refresh as RestartIcon,
} from "@mui/icons-material";

interface PublishingControlButtonProps {
  cameraId: string;
  cameraName: string;
  status: "idle" | "starting" | "running" | "stopping" | "error";
  onStart: (cameraId: string, forceRestart?: boolean) => Promise<void>;
  onStop: (cameraId: string) => Promise<void>;
  variant?: "button" | "icon";
  size?: "small" | "medium" | "large";
  showConfirmation?: boolean;
  disabled?: boolean;
}

/**
 * Botón de control de publicación con estados
 */
export const PublishingControlButton = memo<PublishingControlButtonProps>(
  ({
    cameraId,
    cameraName,
    status,
    onStart,
    onStop,
    variant = "button",
    size = "medium",
    showConfirmation = true,
    disabled = false,
  }) => {
    const [confirmDialog, setConfirmDialog] = useState<
      "start" | "stop" | "restart" | null
    >(null);
    const [isProcessing, setIsProcessing] = useState(false);

    const isTransitioning = status === "starting" || status === "stopping";
    const isRunning = status === "running";
    const isError = status === "error";

    const handleAction = async (action: "start" | "stop" | "restart") => {
      if (showConfirmation) {
        setConfirmDialog(action);
      } else {
        await executeAction(action);
      }
    };

    const executeAction = async (action: "start" | "stop" | "restart") => {
      setIsProcessing(true);
      try {
        switch (action) {
          case "start":
            await onStart(cameraId, false);
            break;
          case "stop":
            await onStop(cameraId);
            break;
          case "restart":
            await onStart(cameraId, true);
            break;
        }
      } finally {
        setIsProcessing(false);
        setConfirmDialog(null);
      }
    };

    const getActionButton = () => {
      if (isTransitioning || isProcessing) {
        return {
          icon: <CircularProgress size={20} />,
          label: status === "starting" ? "Iniciando..." : "Deteniendo...",
          color: "inherit" as const,
          disabled: true,
        };
      }

      if (isRunning) {
        return {
          icon: <StopIcon />,
          label: "Detener",
          color: "error" as const,
          onClick: () => handleAction("stop"),
          disabled: disabled,
        };
      }

      if (isError) {
        return {
          icon: <RestartIcon />,
          label: "Reintentar",
          color: "warning" as const,
          onClick: () => handleAction("restart"),
          disabled: disabled,
        };
      }

      return {
        icon: <StartIcon />,
        label: "Iniciar",
        color: "primary" as const,
        onClick: () => handleAction("start"),
        disabled: disabled,
      };
    };

    const buttonProps = getActionButton();

    const renderButton = () => {
      if (variant === "icon") {
        return (
          <Tooltip title={buttonProps.label}>
            <span>
              <IconButton
                size={size}
                color={buttonProps.color}
                onClick={buttonProps.onClick}
                disabled={buttonProps.disabled}
              >
                {buttonProps.icon}
              </IconButton>
            </span>
          </Tooltip>
        );
      }

      return (
        <Button
          size={size}
          variant="contained"
          color={buttonProps.color}
          startIcon={buttonProps.icon}
          onClick={buttonProps.onClick}
          disabled={buttonProps.disabled}
        >
          {buttonProps.label}
        </Button>
      );
    };

    const getConfirmationMessage = () => {
      switch (confirmDialog) {
        case "start":
          return `¿Iniciar publicación para ${cameraName}?`;
        case "stop":
          return `¿Detener publicación para ${cameraName}?`;
        case "restart":
          return `¿Reiniciar publicación para ${cameraName}?`;
        default:
          return "";
      }
    };

    return (
      <>
        {renderButton()}

        {/* Diálogo de confirmación */}
        <Dialog
          open={confirmDialog !== null}
          onClose={() => setConfirmDialog(null)}
          maxWidth="xs"
          fullWidth
        >
          <DialogTitle>Confirmar Acción</DialogTitle>
          <DialogContent>
            <Typography>{getConfirmationMessage()}</Typography>
            {confirmDialog === "stop" && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Se detendrá la transmisión hacia el servidor MediaMTX.
              </Typography>
            )}
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setConfirmDialog(null)}
              disabled={isProcessing}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => confirmDialog && executeAction(confirmDialog)}
              variant="contained"
              color={confirmDialog === "stop" ? "error" : "primary"}
              disabled={isProcessing}
              startIcon={
                isProcessing ? <CircularProgress size={16} /> : undefined
              }
            >
              {isProcessing ? "Procesando..." : "Confirmar"}
            </Button>
          </DialogActions>
        </Dialog>
      </>
    );
  }
);

PublishingControlButton.displayName = "PublishingControlButton";
