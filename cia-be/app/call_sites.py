"""Finds places in other classes that use a given class.

A plain text search, not a real call graph: a line counts if it mentions the
class name or calls one of its methods, in a file that mentions the class at
all. It can miss usages and report false hits (common names like getId), so
it is only extra context for the model and never creates candidates.
"""

import re
from pathlib import Path

from app.java_parser import parse_methods
from app.models import CallSite, JavaClassDetail, JavaMethod
from app.project_loader import read_java_classes

# Keeps the prompt short for classes that are used everywhere, e.g. AuthDAO in iTrust
MAX_CALL_SITES = 60


def find_call_sites(project_dir: Path, target: JavaClassDetail) -> list[CallSite]:
    class_pattern = re.compile(rf"\b{re.escape(target.id.removesuffix('.java'))}\b")
    method_names = sorted({re.escape(method.name) for method in target.methods if not method.is_constructor})
    usage_pattern = class_pattern
    if method_names:
        # the class name itself, or a call like ".tageUeberfaellig("
        usage_pattern = re.compile(rf"{class_pattern.pattern}|\.\s*(?:{'|'.join(method_names)})\s*\(")

    classes, _ = read_java_classes(project_dir / "src", warnings=[])
    call_sites: list[CallSite] = []

    for other in sorted(classes.values(), key=lambda cls: cls.id):
        if other.id == target.id:
            continue
        source = (project_dir / "src" / other.path).read_text(encoding="utf-8", errors="replace")
        if not class_pattern.search(source):
            continue  # a file that never mentions the class cannot use it

        methods = parse_methods(source)
        for line_number, line in enumerate(source.split("\n"), start=1):
            stripped = line.strip()
            if stripped.startswith(("import ", "//", "*", "/*")):
                continue
            if usage_pattern.search(line):
                call_sites.append(
                    CallSite(
                        class_id=other.id,
                        method_signature=enclosing_method(methods, line_number),
                        line_number=line_number,
                        line=stripped[:200],
                    )
                )
                if len(call_sites) >= MAX_CALL_SITES:
                    return call_sites

    return call_sites


def enclosing_method(methods: list[JavaMethod], line_number: int) -> str:
    """The innermost method that contains the line, or '' for fields and declarations."""
    containing = [method for method in methods if method.start_line <= line_number <= method.end_line]
    if not containing:
        return ""
    return min(containing, key=lambda method: method.end_line - method.start_line).signature
