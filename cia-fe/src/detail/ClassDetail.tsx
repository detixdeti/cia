import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Tab,
  Tabs,
  Tooltip,
  Typography,
} from '@mui/material';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import { fetchClass } from '../api';
import type { JavaClassDetail, Project } from '../types';
import { useCaseKey, useCaseLabel } from '../mapping/mappingModel';
import { LinkedList, SectionTitle } from './DetailParts';
import SourceCode from './SourceCode';
import CreateScenarioDialog from '../scenarios/CreateScenarioDialog';

interface ClassDetailProps {
  project: Project;
  classId: string;
  onNavigate: (key: string) => void;
  onScenarioCreated: (scenarioId: number) => void;
}

type TabName = 'overview' | 'source';

export default function ClassDetail({ project, classId, onNavigate, onScenarioCreated }: ClassDetailProps) {
  const [detail, setDetail] = useState<JavaClassDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabName>('overview');
  // Lines highlighted in the source tab (a method or a field)
  const [highlight, setHighlight] = useState<{ from: number; to: number } | null>(null);
  // Method to start a code change scenario with: '' = whole class, null = dialog closed
  const [changeMethod, setChangeMethod] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchClass(project.id, classId)
      .then((result) => !cancelled && setDetail(result))
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
    // depends on project, not only project.id: applying a scenario can change the class
  }, [project, classId]);

  const linkedUseCases = project.links
    .filter((link) => link.classId === classId)
    .map((link) => {
      const useCase = project.useCases.find((uc) => uc.id === link.useCaseId);
      return { key: useCaseKey(link.useCaseId), label: useCase ? useCaseLabel(useCase) : link.useCaseId };
    });

  const showLinesInSource = (from: number, to: number) => {
    setHighlight({ from, to });
    setTab('source');
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Tabs value={tab} onChange={(_event, value: TabName) => setTab(value)} sx={{ px: 2, minHeight: 40 }}>
        <Tab value="overview" label="Übersicht" sx={{ minHeight: 40 }} />
        <Tab value="source" label="Quelltext" sx={{ minHeight: 40 }} />
      </Tabs>

      {error && (
        <Alert severity="error" sx={{ m: 2 }}>
          Klasse konnte nicht geladen werden: {error}
        </Alert>
      )}
      {!detail && !error && <CircularProgress size={28} sx={{ m: 3, alignSelf: 'center' }} />}

      {detail && tab === 'overview' && (
        <Box sx={{ flex: 1, overflow: 'auto', px: 2, pb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5, fontFamily: 'monospace' }}>
            {detail.path}
          </Typography>

          <Button
            variant="outlined"
            startIcon={<EditOutlinedIcon />}
            sx={{ mt: 1.5 }}
            onClick={() => setChangeMethod('')}
          >
            Code ändern …
          </Button>

          <SectionTitle>Zugeordnete Use Cases ({linkedUseCases.length})</SectionTitle>
          <LinkedList
            items={linkedUseCases}
            emptyText="Keine deklarierte Zuordnung (keine Entwarnung)."
            onNavigate={onNavigate}
          />

          <SectionTitle>Felder ({detail.fields.length})</SectionTitle>
          <List dense disablePadding>
            {detail.fields.map((field) => (
              <ListItemButton
                key={`${field.name}:${field.startLine}`}
                onClick={() => showLinesInSource(field.startLine, field.endLine)}
                sx={{ borderRadius: 1 }}
              >
                <ListItemText
                  primary={field.declaration}
                  secondary={`Zeile ${field.startLine}`}
                  slotProps={{ primary: { sx: { fontFamily: 'monospace', fontSize: 12, wordBreak: 'break-all' } } }}
                />
              </ListItemButton>
            ))}
          </List>

          <SectionTitle>Methoden ({detail.methods.length})</SectionTitle>
          <List dense disablePadding>
            {detail.methods.map((method) => (
              <ListItem
                key={method.signature}
                disablePadding
                secondaryAction={
                  <Tooltip title="Diese Methode ändern (Codeänderung prüfen)">
                    <IconButton edge="end" onClick={() => setChangeMethod(method.signature)}>
                      <EditOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                }
              >
                <ListItemButton
                  onClick={() => showLinesInSource(method.startLine, method.endLine)}
                  sx={{ borderRadius: 1 }}
                >
                  <ListItemText
                    primary={method.signature}
                    secondary={`Zeile ${method.startLine}–${method.endLine}${method.isConstructor ? ' · Konstruktor' : ''}`}
                    slotProps={{ primary: { sx: { fontFamily: 'monospace', fontSize: 13, wordBreak: 'break-all' } } }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {detail && tab === 'source' && (
        <Box sx={{ flex: 1, minHeight: 0 }}>
          <SourceCode source={detail.source} highlightFrom={highlight?.from} highlightTo={highlight?.to} />
        </Box>
      )}

      {changeMethod !== null && (
        <CreateScenarioDialog
          project={project}
          initialChangeType="code"
          initialClassId={classId}
          initialMethodSignature={changeMethod}
          onClose={() => setChangeMethod(null)}
          onCreated={(scenario) => {
            setChangeMethod(null);
            onScenarioCreated(scenario.id);
          }}
        />
      )}
    </Box>
  );
}
