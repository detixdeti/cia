// Gemeinsame Logik fuer Graph und Matrix: Reihenfolge der Artefakte und die
// Texte fuer ihren Zustand. Beide Ansichten zeigen dieselbe Relation T
// (Konzept 4.3) und sollen dieselben Zustaende gleich benennen.

import type { Graph, GraphNode } from './types'

/** Markierung eines Knotens durch Auswahl oder Szenario. */
export type Highlight = 'changed' | 'candidate' | 'neighbor'

export const HIGHLIGHT_TEXT: Record<Highlight, string> = {
  changed: 'geändert',
  candidate: 'Kandidat',
  neighbor: 'verknüpft',
}

/** Die Zustaende eines Knotens als Text. Farben allein tragen keine Aussage
 *  (Konzept 4.8), und "nicht zugeordnet" ist keine Entwarnung (Konzept 4.1). */
export function nodeStates(node: GraphNode, highlight: Highlight | undefined): string[] {
  const states: string[] = []
  if (!node.linked) states.push('nicht zugeordnet')
  if (node.parsed === false) states.push('nicht verarbeitet')
  if (highlight) states.push(HIGHLIGHT_TEXT[highlight])
  return states
}

/** Natuerliche Sortierung: UC2 vor UC10. */
function byName(a: GraphNode, b: GraphNode): number {
  return a.ref.localeCompare(b.ref, undefined, { numeric: true })
}

/** Reihenfolge der Use Cases und Klassen: Use Cases nach Kennung, Klassen nach
 *  dem Mittelwert ihrer Use Cases. Das rueckt Verwandtes zusammen und spart
 *  Kreuzungen, bleibt aber reproduzierbar. */
export function orderColumns(graph: Graph): { useCases: GraphNode[]; classes: GraphNode[] } {
  const useCases = graph.nodes.filter((n) => n.kind === 'use_case').sort(byName)
  const rank = new Map(useCases.map((n, i) => [n.id, i]))

  const ranks = new Map<string, number[]>()
  for (const edge of graph.edges) {
    const list = ranks.get(edge.target) ?? []
    list.push(rank.get(edge.source) ?? 0)
    ranks.set(edge.target, list)
  }
  const mean = (id: string): number => {
    const list = ranks.get(id)
    return list && list.length > 0 ? list.reduce((a, b) => a + b, 0) / list.length : Infinity
  }
  const classes = graph.nodes
    .filter((n) => n.kind === 'class')
    .sort((a, b) => mean(a.id) - mean(b.id) || byName(a, b))

  return { useCases, classes }
}
