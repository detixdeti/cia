// Graphansicht (F2) mit Cytoscape.js.
//
// Regeln aus Konzept 4.8:
// - Artefakttyp und Zustand sind getrennt codiert: Akzentbalken und Fuellung
//   fuer den Typ, Rand und Beschriftung fuer den Zustand.
// - Jeder Zustand steht auch als Text im Knoten, nicht nur als Farbe.
// - Raeumliche Naehe ist kein Abhaengigkeitsnachweis. Deshalb ein festes,
//   deterministisches Layout in zwei Spalten: Use Cases links, Klassen rechts.
//   Die Knoten lassen sich nicht verschieben.

import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
import { Focus, Maximize2, ZoomIn, ZoomOut } from 'lucide-react'
import { nodeStates, orderColumns, type Highlight } from '../graphLayout'
import { currentTheme, useTheme } from '../theme'
import type { Graph, GraphNode } from '../types'

interface Props {
  graph: Graph
  /** Knoten-ID -> Markierung. */
  highlights: Record<string, Highlight>
  /** Nur diese Knoten zeigen. ``null`` zeigt alle. */
  visibleIds: Set<string> | null
  /** Die Auswahl beim Aufbau. Damit bleibt sie beim Wechsel von der Matrix erhalten. */
  initialSelection: string[]
  onSelectionChange: (ids: string[]) => void
}

/** Der Text im Knoten: Name und, falls zutreffend, Zustaende. */
function displayLabel(node: GraphNode, highlight: Highlight | undefined): string {
  const states = nodeStates(node, highlight)
  const name = node.kind === 'class' ? node.ref : node.label
  return states.length > 0 ? `${name}\n${states.join(' · ')}` : name
}

const ROW_GAP = 60
const CLASS_COLUMN_X = 470

/** Feste Positionen: zwei Spalten in der gemeinsamen Reihenfolge, optional kompakt nur fuer sichtbare Knoten. */
function place(
  graph: Graph,
  visibleIds?: Set<string> | null,
): {
  positions: Record<string, { x: number; y: number }>
  headerUc: { x: number; y: number }
  headerClass: { x: number; y: number }
  useCaseCount: number
  classCount: number
} {
  const { useCases, classes } = orderColumns(graph, visibleIds)
  const positions: Record<string, { x: number; y: number }> = {}
  const height = Math.max(useCases.length, classes.length, 1)

  useCases.forEach((n, i) => {
    positions[n.id] = { x: 0, y: (i + (height - useCases.length) / 2) * ROW_GAP }
  })
  classes.forEach((n, i) => {
    positions[n.id] = { x: CLASS_COLUMN_X, y: (i + (height - classes.length) / 2) * ROW_GAP }
  })

  // Falls Knoten ausgeblendet sind, erhalten sie eine Rueckfallposition
  graph.nodes.forEach((n) => {
    if (!positions[n.id]) {
      positions[n.id] = { x: n.kind === 'use_case' ? 0 : CLASS_COLUMN_X, y: 0 }
    }
  })

  const minUcY = useCases.length > 0 ? Math.min(...useCases.map((n) => positions[n.id].y)) : 0
  const minClsY = classes.length > 0 ? Math.min(...classes.map((n) => positions[n.id].y)) : 0

  return {
    positions,
    headerUc: { x: 0, y: minUcY - ROW_GAP * 0.85 },
    headerClass: { x: CLASS_COLUMN_X, y: minClsY - ROW_GAP * 0.85 },
    useCaseCount: useCases.length,
    classCount: classes.length,
  }
}

/** Eine weiche S-Kurve von links nach rechts: waagerecht am Start und am Ziel.
 *  Cytoscape beschreibt Kontrollpunkte als Anteil entlang der Geraden (weight)
 *  und seitlichen Abstand (distance). */
function sCurve(from: { x: number; y: number }, to: { x: number; y: number }) {
  const dx = to.x - from.x
  const dy = to.y - from.y
  const length = Math.hypot(dx, dy)
  if (length === 0 || Math.abs(dy) < 1) return null
  const distance = (dx * dy) / (2 * length)
  return {
    'curve-style': 'unbundled-bezier' as const,
    'control-point-weights': [(dx * dx) / (2 * length * length), (dx * dx + 2 * dy * dy) / (2 * length * length)],
    'control-point-distances': [-distance, distance],
  }
}

