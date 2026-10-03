import { useCallback, useEffect, useState } from 'react';
import { Alert, Box, Button, List, ListItemButton, ListItemText, Paper, Stack, Typography } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined';
import { fetchScenarios } from '../api';
import type { Project, ScenarioDetail, ScenarioSummary } from '../types';
import ScenarioView from './ScenarioView';
import CreateScenarioDialog from './CreateScenarioDialog';
import { CHANGE_TYPE_LABELS, ScenarioStatusChip } from './scenarioLabels';

interface ScenariosPageProps {
  project: Project;
  selectedScenarioId: number | null;
  onSelectScenario: (scenarioId: number | null) => void;
  onShowInGraph: (scenario: ScenarioDetail) => void;
  onProjectChanged: () => void; // a scenario was applied, the project must be read again
}

export default function ScenariosPage({
  project,
  selectedScenarioId,
  onSelectScenario,
  onShowInGraph,
  onProjectChanged,
}: ScenariosPageProps) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const reloadList = useCallback(() => {
    fetchScenarios(project.id)
      .then(setScenarios)
      .catch((e: Error) => setError(e.message));
    // depends on project, not only project.id: applying or resetting changes the list
  }, [project]);

  useEffect(reloadList, [reloadList]);

  return (
    <Paper variant="outlined" sx={{ height: '100%', display: 'flex', overflow: 'hidden' }}>
      <Box
        sx={{
          width: 320,
          flexShrink: 0,
          borderRight: 1,
          borderColor: 'divider',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between', p: 2 }}>
          <Typography variant="h6">Szenarien</Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>
            Neu
          </Button>
        </Stack>

        {error && (
          <Alert severity="error" sx={{ mx: 2 }}>
            {error}
          </Alert>
        )}

        <List sx={{ flex: 1, overflow: 'auto', px: 1 }}>
          {scenarios.map((scenario) => (
            <ListItemButton
              key={scenario.id}
              selected={scenario.id === selectedScenarioId}
              onClick={() => onSelectScenario(scenario.id)}
              sx={{ borderRadius: 1.5, mb: 0.5, alignItems: 'flex-start' }}
            >
              <ListItemText
                primary={scenario.title}
                secondary={
                  <Stack component="span" spacing={0.5} sx={{ mt: 0.5, alignItems: 'flex-start' }}>
                    <ScenarioStatusChip status={scenario.status} />
                    <span>
                      {CHANGE_TYPE_LABELS[scenario.changeType]} · {scenario.analysedCount}/{scenario.candidateCount}{' '}
                      analysiert
                      {scenario.openCount > 0 && ` · ${scenario.openCount} offen`}
                    </span>
                  </Stack>
                }
                slotProps={{ secondary: { component: 'span' } }}
              />
            </ListItemButton>
          ))}
          {scenarios.length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
              Tipp: Szenarien lassen sich auch direkt aus der Zuordnungsansicht anlegen.
            </Typography>
          )}
        </List>
      </Box>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        {selectedScenarioId === null ? (
          <EmptyState
            title={scenarios.length === 0 ? 'Noch keine Szenarien' : 'Kein Szenario ausgewählt'}
            text={
              scenarios.length === 0
                ? 'Lege ein Szenario an, um die Auswirkungen einer Änderung analysieren zu lassen.'
                : 'Wähle links ein Szenario aus oder lege ein neues an.'
            }
            onCreate={() => setDialogOpen(true)}
          />
        ) : (
          <ScenarioView
            key={selectedScenarioId}
            project={project}
            scenarioId={selectedScenarioId}
            onChanged={reloadList}
            onShowInGraph={onShowInGraph}
            onApplied={onProjectChanged}
            onDeleted={() => {
              onSelectScenario(null);
              reloadList();
            }}
          />
        )}
      </Box>

      {dialogOpen && (
        <CreateScenarioDialog
          project={project}
          onClose={() => setDialogOpen(false)}
          onCreated={(scenario) => {
            setDialogOpen(false);
            reloadList();
            onSelectScenario(scenario.id);
          }}
        />
      )}
    </Paper>
  );
}

function EmptyState({ title, text, onCreate }: { title: string; text: string; onCreate: () => void }) {
  return (
    <Stack
      spacing={1.5}
      sx={{ height: '100%', alignItems: 'center', justifyContent: 'center', textAlign: 'center', p: 4 }}
    >
      <ScienceOutlinedIcon sx={{ fontSize: 56, color: 'text.disabled' }} />
      <Typography variant="h6">{title}</Typography>
      <Typography color="text.secondary" sx={{ maxWidth: 360 }}>
        {text}
      </Typography>
      <Button variant="contained" startIcon={<AddIcon />} onClick={onCreate}>
        Neues Szenario
      </Button>
    </Stack>
  );
}
