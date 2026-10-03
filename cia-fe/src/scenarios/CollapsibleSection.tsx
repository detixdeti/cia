import { useState, type ReactNode } from 'react';
import { Box, ButtonBase, Collapse, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

interface CollapsibleSectionProps {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}

// A section that starts collapsed: needed for traceability, but rarely read.
export default function CollapsibleSection({ title, children, defaultOpen = false }: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 1.5 }}>
      <ButtonBase
        onClick={() => setOpen(!open)}
        sx={{ width: '100%', justifyContent: 'flex-start', gap: 0.5, px: 1.25, py: 0.75, borderRadius: 1.5 }}
      >
        <ExpandMoreIcon
          fontSize="small"
          sx={{
            transform: open ? 'rotate(0deg)' : 'rotate(-90deg)',
            transition: 'transform 150ms',
            color: 'text.secondary',
          }}
        />
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
          {title}
        </Typography>
      </ButtonBase>
      <Collapse in={open} unmountOnExit>
        <Box sx={{ px: 1.5, pb: 1.5 }}>{children}</Box>
      </Collapse>
    </Box>
  );
}
