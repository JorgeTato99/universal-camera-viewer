/**
 * 👥 Viewers Chart Component - Universal Camera Viewer
 * Gráfico de área para visualización de viewers
 */

import React, { memo, useMemo } from 'react';
import {
  Box,
  Typography,
  useTheme,
  Skeleton,
  Paper,
  Chip
} from '@mui/material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Brush
} from 'recharts';
import { TrendingUp, TrendingDown } from '@mui/icons-material';
import { formatDate } from '../../utils';

interface ViewerData {
  timestamp: string;
  viewers: number;
  cameras: number;
}

interface ViewersChartProps {
  data: ViewerData[];
  height?: number;
  showBrush?: boolean;
  isLoading?: boolean;
  showStats?: boolean;
}

/**
 * Interface personalizada para el Tooltip
 */
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    name: string;
    color?: string;
    dataKey: string;
    payload: ViewerData;
  }>;
  label?: string;
}

/**
 * Tooltip personalizado
 */
const CustomTooltip = ({ 
  active, 
  payload, 
  label 
}: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    return (
      <Paper sx={{ p: 1.5, boxShadow: 2 }}>
        <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>
          {formatDate(label as string, 'dd/MM HH:mm')}
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', color: '#2196f3' }}>
          Viewers: {payload[0].value}
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary' }}>
          Cámaras activas: {payload[0].payload.cameras}
        </Typography>
      </Paper>
    );
  }
  return null;
};

/**
 * Gráfico de área para viewers
 */
export const ViewersChart = memo<ViewersChartProps>(({
  data,
  height = 250,
  showBrush = true,
  isLoading = false,
  showStats = true
}) => {
  const theme = useTheme();

  // Calcular estadísticas
  const stats = useMemo(() => {
    if (data.length === 0) return null;

    const viewers = data.map(d => d.viewers);
    const current = viewers[viewers.length - 1];
    const previous = viewers[viewers.length - 2] || current;
    const max = Math.max(...viewers);
    const avg = viewers.reduce((a, b) => a + b, 0) / viewers.length;
    const trend = current > previous ? 'up' : current < previous ? 'down' : 'flat';

    return { current, max, avg, trend };
  }, [data]);

  if (isLoading) {
    return (
      <Box sx={{ height: height + (showStats ? 60 : 0) }}>
        <Skeleton variant="rectangular" height={height} />
        {showStats && (
          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            <Skeleton variant="rounded" width={100} height={32} />
            <Skeleton variant="rounded" width={100} height={32} />
            <Skeleton variant="rounded" width={100} height={32} />
          </Box>
        )}
      </Box>
    );
  }

  if (data.length === 0) {
    return (
      <Box
        sx={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'grey.100',
          borderRadius: 1
        }}
      >
        <Typography variant="body2" color="text.secondary">
          Sin datos de viewers
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart
          data={data}
          margin={{ top: 10, right: 30, left: 0, bottom: showBrush ? 30 : 0 }}
        >
          <defs>
            <linearGradient id="colorViewers" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2196f3" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#2196f3" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke={theme.palette.divider}
            vertical={false}
          />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => formatDate(value, 'HH:mm')}
            stroke={theme.palette.text.secondary}
            fontSize={12}
          />
          <YAxis
            stroke={theme.palette.text.secondary}
            fontSize={12}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="viewers"
            stroke="#2196f3"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorViewers)"
          />
          {showBrush && data.length > 20 && (
            <Brush
              dataKey="timestamp"
              height={20}
              stroke={theme.palette.primary.main}
              tickFormatter={(value) => formatDate(value, 'HH:mm')}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>

      {showStats && stats && (
        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Chip
            label={`Actual: ${stats.current}`}
            size="small"
            icon={
              stats.trend === 'up' ? <TrendingUp /> :
              stats.trend === 'down' ? <TrendingDown /> :
              undefined
            }
            color={stats.current > 0 ? 'primary' : 'default'}
          />
          <Chip
            label={`Máximo: ${stats.max}`}
            size="small"
            variant="outlined"
          />
          <Chip
            label={`Promedio: ${stats.avg.toFixed(1)}`}
            size="small"
            variant="outlined"
          />
        </Box>
      )}
    </Box>
  );
});

ViewersChart.displayName = 'ViewersChart';