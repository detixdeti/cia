import { useEffect, useMemo, useRef, type MouseEvent } from 'react';
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  Position,
  ReactFlow,
  useReactFlow,
  useStore,
  type Edge,
  type Node,
  type NodeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Box, Typography, alpha, useTheme } from '@mui/material';
import { artifactColors } from '../theme';
import {
  classKey,
  useCaseKey,
  useCaseLabel,
  type HighlightState,
  type MappingViewData,
  type ScenarioRole,
} from './mappingModel';

const NODE_WIDTH = 260;
const NODE_HEIGHT = 44;
const ROW_HEIGHT = 58;
const COLUMN_GAP = 520;
const HEADER_OFFSET = 50;
const MAX_ROWS_IN_VIEW = 16;

type ArtifactNodeData = {
  label: string;
  kind: 'useCase' | 'class';
  state: HighlightState;
  unlinked: boolean;
  scenarioRole: ScenarioRole | null;
};

type ColumnLabelData = { label: string };

type ArtifactNodeType = Node<ArtifactNodeData, 'artifact'>;
type ColumnLabelNodeType = Node<ColumnLabelData, 'columnLabel'>;

interface TraceGraphProps {
  view: MappingViewData;
  focusKey: string | null;
  onSelect: (key: string, addToSelection: boolean) => void;
  onOpenSubgraph: (key: string) => void;
  onClearSelection: () => void;
}

const nodeTypes = { artifact: ArtifactNode, columnLabel: ColumnLabelNode };

export default function TraceGraph({ view, focusKey, onSelect, onOpenSubgraph, onClearSelection }: TraceGraphProps) {
  const theme = useTheme();
  const { fitView, fitBounds, getViewport, setViewport } = useReactFlow();

  const nodes = useMemo(() => buildNodes(view), [view]);
  const edges = useMemo(
    () => buildEdges(view, theme.palette.primary.main, theme.palette.text.secondary),
    [view, theme],
  );

  // When other nodes become visible, show the graph from the top. Long columns would be
  // unreadable if fitted completely, so at most MAX_ROWS_IN_VIEW rows are fitted.
  // The mapping view stays mounted but hidden on the other pages; a hidden graph has no size.
  const paneWidth = useStore((state) => state.width);
  const isShown = paneWidth > 0;

  // When other nodes become visible, show the graph from the top. Long columns would be
  // unreadable if fitted completely, so at most MAX_ROWS_IN_VIEW rows are fitted.
  // A hidden graph is fitted as soon as it is shown again.
  const visibleNodeIds = nodes.map((node) => node.id).join(',');
  const fittedNodeIds = useRef('');
  useEffect(() => {
    if (!isShown || fittedNodeIds.current === visibleNodeIds) return;
    fittedNodeIds.current = visibleNodeIds;
    const top = Math.min(...nodes.map((node) => node.position.y));
    const bottom = Math.max(...nodes.map((node) => node.position.y)) + NODE_HEIGHT;
    const bounds = {
      x: 0,
      y: top,
      width: COLUMN_GAP + NODE_WIDTH,
      height: Math.min(bottom - top, MAX_ROWS_IN_VIEW * ROW_HEIGHT),
    };
    const frame = requestAnimationFrame(() => fitBounds(bounds, { duration: 300, padding: 0.1 }));
    return () => cancelAnimationFrame(frame);
  }, [visibleNodeIds, isShown, fitBounds]);

  // When the graph area gets narrower or wider (e.g. the detail panel opens),
  // keep both columns visible without jumping away from the current rows.
  useEffect(() => {
    if (!isShown) return;
    const { x, y, zoom } = getViewport();
    const graphWidth = COLUMN_GAP + NODE_WIDTH;
    const newZoom = Math.min(zoom, (paneWidth * 0.9) / graphWidth);
    const topRowInView = -y / zoom;
    const graphFitsAlready = x >= 0 && x + graphWidth * zoom <= paneWidth;
    if (graphFitsAlready) return;
    setViewport({ x: (paneWidth - graphWidth * newZoom) / 2, y: -topRowInView * newZoom, zoom: newZoom });
  }, [paneWidth, isShown, getViewport, setViewport]);

  // Zoom to an artifact chosen in the search field.
  useEffect(() => {
    if (!focusKey) return;
    const frame = requestAnimationFrame(() => fitView({ nodes: [{ id: focusKey }], duration: 400, maxZoom: 1 }));
    return () => cancelAnimationFrame(frame);
  }, [focusKey, fitView]);

  const handleNodeClick = (event: MouseEvent, node: Node) => {
    if (node.type === 'artifact') onSelect(node.id, event.shiftKey);
  };

  const handleNodeDoubleClick = (_event: MouseEvent, node: Node) => {
    if (node.type === 'artifact') onOpenSubgraph(node.id);
  };

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      colorMode={theme.palette.mode}
      onNodeClick={handleNodeClick}
      onNodeDoubleClick={handleNodeDoubleClick}
      onPaneClick={onClearSelection}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      zoomOnDoubleClick={false}
      panOnScroll
      minZoom={0.05}
      proOptions={{ hideAttribution: true }}
      style={{ background: 'transparent' }}
    >
      <Background variant={BackgroundVariant.Dots} gap={22} size={1} />
      <Controls showInteractive={false} position="top-right" />
    </ReactFlow>
  );
}

