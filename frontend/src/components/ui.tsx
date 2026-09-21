// Kleine wiederverwendete Bausteine. Das Aussehen steht in index.css.

import type { ReactNode } from 'react'
import { CircleX, Info, LoaderCircle, TriangleAlert } from 'lucide-react'

export type Tone = 'neutral' | 'muted' | 'info' | 'accent' | 'warn' | 'error'

/** Ein Etikett. Der Text sagt den Zustand, die Farbe unterstuetzt nur. */
export function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

type NoticeTone = 'neutral' | 'info' | 'warn' | 'error'

/** Ein Hinweiskasten mit Symbol. */
export function Notice({
  tone = 'neutral',
  children,
  className = '',
}: {
  tone?: NoticeTone
  children: ReactNode
  className?: string
}) {
  const Icon = tone === 'error' ? CircleX : tone === 'warn' ? TriangleAlert : Info
  return (
    <div className={`notice notice-${tone} ${className}`} role={tone === 'error' ? 'alert' : undefined}>
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  )
}

/** Zeigt eine oder mehrere Fehlermeldungen. Ohne Meldung erscheint nichts. */
export function ErrorBox({ problems }: { problems: string[] | string | null }) {
  if (problems === null) return null
  const list = Array.isArray(problems) ? problems : [problems]
  if (list.length === 0) return null
  return (
    <Notice tone="error" className="my-2">
      {list.length === 1 ? (
        list[0]
      ) : (
        <ul className="list-disc space-y-0.5 pl-4">
          {list.map((p, i) => (
            <li key={i}>{p}</li>
          ))}
        </ul>
      )}
    </Notice>
  )
}

export function Loading({ what = 'Lade' }: { what?: string }) {
  return (
    <p className="flex items-center gap-2 py-2 text-sm text-slate-500">
      <LoaderCircle className="size-4 animate-spin" aria-hidden />
      {what} …
    </p>
  )
}

/** Ein Abschnitt mit kleiner Ueberschrift. */
export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-6 first:mt-0">
      <h3 className="eyebrow mb-2">{title}</h3>
      {children}
    </section>
  )
}
