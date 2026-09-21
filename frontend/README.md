# Frontend

React, TypeScript, Vite und Cytoscape.js. Gestaltet mit Tailwind CSS, Icons von
lucide-react, Schriften Inter und JetBrains Mono (lokal ueber fontsource, keine
externen Anfragen). Die Oberflaeche ruft das Backend unter `VITE_API_URL` auf
(Vorgabe: `http://localhost:8000`).

    npm install
    npm run dev      # Entwicklungsserver auf http://localhost:5173
    npm run lint
    npm run build

Aufbau: `src/api.ts` (Zugriff auf das Backend), `src/types.ts` (Formen der
Antworten), `src/labels.ts` (alle Beschriftungen), `src/index.css` (Design-System:
Buttons, Karten, Badges, Hinweise) und `src/components/` (Import, Graph,
Szenarien, Analyse, Ist-Soll-Vergleich, Entscheidungen, Abdeckung).

Erscheinungsbild: hell und dunkel, umschaltbar oben rechts und standardmaessig
nach dem System. Im Dunkelmodus werden die Farbskalen zentral in `src/index.css`
gespiegelt, sodass alle Farbklassen im Markup von selbst mitkippen.

Gestaltungsregel: Keine Farbe steht allein fuer einen Zustand, und es gibt
bewusst kein Gruen fuer "in Ordnung", denn nichts gefunden zu haben ist keine
Entwarnung (Konzept 4.8 und 4.12).
