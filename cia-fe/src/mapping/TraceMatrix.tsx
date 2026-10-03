import { useEffect, type MouseEvent } from 'react';
import { Box, Tooltip, alpha, useTheme } from '@mui/material';
import { artifactColors } from '../theme';
import { classKey, useCaseKey, type HighlightState, type MappingViewData } from './mappingModel';

const CELL_SIZE = 26;

interface TraceMatrixProps {
  view: MappingViewData;
  focusKey: string | null;
  onSelect: (key: string, addToSelection: boolean) => void;
  onClearSelection: () => void;
}

// Rows are use cases, columns are classes. A filled square is a declared trace link.
export default function TraceMatrix({ view, focusKey, onSelect, onClearSelection }: TraceMatrixProps) {
  const theme = useTheme();
  const highlight = theme.palette.primary.main;

  // Scroll to an artifact chosen in the search field.
  useEffect(() => {
    if (focusKey) {
      // "center", so the target does not end up behind the sticky header row or column
      document
        .getElementById(matrixId(focusKey))
        ?.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
    }
  }, [focusKey]);

  // Headers are sticky, so they must stay opaque. The transparent highlight is
  // therefore painted on top of the paper color, and dimming changes the text color only.
  const headerBackground = (state: HighlightState, key: string) => {
    const paper = theme.palette.background.paper;
    const role = view.roleOf(key);

    // A shown scenario wins over the selection colors (red = changed, yellow = candidate).
    let color: string | null = null;
    if (role === 'changed') color = alpha(theme.palette.error.main, 0.25);
    else if (role === 'candidate') color = alpha(theme.palette.warning.main, 0.22);
    else if (state === 'selected') color = alpha(highlight, 0.28);
    else if (state === 'linked') color = alpha(highlight, 0.12);

    if (color === null) return paper;
    return `linear-gradient(${color}, ${color}), ${paper}`;
  };

  const textColor = (state: HighlightState) =>
    state === 'dimmed' ? theme.palette.text.disabled : theme.palette.text.primary;

  const select = (key: string) => (event: MouseEvent) => onSelect(key, event.shiftKey);

  if (view.useCases.length === 0 || view.classes.length === 0) {
    return <Box sx={{ p: 4, color: 'text.secondary' }}>Keine Einträge für die aktuelle Auswahl.</Box>;
  }

  return (
    <Box
      onClick={(event) => event.target === event.currentTarget && onClearSelection()}
      sx={{
        height: '100%',
        overflow: 'auto',
        '& table': { borderCollapse: 'separate', borderSpacing: 0, fontSize: 12 },
        '& th, & td': { p: 0, borderBottom: `1px solid ${theme.palette.divider}` },
        '& td.cell': {
          width: CELL_SIZE,
          minWidth: CELL_SIZE,
          height: CELL_SIZE,
          textAlign: 'center',
          borderRight: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
          cursor: 'pointer',
        },
        '& .sticky-left': { position: 'sticky', left: 0, zIndex: 2 },
        '& thead th': { position: 'sticky', top: 0, zIndex: 3 },
        '& thead th.sticky-left': { zIndex: 4 },
        '& .sum': { color: 'text.secondary', textAlign: 'center', px: 1, minWidth: 36 },
        '& .link-mark': {
          display: 'block',
          width: 14,
          height: 14,
          mx: 'auto',
          borderRadius: 1,
          bgcolor: 'text.secondary',
        },
        '& .link-mark.active': { bgcolor: highlight, boxShadow: `0 0 0 3px ${alpha(highlight, 0.3)}` },
        '& .link-mark.dimmed': { opacity: 0.25 },
        '& .empty-mark': {
          display: 'block',
          width: 3,
          height: 3,
          mx: 'auto',
          borderRadius: '50%',
          bgcolor: 'divider',
        },
      }}
    >
      <table>
        <thead>
          <tr>
            <th className="sticky-left" style={{ background: theme.palette.background.paper, verticalAlign: 'bottom' }}>
              <Box sx={{ px: 1.5, pb: 1, textAlign: 'left', color: 'text.secondary', fontSize: 11, letterSpacing: 1 }}>
                USE CASES ↓ · KLASSEN →
              </Box>
            </th>
            {view.classes.map((javaClass) => {
              const key = classKey(javaClass.id);
              const state = view.stateOf(key);
              return (
                <th
                  key={key}
                  id={matrixId(key)}
                  onClick={select(key)}
                  title={javaClass.path}
                  style={{
                    background: headerBackground(state, key),
                    color: textColor(state),
                    cursor: 'pointer',
                    verticalAlign: 'bottom',
                    borderBottom: `3px solid ${artifactColors.javaClass}`,
                  }}
                >
                  <Box
                    sx={{
                      writingMode: 'vertical-rl',
                      transform: 'rotate(180deg)',
                      whiteSpace: 'nowrap',
                      py: 1,
                      mx: 'auto',
                      fontWeight: state === 'selected' ? 700 : 500,
                      fontStyle: view.degreeOf(key) === 0 ? 'italic' : 'normal',
                    }}
                  >
                    {javaClass.id}
                  </Box>
                </th>
              );
            })}
            <th className="sum" style={{ background: theme.palette.background.paper, verticalAlign: 'bottom' }}>
              <Tooltip title="Anzahl deklarierter Links (Knotengrad), keine Bewertung">
                <Box sx={{ pb: 1 }}>Σ</Box>
              </Tooltip>
            </th>
          </tr>
        </thead>

        <tbody>
          {view.useCases.map((useCase) => {
            const rowKey = useCaseKey(useCase.id);
            const rowState = view.stateOf(rowKey);
            return (
              <tr key={rowKey}>
                <th
                  id={matrixId(rowKey)}
                  className="sticky-left"
                  onClick={select(rowKey)}
                  style={{
                    background: headerBackground(rowState, rowKey),
                    color: textColor(rowState),
                    cursor: 'pointer',
                    borderLeft: `3px solid ${artifactColors.useCase}`,
                  }}
                >
                  <Box sx={{ display: 'flex', gap: 1, px: 1.5, minWidth: 220, maxWidth: 360, textAlign: 'left' }}>
                    <Box component="span" sx={{ fontFamily: 'monospace', fontWeight: 700 }}>
                      {useCase.id}
                    </Box>
                    <Box
                      component="span"
                      title={useCase.title}
                      sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 400 }}
                    >
                      {useCase.title}
                    </Box>
                    {view.degreeOf(rowKey) === 0 && (
                      <Box component="span" sx={{ color: 'text.secondary', fontStyle: 'italic', whiteSpace: 'nowrap' }}>
                        keine Zuordnung
                      </Box>
                    )}
                  </Box>
                </th>

                {view.classes.map((javaClass) => {
                  const columnKey = classKey(javaClass.id);
                  const columnState = view.stateOf(columnKey);
                  const linked = view.hasLink(useCase.id, javaClass.id);
                  const inSelectedLine = rowState === 'selected' || columnState === 'selected';
                  return (
                    <td
                      key={columnKey}
                      className="cell"
                      onClick={select(rowKey)}
                      title={`${useCase.id} × ${javaClass.id}`}
                      style={{ background: inSelectedLine ? alpha(highlight, 0.08) : undefined }}
                    >
                      {linked ? (
                        <span
                          className={[
                            'link-mark',
                            inSelectedLine ? 'active' : '',
                            rowState === 'dimmed' || columnState === 'dimmed' ? 'dimmed' : '',
                          ].join(' ')}
                        />
                      ) : (
                        <span className="empty-mark" />
                      )}
                    </td>
                  );
                })}

                <td className="sum">{view.degreeOf(rowKey)}</td>
              </tr>
            );
          })}

          <tr>
            <th className="sticky-left" style={{ background: theme.palette.background.paper }}>
              <Box sx={{ px: 1.5, py: 1, textAlign: 'left', color: 'text.secondary', fontSize: 11, letterSpacing: 1 }}>
                Σ LINKS JE KLASSE
              </Box>
            </th>
            {view.classes.map((javaClass) => (
              <td key={javaClass.id} className="sum">
                {view.degreeOf(classKey(javaClass.id))}
              </td>
            ))}
            <td />
          </tr>
        </tbody>
      </table>
    </Box>
  );
}

function matrixId(key: string) {
  return `matrix-${key}`;
}
