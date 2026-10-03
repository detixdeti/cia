"""Applies a reviewed scenario to the working copy of its project.

Only what the user accepted is applied:
- use case changed: the new use case text and the accepted code proposals
- code changed: the changed code and the accepted use case texts

Changes are made by text replacement: the old code or text stored with the
scenario must still be found in the working copy. If another applied scenario
changed the same place in the meantime, nothing is written. All files are only
written when every change could be made.
"""

import re
from pathlib import Path

from app.database import connect, now
from app.models import ScenarioDetail
from app.project_loader import ensure_working_copy, read_java_classes, split_title
from app.scenarios import ScenarioError, get_scenario

CODE_CHANGES = ("modify", "remove", "add")


class ApplyError(ScenarioError):
    pass


def apply_scenario(scenario_id: int) -> None:
    scenario = get_scenario(scenario_id)
    if scenario.applied_at:
        raise ApplyError("Das Szenario wurde bereits übernommen")
    if scenario.status == "running":
        raise ApplyError("Die Analyse läuft noch")

    project_dir = ensure_working_copy(scenario.project_id)
    files = WorkingFiles(project_dir)

    if scenario.change_type == "code":
        apply_code_change(scenario, files)
        apply_accepted_use_case_texts(scenario, files)
    else:
        apply_use_case_change(scenario, files)
        apply_accepted_code_proposals(scenario, files)

    files.write_all()
    with connect() as connection:
        connection.execute("UPDATE scenarios SET applied_at = ? WHERE id = ?", (now(), scenario_id))


def reset_applied_scenarios(project_id: str) -> None:
    with connect() as connection:
        connection.execute("UPDATE scenarios SET applied_at = NULL WHERE project_id = ?", (project_id,))


