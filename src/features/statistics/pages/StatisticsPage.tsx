/**
 * 📊 Statistics Page - Universal Camera Viewer
 * Vista principal de estadísticas del sistema
 */

import React, { memo, useState, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Fade,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Dashboard as DashboardIcon,
  Timeline as TimelineIcon,
  Event as EventIcon,
  Speed as PerformanceIcon,
  NetworkCheck as NetworkIcon,
  Analytics as AnalyticsIcon,
} from "@mui/icons-material";

// Lazy load subsections
const OverviewDashboard = React.lazy(() => import("./overview/OverviewDashboard"));
const ConnectionAnalytics = React.lazy(() => import("./analytics/ConnectionAnalytics"));
const EventTimeline = React.lazy(() => import("./events/EventTimeline"));
const PerformanceMetrics = React.lazy(() => import("./performance/PerformanceMetrics"));
const NetworkScanHistory = React.lazy(() => import("./network/NetworkScanHistory"));
const DetailedReports = React.lazy(() => import("./reports/DetailedReports"));

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = memo(({ children, value, index }: TabPanelProps) => (
  <Box
    role="tabpanel"
    hidden={value !== index}
    id={`statistics-tabpanel-${index}`}
    aria-labelledby={`statistics-tab-${index}`}
  >
    {value === index && <Box>{children}</Box>}
  </Box>
));

TabPanel.displayName = "TabPanel";

const TABS = [
  { label: "General", icon: <DashboardIcon />, path: "overview" },
  { label: "Conexiones", icon: <TimelineIcon />, path: "connections" },
  { label: "Eventos", icon: <EventIcon />, path: "events" },
  { label: "Rendimiento", icon: <PerformanceIcon />, path: "performance" },
  { label: "Red", icon: <NetworkIcon />, path: "network" },
  { label: "Reportes", icon: <AnalyticsIcon />, path: "reports" },
];

export const StatisticsPage = memo(() => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  // Determine active tab from URL
  const pathSegments = location.pathname.split("/");
  const currentPath = pathSegments[pathSegments.length - 1] || "overview";
  const activeTab = TABS.findIndex((tab) => tab.path === currentPath);

  const [value, setValue] = useState(activeTab >= 0 ? activeTab : 0);

  useEffect(() => {
    // Update tab when URL changes
    const newActiveTab = TABS.findIndex((tab) => tab.path === currentPath);
    if (newActiveTab >= 0 && newActiveTab !== value) {
      setValue(newActiveTab);
    }
  }, [currentPath, value]);

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
    navigate(`/statistics/${TABS[newValue].path}`);
  };

  return (
    <Fade in timeout={600}>
      <Box sx={{ width: "100%", height: "100%" }}>
        <Paper
          sx={{
            borderRadius: 2,
            overflow: "hidden",
            height: "100%",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Header */}
          <Box
            sx={{
              px: 3,
              py: 2,
              borderBottom: 1,
              borderColor: "divider",
              background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
              color: "white",
            }}
          >
            <Typography variant="h5" component="h1">
              Estadísticas del Sistema
            </Typography>
          </Box>

          {/* Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <Tabs
              value={value}
              onChange={handleChange}
              variant={isMobile ? "scrollable" : "fullWidth"}
              scrollButtons={isMobile ? "auto" : false}
              sx={{
                "& .MuiTab-root": {
                  minHeight: 64,
                  textTransform: "none",
                },
              }}
            >
              {TABS.map((tab, index) => (
                <Tab
                  key={tab.path}
                  label={
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      {tab.icon}
                      {!isMobile && tab.label}
                    </Box>
                  }
                  id={`statistics-tab-${index}`}
                  aria-controls={`statistics-tabpanel-${index}`}
                />
              ))}
            </Tabs>
          </Box>

          {/* Content */}
          <Box sx={{ flex: 1, overflow: "auto", p: 3 }}>
            <React.Suspense
              fallback={
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    height: "100%",
                  }}
                >
                  <Typography>Cargando...</Typography>
                </Box>
              }
            >
              <TabPanel value={value} index={0}>
                <OverviewDashboard />
              </TabPanel>
              <TabPanel value={value} index={1}>
                <ConnectionAnalytics />
              </TabPanel>
              <TabPanel value={value} index={2}>
                <EventTimeline />
              </TabPanel>
              <TabPanel value={value} index={3}>
                <PerformanceMetrics />
              </TabPanel>
              <TabPanel value={value} index={4}>
                <NetworkScanHistory />
              </TabPanel>
              <TabPanel value={value} index={5}>
                <DetailedReports />
              </TabPanel>
            </React.Suspense>
          </Box>
        </Paper>
      </Box>
    </Fade>
  );
});

StatisticsPage.displayName = "StatisticsPage";

export default StatisticsPage;