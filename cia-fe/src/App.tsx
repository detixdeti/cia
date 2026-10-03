import { useEffect, useMemo, useState } from 'react';
import { Alert, Box, CircularProgress, CssBaseline, ThemeProvider } from '@mui/material';
import { fetchProject, fetchProjects, resetProject } from './api';
import { createAppTheme, type ThemeMode } from './theme';
import type { Project, ProjectSummary, ScenarioDetail } from './types';
import TopBar, { type Page } from './TopBar';
import OverviewPage from './overview/OverviewPage';
import MappingView from './mapping/MappingView';
import { buildScenarioOverlay, type ScenarioOverlay } from './mapping/mappingModel';
import ScenariosPage from './scenarios/ScenariosPage';
import ImportWarnings from './ImportWarnings';
import { NotificationProvider, useNotify } from './components/Notifications';

const THEME_STORAGE_KEY = 'cia-theme-mode';

export default function App() {
  const [themeMode, setThemeMode] = useState<ThemeMode>(
    () => (localStorage.getItem(THEME_STORAGE_KEY) as ThemeMode | null) ?? 'dark',
  );
  const theme = useMemo(() => createAppTheme(themeMode), [themeMode]);

  const toggleThemeMode = () => {
    const next = themeMode === 'dark' ? 'light' : 'dark';
    setThemeMode(next);
    localStorage.setItem(THEME_STORAGE_KEY, next);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <NotificationProvider>
        <AppContent themeMode={themeMode} onToggleTheme={toggleThemeMode} />
      </NotificationProvider>
    </ThemeProvider>
  );
}

function AppContent({ themeMode, onToggleTheme }: { themeMode: ThemeMode; onToggleTheme: () => void }) {
  const notify = useNotify();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [project, setProject] = useState<Project | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState<Page>('overview');
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | null>(null);
  // A scenario marked in the mapping view ("Im Graph anzeigen")
  const [overlay, setOverlay] = useState<ScenarioOverlay | null>(null);

  useEffect(() => {
    fetchProjects()
      .then((list) => {
        setProjects(list);
        // The app always starts with the sample project if it exists.
        const start = list.find((p) => p.id === 'sample-project') ?? list[0];
        if (start) setSelectedProjectId(start.id);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!selectedProjectId) return;
    setProject(null);
    fetchProject(selectedProjectId)
      .then(setProject)
      .catch((e: Error) => setError(e.message));
  }, [selectedProjectId]);

  // Applying a scenario or resetting changes the project files.
  const reloadProject = () => {
    fetchProject(selectedProjectId)
      .then(setProject)
      .catch((e: Error) => setError(e.message));
  };

  const selectProject = (projectId: string) => {
    setSelectedProjectId(projectId);
    setSelectedScenarioId(null);
    setOverlay(null);
  };

  const handleReset = () => {
    resetProject(selectedProjectId)
      .then(() => {
        reloadProject();
        notify('Arbeitsstand zurückgesetzt, es gelten wieder die Originaldateien.');
      })
      .catch((e: Error) => notify(e.message, 'error'));
  };

  const showScenario = (scenarioId: number) => {
    setSelectedScenarioId(scenarioId);
    setPage('scenarios');
  };

  const showScenarioInGraph = (scenario: ScenarioDetail) => {
    setOverlay(buildScenarioOverlay(scenario));
    setPage('mapping');
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopBar
        page={page}
        onPageChange={setPage}
        projects={projects}
        projectId={selectedProjectId}
        onProjectChange={selectProject}
        projectModified={project?.modified ?? false}
        onResetProject={handleReset}
        themeMode={themeMode}
        onToggleTheme={onToggleTheme}
      />

      <Box component="main" sx={{ flex: 1, minHeight: 0, p: 1.5, display: 'flex', flexDirection: 'column', gap: 1 }}>
        {error && <Alert severity="error">Backend nicht erreichbar: {error}</Alert>}

        {!project && !error && (
          <Box sx={{ flex: 1, display: 'grid', placeItems: 'center' }}>
            <CircularProgress />
          </Box>
        )}

        {project && (
          <>
            {page === 'overview' && (
              <OverviewPage key={project.id} project={project} onOpenPage={setPage} onOpenScenario={showScenario} />
            )}

            {page === 'mapping' && <ImportWarnings warnings={project.warnings} />}

            {/* Stays mounted on the other pages, so the selection is kept.
                The key resets selection and filters when another project is chosen. */}
            <Box sx={{ flex: 1, minHeight: 0, display: page === 'mapping' ? 'block' : 'none' }}>
              <MappingView
                key={project.id}
                project={project}
                overlay={overlay}
                onClearOverlay={() => setOverlay(null)}
                onScenarioCreated={showScenario}
              />
            </Box>

            {page === 'scenarios' && (
              <Box sx={{ flex: 1, minHeight: 0 }}>
                <ScenariosPage
                  key={project.id}
                  project={project}
                  selectedScenarioId={selectedScenarioId}
                  onSelectScenario={setSelectedScenarioId}
                  onShowInGraph={showScenarioInGraph}
                  onProjectChanged={reloadProject}
                />
              </Box>
            )}
          </>
        )}
      </Box>
    </Box>
  );
}
