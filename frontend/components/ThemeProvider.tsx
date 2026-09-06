'use client';

import React from 'react';
import { createTheme, ThemeProvider as MUIThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { usePOSStore } from '@/store/usePOSStore';

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  const darkMode = usePOSStore((state) => state.darkMode);
  
  const muiTheme = React.useMemo(() => createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: '#8b5cf6', // Violet
      },
      secondary: {
        main: '#10b981', // Emerald
      },
      background: {
        default: darkMode ? '#0f172a' : '#f8fafc',
        paper: darkMode ? '#1e293b' : '#ffffff',
      },
    },
    typography: {
      fontFamily: 'Inter, Outfit, sans-serif',
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: '8px',
          }
        }
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: '12px',
          }
        }
      }
    }
  }), [darkMode]);

  return (
    <MUIThemeProvider theme={muiTheme}>
      <CssBaseline />
      <div className={darkMode ? 'dark text-slate-100 min-h-screen bg-slate-950' : 'text-slate-800 min-h-screen bg-slate-50'}>
        {children}
      </div>
    </MUIThemeProvider>
  );
}
