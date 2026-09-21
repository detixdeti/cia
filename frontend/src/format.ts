// Kleine Formatierungshilfen.

import type { Signature } from './types'

/** Formatiert einen Zeitpunkt des Backends fuer die Anzeige. */
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('de-DE')
}

/** Die Kennung einer Methode, z. B. "suche(String, String)". Sie entspricht
 *  genau der Kennung, die das Backend dem Modell vorgibt. */
export function signatureText(signature: Signature): string {
  return `${signature.name}(${signature.parameter_types.join(', ')})`
}

/** Aus einer Knoten-ID wie "class:Katalog.java" die Kennung "Katalog.java". */
export function refOf(nodeId: string): string {
  return nodeId.slice(nodeId.indexOf(':') + 1)
}

export function isUseCaseNode(nodeId: string): boolean {
  return nodeId.startsWith('uc:')
}
