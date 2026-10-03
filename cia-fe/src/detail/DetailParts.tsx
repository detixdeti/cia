import type { ReactNode } from 'react';
import { List, ListItemButton, ListItemText, Typography } from '@mui/material';

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <Typography variant="overline" color="text.secondary" component="div" sx={{ mt: 2.5, mb: 0.5, fontWeight: 700 }}>
      {children}
    </Typography>
  );
}

interface LinkedListProps {
  items: { key: string; label: string }[];
  emptyText: string;
  onNavigate: (key: string) => void;
}

// Clickable list of linked artifacts. A click selects the artifact in graph and matrix.
export function LinkedList({ items, emptyText, onNavigate }: LinkedListProps) {
  if (items.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
        {emptyText}
      </Typography>
    );
  }

  return (
    <List dense disablePadding>
      {items.map((item) => (
        <ListItemButton key={item.key} onClick={() => onNavigate(item.key)} sx={{ borderRadius: 1 }}>
          <ListItemText primary={item.label} slotProps={{ primary: { noWrap: true } }} />
        </ListItemButton>
      ))}
    </List>
  );
}