/** Setzt die Kurven aller Kanten. Muss nach jedem neuen Stylesheet wiederholt werden. */
function applyCurves(cy: cytoscape.Core): void {
  cy.edges().forEach((edge) => {
    const curve = sCurve(edge.source().position(), edge.target().position())
    if (curve !== null) edge.style(curve)
  })
}

// Farben je Thema. Es gibt bewusst kein Gruen fuer "in Ordnung" (Konzept 4.12).
const PALETTE = {
  light: {
    card: '#ffffff',
    useCase: { accent: '#6366f1', border: '#c7d2fe', text: '#1e1b4b' },
    cls: { accent: '#0ea5e9', border: '#bae6fd', text: '#082f49' },
    edge: '#a3afc0',
    edgeSelected: '#818cf8',
    focus: '#4f46e5',
    neighbor: '#4f46e5',
    candidate: '#f59e0b',
    changed: '#e11d48',
    unparsed: '#dc2626',
    unlinked: '#94a3b8',
    unlinkedText: '#475569',
    header: '#94a3b8',
    selectedBorder: '#4338ca',
    overlay: '#6366f1',
    shadow: '#0f172a',
    shadowOpacity: 0.07,
  },
  dark: {
    card: '#131e38',
    useCase: { accent: '#818cf8', border: '#39408a', text: '#e0e7ff' },
    cls: { accent: '#38bdf8', border: '#1c4f73', text: '#e0f2fe' },
    edge: '#3b4b6e',
    edgeSelected: '#818cf8',
    focus: '#a5b4fc',
    neighbor: '#818cf8',
    candidate: '#fbbf24',
    changed: '#fb7185',
    unparsed: '#f87171',
    unlinked: '#5d6d8a',
    unlinkedText: '#a3b3cb',
    header: '#6f7f9a',
    selectedBorder: '#a5b4fc',
    overlay: '#818cf8',
    shadow: '#000000',
    shadowOpacity: 0.4,
  },
}

type Palette = (typeof PALETTE)['light']

/** Ein Knoten als Karte: Grund mit farbigem Balken links. */
function card(p: Palette, kind: { accent: string; border: string; text: string }, width: number): cytoscape.Css.Node {
  return {
    shape: 'round-rectangle',
    width,
    'background-color': p.card,
    'background-fill': 'linear-gradient',
    'background-gradient-direction': 'to-right',
    'background-gradient-stop-colors': [kind.accent, kind.accent, p.card, p.card],
    'background-gradient-stop-positions': ['0%', '3%', '3%', '100%'],
    'border-color': kind.border,
    color: kind.text,
  }
}

