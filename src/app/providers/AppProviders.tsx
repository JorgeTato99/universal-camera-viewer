import React from "react";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { BrowserRouter } from "react-router-dom";
import { lightTheme, darkTheme, getTheme } from "../../design-system/theme";

interface AppProvidersProps {
  children: React.ReactNode;
  themeMode?: "light" | "dark";
}

export const AppProviders: React.FC<AppProvidersProps> = ({
  children,
  themeMode = "light",
}) => {
  const theme = getTheme(themeMode);

  return (
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </BrowserRouter>
  );
};

export default AppProviders;
