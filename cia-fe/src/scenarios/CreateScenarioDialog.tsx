import { useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { createScenario } from '../api';
import type { ChangeType, Project, ScenarioCreate, ScenarioDetail } from '../types';
import { useCaseLabel } from '../mapping/mappingModel';
import { CHANGE_TYPE_LABELS } from './scenarioLabels';
import CodeChangeFields from './CodeChangeFields';

const CHANGE_TYPES: ChangeType[] = ['deactivate', 'modify', 'add', 'code'];

interface CreateScenarioDialogProps {
  project: Project;
  initialChangeType?: ChangeType;
  initialUseCaseId?: string;
  initialClassId?: string;
  initialMethodSignature?: string;
  onClose: () => void;
  onCreated: (scenario: ScenarioDetail) => void;
}

// Only mounted while it is open, so every opening starts with a fresh form.
export default function CreateScenarioDialog({
  project,
  initialChangeType = 'modify',
  initialUseCaseId = '',
  initialClassId = '',
  initialMethodSignature = '',
  onClose,
  onCreated,
}: CreateScenarioDialogProps) {
  const [changeType, setChangeType] = useState<ChangeType>(initialChangeType);
  const [title, setTitle] = useState('');
  // existing use case (deactivate, modify)
  const [useCaseId, setUseCaseId] = useState(initialUseCaseId);
  const [newText, setNewText] = useState(() => project.useCases.find((uc) => uc.id === initialUseCaseId)?.text ?? '');
  // new use case (add)
  const [newUseCaseId, setNewUseCaseId] = useState(() => suggestNewUseCaseId(project));
  const [newUseCaseText, setNewUseCaseText] = useState('');
  const [classIds, setClassIds] = useState<string[]>([]);
  // code change
  const [classId, setClassId] = useState(initialClassId);
  const [methodSignature, setMethodSignature] = useState(initialMethodSignature);
  const [newCode, setNewCode] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const selectUseCase = (id: string) => {
    setUseCaseId(id);
    // the new text starts as a copy of the current one
    setNewText(project.useCases.find((uc) => uc.id === id)?.text ?? '');
  };

  const buildRequest = (): ScenarioCreate => {
    if (changeType === 'code') return { changeType, title, classId, methodSignature, newCode };
    if (changeType === 'add')
      return { changeType, title, useCaseId: newUseCaseId.trim(), newText: newUseCaseText, classIds };
    if (changeType === 'modify') return { changeType, title, useCaseId, newText };
    return { changeType, title, useCaseId };
  };

  const handleSubmit = () => {
    setSaving(true);
    setError(null);
    createScenario(project.id, buildRequest())
      .then(onCreated)
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  };

  const canSubmit = changeType === 'code' ? classId !== '' : changeType === 'add' || useCaseId !== '';

  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>Neues Änderungsszenario</DialogTitle>
      <DialogContent>
        <Stack spacing={2.5} sx={{ pt: 1 }}>
          <ToggleButtonGroup
            exclusive
            value={changeType}
            onChange={(_event, value: ChangeType | null) => value && setChangeType(value)}
          >
            {CHANGE_TYPES.map((type) => (
              <ToggleButton key={type} value={type} sx={{ px: 2 }}>
                {CHANGE_TYPE_LABELS[type]}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>

          {(changeType === 'deactivate' || changeType === 'modify') && (
            <ExistingUseCaseFields
              project={project}
              useCaseId={useCaseId}
              newText={changeType === 'modify' ? newText : null}
              onUseCaseChange={selectUseCase}
              onNewTextChange={setNewText}
            />
          )}

          {changeType === 'add' && (
            <>
              <TextField
                label="Kennung des neuen Use Cases"
                value={newUseCaseId}
                onChange={(e) => setNewUseCaseId(e.target.value)}
              />
              <TextField
                label="Text des neuen Use Cases"
                multiline
                minRows={8}
                maxRows={16}
                value={newUseCaseText}
                onChange={(e) => setNewUseCaseText(e.target.value)}
              />
              <Autocomplete
                multiple
                options={project.classes.map((cls) => cls.id)}
                value={classIds}
                onChange={(_event, value) => setClassIds(value)}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Zu untersuchende Klassen"
                    helperText="Für neue Use Cases gibt es keine Trace-Links. Die Auswahl gilt nur in diesem Szenario."
                  />
                )}
              />
            </>
          )}

          {changeType === 'code' && (
            <CodeChangeFields
              project={project}
              classId={classId}
              methodSignature={methodSignature}
              newCode={newCode}
              onClassChange={setClassId}
              onMethodChange={setMethodSignature}
              onNewCodeChange={setNewCode}
            />
          )}

          <TextField
            label="Titel (optional)"
            placeholder="wird sonst automatisch erzeugt"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          {error && <Alert severity="error">{error}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Abbrechen</Button>
        <Button variant="contained" disabled={saving || !canSubmit} onClick={handleSubmit}>
          Szenario anlegen
        </Button>
      </DialogActions>
    </Dialog>
  );
}

interface ExistingUseCaseFieldsProps {
  project: Project;
  useCaseId: string;
  newText: string | null; // null when the use case is deactivated
  onUseCaseChange: (useCaseId: string) => void;
  onNewTextChange: (text: string) => void;
}

function ExistingUseCaseFields({
  project,
  useCaseId,
  newText,
  onUseCaseChange,
  onNewTextChange,
}: ExistingUseCaseFieldsProps) {
  const useCase = project.useCases.find((uc) => uc.id === useCaseId) ?? null;
  const linkedClassIds = project.links.filter((link) => link.useCaseId === useCaseId).map((link) => link.classId);

  return (
    <>
      <Autocomplete
        options={project.useCases}
        value={useCase}
        getOptionLabel={useCaseLabel}
        onChange={(_event, selected) => onUseCaseChange(selected?.id ?? '')}
        renderInput={(params) => <TextField {...params} label="Use Case" />}
      />

      {newText === null && useCase && (
        <Box sx={{ p: 1.5, borderRadius: 1, bgcolor: 'action.hover', maxHeight: 200, overflow: 'auto' }}>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
            {useCase.text}
          </Typography>
        </Box>
      )}

      {newText !== null && (
        <TextField
          label="Neuer Text"
          multiline
          minRows={8}
          maxRows={16}
          value={newText}
          onChange={(e) => onNewTextChange(e.target.value)}
        />
      )}

      {useCase && (
        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.75 }}>
            Kandidatenklassen aus den Trace-Links ({linkedClassIds.length}):
          </Typography>
          <Stack direction="row" useFlexGap sx={{ gap: 0.75, flexWrap: 'wrap' }}>
            {linkedClassIds.map((id) => (
              <Chip key={id} label={id} />
            ))}
            {linkedClassIds.length === 0 && (
              <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                keine – für diesen Use Case ist keine Analyse möglich
              </Typography>
            )}
          </Stack>
        </Box>
      )}
    </>
  );
}

// Next free number, e.g. "UC7" if UC1 to UC6 exist (iTrust ids like "UC40S7" count as 40).
function suggestNewUseCaseId(project: Project) {
  const numbers = project.useCases.map((uc) => Number(/^UC(\d+)/.exec(uc.id)?.[1] ?? 0));
  return `UC${Math.max(0, ...numbers) + 1}`;
}
