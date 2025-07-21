/**
 * 🔌 Test Connection Button Component - Universal Camera Viewer
 * Botón para probar conexión con estados visuales
 */

import React, { memo, useState } from "react";
import {
  Button,
  CircularProgress,
  Box,
  Typography,
  Collapse,
  Alert,
  IconButton,
  Fade,
} from "@mui/material";
import {
  WifiTethering as TestIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Close as CloseIcon,
} from "@mui/icons-material";

interface TestConnectionButtonProps {
  onTest: () => Promise<{ success: boolean; message?: string; details?: any }>;
  disabled?: boolean;
  fullWidth?: boolean;
  showDetails?: boolean;
}

type TestState = "idle" | "testing" | "success" | "error";

/**
 * Botón de prueba de conexión con retroalimentación visual
 */
export const TestConnectionButton = memo<TestConnectionButtonProps>(
  ({ onTest, disabled = false, fullWidth = false, showDetails = true }) => {
    const [state, setState] = useState<TestState>("idle");
    const [result, setResult] = useState<{
      message?: string;
      details?: any;
    } | null>(null);

    const handleTest = async () => {
      setState("testing");
      setResult(null);

      try {
        const response = await onTest();
        setState(response.success ? "success" : "error");
        setResult({
          message: response.message,
          details: response.details,
        });

        // Auto-limpiar después de 10 segundos si es exitoso
        if (response.success) {
          setTimeout(() => {
            setState("idle");
            setResult(null);
          }, 10000);
        }
      } catch (error) {
        setState("error");
        setResult({
          message: "Error al probar la conexión",
          details: error,
        });
      }
    };

    const getButtonProps = () => {
      switch (state) {
        case "testing":
          return {
            color: "inherit" as const,
            startIcon: <CircularProgress size={20} />,
            children: "Probando conexión...",
            disabled: true,
          };
        case "success":
          return {
            color: "success" as const,
            startIcon: <SuccessIcon />,
            children: "Conexión exitosa",
            disabled: false,
          };
        case "error":
          return {
            color: "error" as const,
            startIcon: <ErrorIcon />,
            children: "Error de conexión",
            disabled: false,
          };
        default:
          return {
            color: "primary" as const,
            startIcon: <TestIcon />,
            children: "Probar Conexión",
            disabled: disabled,
          };
      }
    };

    const buttonProps = getButtonProps();

    return (
      <Box>
        <Fade in timeout={200}>
          <Box>
            <Button
              variant="outlined"
              onClick={handleTest}
              fullWidth={fullWidth}
              {...buttonProps}
            />
          </Box>
        </Fade>

        {showDetails && result && (
          <Collapse in={!!result} timeout={300}>
            <Alert
              severity={state === "success" ? "success" : "error"}
              sx={{ mt: 2 }}
              action={
                <IconButton
                  size="small"
                  onClick={() => {
                    setResult(null);
                    setState("idle");
                  }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              }
            >
              <Typography variant="body2">
                {result.message ||
                  (state === "success"
                    ? "Conexión establecida correctamente"
                    : "No se pudo establecer la conexión")}
              </Typography>

              {result.details && (
                <Box sx={{ mt: 1 }}>
                  <Typography
                    variant="caption"
                    sx={{ display: "block", fontWeight: 500 }}
                  >
                    Detalles:
                  </Typography>
                  <Typography
                    variant="caption"
                    component="pre"
                    sx={{
                      fontFamily: "monospace",
                      fontSize: "0.75rem",
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                      mt: 0.5,
                    }}
                  >
                    {typeof result.details === "object"
                      ? JSON.stringify(result.details, null, 2)
                      : result.details}
                  </Typography>
                </Box>
              )}
            </Alert>
          </Collapse>
        )}
      </Box>
    );
  }
);

TestConnectionButton.displayName = "TestConnectionButton";
