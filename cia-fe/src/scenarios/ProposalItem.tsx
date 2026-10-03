import { Alert, Box, Button, Chip, Stack, Typography } from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import type { Assessment, Decision, Proposal } from '../types';
import SideBySideDiff from './SideBySideDiff';

export const ASSESSMENT_LABELS: Record<Assessment, string> = {
  modify: 'Änderung vorgeschlagen',
  remove: 'Entfernung vorgeschlagen',
  add: 'Neue Methode vorgeschlagen',
  no_change: 'Im Kontext kein Änderungsbedarf erkennbar',
  deviation: 'Mögliche Abweichung vom Use Case',
  no_deviation: 'Im Kontext keine Abweichung erkennbar',
  unclear: 'Nicht ausreichend beurteilbar',
};

const ASSESSMENT_COLORS: Record<Assessment, 'warning' | 'error' | 'info' | 'default' | 'secondary'> = {
  modify: 'warning',
  remove: 'error',
  add: 'info',
  no_change: 'default',
  deviation: 'warning',
  no_deviation: 'default',
  unclear: 'secondary',
};

// Proposals with a concrete change the user can accept or reject.
export function isActionable(proposal: Proposal) {
  return ['modify', 'remove', 'add', 'deviation'].includes(proposal.assessment);
}

interface ProposalItemProps {
  proposal: Proposal;
  isCodeChange: boolean; // true: the proposal is a new use case text, false: new method code
  readOnly: boolean; // the scenario was applied, decisions are final
  onDecide: (decision: Decision) => void;
}

export default function ProposalItem({ proposal, isCodeChange, readOnly, onDecide }: ProposalItemProps) {
  const actionable = isActionable(proposal);

  // Clicking the active decision again resets it to "open".
  const toggle = (decision: Decision) => onDecide(proposal.decision === decision ? 'open' : decision);

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 1.5, p: 1.5 }}>
      <Stack direction="row" sx={{ alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        {!isCodeChange && (
          <Typography sx={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 14, wordBreak: 'break-all' }}>
            {proposal.target || '(ohne Signatur)'}
          </Typography>
        )}
        <Chip color={ASSESSMENT_COLORS[proposal.assessment]} label={ASSESSMENT_LABELS[proposal.assessment]} />
        {readOnly && proposal.decision === 'open' && isActionable(proposal) && (
          <Chip variant="outlined" label="nicht übernommen" />
        )}
        {proposal.decision !== 'open' && (
          <Chip
            variant="outlined"
            color={proposal.decision === 'accepted' ? 'success' : 'default'}
            label={decisionLabel(proposal)}
          />
        )}
      </Stack>

      {proposal.referenceProblem && (
        <Alert severity="warning" sx={{ mt: 1 }}>
          Referenz nicht bestätigt: {proposal.referenceProblem}
        </Alert>
      )}

      <Typography variant="body2" sx={{ mt: 1 }}>
        <Box component="span" sx={{ color: 'text.secondary' }}>
          Begründung des Modells:{' '}
        </Box>
        {proposal.reason || '–'}
      </Typography>

      {proposal.requirementReference && (
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          <Box component="span" sx={{ color: 'text.secondary' }}>
            Anforderungsstelle:{' '}
          </Box>
          <i>„{proposal.requirementReference}“</i>
        </Typography>
      )}

      {actionable && (
        <>
          <Box sx={{ mt: 1.5 }}>
            {isCodeChange ? (
              <SideBySideDiff
                before={proposal.originalCode}
                after={proposal.proposedCode}
                beforeLabel="Bisheriger Use-Case-Text"
                afterLabel="Vorgeschlagener Text (passend zur Codeänderung)"
                monospace={false}
              />
            ) : (
              <SideBySideDiff
                before={proposal.originalCode}
                after={proposal.proposedCode}
                beforeLabel={proposal.assessment === 'add' ? 'Ist (Methode existiert nicht)' : 'Ist'}
                afterLabel={
                  proposal.assessment === 'remove' ? 'Soll (Methode entfernt)' : 'Soll (Vorschlag des Modells)'
                }
              />
            )}
          </Box>

          {isCodeChange && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Zuerst klären: Ist die Codeänderung fachlich gewollt? Wenn nicht, gilt der bisherige Text weiter und der
              Code muss korrigiert werden.
            </Typography>
          )}

          <Stack direction="row" spacing={1} sx={{ mt: 1.5, flexWrap: 'wrap', gap: 1 }}>
            <Button
              variant={proposal.decision === 'accepted' ? 'contained' : 'outlined'}
              color="success"
              startIcon={<CheckIcon />}
              disabled={readOnly}
              onClick={() => toggle('accepted')}
            >
              {isCodeChange ? 'Änderung gewollt – Text übernehmen' : 'Annehmen'}
            </Button>
            <Button
              variant={proposal.decision === 'rejected' ? 'contained' : 'outlined'}
              color="inherit"
              startIcon={<CloseIcon />}
              disabled={readOnly}
              onClick={() => toggle('rejected')}
            >
              {isCodeChange ? 'Nicht gewollt – Code korrigieren' : 'Verwerfen'}
            </Button>
          </Stack>
        </>
      )}

      {proposal.assessment === 'unclear' && (
        // Nothing to accept here: the user documents that they looked at the open case.
        <Button
          sx={{ mt: 1.5 }}
          variant={proposal.decision === 'accepted' ? 'contained' : 'outlined'}
          color="inherit"
          startIcon={<CheckIcon />}
          disabled={readOnly}
          onClick={() => toggle('accepted')}
        >
          Als geprüft markieren
        </Button>
      )}
    </Box>
  );
}

function decisionLabel(proposal: Proposal) {
  if (proposal.assessment === 'unclear') return 'geprüft';
  if (proposal.assessment === 'deviation') {
    return proposal.decision === 'accepted' ? 'Text wird angepasst' : 'Code wird korrigiert';
  }
  return proposal.decision === 'accepted' ? 'angenommen' : 'verworfen';
}
