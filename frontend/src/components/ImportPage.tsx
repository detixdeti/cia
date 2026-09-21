// Neuen Ausgangsstand hochladen (F1).
//
// Der Browser liest die Dateien als Text und schickt sie als JSON an das
// Backend. Ein Upload ergibt immer einen neuen Ausgangsstand; ein bestehender
// wird nie ueberschrieben (Konzept 4.2).

import { useState } from 'react'
import type { ChangeEvent, ReactNode } from 'react'
import { FileCode, FileText, FolderOpen, Link2, type LucideIcon } from 'lucide-react'
import { api, type UploadedFile } from '../api'
import type { BaselineDetail } from '../types'
import { ImportReport } from './ImportReport'
import { ErrorBox } from './ui'

interface Props {
  /** Ob es schon Ausgangsstaende gibt. Dann kann man den Import abbrechen. */
  canCancel: boolean
  onCancel: () => void
  /** Der Anwender hat den Bericht gesehen und will mit dem Stand arbeiten. */
  onUse: (baselineId: string) => void
}

const USE_CASE_ENDINGS = ['.md', '.txt']

function hasEnding(file: File, endings: string[]): boolean {
  return endings.some((ending) => file.name.toLowerCase().endsWith(ending))
}

/** Der Pfad, unter dem die Datei hochgeladen wird: bei Ordnern mit Unterordnern. */
function pathOf(file: File): string {
  return file.webkitRelativePath || file.name
}

async function readAll(files: File[]): Promise<UploadedFile[]> {
  return Promise.all(files.map(async (file) => ({ path: pathOf(file), content: await file.text() })))
}

/** Gibt die Dateien einer Auswahl zurueck, die der Import verwendet. */
function filesOf(event: ChangeEvent<HTMLInputElement>, endings: string[]): { used: File[]; skipped: number } {
  const all = Array.from(event.target.files ?? [])
  const used = all.filter((f) => hasEnding(f, endings))
  return { used, skipped: all.length - used.length }
}

/** Ein Ablagefeld: Ein Klick oeffnet die Dateiauswahl. */
function FilePicker({
  icon: Icon,
  title,
  hint,
  summary,
  children,
}: {
  icon: LucideIcon
  title: string
  hint: ReactNode
  summary: string | null
  /** Das eigentliche <input type="file">. */
  children: ReactNode
}) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-xl border-2 border-dashed border-slate-300 bg-surface p-4 transition focus-within:ring-2 focus-within:ring-indigo-300 hover:border-indigo-400 hover:bg-indigo-50/40">
      <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-indigo-50 text-indigo-600">
        <Icon className="size-5" aria-hidden />
      </div>
      <div className="min-w-0">
        <div className="text-sm font-semibold text-slate-900">{title}</div>
        <div className="text-xs text-slate-500">{hint}</div>
        {summary && <div className="mt-1 text-xs font-medium text-indigo-700">{summary}</div>}
      </div>
      {children}
    </label>
  )
}

