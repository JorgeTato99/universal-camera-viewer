/**
 * 📊 Active Publications Widget - Universal Camera Viewer
 * Widget para mostrar contador animado de publicaciones activas
 */

import React, { memo, useEffect, useState } from "react";
import { Card, CardContent, Box, Typography, Fade } from "@mui/material";
import {
  PlayCircle as ActiveIcon,
  Stop as InactiveIcon,
  TrendingUp,
  TrendingDown,
  TrendingFlat,
} from "@mui/icons-material";

interface ActivePublicationsWidgetProps {
  currentCount: number;
  previousCount?: number;
  totalCameras: number;
  isLoading?: boolean;
}

/**
 * Widget de publicaciones activas con animación
 */
export const ActivePublicationsWidget = memo<ActivePublicationsWidgetProps>(
  ({ currentCount, previousCount = 0, totalCameras, isLoading = false }) => {
    const [displayCount, setDisplayCount] = useState(currentCount);
    const trend =
      currentCount > previousCount
        ? "up"
        : currentCount < previousCount
        ? "down"
        : "flat";
    const percentage =
      totalCameras > 0 ? (currentCount / totalCameras) * 100 : 0;

    // Animación del contador
    useEffect(() => {
      if (displayCount === currentCount) return;

      const duration = 500; // ms
      const steps = 20;
      const stepDuration = duration / steps;
      const increment = (currentCount - displayCount) / steps;

      let step = 0;
      const timer = setInterval(() => {
        step++;
        if (step === steps) {
          setDisplayCount(currentCount);
          clearInterval(timer);
        } else {
          setDisplayCount((prev) => Math.round(prev + increment));
        }
      }, stepDuration);

      return () => clearInterval(timer);
    }, [currentCount, displayCount]);

    const getTrendIcon = () => {
      switch (trend) {
        case "up":
          return <TrendingUp sx={{ color: "#4caf50" }} />;
        case "down":
          return <TrendingDown sx={{ color: "#f44336" }} />;
        default:
          return <TrendingFlat sx={{ color: "#9e9e9e" }} />;
      }
    };

    return (
      <Card sx={{ height: "100%" }}>
        <CardContent>
          <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
            <ActiveIcon sx={{ mr: 1, color: "primary.main" }} />
            <Typography variant="h6">Publicaciones Activas</Typography>
          </Box>

          <Fade in timeout={300}>
            <Typography
              variant="h2"
              sx={{
                fontWeight: 300,
                color: currentCount > 0 ? "primary.main" : "text.secondary",
                mb: 1,
                transition: "all 0.3s ease-in-out",
              }}
            >
              {displayCount}
            </Typography>
          </Fade>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              de {totalCameras} cámaras
            </Typography>
            {!isLoading && trend !== "flat" && getTrendIcon()}
          </Box>

          <Box
            sx={{
              position: "relative",
              height: 4,
              bgcolor: "grey.200",
              borderRadius: 2,
            }}
          >
            <Box
              sx={{
                position: "absolute",
                height: "100%",
                width: `${percentage}%`,
                backgroundColor: currentCount > 0 ? "#2196f3" : "#9e9e9e",
                borderRadius: 2,
                transition: "width 0.5s ease-out",
              }}
            />
          </Box>

          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: "block", mt: 1, textAlign: "right" }}
          >
            {percentage.toFixed(0)}% activo
          </Typography>
        </CardContent>
      </Card>
    );
  }
);

ActivePublicationsWidget.displayName = "ActivePublicationsWidget";
