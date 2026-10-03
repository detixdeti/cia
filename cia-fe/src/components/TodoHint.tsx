import { Box, Typography } from '@mui/material';
import ConstructionOutlinedIcon from '@mui/icons-material/ConstructionOutlined';

// DEMO-BETREUER: Platzhalter für Funktionen, die noch nicht gezeigt werden.
export default function TodoHint({ children }: { children: string }) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        px: 1.25,
        py: 0.75,
        my: 1.5,
        border: '1px dashed',
        borderColor: 'warning.main',
        borderRadius: 1.5,
        color: 'warning.main',
      }}
    >
      <ConstructionOutlinedIcon fontSize="small" />
      <Typography variant="body2">TODO: {children}</Typography>
    </Box>
  );
}
