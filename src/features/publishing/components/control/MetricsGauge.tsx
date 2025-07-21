/**
 * 🎯 Metrics Gauge Component - Universal Camera Viewer
 * Medidor circular estilo speedometer para métricas
 */

import React, { memo } from "react";
import { Box, Typography, useTheme } from "@mui/material";

interface MetricsGaugeProps {
  value: number;
  maxValue: number;
  label: string;
  unit: string;
  size?: number;
  thresholds?: {
    warning: number;
    critical: number;
  };
  showPercentage?: boolean;
}

/**
 * Medidor circular para visualizar métricas
 */
export const MetricsGauge = memo<MetricsGaugeProps>(
  ({
    value,
    maxValue,
    label,
    unit,
    size = 120,
    thresholds = { warning: 70, critical: 90 },
    showPercentage = false,
  }) => {
    const theme = useTheme();
    const percentage = Math.min((value / maxValue) * 100, 100);
    const strokeWidth = size * 0.08;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference * 0.75; // 270 degrees max

    const getColor = () => {
      const percentageValue = (value / maxValue) * 100;
      if (percentageValue >= thresholds.critical)
        return theme.palette.error.main;
      if (percentageValue >= thresholds.warning)
        return theme.palette.warning.main;
      return theme.palette.primary.main;
    };

    const color = getColor();

    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          position: "relative",
        }}
      >
        <Box sx={{ position: "relative", width: size, height: size }}>
          <svg
            width={size}
            height={size}
            style={{ transform: "rotate(-135deg)" }}
          >
            {/* Fondo del arco */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={theme.palette.grey[300]}
              strokeWidth={strokeWidth}
              strokeDasharray={`${circumference * 0.75} ${
                circumference * 0.25
              }`}
            />

            {/* Arco de progreso */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={`${circumference * 0.75} ${
                circumference * 0.25
              }`}
              strokeDashoffset={offset}
              style={{
                transition: "stroke-dashoffset 1s ease-out"
              }}
            />
          </svg>

          {/* Valor central */}
          <Box
            sx={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              textAlign: "center",
            }}
          >
            <Typography
              variant="h5"
              sx={{
                fontWeight: 500,
                color,
                fontSize: size * 0.2,
                lineHeight: 1,
              }}
            >
              {value.toFixed(0)}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: "text.secondary",
                fontSize: size * 0.1,
              }}
            >
              {unit}
            </Typography>
          </Box>
        </Box>

        {/* Etiqueta */}
        <Typography
          variant="body2"
          sx={{
            mt: 1,
            color: "text.secondary",
            textAlign: "center",
          }}
        >
          {label}
        </Typography>

        {/* Porcentaje opcional */}
        {showPercentage && (
          <Typography
            variant="caption"
            sx={{
              color: "text.secondary",
              fontWeight: 500,
            }}
          >
            {percentage.toFixed(0)}%
          </Typography>
        )}
      </Box>
    );
  }
);

MetricsGauge.displayName = "MetricsGauge";
