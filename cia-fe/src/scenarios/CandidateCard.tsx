import { useState } from 'react';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Stack,
  Typography,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RefreshIcon from '@mui/icons-material/Refresh';
import type { Analysis, Candidate, Decision, Project, ScenarioDetail } from '../types';
import { artifactColors } from '../theme';
import { useCaseLabel } from '../mapping/mappingModel';
import { SectionTitle } from '../detail/DetailParts';
import ProposalItem, { isActionable } from './ProposalItem';
import CollapsibleSection from './CollapsibleSection';

interface CandidateCardProps {
  project: Project;
  scenario: ScenarioDetail;
  candidate: Candidate;
  onDecide: (proposalId: number, decision: Decision) => void;
  onReanalyze: (artifactId: string) => void;
}

// One candidate of a scenario: a class (use case changed) or a use case (code changed).
export default function CandidateCard({ project, scenario, candidate, onDecide, onReanalyze }: CandidateCardProps) {
  const analysis = candidate.analysis;
  const isCodeChange = scenario.changeType === 'code';
  // After applying, the scenario is final: no new decisions and no new analyses.
  const readOnly = scenario.appliedAt !== null;

  const useCase = isCodeChange ? project.useCases.find((uc) => uc.id === candidate.artifactId) : undefined;
  const label = useCase ? useCaseLabel(useCase) : candidate.artifactId;

  const actionable = analysis?.proposals.filter(isActionable) ?? [];
  const unclear = analysis?.proposals.filter((proposal) => proposal.assessment === 'unclear') ?? [];
  const noChange =
    analysis?.proposals.filter((p) => p.assessment === 'no_change' || p.assessment === 'no_deviation') ?? [];
  const openCount = readOnly
    ? 0
    : [...actionable, ...unclear].filter((proposal) => proposal.decision === 'open').length;
  const isBusy = analysis?.status === 'pending' || analysis?.status === 'running';

  // Cards with something to decide start open, the others closed.
  const [expandedByUser, setExpandedByUser] = useState<boolean | null>(null);
  const expanded = expandedByUser ?? (openCount > 0 || analysis?.status === 'failed');

  return (
    <Accordion
      disableGutters
      variant="outlined"
      expanded={expanded}
      onChange={(_event, isExpanded) => setExpandedByUser(isExpanded)}
      sx={{ '&:before': { display: 'none' }, borderRadius: 1.5 }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" sx={{ alignItems: 'center', gap: 1.5, flex: 1, flexWrap: 'wrap', pr: 1 }}>
          <Box
            sx={{
              width: 4,
              height: 22,
              borderRadius: 1,
              bgcolor: isCodeChange ? artifactColors.useCase : artifactColors.javaClass,
            }}
          />
          <Typography sx={{ fontWeight: 600 }}>{label}</Typography>
          <AnalysisStatusChip analysis={analysis} />
          {analysis?.status === 'done' && <ResultSummary isCodeChange={isCodeChange} analysis={analysis} />}
          {openCount > 0 && (
            <Typography variant="body2" color="text.secondary">
              · {openCount} offen
            </Typography>
          )}
          {analysis?.statusMessage && (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              {analysis.statusMessage}
            </Typography>
          )}
        </Stack>
      </AccordionSummary>

      <AccordionDetails sx={{ pt: 0 }}>
        {!analysis && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Noch nicht analysiert.
          </Typography>
        )}

        {analysis?.status === 'failed' && (
          <Alert
            severity="error"
            sx={{ mt: 1 }}
            action={
              <Button
                color="inherit"
                startIcon={<RefreshIcon />}
                disabled={readOnly}
                onClick={() => onReanalyze(candidate.artifactId)}
              >
                Erneut
              </Button>
            }
          >
            Analyse fehlgeschlagen, der Kandidat bleibt offen: {analysis.error}
          </Alert>
        )}

        {analysis?.status === 'done' && (
          <Stack spacing={1.5} sx={{ mt: 1 }}>
            {analysis.classNote && <Alert severity="info">Hinweis auf Klassenebene: {analysis.classNote}</Alert>}
            {!isCodeChange && actionable.length === 0 && unclear.length > 0 && (
              <Typography variant="body2">
                Das Modell konnte {unclear.length} Methode{unclear.length === 1 ? '' : 'n'} im gegebenen Kontext nicht
                beurteilen. Diese Fälle bleiben offen, bis sie als geprüft markiert sind.
              </Typography>
            )}
            {!isCodeChange && actionable.length === 0 && unclear.length === 0 && (
              <Typography variant="body2">
                Das Modell schlägt für diese Klasse keine Änderung vor. Das ist ein Prüfergebnis im gegebenen Kontext,
                keine Garantie fehlender Auswirkungen.
              </Typography>
            )}
            {/* Everything the user has to decide comes first and stays visible. */}
            {[...actionable, ...unclear].map((proposal) => (
              <ProposalItem
                key={proposal.id}
                proposal={proposal}
                isCodeChange={isCodeChange}
                readOnly={readOnly}
                onDecide={(decision) => onDecide(proposal.id, decision)}
              />
            ))}

            {noChange.length > 0 && (
              <CollapsibleSection
                title={
                  isCodeChange ? 'Keine Abweichung erkennbar – Begründung' : `Ohne Änderungsbedarf (${noChange.length})`
                }
              >
                <Stack spacing={0.75}>
                  {noChange.map((proposal) => (
                    <Typography key={proposal.id} variant="body2">
                      {!isCodeChange && (
                        <Box component="span" sx={{ fontFamily: 'monospace', fontWeight: 700 }}>
                          {proposal.target}:{' '}
                        </Box>
                      )}
                      {proposal.reason || '–'}
                    </Typography>
                  ))}
                  {!isCodeChange && (
                    <Typography variant="caption" color="text.secondary">
                      Kein Änderungsbedarf im gegebenen Kontext, keine Garantie fehlender Auswirkungen. Nicht genannte
                      Methoden und Felder hat das Modell nicht beurteilt.
                    </Typography>
                  )}
                </Stack>
              </CollapsibleSection>
            )}
          </Stack>
        )}

        {!isCodeChange && (
          <Box sx={{ mt: 1.5 }}>
            <ClassContext project={project} scenario={scenario} classId={candidate.artifactId} analysis={analysis} />
          </Box>
        )}

        {analysis && !isBusy && (
          <Box sx={{ mt: 1.5 }}>
            <CollapsibleSection title="Protokoll: Prompt und Antwort des Modells">
              <AnalysisLog analysis={analysis} />
            </CollapsibleSection>
          </Box>
        )}

        {analysis?.status === 'done' && !readOnly && (
          <Button startIcon={<RefreshIcon />} sx={{ mt: 1.5 }} onClick={() => onReanalyze(candidate.artifactId)}>
            Neu analysieren
          </Button>
        )}
      </AccordionDetails>
    </Accordion>
  );
}

