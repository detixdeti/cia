import { useState } from 'react';
import { Box, Button, Chip, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EditNoteIcon from '@mui/icons-material/EditNote';
import BlockIcon from '@mui/icons-material/Block';
import type { ChangeType, Project } from '../types';
import { artifactColors } from '../theme';
import { classKey, parseKey } from '../mapping/mappingModel';
import CreateScenarioDialog from '../scenarios/CreateScenarioDialog';
import ClassDetail from './ClassDetail';
import { LinkedList, SectionTitle } from './DetailParts';

interface DetailPanelProps {
  project: Project;
  detailKey: string;
  onNavigate: (key: string) => void;
  onClose: () => void;
  onScenarioCreated: (scenarioId: number) => void;
}

// Shows the selected use case or class next to the graph / matrix.
export default function DetailPanel({ project, detailKey, onNavigate, onClose, onScenarioCreated }: DetailPanelProps) {
  const { kind, id } = parseKey(detailKey);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Stack direction="row" sx={{ alignItems: 'center', gap: 1, px: 2, pt: 1.5, pb: 1 }}>
        <Chip
          label={kind === 'useCase' ? 'Use Case' : 'Klasse'}
          sx={{ bgcolor: kind === 'useCase' ? artifactColors.useCase : artifactColors.javaClass, color: '#fff' }}
        />
        <Typography variant="subtitle1" noWrap sx={{ fontWeight: 700, flex: 1 }} title={id}>
          {id}
        </Typography>
        <Tooltip title="Schließen">
          <IconButton onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Stack>

      <Box sx={{ flex: 1, minHeight: 0 }}>
        {kind === 'useCase' ? (
          <UseCaseDetail
            project={project}
            useCaseId={id}
            onNavigate={onNavigate}
            onScenarioCreated={onScenarioCreated}
          />
        ) : (
          // key: reload when another class is shown
          <ClassDetail
            key={id}
            project={project}
            classId={id}
            onNavigate={onNavigate}
            onScenarioCreated={onScenarioCreated}
          />
        )}
      </Box>
    </Box>
  );
}

interface UseCaseDetailProps {
  project: Project;
  useCaseId: string;
  onNavigate: (key: string) => void;
  onScenarioCreated: (scenarioId: number) => void;
}

function UseCaseDetail({ project, useCaseId, onNavigate, onScenarioCreated }: UseCaseDetailProps) {
  // Which kind of scenario the dialog should start with; null = dialog closed.
  const [dialogChangeType, setDialogChangeType] = useState<ChangeType | null>(null);

  const useCase = project.useCases.find((uc) => uc.id === useCaseId);
  if (!useCase) return null;

  const linkedClasses = project.links
    .filter((link) => link.useCaseId === useCaseId)
    .map((link) => ({ key: classKey(link.classId), label: link.classId }));

  return (
    <Box sx={{ height: '100%', overflow: 'auto', px: 2, pb: 2 }}>
      {useCase.title && (
        <Typography variant="h6" sx={{ mb: 1.5 }}>
          {useCase.title}
        </Typography>
      )}

      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <Button variant="outlined" startIcon={<EditNoteIcon />} onClick={() => setDialogChangeType('modify')}>
          Ändern …
        </Button>
        <Button variant="outlined" startIcon={<BlockIcon />} onClick={() => setDialogChangeType('deactivate')}>
          Deaktivieren …
        </Button>
      </Stack>

      <Typography variant="body2" component="div" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
        {useCase.text}
      </Typography>

      <SectionTitle>Zugeordnete Klassen ({linkedClasses.length})</SectionTitle>
      <LinkedList
        items={linkedClasses}
        emptyText="Keine deklarierte Zuordnung (keine Entwarnung)."
        onNavigate={onNavigate}
      />

      {dialogChangeType && (
        <CreateScenarioDialog
          project={project}
          initialChangeType={dialogChangeType}
          initialUseCaseId={useCaseId}
          onClose={() => setDialogChangeType(null)}
          onCreated={(scenario) => {
            setDialogChangeType(null);
            onScenarioCreated(scenario.id);
          }}
        />
      )}
    </Box>
  );
}
