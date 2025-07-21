/**
 * 📈 Metrics Line Chart Component - Universal Camera Viewer
 * Gráfico de líneas con múltiples series y leyenda
 */

import React, { memo } from 'react';
import {
  Box,
  Paper,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Skeleton,
  useTheme
} from "@mui/material";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { PublishMetrics } from "../../types";
import { formatDate } from "../../utils";

interface MetricsLineChartProps {
  data: PublishMetrics[];
  series: Array<{
    dataKey: keyof PublishMetrics;
    name: string;
    color: string;
    unit?: string;
  }>;
  height?: number;
  timeRange?: "1h" | "6h" | "24h" | "7d";
  onTimeRangeChange?: (range: "1h" | "6h" | "24h" | "7d") => void;
  isLoading?: boolean;
}

/**
 * Interface personalizada para el Tooltip
 */
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    name: string;
    color: string;
    dataKey: string;
    unit?: string;
  }>;
  label?: string;
}

/**
 * Tooltip personalizado para el gráfico
 */
const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    return (
      <Paper sx={{ p: 1.5, boxShadow: 2 }}>
        <Typography variant="caption" sx={{ display: "block", mb: 0.5 }}>
          {formatDate(label as string, "HH:mm:ss")}
        </Typography>
        {payload.map((entry, index: number) => (
          <Typography
            key={index}
            variant="caption"
            sx={{
              display: "block",
              color: entry.color,
            }}
          >
            {entry.name}: {entry.value?.toFixed(1)} {entry.unit || ""}
          </Typography>
        ))}
      </Paper>
    );
  }
  return null;
};

/**
 * Gráfico de líneas para métricas
 */
export const MetricsLineChart = memo<MetricsLineChartProps>(
  ({
    data,
    series,
    height = 300,
    timeRange = "1h",
    onTimeRangeChange,
    isLoading = false,
  }) => {
    const theme = useTheme();

    if (isLoading) {
      return (
        <Box sx={{ height }}>
          <Skeleton variant="rectangular" height={height} />
        </Box>
      );
    }

    if (data.length === 0) {
      return (
        <Box
          sx={{
            height,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            bgcolor: "grey.100",
            borderRadius: 1,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Sin datos disponibles
          </Typography>
        </Box>
      );
    }

    return (
      <Box>
        {onTimeRangeChange && (
          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
            <ToggleButtonGroup
              value={timeRange}
              exclusive
              onChange={(_, value) => value && onTimeRangeChange(value)}
              size="small"
            >
              <ToggleButton value="1h">1h</ToggleButton>
              <ToggleButton value="6h">6h</ToggleButton>
              <ToggleButton value="24h">24h</ToggleButton>
              <ToggleButton value="7d">7d</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        )}

        <ResponsiveContainer width="100%" height={height}>
          <LineChart
            data={data}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={theme.palette.divider}
              vertical={false}
            />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) => formatDate(value, "HH:mm")}
              stroke={theme.palette.text.secondary}
              fontSize={12}
            />
            <YAxis stroke={theme.palette.text.secondary} fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="line"
              wrapperStyle={{
                fontSize: "12px",
                paddingTop: "10px",
              }}
            />
            {series.map((serie) => (
              <Line
                key={serie.dataKey}
                type="monotone"
                dataKey={serie.dataKey}
                name={serie.name}
                stroke={serie.color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
                unit={serie.unit}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </Box>
    );
  }
);

MetricsLineChart.displayName = "MetricsLineChart";
