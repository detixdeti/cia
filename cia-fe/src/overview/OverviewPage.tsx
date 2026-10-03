import { useEffect, useState, type ReactNode } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  Typography,
  alpha,
} from '@mui/material';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import AddIcon from '@mui/icons-material/Add';
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';
import CodeIcon from '@mui/icons-material/Code';
import LinkIcon from '@mui/icons-material/Link';
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined';
import { fetchScenarios } from '../api';
import type { Project, ScenarioSummary } from '../types';
import type { Page } from '../TopBar';
import { artifactColors } from '../theme';
import Logo from '../components/Logo';
import CreateScenarioDialog from '../scenarios/CreateScenarioDialog';
import { CHANGE_TYPE_LABELS, ScenarioStatusChip } from '../scenarios/scenarioLabels';

interface OverviewPageProps {
  project: Project;
  onOpenPage: (page: Page) => void;
  onOpenScenario: (scenarioId: number) => void;
}

// Start page: what the project contains and where to go next.
export default function OverviewPage({ project, onOpenPage, onOpenScenario }: OverviewPageProps) {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    fetchScenarios(project.id)
      .then(setScenarios)
      .catch(() => setScenarios([]));
  }, [project]);

  const linkedUseCases = new Set(project.links.map((link) => link.useCaseId));
  const linkedClasses = new Set(project.links.map((link) => link.classId));
  const openScenarios = scenarios.filter((s) => s.status !== 'applied' && s.status !== 'completed').length;

  return (
    <Box sx={{ flex: 1, overflow: 'auto' }}>
      <Box sx={{ maxWidth: 1100, mx: 'auto', py: 3, px: 2 }}>
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent sx={{ display: 'flex', gap: 3, alignItems: 'center', flexWrap: 'wrap', p: 3 }}>
            <Logo size={64} />
            <Box sx={{ flex: 1, minWidth: 280 }}>
              <Typography variant="overline" color="text.secondary">
                Projekt
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 800 }}>
                {project.name}
              </Typography>
              <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                Wie wirkt sich eine Änderung an einem Use Case auf den Code aus – und umgekehrt? Die Trace-Links
                bestimmen, was geprüft wird, das Sprachmodell schlägt konkrete Anpassungen vor.
              </Typography>
            </Box>
            <Stack direction="row" spacing={1}>
              <Button variant="outlined" startIcon={<AccountTreeOutlinedIcon />} onClick={() => onOpenPage('mapping')}>
                Zuordnungen öffnen
              </Button>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>
                Neues Szenario
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {project.modified && (
          <Alert severity="warning" variant="outlined" sx={{ mb: 3 }}>
            Im Arbeitsstand sind übernommene Szenarien enthalten. Zurücksetzen über „Arbeitsstand geändert“ oben rechts.
          </Alert>
        )}

        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2, mb: 3 }}>
          <StatCard
            icon={<ArticleOutlinedIcon />}
            color={artifactColors.useCase}
            label="Use Cases"
            value={project.useCases.length}
            detail={`${project.useCases.length - linkedUseCases.size} ohne Zuordnung`}
          />
          <StatCard
            icon={<CodeIcon />}
            color={artifactColors.javaClass}
            label="Klassen"
            value={project.classes.length}
            detail={`${project.classes.length - linkedClasses.size} ohne Zuordnung`}
          />
          <StatCard
            icon={<LinkIcon />}
            color="#38bdf8"
            label="Trace-Links"
            value={project.links.length}
            detail={`Ø ${(project.links.length / Math.max(linkedUseCases.size, 1)).toFixed(1)} Klassen je Use Case`}
          />
          <StatCard
            icon={<ScienceOutlinedIcon />}
            color="#f59e0b"
            label="Szenarien"
            value={scenarios.length}
            detail={`${openScenarios} in Bearbeitung`}
          />
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                So funktioniert's
              </Typography>
              <Step number={1} title="Zuordnungen erkunden">
                Graph und Matrix zeigen, welche Klassen zu welchem Use Case gehören.
              </Step>
              <Step number={2} title="Szenario anlegen">
                Einen Use Case ändern, deaktivieren oder neu anlegen – oder eine Codeänderung eingeben.
              </Step>
              <Step number={3} title="Vorschläge prüfen und übernehmen">
                Das Modell analysiert jeden Kandidaten. Vorschläge annehmen oder verwerfen und das Ergebnis in den
                Arbeitsstand übernehmen.
              </Step>
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent>
              <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="h6">Letzte Szenarien</Typography>
                {scenarios.length > 0 && <Button onClick={() => onOpenPage('scenarios')}>Alle anzeigen</Button>}
              </Stack>
              {scenarios.length === 0 ? (
                <Typography color="text.secondary" sx={{ py: 3, textAlign: 'center' }}>
                  Noch keine Szenarien angelegt.
                </Typography>
              ) : (
                <List disablePadding>
                  {scenarios.slice(0, 5).map((scenario) => (
                    <ListItemButton
                      key={scenario.id}
                      onClick={() => onOpenScenario(scenario.id)}
                      sx={{ borderRadius: 1.5 }}
                    >
                      <ListItemText
                        primary={scenario.title}
                        secondary={`${CHANGE_TYPE_LABELS[scenario.changeType]} · ${scenario.analysedCount}/${scenario.candidateCount} analysiert`}
                      />
                      <ScenarioStatusChip status={scenario.status} />
                    </ListItemButton>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>

      {dialogOpen && (
        <CreateScenarioDialog
          project={project}
          onClose={() => setDialogOpen(false)}
          onCreated={(scenario) => onOpenScenario(scenario.id)}
        />
      )}
    </Box>
  );
}

interface StatCardProps {
  icon: ReactNode;
  color: string;
  label: string;
  value: number;
  detail: string;
}

function StatCard({ icon, color, label, value, detail }: StatCardProps) {
  return (
    <Card variant="outlined">
      <CardContent sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
        <Box
          sx={{
            width: 44,
            height: 44,
            borderRadius: 2,
            display: 'grid',
            placeItems: 'center',
            color,
            bgcolor: alpha(color, 0.15),
          }}
        >
          {icon}
        </Box>
        <Box>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 800, lineHeight: 1.2 }}>
            {value}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {detail}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

function Step({ number, title, children }: { number: number; title: string; children: ReactNode }) {
  return (
    <Stack direction="row" spacing={1.5} sx={{ mb: 2 }}>
      <Box
        sx={{
          width: 26,
          height: 26,
          flexShrink: 0,
          borderRadius: '50%',
          display: 'grid',
          placeItems: 'center',
          fontWeight: 700,
          fontSize: 13,
          color: 'primary.contrastText',
          bgcolor: 'primary.main',
        }}
      >
        {number}
      </Box>
      <Box>
        <Typography sx={{ fontWeight: 600 }}>{title}</Typography>
        <Typography variant="body2" color="text.secondary">
          {children}
        </Typography>
      </Box>
    </Stack>
  );
}
