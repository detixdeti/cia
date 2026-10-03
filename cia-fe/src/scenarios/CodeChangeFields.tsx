import { useEffect, useState } from 'react';
import { Alert, Autocomplete, Box, Chip, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { fetchClass } from '../api';
import type { JavaClassDetail, Project } from '../types';

interface CodeChangeFieldsProps {
  project: Project;
  classId: string;
  methodSignature: string; // '' = the whole class
  newCode: string;
  onClassChange: (classId: string) => void;
  onMethodChange: (methodSignature: string) => void;
  onNewCodeChange: (code: string) => void;
}

// Form part for a code change: pick a class (and optionally a method), see its
// current code and enter the changed version. There is no Git connection.
export default function CodeChangeFields({
  project,
  classId,
  methodSignature,
  newCode,
  onClassChange,
  onMethodChange,
  onNewCodeChange,
}: CodeChangeFieldsProps) {
  const [detail, setDetail] = useState<JavaClassDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDetail(null);
    if (!classId) return;
    let cancelled = false;
    fetchClass(project.id, classId)
      .then((result) => !cancelled && setDetail(result))
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [project.id, classId]);

  const originalCode = detail ? codeOf(detail, methodSignature) : '';

  // The changed code starts as a copy of the current code whenever another class or method
  // is chosen. onNewCodeChange is left out of the dependencies, it is a new function on every render.
  useEffect(() => {
    if (detail) onNewCodeChange(codeOf(detail, methodSignature));
  }, [detail, methodSignature]);

  const linkedUseCaseIds = project.links.filter((link) => link.classId === classId).map((link) => link.useCaseId);

  return (
    <>
      <Autocomplete
        options={project.classes.map((cls) => cls.id)}
        value={classId || null}
        onChange={(_event, value) => {
          onClassChange(value ?? '');
          onMethodChange('');
        }}
        renderInput={(params) => <TextField {...params} label="Klasse" />}
      />

      {detail && (
        <TextField
          select
          label="Geänderter Teil"
          value={methodSignature}
          onChange={(e) => onMethodChange(e.target.value)}
        >
          <MenuItem value="">Ganze Klasse</MenuItem>
          {detail.methods.map((method) => (
            <MenuItem key={method.signature} value={method.signature} sx={{ fontFamily: 'monospace', fontSize: 13 }}>
              {method.signature}
            </MenuItem>
          ))}
        </TextField>
      )}

      {error && <Alert severity="error">{error}</Alert>}

      {detail && (
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
          <TextField
            label="Bisheriger Code"
            multiline
            minRows={10}
            maxRows={20}
            value={originalCode}
            slotProps={{ input: { readOnly: true, sx: codeFont } }}
            sx={{ flex: 1 }}
          />
          <TextField
            label="Geänderter Code"
            multiline
            minRows={10}
            maxRows={20}
            value={newCode}
            onChange={(event) => onNewCodeChange(event.target.value)}
            slotProps={{ input: { sx: codeFont } }}
            sx={{ flex: 1 }}
          />
        </Stack>
      )}

      {classId && (
        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.75 }}>
            Kandidaten-Use-Cases aus den Trace-Links ({linkedUseCaseIds.length}):
          </Typography>
          <Stack direction="row" useFlexGap sx={{ gap: 0.75, flexWrap: 'wrap' }}>
            {linkedUseCaseIds.map((useCaseId) => (
              <Chip key={useCaseId} label={useCaseId} />
            ))}
            {linkedUseCaseIds.length === 0 && (
              <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                keine – die Klasse ist keinem Use Case zugeordnet
              </Typography>
            )}
          </Stack>
        </Box>
      )}
    </>
  );
}

const codeFont = { fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace', fontSize: 12.5 };

function codeOf(detail: JavaClassDetail, methodSignature: string) {
  const method = detail.methods.find((m) => m.signature === methodSignature);
  if (!method) return detail.source;
  return detail.source
    .split('\n')
    .slice(method.startLine - 1, method.endLine)
    .join('\n');
}
