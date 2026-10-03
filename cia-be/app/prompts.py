"""Prompt templates for the impact analysis.

The version is stored with every analysis, so results can be traced back to
the prompt that produced them. Increase it whenever a text below changes.

Version history:
1 - requirement change, class source and other use cases of the class
2 - adds usages of the class in other classes; adds the code change direction
3 - fields (constants, attributes) can be proposed too, not only methods
"""

from app.models import CallSite

PROMPT_VERSION = "3"


# --- Use case changed -> which methods of a linked class must change? ---

REQUIREMENT_CHANGE_SYSTEM_PROMPT = """\
Du unterstützt eine Change Impact Analysis zwischen Anforderungen (Use Cases) und Java-Code.
Du erhältst einen Änderungsauftrag an einem Use Case und eine Java-Klasse, die diesem Use Case
über einen deklarierten Trace-Link zugeordnet ist. Beurteile, welche Methoden und Felder
(Attribute, Konstanten) dieser Klasse angepasst werden müssen, damit der geänderte Zielzustand
erreicht wird.

Regeln:
- Ein Trace-Link bedeutet nur, dass die Klasse geprüft werden muss. Er bedeutet nicht, dass sie geändert werden muss.
- Die weiterhin gültigen Use Cases müssen erfüllt bleiben. Entferne oder ändere kein Verhalten, das sie noch benötigen.
- Die Verwendungen der Klasse in anderen Klassen zeigen, welches Verhalten von außen noch gebraucht wird.
  Sie stammen aus einer Textsuche und können unvollständig oder ungenau sein.
- Achte besonders auf Werte im Use-Case-Text (Zahlen, Fristen, Beträge, Grenzen). Sie sind im Code
  oft als Konstanten oder Felder umgesetzt; ändert sich ein solcher Wert, schlage die Änderung des Feldes vor.
- Nenne nur Methoden und Felder, die im gegebenen Code tatsächlich vorkommen: Methoden mit exakt der
  angegebenen Signatur, Felder mit ihrem angegebenen Namen. Eine neue Methode kennzeichnest du mit "add".
- Erfinde keine Klassen, Methoden oder Bibliotheken, die im gegebenen Kontext nicht vorkommen.
- Wenn der Kontext für eine Beurteilung nicht reicht, verwende "unclear" und begründe, was fehlt.
- Antworte auf Deutsch.

Antworte ausschließlich mit einem JSON-Objekt in diesem Format, ohne weiteren Text:
{
  "class_note": "kurzer Hinweis auf Klassenebene, der keiner Methode und keinem Feld zuzuordnen ist; leer, wenn nicht nötig",
  "proposals": [
    {
      "signature": "methodenName(Typ1, Typ2) oder FELDNAME",
      "assessment": "modify | remove | add | no_change | unclear",
      "reason": "kurze fachliche Begründung",
      "requirement_reference": "die betroffene Stelle im Use-Case-Text",
      "proposed_code": "vollständiger neuer Code der Methode bzw. vollständige neue Felddeklaration; leer bei remove, no_change und unclear"
    }
  ]
}
Nenne in "proposals" alle Methoden und Felder, die du für relevant hältst. Was du nicht nennst,
gilt als nicht beurteilt.
"""

CHANGE_DESCRIPTIONS = {
    "deactivate": "Der Use Case entfällt künftig vollständig.",
    "modify": "Der Text des Use Cases wird geändert.",
    "add": "Ein neuer Use Case kommt hinzu.",
}