function ResultSummary({ isCodeChange, analysis }: { isCodeChange: boolean; analysis: Analysis }) {
  const count = (assessment: string) => analysis.proposals.filter((p) => p.assessment === assessment).length;
  let text: string;

  if (isCodeChange) {
    if (count('deviation') > 0) text = 'mögliche Abweichung';
    else if (count('unclear') > 0) text = 'nicht beurteilbar';
    else text = 'keine Abweichung erkennbar';
  } else {
    const changes = analysis.proposals.filter(isActionable).length;
    text = `${changes} Änderungsvorschl${changes === 1 ? 'ag' : 'äge'}`;
    if (count('unclear') > 0) text += ` · ${count('unclear')} nicht beurteilbar`;
  }

  return (
    <Typography variant="body2" color="text.secondary">
      {text}
    </Typography>
  );
}

interface ClassContextProps {
  project: Project;
  scenario: ScenarioDetail;
  classId: string;
  analysis: Analysis | null;
}

// What the model got as context for a class: the use cases that stay valid and
// the usages of the class in other classes.
function ClassContext({ project, scenario, classId, analysis }: ClassContextProps) {
  const otherUseCases = project.links
    .filter((link) => link.classId === classId && link.useCaseId !== scenario.useCaseId)
    .map((link) => project.useCases.find((uc) => uc.id === link.useCaseId))
    .filter((useCase) => useCase !== undefined);
  const callSites = analysis && analysis.status !== 'pending' ? analysis.callSites : null;

  const title =
    `Kontext für das Modell: ${otherUseCases.length} weiterhin gültige Use Cases` +
    (callSites ? ` · ${callSites.length} Verwendungen in anderen Klassen` : '');

  return (
    <CollapsibleSection title={title}>
      <SectionTitle>Weiterhin gültige Use Cases dieser Klasse</SectionTitle>
      <Typography variant="body2">
        {otherUseCases.length > 0
          ? otherUseCases.map(useCaseLabel).join(' · ')
          : 'Keine weiteren deklarierten Zuordnungen. Das schließt andere Verwendungen nicht aus.'}
      </Typography>

      {callSites && (
        <>
          <SectionTitle>Verwendungen in anderen Klassen (Textsuche)</SectionTitle>
          {callSites.length === 0 ? (
            <Typography variant="body2">
              Keine Fundstellen in den importierten Klassen. Das belegt nicht, dass es keine weiteren Verwendungen gibt.
            </Typography>
          ) : (
            <Box component="ul" sx={{ m: 0, pl: 2.5, fontSize: 12 }}>
              {callSites.map((site) => (
                <li key={`${site.classId}:${site.lineNumber}`}>
                  <b>{site.classId}</b>
                  {site.methodSignature && <> · {site.methodSignature}</>} · Zeile {site.lineNumber}:{' '}
                  <Box component="code" sx={{ fontSize: 11.5 }}>
                    {site.line}
                  </Box>
                </li>
              ))}
            </Box>
          )}
        </>
      )}
    </CollapsibleSection>
  );
}

