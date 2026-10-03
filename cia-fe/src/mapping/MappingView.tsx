import { useEffect, useMemo, useState } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Divider,
  FormControlLabel,
  InputAdornment,
  Paper,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import GridOnOutlinedIcon from '@mui/icons-material/GridOnOutlined';
import SearchIcon from '@mui/icons-material/Search';
import CenterFocusStrongOutlinedIcon from '@mui/icons-material/CenterFocusStrongOutlined';
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap';
import type { Project } from '../types';
import {
  buildNeighbors,
  classKey,
  computeMappingView,
  useCaseKey,
  useCaseLabel,
  type ScenarioOverlay,
} from './mappingModel';
import TraceGraph from './TraceGraph';
import TraceMatrix from './TraceMatrix';
import Legend from './Legend';
import DetailPanel from '../detail/DetailPanel';
import ResizablePanel from '../components/ResizablePanel';

type ViewMode = 'graph' | 'matrix';

interface SearchOption {
  key: string;
  label: string;
  group: string;
}

interface MappingViewProps {
  project: Project;
  overlay: ScenarioOverlay | null; // a scenario to mark in graph and matrix
  onClearOverlay: () => void;
  onScenarioCreated: (scenarioId: number) => void;
}

export default function MappingView({ project, overlay, onClearOverlay, onScenarioCreated }: MappingViewProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('graph');
  const [selection, setSelection] = useState<Set<string>>(new Set());
  const [subgraphOnly, setSubgraphOnly] = useState(false);
  const [showIndirect, setShowIndirect] = useState(false);
  const [showUnlinked, setShowUnlinked] = useState(true);
  const [focusKey, setFocusKey] = useState<string | null>(null);
  // The artifact shown in the detail panel: the one clicked last, as long as it is still selected.
  const [detailKey, setDetailKey] = useState<string | null>(null);
  const showDetail = detailKey !== null && selection.has(detailKey);

  const neighbors = useMemo(() => buildNeighbors(project.links), [project]);

  const view = useMemo(
    () => computeMappingView(project, neighbors, { selection, subgraphOnly, showIndirect, showUnlinked }, overlay),
    [project, neighbors, selection, subgraphOnly, showIndirect, showUnlinked, overlay],
  );

  // A shown scenario starts with the subgraph around the changed artifact. A new
  // use case is not in the graph yet, then its candidates are selected instead.
  useEffect(() => {
    if (!overlay) return;
    const allKeys = [...project.useCases.map((uc) => useCaseKey(uc.id)), ...project.classes.map((c) => classKey(c.id))];
    setSelection(new Set(allKeys.includes(overlay.changedKey) ? [overlay.changedKey] : overlay.candidateKeys));
    setDetailKey(null);
    setSubgraphOnly(true);
  }, [overlay, project]);

  const searchOptions = useMemo<SearchOption[]>(
    () => [
      ...project.useCases.map((uc) => ({ key: useCaseKey(uc.id), label: useCaseLabel(uc), group: 'Use Cases' })),
      ...project.classes.map((cls) => ({ key: classKey(cls.id), label: cls.id, group: 'Klassen' })),
    ],
    [project],
  );

  // Click selects one artifact, Shift+Click adds or removes it from the selection.
  const handleSelect = (key: string, addToSelection: boolean) => {
    setDetailKey(key);
    setSelection((current) => {
      if (addToSelection) {
        const next = new Set(current);
        if (next.has(key)) next.delete(key);
        else next.add(key);
        return next;
      }
      if (current.size === 1 && current.has(key)) return new Set();
      return new Set([key]);
    });
  };

  const handleOpenSubgraph = (key: string) => {
    setSelection(new Set([key]));
    setDetailKey(key);
    setSubgraphOnly(true);
  };

  const handleClearSelection = () => {
    setSelection(new Set());
    setSubgraphOnly(false);
  };

  // Used by the search field and by links in the detail panel.
  const selectAndFocus = (key: string) => {
    setSelection(new Set([key]));
    setDetailKey(key);
    setFocusKey(key);
  };

  return (
    <Paper variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Stack spacing={1.5} sx={{ p: 2 }}>
        <Stack
          direction="row"
          sx={{ alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}
        >
          <Typography variant="h6">Zuordnungen</Typography>
          <Typography variant="body2" color="text.secondary">
            {project.useCases.length} Use Cases · {project.classes.length} Klassen · {project.links.length} Trace-Links
          </Typography>
        </Stack>

        <Stack direction="row" spacing={1.5} useFlexGap sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
          <Autocomplete
            sx={{ flex: 1, minWidth: 260 }}

            options={searchOptions}
            groupBy={(option) => option.group}
            getOptionLabel={(option) => option.label}
            value={null}
            blurOnSelect
            onChange={(_event, option) => option && selectAndFocus(option.key)}
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder="Suchen (z. B. UC20, Cart) …"
                slotProps={{
                  ...params.slotProps,
                  input: {
                    ...params.slotProps.input,
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon fontSize="small" />
                      </InputAdornment>
                    ),
                  },
                }}
              />
            )}
          />

          <Tooltip title={selection.size === 0 ? 'Zuerst einen Use Case oder eine Klasse auswählen' : ''}>
            <span>
              <Button
                variant={view.isSubgraph ? 'contained' : 'outlined'}
                startIcon={view.isSubgraph ? <ZoomOutMapIcon /> : <CenterFocusStrongOutlinedIcon />}
                disabled={selection.size === 0}
                onClick={() => setSubgraphOnly(!view.isSubgraph)}
              >
                {view.isSubgraph ? 'Gesamtgraph' : 'Teilgraph'}
              </Button>
            </span>
          </Tooltip>

          <ToggleButtonGroup
            exclusive
            value={viewMode}
            onChange={(_event, value: ViewMode | null) => value && setViewMode(value)}
          >
            <ToggleButton value="graph" sx={{ px: 1.5, gap: 0.75 }}>
              <AccountTreeOutlinedIcon fontSize="small" /> Graph
            </ToggleButton>
            <ToggleButton value="matrix" sx={{ px: 1.5, gap: 0.75 }}>
              <GridOnOutlinedIcon fontSize="small" /> Matrix
            </ToggleButton>
          </ToggleButtonGroup>
        </Stack>

        <Stack direction="row" spacing={2} useFlexGap sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
          <Tooltip title="Zeigt zusätzlich, was über die direkt verknüpften Elemente erreichbar ist (z. B. weitere Use Cases derselben Klasse). Das ist keine fachliche Abhängigkeit.">
            <FormControlLabel
              control={<Switch checked={showIndirect} onChange={(e) => setShowIndirect(e.target.checked)} />}
              label={<Typography variant="body2">Indirekte Nachbarn</Typography>}
            />
          </Tooltip>
          <FormControlLabel
            control={<Switch checked={showUnlinked} onChange={(e) => setShowUnlinked(e.target.checked)} />}
            label={<Typography variant="body2">Elemente ohne Zuordnung</Typography>}
          />
          <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
            Klick wählt aus · Umschalt+Klick wählt mehrere · Doppelklick öffnet den Teilgraphen
          </Typography>
        </Stack>

        {overlay && (
          <Alert
            severity="warning"
            variant="outlined"
            action={
              <Button
                color="inherit"

                onClick={() => {
                  // The scenario opened the subgraph, so hiding it returns to the full graph.
                  onClearOverlay();
                  handleClearSelection();
                }}
              >
                Ausblenden
              </Button>
            }
          >
            Szenario „{overlay.title}“ wird angezeigt: rot das geänderte Artefakt, gelb die Kandidaten aus den
            Trace-Links.
          </Alert>
        )}
      </Stack>

      <Divider />

      <Box sx={{ flex: 1, minHeight: 0, display: 'flex' }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {viewMode === 'graph' ? (
            <ReactFlowProvider>
              <TraceGraph
                view={view}
                focusKey={focusKey}
                onSelect={handleSelect}
                onOpenSubgraph={handleOpenSubgraph}
                onClearSelection={handleClearSelection}
              />
            </ReactFlowProvider>
          ) : (
            <TraceMatrix
              view={view}
              focusKey={focusKey}
              onSelect={handleSelect}
              onClearSelection={handleClearSelection}
            />
          )}
        </Box>

        {showDetail && (
          <ResizablePanel storageKey="cia-detail-panel-width" defaultWidth={440}>
            <DetailPanel
              project={project}
              detailKey={detailKey}
              onNavigate={selectAndFocus}
              onClose={() => setDetailKey(null)}
              onScenarioCreated={onScenarioCreated}
            />
          </ResizablePanel>
        )}
      </Box>

      <Divider />
      <Box sx={{ px: 2, py: 1.25 }}>
        <Legend showIndirect={showIndirect} showScenario={overlay !== null} />
      </Box>
    </Paper>
  );
}
