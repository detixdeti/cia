import { useState } from 'react';
import {
  AppBar,
  Box,
  Button,
  ButtonBase,
  Chip,
  IconButton,
  MenuItem,
  Stack,
  Tab,
  Tabs,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import AssignmentOutlinedIcon from '@mui/icons-material/AssignmentOutlined';
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined';
import type { ProjectSummary } from './types';
import type { ThemeMode } from './theme';
import Logo from './components/Logo';
import ConfirmDialog from './components/ConfirmDialog';

export type Page = 'overview' | 'mapping' | 'scenarios';

// Link to the questionnaire of the user study. As long as it is empty, the button is disabled.
const SURVEY_URL: string = '';

interface TopBarProps {
  page: Page;
  onPageChange: (page: Page) => void;
  projects: ProjectSummary[];
  projectId: string;
  onProjectChange: (projectId: string) => void;
  projectModified: boolean;
  onResetProject: () => void;
  themeMode: ThemeMode;
  onToggleTheme: () => void;
}

export default function TopBar({
  page,
  onPageChange,
  projects,
  projectId,
  onProjectChange,
  projectModified,
  onResetProject,
  themeMode,
  onToggleTheme,
}: TopBarProps) {
  const [confirmReset, setConfirmReset] = useState(false);

  return (
    <AppBar position="static" color="inherit" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Toolbar sx={{ gap: 2, py: 1 }}>
        <ButtonBase onClick={() => onPageChange('overview')} sx={{ gap: 1.25, borderRadius: 1.5, pr: 1 }}>
          <Logo size={34} />
          <Box sx={{ textAlign: 'left' }}>
            <Typography sx={{ fontWeight: 800, lineHeight: 1.15, fontSize: 15 }}>Change Impact Analysis</Typography>
            <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.1 }}>
              Use Cases ↔ Java-Code
            </Typography>
          </Box>
        </ButtonBase>

        <Tabs value={page} onChange={(_event, value: Page) => onPageChange(value)} sx={{ flex: 1, ml: 2 }}>
          <Tab
            value="overview"
            label="Übersicht"
            icon={<DashboardOutlinedIcon fontSize="small" />}
            iconPosition="start"
          />
          <Tab
            value="mapping"
            label="Zuordnungen"
            icon={<AccountTreeOutlinedIcon fontSize="small" />}
            iconPosition="start"
          />
          <Tab
            value="scenarios"
            label="Szenarien"
            icon={<ScienceOutlinedIcon fontSize="small" />}
            iconPosition="start"
          />
        </Tabs>

        <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          {projectModified && (
            <Tooltip title="Übernommene Szenarien sind im Arbeitsstand enthalten, die Originaldateien bleiben unverändert. Klicken zum Zurücksetzen.">
              <Chip
                color="warning"
                variant="outlined"
                icon={<RestartAltIcon />}
                label="Arbeitsstand geändert"
                onClick={() => setConfirmReset(true)}
              />
            </Tooltip>
          )}

          <Tooltip title={SURVEY_URL ? 'Umfrage in einem neuen Tab öffnen' : 'Der Link zur Umfrage folgt'}>
            {/* span: a disabled button cannot show a tooltip itself */}
            <span>
              <Button
                variant="contained"
                startIcon={<AssignmentOutlinedIcon />}
                href={SURVEY_URL}
                target="_blank"
                rel="noopener noreferrer"
                disabled={!SURVEY_URL}
              >
                Zur Umfrage
              </Button>
            </span>
          </Tooltip>

          <TextField
            select
            label="Projekt"
            value={projectId}
            onChange={(event) => onProjectChange(event.target.value)}
            sx={{ minWidth: 200 }}
          >
            {projects.map((project) => (
              <MenuItem key={project.id} value={project.id}>
                {project.name}
              </MenuItem>
            ))}
          </TextField>

          <Tooltip title={themeMode === 'dark' ? 'Heller Modus' : 'Dunkler Modus'}>
            <IconButton onClick={onToggleTheme}>
              {themeMode === 'dark' ? <LightModeOutlinedIcon /> : <DarkModeOutlinedIcon />}
            </IconButton>
          </Tooltip>
        </Stack>
      </Toolbar>

      <ConfirmDialog
        open={confirmReset}
        title="Arbeitsstand zurücksetzen?"
        confirmLabel="Zurücksetzen"
        color="warning"
        onConfirm={onResetProject}
        onClose={() => setConfirmReset(false)}
      >
        Alle übernommenen Szenarien werden verworfen und das Projekt wird wieder aus den Originaldateien gelesen. Die
        Szenarien selbst und ihre Analyseergebnisse bleiben erhalten.
      </ConfirmDialog>
    </AppBar>
  );
}