function buildNodes(view: MappingViewData): Node[] {
  // Use cases on the left, classes on the right; the position has no further meaning.
  // The shorter column is centered, unless the graph is too tall to see at once.
  const rowCount = Math.max(view.useCases.length, view.classes.length);
  const centerColumns = rowCount <= MAX_ROWS_IN_VIEW;
  const useCaseOffset = centerColumns ? ((rowCount - view.useCases.length) * ROW_HEIGHT) / 2 : 0;
  const classOffset = centerColumns ? ((rowCount - view.classes.length) * ROW_HEIGHT) / 2 : 0;

  const nodes: Node[] = [];

  nodes.push(columnLabel('label:useCases', `Use Cases (${view.useCases.length})`, 0, useCaseOffset - HEADER_OFFSET));
  nodes.push(columnLabel('label:classes', `Klassen (${view.classes.length})`, COLUMN_GAP, classOffset - HEADER_OFFSET));

  view.useCases.forEach((useCase, index) => {
    const key = useCaseKey(useCase.id);
    nodes.push(artifactNode(key, useCaseLabel(useCase), 'useCase', view, 0, useCaseOffset + index * ROW_HEIGHT));
  });

  view.classes.forEach((javaClass, index) => {
    const key = classKey(javaClass.id);
    nodes.push(artifactNode(key, javaClass.id, 'class', view, COLUMN_GAP, classOffset + index * ROW_HEIGHT));
  });

  return nodes;
}

function artifactNode(
  key: string,
  label: string,
  kind: 'useCase' | 'class',
  view: MappingViewData,
  x: number,
  y: number,
): ArtifactNodeType {
  return {
    id: key,
    type: 'artifact',
    position: { x, y },
    data: {
      label,
      kind,
      state: view.stateOf(key),
      unlinked: view.degreeOf(key) === 0,
      scenarioRole: view.roleOf(key),
    },
  };
}

function columnLabel(id: string, label: string, x: number, y: number): ColumnLabelNodeType {
  return { id, type: 'columnLabel', position: { x, y }, data: { label }, selectable: false };
}

function buildEdges(view: MappingViewData, highlightColor: string, neutralColor: string): Edge[] {
  return view.links.map((link) => {
    const state = view.linkStateOf(link);
    let stroke = alpha(neutralColor, 0.45);
    let strokeWidth = 1.2;
    let zIndex = 0;

    if (state === 'selected') {
      stroke = highlightColor;
      strokeWidth = 2.4;
      zIndex = 2;
    } else if (state === 'indirect') {
      stroke = alpha(highlightColor, 0.45);
      strokeWidth = 1.4;
      zIndex = 1;
    } else if (state === 'dimmed') {
      stroke = alpha(neutralColor, 0.12);
    }

    return {
      id: `${link.useCaseId}->${link.classId}`,
      source: useCaseKey(link.useCaseId),
      target: classKey(link.classId),
      style: { stroke, strokeWidth, strokeDasharray: state === 'indirect' ? '5 4' : undefined },
      zIndex,
    };
  });
}

function ArtifactNode({ data }: NodeProps<ArtifactNodeType>) {
  const theme = useTheme();
  const typeColor = data.kind === 'useCase' ? artifactColors.useCase : artifactColors.javaClass;
  const highlight = theme.palette.primary.main;

  let borderColor = theme.palette.divider;
  let background = theme.palette.background.paper;
  let opacity = 1;

  if (data.state === 'selected') {
    borderColor = highlight;
    background = alpha(highlight, theme.palette.mode === 'dark' ? 0.22 : 0.12);
  } else if (data.state === 'linked') {
    borderColor = highlight;
  } else if (data.state === 'indirect') {
    borderColor = alpha(highlight, 0.6);
    opacity = 0.8;
  } else if (data.state === 'dimmed') {
    opacity = 0.3;
  }

  // A shown scenario wins over the selection colors; the caption below repeats it in words.
  if (data.scenarioRole === 'changed') borderColor = theme.palette.error.main;
  if (data.scenarioRole === 'candidate') borderColor = theme.palette.warning.main;
  const caption = [
    data.scenarioRole === 'changed' && 'im Szenario geändert',
    data.scenarioRole === 'candidate' && 'Kandidat des Szenarios',
    data.unlinked && 'keine Zuordnung',
  ]
    .filter(Boolean)
    .join(' · ');

  return (
    <Box
      title={data.label}
      sx={{
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        px: 1.5,
        borderRadius: 1.5,
        border: data.scenarioRole ? '2.5px solid' : '1.5px solid',
        borderStyle: data.unlinked || data.state === 'indirect' ? 'dashed' : 'solid',
        borderColor,
        borderLeft: `5px solid ${typeColor}`,
        bgcolor: background,
        opacity,
        cursor: 'pointer',
        boxShadow: data.state === 'selected' ? `0 0 0 3px ${alpha(highlight, 0.25)}` : 'none',
        transition: 'opacity 150ms, border-color 150ms, background-color 150ms',
      }}
    >
      {data.kind === 'class' && <Handle type="target" position={Position.Left} style={hiddenHandle} />}
      <Typography variant="body2" noWrap sx={{ fontWeight: data.state === 'selected' ? 700 : 500 }}>
        {data.label}
      </Typography>
      {caption && (
        <Typography variant="caption" color="text.secondary" noWrap sx={{ lineHeight: 1.2 }}>
          {caption}
        </Typography>
      )}
      {data.kind === 'useCase' && <Handle type="source" position={Position.Right} style={hiddenHandle} />}
    </Box>
  );
}

function ColumnLabelNode({ data }: NodeProps<ColumnLabelNodeType>) {
  return (
    <Typography
      variant="overline"
      color="text.secondary"
      sx={{ width: NODE_WIDTH, display: 'block', textAlign: 'center', fontWeight: 700, letterSpacing: 1.2 }}
    >
      {data.label}
    </Typography>
  );
}

const hiddenHandle = { opacity: 0, pointerEvents: 'none' as const };
