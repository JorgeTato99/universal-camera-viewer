/**
 * 🎯 MainLayout Component - Universal Camera Viewer
 * Layout principal tipo VS Code con TopBar y Sidebar
 */

import React, { useState, useEffect } from "react";
import { Box, useMediaQuery, useTheme } from "@mui/material";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";
import { colorTokens } from "../../design-system/tokens";

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Auto-colapsar en móviles
  useEffect(() => {
    if (isMobile) {
      setSidebarCollapsed(true);
      setMobileMenuOpen(false);
    }
  }, [isMobile]);

  const handleSidebarToggle = () => {
    if (isMobile) {
      setMobileMenuOpen(!mobileMenuOpen);
    } else {
      setSidebarCollapsed(!sidebarCollapsed);
    }
  };

  const handleMobileMenuToggle = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  // Calcular el ancho del sidebar
  const sidebarWidth = sidebarCollapsed ? 48 : 240;

  return (
    <Box
      sx={{
        display: "flex",
        height: "100vh",
        backgroundColor: colorTokens.background.light,
        overflow: "hidden",
      }}
    >
      {/* TopBar fijo */}
      <TopBar
        onMenuToggle={handleMobileMenuToggle}
        sidebarCollapsed={sidebarCollapsed}
      />

      {/* Sidebar */}
      <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          zIndex: theme.zIndex.drawer,
          transition: "transform 0.2s ease",
          transform: {
            xs: mobileMenuOpen ? "translateX(0)" : "translateX(-100%)",
            md: "translateX(0)",
          },
        }}
      >
        <Sidebar collapsed={sidebarCollapsed} onToggle={handleSidebarToggle} />
      </Box>

      {/* Overlay para móviles */}
      {isMobile && mobileMenuOpen && (
        <Box
          sx={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            zIndex: theme.zIndex.drawer - 1,
          }}
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Contenido principal */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          height: "100vh",
          overflow: "auto",
          backgroundColor: colorTokens.background.light,
          marginLeft: {
            xs: 0,
            md: `${sidebarWidth}px`,
          },
          marginTop: "32px", // Altura del TopBar
          transition: "margin-left 0.2s ease",
          position: "relative",
        }}
      >
        {/* Área de contenido */}
        <Box
          sx={{
            height: "calc(100vh - 32px)",
            overflow: "auto",
            position: "relative",
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};