def build_requirement_change_prompt(
    change_type: str,
    use_case_id: str,
    original_text: str,
    new_text: str,
    class_id: str,
    source_with_line_numbers: str,
    method_signatures: list[str],
    field_declarations: list[str],
    other_use_cases: list[tuple[str, str]],
    call_sites: list[CallSite],
) -> str:
    parts = [
        "## Änderungsauftrag",
        f"Art der Änderung: {CHANGE_DESCRIPTIONS[change_type]}",
        f"Betroffener Use Case: {use_case_id}",
    ]

    if change_type != "add":
        parts += ["", "### Bisheriger Text", original_text]
    if change_type != "deactivate":
        parts += ["", "### Neuer Text", new_text]

    parts += ["", "## Weiterhin gültige Use Cases, die derselben Klasse zugeordnet sind"]
    if other_use_cases:
        for other_id, other_text in other_use_cases:
            parts += [f"### {other_id}", other_text, ""]
    else:
        parts += ["Keine."]

    parts += ["", f"## Verwendungen von {class_id} in anderen Klassen des Projekts (Textsuche)"]
    parts += format_call_sites(call_sites)

    parts += [
        "",
        f"## Zu prüfende Klasse: {class_id}",
        "Vorhandene Methoden (exakte Signaturen):",
        *[f"- {signature}" for signature in method_signatures],
        "",
        "Vorhandene Felder (Name: Deklaration):",
        *([f"- {declaration}" for declaration in field_declarations] or ["- keine"]),
        "",
        "Quelltext mit Zeilennummern:",
        "```java",
        source_with_line_numbers,
        "```",
    ]
    return "\n".join(parts)


def format_call_sites(call_sites: list[CallSite]) -> list[str]:
    if not call_sites:
        return ["Keine Fundstellen in den importierten Klassen."]
    lines = []
    for site in call_sites:
        location = f"{site.class_id}, {site.method_signature}" if site.method_signature else site.class_id
        lines.append(f"- {location}, Zeile {site.line_number}: {site.line}")
    return lines


# --- Code changed -> is a linked use case still fulfilled? ---

CODE_CHANGE_SYSTEM_PROMPT = """\
Du unterstützt eine Change Impact Analysis zwischen Java-Code und Anforderungen (Use Cases).
Du erhältst eine Codeänderung an einer Klasse und einen Use Case, der dieser Klasse über einen
deklarierten Trace-Link zugeordnet ist. Beurteile, ob der Use Case nach der Codeänderung
weiterhin so erfüllt wird, wie sein Text es beschreibt.

Regeln:
- Ausschlaggebend ist eine Änderung des Verhaltens, nicht der Umfang des Textunterschieds.
  Eine reine Umbenennung ist meist keine Abweichung, eine kleine Änderung einer Bedingung kann eine sein.
- Bei einer Abweichung schlägst du einen angepassten Use-Case-Text vor, der das neue Verhalten beschreibt.
  Der Anwender entscheidet danach, ob die Codeänderung gewollt ist oder der Code korrigiert werden muss.
- Ändere im Vorschlag nur die betroffenen Stellen und lasse den übrigen Text unverändert.
- Wenn der Kontext für eine Beurteilung nicht reicht, verwende "unclear" und begründe, was fehlt.
- Antworte auf Deutsch, außer der Use Case ist auf Englisch verfasst; dann formuliere den Textvorschlag auf Englisch.

Antworte ausschließlich mit einem JSON-Objekt in diesem Format, ohne weiteren Text:
{
  "assessment": "deviation | no_deviation | unclear",
  "reason": "kurze fachliche Begründung",
  "requirement_reference": "die betroffene Stelle im Use-Case-Text",
  "proposed_text": "vollständiger angepasster Use-Case-Text; leer bei no_deviation und unclear"
}
"""


def build_code_change_prompt(
    use_case_id: str,
    use_case_text: str,
    class_id: str,
    method_signature: str,
    original_code: str,
    new_code: str,
    class_source: str,
) -> str:
    changed = f"Methode {method_signature} in {class_id}" if method_signature else f"Klasse {class_id}"
    parts = [
        "## Codeänderung",
        f"Geändert: {changed}",
        "",
        "### Bisheriger Code",
        "```java",
        original_code,
        "```",
        "",
        "### Geänderter Code",
        "```java",
        new_code,
        "```",
        "",
        f"## Zu prüfender Use Case: {use_case_id}",
        use_case_text,
    ]
    if method_signature:
        # Only a method changed: the rest of the class helps to understand it.
        parts += ["", f"## Vollständige Klasse {class_id} vor der Änderung (Kontext)", "```java", class_source, "```"]
    return "\n".join(parts)