function AnalysisStatusChip({ analysis }: { analysis: Analysis | null }) {
  const status = analysis?.status;
  if (!status) return <Chip variant="outlined" label="nicht analysiert" />;
  if (status === 'pending') return <Chip variant="outlined" label="wartet" />;
  if (status === 'running') {
    return <Chip color="primary" icon={<CircularProgress size={12} color="inherit" />} label="läuft" />;
  }
  if (status === 'failed') return <Chip color="error" label="fehlgeschlagen" />;
  return <Chip color="success" variant="outlined" label="analysiert" />;
}

// Everything that went into and came out of the model call.
function AnalysisLog({ analysis }: { analysis: Analysis }) {
  return (
    <Box>
      <Typography variant="body2" color="text.secondary">
        Modell: {analysis.model || '–'} · Prompt-Version: {analysis.promptVersion || '–'} · gestartet:{' '}
        {analysis.startedAt ?? '–'} · beendet: {analysis.finishedAt ?? '–'}
      </Typography>
      <LogText title="Prompt" text={analysis.prompt} />
      <LogText title="Antwort des Modells" text={analysis.rawAnswer} />
      <LogText title="Reasoning des Modells" text={analysis.reasoning} />
    </Box>
  );
}

function LogText({ title, text }: { title: string; text: string }) {
  if (!text) return null;
  return (
    <Box sx={{ mt: 1.5 }}>
      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
        {title}
      </Typography>
      <Box
        component="pre"
        sx={{
          m: 0,
          p: 1,
          maxHeight: 300,
          overflow: 'auto',
          fontSize: 12,
          whiteSpace: 'pre-wrap',
          bgcolor: 'action.hover',
          borderRadius: 1,
        }}
      >
        {text}
      </Box>
    </Box>
  );
}