function buildStyle(p: Palette): cytoscape.StylesheetJson {
  return [
    {
      selector: 'node',
      style: {
        label: 'data(display)',
        'font-family': 'Inter Variable, system-ui, sans-serif',
        'font-size': 12,
        'font-weight': 500,
        'line-height': 1.3,
        'text-wrap': 'wrap',
        'text-max-width': '180px',
        'text-valign': 'center',
        'text-halign': 'center',
        height: 'label',
        padding: '11px',
        'border-width': 1.5,
        // Ein weicher Schatten, damit die Karten vom Grund abheben.
        'underlay-color': p.shadow,
        'underlay-opacity': p.shadowOpacity,
        'underlay-padding': 2,
        'underlay-shape': 'round-rectangle',
        'transition-property': 'opacity',
        'transition-duration': 120,
      },
    },
    // Typ: Akzentbalken links
    { selector: 'node[kind = "use_case"]', style: card(p, p.useCase, 224) },
    { selector: 'node[kind = "class"]', style: card(p, p.cls, 204) },
    // Zustand: Rand
    { selector: 'node[!linked]', style: { 'border-style': 'dashed', 'border-color': p.unlinked, color: p.unlinkedText } },
    { selector: 'node[?unparsed]', style: { 'border-style': 'dotted', 'border-color': p.unparsed, 'border-width': 2.5 } },
    { selector: 'node.neighbor', style: { 'border-color': p.neighbor, 'border-width': 2.5, 'border-style': 'solid' } },
    { selector: 'node.candidate', style: { 'border-color': p.candidate, 'border-width': 3, 'border-style': 'solid' } },
    { selector: 'node.changed', style: { 'border-color': p.changed, 'border-width': 3, 'border-style': 'solid' } },
    {
      selector: 'node:selected',
      style: {
        'overlay-color': p.overlay,
        'overlay-opacity': 0.12,
        'overlay-padding': 6,
        'border-color': p.selectedBorder,
        'border-width': 2.5,
        'border-style': 'solid',
      },
    },
    // Spaltenueberschriften: reine Beschriftung
    {
      selector: 'node.header',
      style: {
        shape: 'rectangle',
        width: 224,
        height: 18,
        padding: '0px',
        'background-opacity': 0,
        'background-fill': 'solid',
        'border-width': 0,
        'underlay-opacity': 0,
        color: p.header,
        'font-size': 11,
        'font-weight': 700,
        'text-transform': 'uppercase',
      },
    },
    // Kanten: weiche Kurven. Die Kontrollpunkte setzt der Code je Kante.
    { selector: 'edge', style: { width: 1.5, 'line-color': p.edge, 'curve-style': 'unbundled-bezier' } },
    { selector: 'edge.sel', style: { 'line-color': p.edgeSelected, width: 2.2 } },
    // Beim Ueberfahren eines Knotens: Nachbarschaft hervorheben, den Rest abdunkeln.
    { selector: '.dim', style: { opacity: 0.2 } },
    { selector: 'edge.focus', style: { 'line-color': p.focus, width: 2.5 } },
    { selector: '.hidden', style: { display: 'none' } },
  ]
}

function legendFor(p: Palette): { label: string; accent?: string; border: string; style?: string }[] {
  return [
    { label: 'Use Case', accent: p.useCase.accent, border: p.useCase.border },
    { label: 'Klasse', accent: p.cls.accent, border: p.cls.border },
    { label: 'keine deklarierte Zuordnung (keine Entwarnung)', border: p.unlinked, style: 'dashed' },
    { label: 'nicht verarbeitet', border: p.unparsed, style: 'dotted' },
    { label: 'mit der Auswahl verknüpft', border: p.neighbor },
    { label: 'Kandidat des Szenarios', border: p.candidate },
    { label: 'im Szenario geändert', border: p.changed },
  ]
}

const FIT_PADDING = 70

