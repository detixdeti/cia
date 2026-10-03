import { Chip } from '@mui/material';
import type { ChangeType, ScenarioStatus } from '../types';

export const CHANGE_TYPE_LABELS: Record<ChangeType, string> = {
  deactivate: 'Deaktivieren',
  modify: 'Ändern',
  add: 'Neu anlegen',
  code: 'Code ändern',
};

const STATUS_LABELS: Record<ScenarioStatus, string> = {
  created: 'angelegt',
  running: 'Analyse läuft',
  review: 'zur Prüfung bereit',
  completed: 'abgeschlossen',
  applied: 'übernommen',
};

const STATUS_COLORS: Record<ScenarioStatus, 'default' | 'primary' | 'warning' | 'success'> = {
  created: 'default',
  running: 'primary',
  review: 'warning',
  completed: 'success',
  applied: 'success',
};

export function ScenarioStatusChip({ status }: { status: ScenarioStatus }) {
  return (
    <Chip
      variant={status === 'applied' ? 'filled' : 'outlined'}
      color={STATUS_COLORS[status]}
      label={STATUS_LABELS[status]}
    />
  );
}