class WorkingFiles:
    """Reads files of the working copy and collects the new contents until write_all()."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.changed: dict[Path, str | None] = {}  # None = delete the file

    def read(self, path: Path) -> str | None:
        if path in self.changed:
            return self.changed[path]
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def write(self, path: Path, content: str | None) -> None:
        self.changed[path] = content

    def write_all(self) -> None:
        for path, content in self.changed.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(content, encoding="utf-8")

    def class_path(self, class_id: str) -> Path:
        classes, _ = read_java_classes(self.project_dir / "src", warnings=[])
        if class_id not in classes:
            raise ApplyError(f"Klasse {class_id} existiert im Arbeitsstand nicht")
        return self.project_dir / "src" / classes[class_id].path

    def use_case_path(self, use_case_id: str) -> Path | None:
        for file in (self.project_dir / "usecases").iterdir():
            if file.stem == use_case_id and self.read(file) is not None:
                return file
        return None

    @property
    def tracelinks_path(self) -> Path:
        return self.project_dir / "tracelinks.txt"


# --- Use case changed ---


def apply_use_case_change(scenario: ScenarioDetail, files: WorkingFiles) -> None:
    use_case_id = scenario.use_case_id
    path = files.use_case_path(use_case_id)

    if scenario.change_type == "add":
        if path is not None:
            raise ApplyError(f"Use Case {use_case_id} existiert im Arbeitsstand bereits")
        files.write(files.project_dir / "usecases" / f"{use_case_id}.md", scenario.new_text.strip() + "\n")
        # The classes chosen for the analysis become the trace links of the new use case.
        links = files.read(files.tracelinks_path) or ""
        new_lines = "".join(f"{use_case_id} -> {candidate.artifact_id}\n" for candidate in scenario.candidates)
        files.write(files.tracelinks_path, links.rstrip("\n") + "\n" + new_lines)
        return

    if path is None:
        raise ApplyError(f"Use Case {use_case_id} existiert im Arbeitsstand nicht mehr")
    title, current_text = split_title(files.read(path).strip())
    if current_text.strip() != scenario.original_text.strip():
        raise ApplyError(f"{use_case_id} wurde seit dem Anlegen des Szenarios geändert")

    if scenario.change_type == "deactivate":
        files.write(path, None)
        # Without the use case its trace links would point to nothing.
        links = files.read(files.tracelinks_path) or ""
        kept = [line for line in links.split("\n") if not re.match(rf"^\s*{re.escape(use_case_id)}\s*->", line)]
        files.write(files.tracelinks_path, "\n".join(kept))
    else:
        files.write(path, use_case_file_content(path, use_case_id, title, scenario.new_text))


def apply_accepted_code_proposals(scenario: ScenarioDetail, files: WorkingFiles) -> None:
    for candidate in scenario.candidates:
        accepted = [
            proposal
            for proposal in (candidate.analysis.proposals if candidate.analysis else [])
            if proposal.decision == "accepted" and proposal.assessment in CODE_CHANGES
        ]
        if not accepted:
            continue

        path = files.class_path(candidate.artifact_id)
        source = files.read(path)
        for proposal in accepted:
            where = f"{candidate.artifact_id}: {proposal.target}"
            if proposal.reference_problem:
                raise ApplyError(
                    f"{where} kann nicht übernommen werden ({proposal.reference_problem}). Bitte verwerfen."
                )
            if proposal.assessment == "add":
                source = insert_before_class_end(source, proposal.proposed_code)
            else:
                new_code = "" if proposal.assessment == "remove" else proposal.proposed_code
                source = replace_once(source, proposal.original_code, new_code, where)
        files.write(path, source)


# --- Code changed ---


def apply_code_change(scenario: ScenarioDetail, files: WorkingFiles) -> None:
    path = files.class_path(scenario.class_id)
    source = files.read(path)
    if scenario.method_signature:
        source = replace_once(
            source, scenario.original_code, scenario.new_code, f"{scenario.class_id}: {scenario.method_signature}"
        )
    else:
        if source != scenario.original_code:
            raise ApplyError(f"{scenario.class_id} wurde seit dem Anlegen des Szenarios geändert")
        source = scenario.new_code
    files.write(path, source)


def apply_accepted_use_case_texts(scenario: ScenarioDetail, files: WorkingFiles) -> None:
    for candidate in scenario.candidates:
        for proposal in candidate.analysis.proposals if candidate.analysis else []:
            # "accepted" for a deviation means: the code change is intended, adapt the text.
            if proposal.assessment != "deviation" or proposal.decision != "accepted":
                continue
            path = files.use_case_path(proposal.target)
            if path is None:
                raise ApplyError(f"Use Case {proposal.target} existiert im Arbeitsstand nicht mehr")
            title, current_text = split_title(files.read(path).strip())
            if current_text.strip() != proposal.original_code.strip():
                raise ApplyError(f"{proposal.target} wurde seit der Analyse geändert")
            files.write(path, use_case_file_content(path, proposal.target, title, proposal.proposed_code))


# --- Text helpers ---


def use_case_file_content(path: Path, use_case_id: str, title: str, text: str) -> str:
    """Keeps the "# UC1: Title" line of Markdown use cases."""
    if path.suffix == ".md" and title:
        return f"# {use_case_id}: {title}\n\n{text.strip()}\n"
    return text.strip() + "\n"


def replace_once(source: str, old: str, new: str, where: str) -> str:
    if not old or old not in source:
        raise ApplyError(f"{where} hat sich seit der Analyse geändert und kann nicht übernommen werden")
    if not new:
        # Removing a method: also drop its line break, so no empty line is left behind.
        old_with_newline = old + "\n"
        return source.replace(old_with_newline if old_with_newline in source else old, "", 1)
    return source.replace(old, match_indentation(new, old), 1)


def match_indentation(new_code: str, old_code: str) -> str:
    """Models often return code without the indentation of the class body; add it back."""
    indent = re.match(r"[ \t]*", old_code).group()
    if not indent or new_code[:1] in (" ", "\t"):
        return new_code
    return "\n".join(indent + line if line.strip() else line for line in new_code.split("\n"))


def insert_before_class_end(source: str, code: str) -> str:
    end = source.rstrip().rfind("}")
    if end == -1:
        raise ApplyError("Ende der Klasse nicht gefunden, neue Methode kann nicht eingefügt werden")
    return source[:end].rstrip("\n") + "\n\n" + match_indentation(code.strip("\n"), "    ") + "\n" + source[end:]
