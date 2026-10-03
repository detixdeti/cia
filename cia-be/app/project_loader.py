"""Reads a project (use cases, Java files, tracelinks.txt) from disk.

The fixture folders are never changed. When the user applies a scenario, the
project is first copied into a working copy (WORKSPACE_DIR/<project>), and
from then on everything is read from that copy. Resetting deletes the copy.

Expected folder layout of a project:

    <project>/
        tracelinks.txt      one link per line: "UC1 -> Person.java", "#" starts a comment
        usecases/           one file per use case, the file name is the use case id
        src/                Java sources, the file name is the class id
"""

import os
import re
import shutil
from pathlib import Path

from app.java_parser import parse_members
from app.models import JavaClass, JavaClassDetail, Project, ProjectSummary, TraceLink, UseCase

DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"
FIXTURES_DIR = Path(os.environ.get("FIXTURES_DIR", DEFAULT_FIXTURES_DIR))
DEFAULT_WORKSPACE_DIR = Path(__file__).resolve().parents[1] / "workspaces"
WORKSPACE_DIR = Path(os.environ.get("WORKSPACE_DIR", DEFAULT_WORKSPACE_DIR))

LINK_PATTERN = re.compile(r"^(\S+)\s*->\s*(\S+)$")
MARKDOWN_TITLE_PATTERN = re.compile(r"^#\s*[^:]+:\s*(.+)$")


def list_projects() -> list[ProjectSummary]:
    projects = []
    for folder in sorted(FIXTURES_DIR.iterdir()):
        if (folder / "tracelinks.txt").is_file():
            projects.append(ProjectSummary(id=folder.name, name=folder.name))
    return projects


def find_project_dir(project_id: str) -> Path | None:
    """The folder with the current state of a project: the working copy if there
    is one, otherwise the fixture folder. None if there is no such project."""
    if project_id not in {project.id for project in list_projects()}:
        return None
    working_copy = WORKSPACE_DIR / project_id
    return working_copy if working_copy.is_dir() else FIXTURES_DIR / project_id


def ensure_working_copy(project_id: str) -> Path:
    """Copies the fixture folder on first use and returns the working copy."""
    working_copy = WORKSPACE_DIR / project_id
    if not working_copy.is_dir():
        shutil.copytree(FIXTURES_DIR / project_id, working_copy)
    return working_copy


def delete_working_copy(project_id: str) -> None:
    shutil.rmtree(WORKSPACE_DIR / project_id, ignore_errors=True)


def load_project(project_dir: Path) -> Project:
    warnings: list[str] = []

    use_cases = read_use_cases(project_dir / "usecases")
    classes, ambiguous_class_names = read_java_classes(project_dir / "src", warnings)
    links = read_trace_links(project_dir / "tracelinks.txt", use_cases, classes, ambiguous_class_names, warnings)

    return Project(
        id=project_dir.name,
        name=project_dir.name,
        use_cases=sorted(use_cases.values(), key=lambda uc: natural_sort_key(uc.id)),
        classes=sorted(classes.values(), key=lambda cls: cls.id.lower()),
        links=links,
        warnings=warnings,
        modified=project_dir.parent == WORKSPACE_DIR,
    )


def load_class_detail(project_dir: Path, class_id: str) -> JavaClassDetail | None:
    """Source code, methods and fields of one class, or None if the class id is unknown."""
    classes, _ = read_java_classes(project_dir / "src", warnings=[])
    if class_id not in classes:
        return None

    path = classes[class_id].path
    source = (project_dir / "src" / path).read_text(encoding="utf-8", errors="replace")
    methods, fields = parse_members(source)
    return JavaClassDetail(id=class_id, path=path, source=source, methods=methods, fields=fields)


def read_use_cases(usecases_dir: Path) -> dict[str, UseCase]:
    use_cases = {}
    for file in usecases_dir.iterdir():
        if file.name.startswith(".") or not file.is_file():
            continue

        use_case_id = file.stem
        text = file.read_text(encoding="utf-8", errors="replace").strip()
        title, text = split_title(text)
        use_cases[use_case_id] = UseCase(id=use_case_id, title=title, text=text)
    return use_cases


def split_title(text: str) -> tuple[str, str]:
    """Markdown use cases start with "# UC1: Title". Plain text use cases have no title."""
    first_line, _, rest = text.partition("\n")
    match = MARKDOWN_TITLE_PATTERN.match(first_line.strip())
    if match:
        return match.group(1).strip(), rest.strip()
    return "", text


def read_java_classes(src_dir: Path, warnings: list[str]) -> tuple[dict[str, JavaClass], set[str]]:
    """The file name is used as class id. If two files share a name, the id is ambiguous."""
    classes = {}
    ambiguous_names = set()

    for file in sorted(src_dir.rglob("*.java")):
        path = file.relative_to(src_dir).as_posix()
        if file.name in classes:
            ambiguous_names.add(file.name)
            warnings.append(f"Dateiname {file.name} ist nicht eindeutig ({classes[file.name].path} und {path})")
            continue
        classes[file.name] = JavaClass(id=file.name, path=path)

    return classes, ambiguous_names


def read_trace_links(
    tracelinks_file: Path,
    use_cases: dict[str, UseCase],
    classes: dict[str, JavaClass],
    ambiguous_class_names: set[str],
    warnings: list[str],
) -> list[TraceLink]:
    links = []
    seen = set()

    lines = tracelinks_file.read_text(encoding="utf-8", errors="replace").splitlines()
    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        match = LINK_PATTERN.match(line)
        if not match:
            warnings.append(f"Zeile {line_number}: Format nicht erkannt: '{line}'")
            continue

        use_case_id, class_id = match.groups()
        if use_case_id not in use_cases:
            warnings.append(f"Zeile {line_number}: Use Case {use_case_id} existiert nicht")
            continue
        if class_id in ambiguous_class_names:
            warnings.append(f"Zeile {line_number}: Klasse {class_id} ist mehrdeutig, Link ignoriert")
            continue
        if class_id not in classes:
            warnings.append(f"Zeile {line_number}: Klasse {class_id} existiert nicht")
            continue
        if (use_case_id, class_id) in seen:
            warnings.append(
                f"Zeile {line_number}: Link {use_case_id} -> {class_id} ist doppelt und wurde zusammengefasst"
            )
            continue

        seen.add((use_case_id, class_id))
        links.append(TraceLink(use_case_id=use_case_id, class_id=class_id))

    return links


def natural_sort_key(value: str) -> list:
    """Sorts "UC2" before "UC10"."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]
