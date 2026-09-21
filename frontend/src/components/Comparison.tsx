// Ist-Soll-Vergleich (F5, Konzept 4.6): der unveraenderte Ausgangstext neben dem
// Vorschlag, Unterschiede hervorgehoben.
//
// Der Vergleich ist bewusst einfach: Eine Zeile wird hervorgehoben, wenn sie im
// anderen Text nicht vorkommt. Jede hervorgehobene Zeile traegt zusaetzlich ein
// Zeichen (- oder +), damit die Kennzeichnung nicht nur an der Farbe haengt.

interface Props {
  beforeTitle: string
  afterTitle: string
  before: string
  after: string
}

function lines(text: string): string[] {
  return text.split('\n')
}

function Side({ title, text, other, mark }: { title: string; text: string; other: string; mark: '−' | '+' }) {
  const otherLines = new Set(lines(other).map((l) => l.trim()))
  return (
    <div className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-surface">
      <h5 className="border-b border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700">{title}</h5>
      <div className="max-h-72 overflow-auto py-1">
        {lines(text).map((line, i) => {
          const differs = line.trim() !== '' && !otherLines.has(line.trim())
          return (
            <div key={i} className={`diff-line ${differs ? (mark === '−' ? 'diff-removed' : 'diff-added') : ''}`}>
              <span className="diff-mark">{differs ? mark : ' '}</span>
              {line || ' '}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function Comparison({ beforeTitle, afterTitle, before, after }: Props) {
  return (
    <div data-testid="comparison" className="@container my-3">
      <div className="grid gap-3 @md:grid-cols-2">
        <Side title={beforeTitle} text={before} other={after} mark="−" />
        <Side title={afterTitle} text={after} other={before} mark="+" />
      </div>
      <p className="mt-1.5 text-xs text-slate-500">
        Hervorgehoben sind Zeilen, die im jeweils anderen Text nicht vorkommen.
      </p>
    </div>
  )
}
