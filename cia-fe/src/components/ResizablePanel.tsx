import { useState, type MouseEvent, type ReactNode } from 'react';
import { Box } from '@mui/material';

const MIN_WIDTH = 320;
const MAX_SHARE_OF_WINDOW = 0.75;

interface ResizablePanelProps {
  storageKey: string; // the chosen width is remembered in localStorage under this key
  defaultWidth: number;
  children: ReactNode;
}

// A panel on the right side whose width can be changed by dragging its left edge.
export default function ResizablePanel({ storageKey, defaultWidth, children }: ResizablePanelProps) {
  const [width, setWidth] = useState(() => Number(localStorage.getItem(storageKey)) || defaultWidth);

  const startResize = (event: MouseEvent) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = width;
    let latestWidth = startWidth;

    const onMove = (moveEvent: globalThis.MouseEvent) => {
      // Dragging to the left makes the panel wider.
      const wanted = startWidth + startX - moveEvent.clientX;
      latestWidth = Math.round(Math.min(Math.max(wanted, MIN_WIDTH), window.innerWidth * MAX_SHARE_OF_WINDOW));
      setWidth(latestWidth);
    };

    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      localStorage.setItem(storageKey, String(latestWidth));
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    // Keep the resize cursor and avoid selecting text while dragging.
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  return (
    <Box sx={{ width, flexShrink: 0, position: 'relative', borderLeft: 1, borderColor: 'divider' }}>
      <Box
        onMouseDown={startResize}
        onDoubleClick={() => {
          setWidth(defaultWidth);
          localStorage.setItem(storageKey, String(defaultWidth));
        }}
        title="Ziehen zum Vergrößern · Doppelklick setzt die Breite zurück"
        sx={{
          position: 'absolute',
          left: -4,
          top: 0,
          bottom: 0,
          width: 8,
          cursor: 'col-resize',
          zIndex: 10,
          '&:hover, &:active': { bgcolor: 'primary.main', opacity: 0.4 },
        }}
      />
      {children}
    </Box>
  );
}
