"""Java-Parser auf Basis von tree-sitter.

Konzept Abschnitt 4.5 verlangt, aus den importierten Java-Dateien die
Methodensignaturen und die zugehoerigen Quelltextbereiche zu erschliessen.
Beide Angaben werden benoetigt, um Modellvorschlaege bestehenden Methoden
zuzuordnen und die Ausschnitte fuer den Ist-Soll-Vergleich zu bestimmen.

tree-sitter wurde gewaehlt, weil es exakte Byte- und Zeilenbereiche liefert und
auch bei syntaktisch unvollstaendigen Dateien ein Ergebnis zurueckgibt. Eine
gescheiterte Verarbeitung bleibt dabei als solche erkennbar und wird nicht in
eine leere Methodenliste umgewandelt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain.artifacts import (
    JavaClass,
    JavaMethod,
    MethodRef,
    MethodSignature,
    SourceRange,
)
from ..domain.ids import BaselineId, ClassId


class JavaParser(Protocol):
    """Schnittstelle des Parsers.

    Der Rest des Systems haengt nur von dieser Schnittstelle ab. Die Wahl der
    Bibliothek bleibt damit eine Implementierungsentscheidung.
    """

    def parse(
        self, baseline_id: BaselineId, class_id: ClassId, relative_path: str, source: str
    ) -> JavaClass: ...


@dataclass(frozen=True, slots=True)
class _RawMethod:
    name: str
    parameter_types: tuple[str, ...]
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    is_constructor: bool


class TreeSitterJavaParser:
    """Parser auf Basis von ``tree-sitter-java``."""

    def __init__(self) -> None:
        try:
            import tree_sitter_java
            from tree_sitter import Language, Parser
        except ImportError as exc:  # pragma: no cover - Abhaengigkeit fehlt
            raise RuntimeError(
                "tree-sitter und tree-sitter-java werden benoetigt. "
                "Installation: pip install tree-sitter tree-sitter-java"
            ) from exc

        self._language = Language(tree_sitter_java.language())
        self._parser = Parser(self._language)

    def parse(
        self,
        baseline_id: BaselineId,
        class_id: ClassId,
        relative_path: str,
        source: str,
    ) -> JavaClass:
        file_name = relative_path.rsplit("/", 1)[-1]
        data = source.encode("utf-8")

        try:
            tree = self._parser.parse(data)
        except Exception as exc:  # pragma: no cover - defensiv
            return JavaClass(
                id=class_id,
                baseline_id=baseline_id,
                file_name=file_name,
                relative_path=relative_path,
                source=source,
                parsed=False,
                parse_error=f"Parser hat abgebrochen: {exc}",
            )

        root = tree.root_node
        if root.has_error:
            # Konzept 4.13: Eine nicht verarbeitete Klasse muss unabhaengig vom
            # Ergebnis der uebrigen sichtbar bleiben. Die bereits erkannten
            # Methoden werden trotzdem uebernommen, der Befund aber vermerkt.
            parse_error = "Die Datei enthaelt syntaktisch nicht aufloesbare Stellen"
        else:
            parse_error = None

        raw_methods = self._collect_methods(root, data)
        methods = tuple(
            JavaMethod(
                ref=MethodRef(
                    baseline_id=baseline_id,
                    class_id=class_id,
                    signature=MethodSignature(
                        name=raw.name, parameter_types=raw.parameter_types
                    ),
                    source_range=SourceRange(
                        start_line=raw.start_line,
                        end_line=raw.end_line,
                        start_byte=raw.start_byte,
                        end_byte=raw.end_byte,
                    ),
                ),
                source=data[raw.start_byte : raw.end_byte].decode("utf-8", "replace"),
                is_constructor=raw.is_constructor,
            )
            for raw in raw_methods
        )

        return JavaClass(
            id=class_id,
            baseline_id=baseline_id,
            file_name=file_name,
            relative_path=relative_path,
            source=source,
            methods=methods,
            parsed=parse_error is None,
            parse_error=parse_error,
        )

    def _collect_methods(self, root, data: bytes) -> list[_RawMethod]:
        """Sammelt Methoden- und Konstruktordeklarationen.

        Innere Klassen werden mit durchlaufen. Ihre Methoden erscheinen in
        derselben Liste, weil die Linkgranularitaet auf Dateiebene liegt
        (Konzept 4.2).
        """
        found: list[_RawMethod] = []
        stack = [root]

        while stack:
            node = stack.pop()
            kind = node.type
            if kind in ("method_declaration", "constructor_declaration"):
                raw = self._read_declaration(node, data, kind == "constructor_declaration")
                if raw is not None:
                    found.append(raw)
            stack.extend(reversed(node.children))

        found.sort(key=lambda m: m.start_byte)
        return found

    def _read_declaration(self, node, data: bytes, is_constructor: bool) -> _RawMethod | None:
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        if name_node is None:
            return None

        name = data[name_node.start_byte : name_node.end_byte].decode("utf-8", "replace")
        parameter_types = self._read_parameter_types(params_node, data)

        return _RawMethod(
            name=name,
            parameter_types=parameter_types,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            is_constructor=is_constructor,
        )

    @staticmethod
    def _read_parameter_types(params_node, data: bytes) -> tuple[str, ...]:
        """Liest die Parametertypen einer Deklaration.

        Konzept 4.2 verlangt, ueberladene Methoden anhand von Name und
        Parametertypen zu unterscheiden. Der Typ wird so uebernommen, wie er im
        Quelltext steht; eine Aufloesung importierter Namen findet nicht statt.
        Fuer die Unterscheidung innerhalb einer Datei genuegt das.
        """
        if params_node is None:
            return ()

        types: list[str] = []
        for child in params_node.named_children:
            if child.type == "formal_parameter":
                type_node = child.child_by_field_name("type")
                if type_node is not None:
                    types.append(
                        data[type_node.start_byte : type_node.end_byte]
                        .decode("utf-8", "replace")
                        .strip()
                    )
            elif child.type == "spread_parameter":
                # Ein Varargs-Parameter. Der Typknoten ist das erste benannte
                # Kind; die Ellipse gehoert zur Signatur und bleibt erhalten.
                if child.named_children:
                    first = child.named_children[0]
                    text = (
                        data[first.start_byte : first.end_byte]
                        .decode("utf-8", "replace")
                        .strip()
                    )
                    types.append(f"{text}...")
        return tuple(types)


def class_id_for(file_name: str) -> ClassId:
    """Bildet die Klassenkennung aus dem Dateinamen.

    Konzept 4.2: Im bereitgestellten Beispielsystem reichen Dateinamen zur
    eindeutigen Identifikation aus. Die Linkdatei nennt ebenfalls Dateinamen,
    deshalb wird hier keine Paketaufloesung vorgenommen. Fuer den allgemeinen
    Fall gleichnamiger Dateien waeren weitergehende Kennungen erforderlich;
    der Import weist eine Mehrdeutigkeit als Fehler aus.
    """
    return ClassId(file_name.rsplit("/", 1)[-1])