export function GraphView({ graph, highlights, visibleIds, initialSelection, onSelectionChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)
  const selectionHandler = useRef(onSelectionChange)
  const initialSelectionRef = useRef(initialSelection)
  const theme = useTheme()
  const palette = PALETTE[theme]

  useEffect(() => {
    selectionHandler.current = onSelectionChange
  })

  // Den Graphen aufbauen. Bei einem anderen Ausgangsstand wird er neu gebaut.
  useEffect(() => {
    const container = containerRef.current
    if (container === null) return
    const { positions, headerUc, headerClass, useCaseCount, classCount } = place(graph, null)

    const cy = cytoscape({
      container,
      elements: [
        ...graph.nodes.map((n) => ({
          group: 'nodes' as const,
          data: {
            id: n.id,
            kind: n.kind,
            linked: n.linked,
            unparsed: n.parsed === false,
            display: displayLabel(n, undefined),
          },
          position: positions[n.id],
        })),
        // Ueberschriften ueber den Spalten
        {
          group: 'nodes' as const,
          data: { id: 'header:uc', display: `Use Cases (${useCaseCount})` },
          position: headerUc,
          classes: 'header',
          selectable: false,
          grabbable: false,
          pannable: true,
        },
        {
          group: 'nodes' as const,
          data: { id: 'header:class', display: `Klassen (${classCount})` },
          position: headerClass,
          classes: 'header',
          selectable: false,
          grabbable: false,
          pannable: true,
        },
        ...graph.edges.map((e) => ({
          group: 'edges' as const,
          data: { id: e.id, source: e.source, target: e.target },
        })),
      ],
      style: buildStyle(PALETTE[currentTheme()]),
      layout: { name: 'preset' },
      boxSelectionEnabled: true,
      // Die Anordnung hat keine Bedeutung. Deshalb lassen sich Knoten nicht verschieben.
      autoungrabify: true,
      minZoom: 0.05,
      maxZoom: 3.5,
    })

    applyCurves(cy)
    cy.fit(undefined, FIT_PADDING)

    // Die Auswahl der anderen Ansicht uebernehmen, bevor auf Aenderungen gehoert wird.
    for (const id of initialSelectionRef.current) cy.getElementById(id).select()
    cy.nodes(':selected').connectedEdges().addClass('sel')

    // Auswahl: Kanten der ausgewaehlten Knoten leicht hervorheben.
    cy.on('select unselect', () => {
      const selected = cy.nodes(':selected')
      cy.edges().removeClass('sel')
      selected.connectedEdges().addClass('sel')
      selectionHandler.current(selected.map((n) => n.id()))
    })

    // Ueberfahren: Nachbarschaft hervorheben.
    cy.on('mouseover', 'node[kind]', (event) => {
      const neighbourhood = event.target.closedNeighborhood()
      cy.elements().not(neighbourhood).not('.header').addClass('dim')
      neighbourhood.edges().addClass('focus')
      container.style.cursor = 'pointer'
    })
    cy.on('mouseout', 'node[kind]', () => {
      cy.elements().removeClass('dim focus')
      container.style.cursor = 'default'
    })

    // Doppelklick auf einen Knoten zoomt auf diesen und seine direkten Nachbarn
    cy.on('dblclick', 'node[kind]', (event) => {
      const target = event.target
      cy.fit(target.closedNeighborhood().not('.hidden'), FIT_PADDING)
    })

    // Die Schrift laedt nach; danach neu zeichnen, damit sie im Graphen erscheint.
    void document.fonts.ready.then(() => {
      if (!cy.destroyed()) cy.forceRender()
    })

    cyRef.current = cy
    // Nur im Entwicklungsbetrieb: Damit koennen Browser-Tests Knoten auswaehlen.
    if (import.meta.env.DEV) (window as unknown as { __cy?: cytoscape.Core }).__cy = cy
    return () => {
      cy.destroy()
      cyRef.current = null
    }
  }, [graph])

  // Themawechsel: neue Farben, Auswahl und Markierungen bleiben erhalten.
  useEffect(() => {
    const cy = cyRef.current
    if (cy === null) return
    cy.style(buildStyle(palette))
    applyCurves(cy)
  }, [palette])

  // Markierungen und Zustandstexte aktualisieren.
  useEffect(() => {
    const cy = cyRef.current
    if (cy === null) return
    const byId = new Map(graph.nodes.map((n) => [n.id, n]))
    cy.batch(() => {
      cy.nodes('[kind]').forEach((node) => {
        const info = byId.get(node.id())
        const highlight = highlights[node.id()]
        node.removeClass('changed candidate neighbor')
        if (highlight) node.addClass(highlight)
        if (info) node.data('display', displayLabel(info, highlight))
      })
    })
  }, [graph, highlights])

  // Nur einen Teilgraphen zeigen: Positionen dynamisch kompakt neu anordnen und Kurven anpassen.
  useEffect(() => {
    const cy = cyRef.current
    if (cy === null) return

    const { positions, headerUc, headerClass, useCaseCount, classCount } = place(graph, visibleIds)

    cy.batch(() => {
      // 1. Zustaende und Positionen fuer Knoten aktualisieren
      cy.nodes('[kind]').forEach((node) => {
        const isHidden = visibleIds !== null && !visibleIds.has(node.id())
        node.toggleClass('hidden', isHidden)
        if (!isHidden && positions[node.id()]) {
          node.position(positions[node.id()])
        }
      })

      // 2. Spaltenueberschriften anpassen & positionieren
      const ucHeader = cy.getElementById('header:uc')
      const clsHeader = cy.getElementById('header:class')
      if (ucHeader.nonempty()) {
        ucHeader.position(headerUc)
        ucHeader.data('display', `Use Cases (${useCaseCount})`)
      }
      if (clsHeader.nonempty()) {
        clsHeader.position(headerClass)
        clsHeader.data('display', `Klassen (${classCount})`)
      }

      // 3. Kanten ein-/ausblenden
      cy.edges().forEach((edge) => {
        const hide =
          visibleIds !== null && (!visibleIds.has(edge.source().id()) || !visibleIds.has(edge.target().id()))
        edge.toggleClass('hidden', hide)
      })
    })

    applyCurves(cy)
    const visibleNodes = cy.nodes().not('.hidden')
    cy.fit(visibleNodes, FIT_PADDING)
  }, [graph, visibleIds])

  function handleZoomIn() {
    const cy = cyRef.current
    if (!cy) return
    cy.zoom({ level: cy.zoom() * 1.3, position: { x: cy.width() / 2, y: cy.height() / 2 } })
  }

  function handleZoomOut() {
    const cy = cyRef.current
    if (!cy) return
    cy.zoom({ level: cy.zoom() / 1.3, position: { x: cy.width() / 2, y: cy.height() / 2 } })
  }

  function handleFit() {
    const cy = cyRef.current
    if (!cy) return
    cy.fit(cy.nodes().not('.hidden'), FIT_PADDING)
  }

  function handleFocusSelection() {
    const cy = cyRef.current
    if (!cy) return
    const sel = cy.nodes(':selected').not('.hidden')
    if (sel.nonempty()) {
      cy.fit(sel.closedNeighborhood().not('.hidden'), FIT_PADDING)
    } else {
      cy.fit(cy.nodes().not('.hidden'), FIT_PADDING)
    }
  }

  return (
    <div className="relative">
      <div
        ref={containerRef}
        data-testid="graph"
        className="h-[62vh] min-h-[480px] bg-[radial-gradient(var(--dot)_1px,transparent_1px)] [background-size:20px_20px] lg:h-[calc(100vh-15.5rem)]"
      />

      {/* Schwebende Bedienelemente fuer Zoom und Navigation */}
      <div className="glass absolute top-4 right-4 flex items-center gap-1 rounded-xl p-1 shadow-sm">
        <button
          className="btn btn-quiet btn-sm !p-1.5"
          onClick={handleZoomIn}
          title="Vergrößern"
          aria-label="Vergrößern"
        >
          <ZoomIn className="size-4" aria-hidden />
        </button>
        <button
          className="btn btn-quiet btn-sm !p-1.5"
          onClick={handleZoomOut}
          title="Verkleinern"
          aria-label="Verkleinern"
        >
          <ZoomOut className="size-4" aria-hidden />
        </button>
        <button
          className="btn btn-quiet btn-sm !p-1.5"
          onClick={handleFocusSelection}
          title="Auf Auswahl fokussieren"
          aria-label="Auf Auswahl fokussieren"
        >
          <Focus className="size-4" aria-hidden />
        </button>
        <div className="mx-0.5 h-4 w-px bg-slate-300" aria-hidden />
        <button
          className="btn btn-quiet btn-sm gap-1.5 !px-2.5 !py-1 text-xs font-medium"
          onClick={handleFit}
          title="Ansicht einpassen"
        >
          <Maximize2 className="size-3.5" aria-hidden />
          Einpassen
        </button>
      </div>

      <ul className="glass absolute inset-x-4 bottom-4 flex flex-wrap gap-x-4 gap-y-1 rounded-xl px-3.5 py-2 text-xs text-slate-600 shadow-sm">
        {legendFor(palette).map((item) => (
          <li key={item.label} className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-5 rounded-sm border-2"
              style={{
                background: palette.card,
                borderColor: item.border,
                borderStyle: item.style ?? 'solid',
                borderLeftColor: item.accent ?? item.border,
                borderLeftWidth: item.accent ? 5 : 2,
              }}
            />
            {item.label}
          </li>
        ))}
      </ul>
    </div>
  )
}
