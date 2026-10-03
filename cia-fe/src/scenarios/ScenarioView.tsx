import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  LinearProgress,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined';
import DoneAllIcon from '@mui/icons-material/DoneAll';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import {
  acceptAllChanges,
  applyScenario,
  deleteScenario,
  fetchScenario,
  setDecision,
  startAnalysis,
  startCandidateAnalysis,
} from '../api';
import type { Decision, Project, ScenarioDetail } from '../types';
import CandidateCard from './CandidateCard';
import SideBySideDiff from './SideBySideDiff';
import { CHANGE_TYPE_LABELS, ScenarioStatusChip } from './scenarioLabels';
import { SectionTitle } from '../detail/DetailParts';
import { isActionable } from './ProposalItem';
import ConfirmDialog from '../components/ConfirmDialog';
import { useNotify } from '../components/Notifications';

// The model can take minutes, so the scenario is reloaded regularly while it runs.
const POLL_INTERVAL_MS = 3000;

interface ScenarioViewProps {
  project: Project;
  scenarioId: number;
  onChanged: () => void; // status or counts may have changed, the list should reload
  onDeleted: () => void;
  onShowInGraph: (scenario: ScenarioDetail) => void;
  onApplied: () => void; // the working copy changed, the project must be reloaded
}

export default function ScenarioView({
  project,
  scenarioId,
  onChanged,
  onDeleted,
  onShowInGraph,
  onApplied,
}: ScenarioViewProps) {
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<'apply' | 'delete' | null>(null);
  const notify = useNotify();

  const reload = useCallback(() => {
    fetchScenario(scenarioId)
      .then((result) => {
        setScenario(result);
        setError(null);
      })
      .catch((e: Error) => setError(e.message));
  }, [scenarioId]);

  // Also reload when the project was reloaded, e.g. after a reset.
  useEffect(reload, [reload, project]);

  const isRunning = scenario?.status === 'running';
  useEffect(() => {
    if (!isRunning) return;
    const timer = setInterval(reload, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [isRunning, reload]);

  const listState = scenario ? `${scenario.status}|${scenario.analysedCount}|${scenario.openCount}` : '';
  useEffect(() => {
    if (listState) onChanged();
  }, [listState, onChanged]);

  const runAction = (action: Promise<unknown>) => action.then(reload).catch((e: Error) => setError(e.message));

  const handleDecide = (proposalId: number, decision: Decision) => runAction(setDecision(proposalId, decision));

  const handleAcceptAll = () => {
    acceptAllChanges(scenarioId)
      .then(({ accepted }) => {
        reload();
        notify(`${accepted} Änderungsvorschl${accepted === 1 ? 'ag' : 'äge'} angenommen`);
      })
      .catch((e: Error) => setError(e.message));
  };

  const handleApply = () => {
    applyScenario(scenarioId)
      .then(() => {
        reload();
        onApplied();
        notify('In den Arbeitsstand übernommen. Neue Szenarien bauen darauf auf.');
      })
      .catch((e: Error) => setError(e.message));
  };

  const handleDelete = () => {
    deleteScenario(scenarioId)
      .then(() => {
        onDeleted();
        notify('Szenario gelöscht');
      })
      .catch((e: Error) => setError(e.message));
  };

  if (!scenario) {
    return error ? <Alert severity="error">{error}</Alert> : <CircularProgress sx={{ m: 4 }} />;
  }

  const isCodeChange = scenario.changeType === 'code';
  const statuses = scenario.candidates.map((candidate) => candidate.analysis?.status);
  const missing = statuses.filter((status) => status === undefined || status === 'failed').length;
  const finished = statuses.filter((status) => status === 'done' || status === 'failed').length;

  const acceptable = scenario.candidates
    .flatMap((candidate) => candidate.analysis?.proposals ?? [])
    .filter((proposal) => isActionable(proposal) && proposal.decision === 'open' && !proposal.referenceProblem).length;

  let analyzeLabel = 'Offene Kandidaten analysieren';
  if (isRunning) analyzeLabel = 'Analyse läuft';
  else if (scenario.status === 'created') analyzeLabel = 'Analyse starten';

  return (
    <Box sx={{ height: '100%', overflow: 'auto', p: 2.5 }}>
      <Stack direction="row" sx={{ alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          {scenario.title}
        </Typography>
        <Chip label={CHANGE_TYPE_LABELS[scenario.changeType]} />
        <ScenarioStatusChip status={scenario.status} />
        <Box sx={{ flex: 1 }} />
        {!scenario.appliedAt && (
          <Tooltip title="Schreibt die Änderung und alle angenommenen Vorschläge in den Arbeitsstand. Die Originaldateien bleiben unverändert.">
            <span>
              <Button
                variant="contained"
                color="success"
                startIcon={<DoneAllIcon />}
                disabled={isRunning || scenario.status === 'created'}
                onClick={() => setConfirm('apply')}
              >
                In Arbeitsstand übernehmen
              </Button>
            </span>
          </Tooltip>
        )}
        <Button startIcon={<AccountTreeOutlinedIcon />} onClick={() => onShowInGraph(scenario)}>
          Im Graph anzeigen
        </Button>
        <Tooltip title="Szenario löschen">
          <IconButton onClick={() => setConfirm('delete')}>
            <DeleteOutlineIcon />
          </IconButton>
        </Tooltip>
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
        {isCodeChange ? `Klasse ${scenario.classId}` : `Use Case ${scenario.useCaseId}`} · angelegt{' '}
        {scenario.createdAt.replace('T', ' ')}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {scenario.appliedAt && (
        <Alert severity="success" variant="outlined" sx={{ mt: 2 }}>
          Am {scenario.appliedAt.replace('T', ' ')} in den Arbeitsstand übernommen. Die Entscheidungen sind damit
          abgeschlossen; für weitere Änderungen ein neues Szenario anlegen.
        </Alert>
      )}

      <SectionTitle>Änderungsauftrag</SectionTitle>
      {isCodeChange ? (
        <SideBySideDiff
          before={scenario.originalCode}
          after={scenario.newCode}
          beforeLabel={`Bisheriger Code${scenario.methodSignature ? ` · ${scenario.methodSignature}` : ''}`}
          afterLabel="Geänderter Code"
        />
      ) : scenario.changeType === 'deactivate' ? (
        <Alert severity="info" variant="outlined">
          {scenario.useCaseId} entfällt künftig. Der bisherige Text und die Trace-Links bleiben für die Analyse
          verfügbar.
        </Alert>
      ) : (
        <SideBySideDiff
          before={scenario.originalText}
          after={scenario.newText}
          beforeLabel={scenario.changeType === 'add' ? 'Bisher (Use Case existiert nicht)' : 'Bisheriger Text'}
          afterLabel="Neuer Text"
          monospace={false}
        />
      )}

      <Stack direction="row" sx={{ alignItems: 'center', gap: 2, mt: 3, mb: 1 }}>
        <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 700 }}>
          {isCodeChange ? 'Kandidaten-Use-Cases' : 'Kandidatenklassen'} ({scenario.candidateCount})
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {scenario.changeType === 'add'
            ? 'manuell zugeordnet'
            : `aus den Trace-Links von ${isCodeChange ? scenario.classId : scenario.useCaseId}`}
        </Typography>
        <Box sx={{ flex: 1 }} />
        {acceptable > 0 && !scenario.appliedAt && (
          <Button variant="outlined" color="success" startIcon={<CheckCircleOutlineIcon />} onClick={handleAcceptAll}>
            Alle Änderungsvorschläge annehmen ({acceptable})
          </Button>
        )}
        <Button
          variant="contained"
          startIcon={isRunning ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}
          disabled={isRunning || missing === 0 || scenario.appliedAt !== null}
          onClick={() => runAction(startAnalysis(scenario.id))}
        >
          {analyzeLabel}
        </Button>
      </Stack>

      {scenario.status !== 'created' && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress
            variant={isRunning && finished === 0 ? 'indeterminate' : 'determinate'}
            value={(finished / Math.max(scenario.candidateCount, 1)) * 100}
          />
          <Typography variant="caption" color="text.secondary">
            {finished} von {scenario.candidateCount} Kandidaten bearbeitet
            {isRunning && ' · das Modell ist langsam, die Ergebnisse erscheinen nach und nach'}
          </Typography>
        </Box>
      )}

      {scenario.candidates.length === 0 && (
        <Alert severity="warning">
          Keine Zuordnung für die Analyse vorhanden. Das bedeutet nicht, dass die Änderung wirkungslos ist.
        </Alert>
      )}

      <Stack spacing={1}>
        {scenario.candidates.map((candidate) => (
          <CandidateCard
            key={candidate.artifactId}
            project={project}
            scenario={scenario}
            candidate={candidate}
            onDecide={handleDecide}
            onReanalyze={(artifactId) => runAction(startCandidateAnalysis(scenario.id, artifactId))}
          />
        ))}
      </Stack>

      <ConfirmDialog
        open={confirm === 'apply'}
        title="In den Arbeitsstand übernehmen?"
        confirmLabel="Übernehmen"
        color="success"
        onConfirm={handleApply}
        onClose={() => setConfirm(null)}
      >
        Die Änderung und alle angenommenen Vorschläge werden in den Arbeitsstand geschrieben; neue Szenarien bauen
        darauf auf. Danach sind die Entscheidungen abgeschlossen.
        {scenario.openCount > 0 && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Noch {scenario.openCount} offene Punkte. Nicht angenommene Vorschläge werden nicht übernommen.
          </Alert>
        )}
      </ConfirmDialog>

      <ConfirmDialog
        open={confirm === 'delete'}
        title="Szenario löschen?"
        confirmLabel="Löschen"
        color="error"
        onConfirm={handleDelete}
        onClose={() => setConfirm(null)}
      >
        „{scenario.title}“ wird mit allen Analyseergebnissen und Entscheidungen gelöscht.
      </ConfirmDialog>
    </Box>
  );
}
