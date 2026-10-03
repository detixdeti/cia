import { createTheme } from '@mui/material/styles';

export type ThemeMode = 'light' | 'dark';

// Colors for the artifact types. They are deliberately different from the
// highlight color (primary), so type and selection state never get mixed up.
export const artifactColors = {
  useCase: '#8b5cf6',
  javaClass: '#14b8a6',
};

export function createAppTheme(mode: ThemeMode) {
  const isDark = mode === 'dark';

  return createTheme({
    palette: {
      mode,
      primary: { main: isDark ? '#38bdf8' : '#0284c7' },
      background: {
        default: isDark ? '#0d1117' : '#f4f6f9',
        paper: isDark ? '#151b23' : '#ffffff',
      },
    },
    shape: { borderRadius: 10 },
    // A compact look: smaller base font and small controls everywhere,
    // so graph, matrix and detail panel fit on one screen.
    typography: {
      fontSize: 12.5,
      fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
      h5: { fontSize: '1.3rem' },
      h6: { fontSize: '1.05rem' },
    },
    spacing: 7,
    components: {
      MuiButton: {
        defaultProps: { disableElevation: true, size: 'small' },
        styleOverrides: { root: { textTransform: 'none', fontWeight: 600 } },
      },
      MuiToggleButton: { styleOverrides: { root: { textTransform: 'none', fontWeight: 600 } } },
      MuiIconButton: { defaultProps: { size: 'small' } },
      MuiTextField: { defaultProps: { size: 'small' } },
      MuiAutocomplete: { defaultProps: { size: 'small' } },
      MuiToggleButtonGroup: { defaultProps: { size: 'small' } },
      MuiChip: { defaultProps: { size: 'small' } },
      MuiSwitch: { defaultProps: { size: 'small' } },
      MuiList: { defaultProps: { dense: true } },
      MuiToolbar: { defaultProps: { variant: 'dense' } },
      MuiTab: {
        styleOverrides: {
          root: { minHeight: 40, paddingTop: 6, paddingBottom: 6, textTransform: 'none', fontWeight: 600 },
        },
      },
      MuiTabs: { styleOverrides: { root: { minHeight: 40 } } },
      MuiPaper: { defaultProps: { elevation: 0 } },
      MuiAppBar: { styleOverrides: { root: { backgroundImage: 'none' } } },
      MuiTooltip: { defaultProps: { arrow: true, enterDelay: 400 } },
    },
  });
}
