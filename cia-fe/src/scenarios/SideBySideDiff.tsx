import { diffLines } from 'diff';
import { Box, Typography, alpha, useTheme } from '@mui/material';

interface SideBySideDiffProps {
  before: string;
  after: string;
  beforeLabel: string;
  afterLabel: string;
  monospace?: boolean;
}

interface Row {
  left: string | null; // null = no line on this side
  right: string | null;
  changed: boolean;
}

// Shows the current state (left) next to the proposed state (right).
// Removed lines are red on the left, added lines green on the right.
export default function SideBySideDiff({
  before,
  after,
  beforeLabel,
  afterLabel,
  monospace = true,
}: SideBySideDiffProps) {
  const theme = useTheme();
  const rows = buildRows(before, after);
  const removedColor = alpha(theme.palette.error.main, 0.16);
  const addedColor = alpha(theme.palette.success.main, 0.16);
  const emptyColor = alpha(theme.palette.text.primary, 0.03);

  const cellColor = (text: string | null, changed: boolean, changedColor: string) => {
    if (text === null) return emptyColor;
    return changed ? changedColor : undefined;
  };

  return (
    <Box
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        overflow: 'auto',
        maxHeight: 480,
        fontFamily: monospace ? 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' : 'inherit',
        fontSize: monospace ? 12 : 13,
        lineHeight: 1.6,
        '& table': { borderCollapse: 'collapse', width: '100%', tableLayout: 'fixed' },
        // pre-wrap keeps indentation but wraps long lines instead of running into the other column
        '& td': { verticalAlign: 'top', px: 1, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' },
        '& td + td': { borderLeft: `1px solid ${theme.palette.divider}` },
        '& thead td': {
          position: 'sticky',
          top: 0,
          bgcolor: 'background.paper',
          py: 0.5,
          borderBottom: `1px solid ${theme.palette.divider}`,
        },
      }}
    >
      <table>
        <thead>
          <tr>
            <td>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                {beforeLabel}
              </Typography>
            </td>
            <td>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                {afterLabel}
              </Typography>
            </td>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {/* a non-breaking space keeps empty lines at full height */}
              <td style={{ background: cellColor(row.left, row.changed, removedColor) }}>{row.left || ' '}</td>
              <td style={{ background: cellColor(row.right, row.changed, addedColor) }}>{row.right || ' '}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Box>
  );
}

// Turns the line diff into table rows. A block of removed lines followed by a
// block of added lines is shown side by side; the shorter side gets empty cells.
function buildRows(before: string, after: string): Row[] {
  const rows: Row[] = [];
  let removed: string[] = [];

  const flushRemoved = (added: string[]) => {
    const count = Math.max(removed.length, added.length);
    for (let i = 0; i < count; i++) {
      rows.push({ left: removed[i] ?? null, right: added[i] ?? null, changed: true });
    }
    removed = [];
  };

  // Without a final newline the last line would count as changed as soon as text is appended.
  const withFinalNewline = (text: string) => (text === '' || text.endsWith('\n') ? text : `${text}\n`);

  for (const part of diffLines(withFinalNewline(before), withFinalNewline(after))) {
    const lines = part.value.replace(/\n$/, '').split('\n');
    if (part.removed) {
      removed.push(...lines);
    } else if (part.added) {
      flushRemoved(lines);
    } else {
      flushRemoved([]);
      for (const line of lines) rows.push({ left: line, right: line, changed: false });
    }
  }
  flushRemoved([]);
  return rows;
}
