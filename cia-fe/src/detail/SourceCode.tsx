import { useEffect, useRef } from 'react';
import { Box, alpha, useTheme } from '@mui/material';

interface SourceCodeProps {
  source: string;
  highlightFrom?: number; // 1-based line numbers, inclusive
  highlightTo?: number;
}

// Plain source code view with line numbers. The highlighted lines are scrolled into view.
export default function SourceCode({ source, highlightFrom, highlightTo }: SourceCodeProps) {
  const theme = useTheme();
  const firstHighlightedLine = useRef<HTMLDivElement>(null);

  useEffect(() => {
    firstHighlightedLine.current?.scrollIntoView({ block: 'start' });
  }, [highlightFrom]);

  const lines = source.split('\n');
  const isHighlighted = (lineNumber: number) =>
    highlightFrom !== undefined &&
    highlightTo !== undefined &&
    lineNumber >= highlightFrom &&
    lineNumber <= highlightTo;

  return (
    <Box
      sx={{
        height: '100%',
        overflow: 'auto',
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
        fontSize: 12,
        lineHeight: 1.6,
        bgcolor: theme.palette.mode === 'dark' ? '#0d1117' : '#f6f8fa',
        '& .line': { display: 'flex', scrollMarginTop: 24 },
        '& .line.highlighted': { bgcolor: alpha(theme.palette.primary.main, 0.15) },
        '& .line-number': {
          width: 48,
          flexShrink: 0,
          pr: 1.5,
          textAlign: 'right',
          color: 'text.disabled',
          userSelect: 'none',
        },
        '& .line-text': { whiteSpace: 'pre', pr: 2 },
      }}
    >
      {lines.map((line, index) => {
        const lineNumber = index + 1;
        return (
          <div
            key={lineNumber}
            ref={lineNumber === highlightFrom ? firstHighlightedLine : undefined}
            className={isHighlighted(lineNumber) ? 'line highlighted' : 'line'}
          >
            <span className="line-number">{lineNumber}</span>
            <span className="line-text">{line}</span>
          </div>
        );
      })}
    </Box>
  );
}