export function ImportPage({ canCancel, onCancel, onUse }: Props) {
  const [label, setLabel] = useState('')
  const [useCases, setUseCases] = useState<File[]>([])
  const [sources, setSources] = useState<File[]>([])
  const [sourceMode, setSourceMode] = useState<'files' | 'folder' | null>(null)
  const [skipped, setSkipped] = useState(0)
  const [linkFile, setLinkFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string[] | null>(null)
  const [report, setReport] = useState<BaselineDetail | null>(null)

  function pickSources(mode: 'files' | 'folder') {
    return (event: ChangeEvent<HTMLInputElement>) => {
      const { used, skipped: ignored } = filesOf(event, ['.java'])
      setSources(used)
      setSkipped(ignored)
      setSourceMode(mode)
    }
  }

  async function submit() {
    setBusy(true)
    setError(null)
    try {
      const result = await api.upload({
        label: label.trim() || 'Upload',
        use_cases: await readAll(useCases),
        sources: await readAll(sources),
        trace_links: linkFile ? { path: linkFile.name, content: await linkFile.text() } : null,
      })
      setReport(result)
    } catch (e) {
      setError([e instanceof Error ? e.message : String(e)])
    } finally {
      setBusy(false)
    }
  }

  if (report !== null) {
    return (
      <div className="card reveal mx-auto max-w-3xl p-7">
        <ImportReport report={report} />
        {report.has_errors && (
          <p className="mt-4 text-sm text-slate-600">
            Betroffene Angaben wurden nicht übernommen, der Rest ist nutzbar. Sie können mit dem Stand arbeiten oder die
            Dateien korrigieren und erneut hochladen. Der Stand wird dabei nicht überschrieben, es entsteht ein neuer.
          </p>
        )}
        <div className="mt-5 flex flex-wrap gap-2">
          <button className="btn btn-primary" onClick={() => onUse(report.baseline_id)}>
            Mit diesem Stand arbeiten
          </button>
          <button className="btn" onClick={() => setReport(null)}>
            Dateien korrigieren
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="card reveal mx-auto max-w-3xl p-7">
      <h2 className="text-xl font-semibold text-slate-900">Neuer Ausgangsstand</h2>
      <p className="mt-1 text-sm text-slate-600">
        Laden Sie Use Cases, Java-Quelltext und die Datei mit den Trace-Links hoch. Jeder Upload ergibt einen neuen,
        unveränderlichen Stand. Vor der Übernahme sehen Sie einen Bericht mit allen Befunden.
      </p>

      <div className="mt-5">
        <label htmlFor="baseline-label" className="field-label">
          Name des Standes
        </label>
        <input
          id="baseline-label"
          data-testid="baseline-label"
          className="input"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="z. B. Bibliothek v1"
        />
      </div>

      <div className="mt-4 space-y-3">
        <FilePicker
          icon={FileText}
          title="Use Cases"
          hint={
            <>
              Eine <code>.md</code>- oder <code>.txt</code>-Datei je Use Case. Erste Zeile: <code># UC1: Titel</code>.
              Ohne Überschrift gilt der Dateiname als Kennung.
            </>
          }
          summary={useCases.length > 0 ? `${useCases.length} Dateien gewählt` : null}
        >
          <input
            data-testid="file-usecases"
            type="file"
            multiple
            accept=".md,.txt"
            className="sr-only"
            onChange={(e) => setUseCases(filesOf(e, USE_CASE_ENDINGS).used)}
          />
        </FilePicker>

        <div className="grid gap-3 sm:grid-cols-2">
          <FilePicker
            icon={FileCode}
            title="Java-Dateien"
            hint="Einzelne .java-Dateien wählen. Klassen werden über den Dateinamen erkannt."
            summary={sourceMode === 'files' ? `${sources.length} Dateien gewählt` : null}
          >
            <input
              data-testid="file-java-files"
              type="file"
              multiple
              accept=".java"
              className="sr-only"
              onChange={pickSources('files')}
            />
          </FilePicker>
          <FilePicker
            icon={FolderOpen}
            title="Java-Ordner"
            hint="Einen ganzen Ordner wählen. Dateien ohne .java werden nicht mitgeschickt."
            summary={sourceMode === 'folder' ? `${sources.length} Dateien gewählt` : null}
          >
            <input
              data-testid="file-java-folder"
              type="file"
              multiple
              className="sr-only"
              onChange={pickSources('folder')}
              {...{ webkitdirectory: '' }}
            />
          </FilePicker>
        </div>
        {skipped > 0 && <p className="text-xs text-slate-500">{skipped} Dateien ohne .java werden nicht mitgeschickt.</p>}

        <FilePicker
          icon={Link2}
          title="Trace-Links"
          hint={
            <>
              Textdatei, eine Zuordnung je Zeile: <code>UC1 -&gt; Person.java</code>
            </>
          }
          summary={linkFile ? linkFile.name : null}
        >
          <input
            data-testid="file-links"
            type="file"
            accept=".txt,.csv"
            className="sr-only"
            onChange={(e) => setLinkFile(e.target.files?.[0] ?? null)}
          />
        </FilePicker>
      </div>

      <ErrorBox problems={error} />

      <div className="mt-6 flex flex-wrap gap-2">
        <button
          className="btn btn-primary"
          disabled={busy || (useCases.length === 0 && sources.length === 0 && linkFile === null)}
          onClick={submit}
        >
          {busy ? 'Importiere …' : 'Prüfen und importieren'}
        </button>
        {canCancel && (
          <button className="btn" onClick={onCancel}>
            Abbrechen
          </button>
        )}
      </div>
    </div>
  )
}
