import { Box, Stack, Typography, alpha, useTheme } from '@mui/material';
import { artifactColors } from '../theme';

interface LegendProps {
  showIndirect: boolean;
  showScenario: boolean;
}

export default function Legend({ showIndirect, showScenario }: LegendProps) {
  const theme = useTheme();
  const highlight = theme.palette.primary.main;
  const divider = theme.palette.divider;

  return (
    <Stack direction="row" spacing={2.5} useFlexGap sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
      <LegendItem
        label="Use Case"
        swatch={{ border: `1.5px solid ${divider}`, borderLeft: `5px solid ${artifactColors.useCase}` }}
      />
      <LegendItem
        label="Klasse"
        swatch={{ border: `1.5px solid ${divider}`, borderLeft: `5px solid ${artifactColors.javaClass}` }}
      />
      <LegendItem
        label="ausgewählt"
        swatch={{ border: `1.5px solid ${highlight}`, background: alpha(highlight, 0.2) }}
      />
      <LegendItem label="direkt verknüpft" swatch={{ border: `1.5px solid ${highlight}` }} />
      {showIndirect && (
        <LegendItem
          label="indirekt (über gemeinsame Nachbarn)"
          swatch={{ border: `1.5px dashed ${alpha(highlight, 0.6)}` }}
        />
      )}
      <LegendItem
        label="keine deklarierte Zuordnung (keine Entwarnung)"
        swatch={{ border: `1.5px dashed ${theme.palette.text.secondary}` }}
      />
      {showScenario && (
        <>
          <LegendItem label="im Szenario geändert" swatch={{ border: `2px solid ${theme.palette.error.main}` }} />
          <LegendItem label="Kandidat des Szenarios" swatch={{ border: `2px solid ${theme.palette.warning.main}` }} />
        </>
      )}
    </Stack>
  );
}

function LegendItem({ label, swatch }: { label: string; swatch: object }) {
  return (
    <Stack direction="row" spacing={0.75} sx={{ alignItems: 'center' }}>
      <Box sx={{ width: 22, height: 12, borderRadius: 0.75, ...swatch }} />
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
    </Stack>
  );
}
