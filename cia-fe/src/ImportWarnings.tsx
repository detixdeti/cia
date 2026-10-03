import { useState } from 'react';
import { Alert, Button, Collapse } from '@mui/material';

// Shows problems found while importing the project (duplicate links, unknown ids, ...).
export default function ImportWarnings({ warnings }: { warnings: string[] }) {
  const [open, setOpen] = useState(false);

  if (warnings.length === 0) return null;

  return (
    <Alert
      severity="info"
      action={
        <Button color="inherit" onClick={() => setOpen(!open)}>
          {open ? 'Ausblenden' : 'Anzeigen'}
        </Button>
      }
    >
      {warnings.length} Hinweis{warnings.length > 1 ? 'e' : ''} beim Import
      <Collapse in={open}>
        <ul style={{ margin: '8px 0 0', paddingLeft: 18 }}>
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      </Collapse>
    </Alert>
  );
}
