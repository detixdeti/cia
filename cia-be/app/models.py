from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Python uses snake_case, the JSON for the frontend uses camelCase."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UseCase(ApiModel):
    id: str
    title: str
    text: str


class JavaClass(ApiModel):
    id: str  # file name, e.g. "Buch.java"
    path: str  # path relative to src/, e.g. "de/hska/bib/Buch.java"


class JavaMethod(ApiModel):
    name: str
    signature: str  # e.g. "ausleihen(Mitglied, Buch)", unique within a class
    is_constructor: bool
    start_line: int  # 1-based, inclusive
    end_line: int


class JavaField(ApiModel):
    name: str  # e.g. "LEIHFRIST_TAGE"; several names if declared together ("a, b")
    declaration: str  # e.g. "private static final int LEIHFRIST_TAGE = 28;"
    start_line: int
    end_line: int


class JavaClassDetail(ApiModel):
    id: str
    path: str
    source: str
    methods: list[JavaMethod]
    fields: list[JavaField]


class CallSite(ApiModel):
    class_id: str
    method_signature: str  # enclosing method, '' outside of methods
    line_number: int
    line: str


class TraceLink(ApiModel):
    use_case_id: str
    class_id: str


class ProjectSummary(ApiModel):
    id: str
    name: str


class Project(ApiModel):
    id: str
    name: str
    use_cases: list[UseCase]
    classes: list[JavaClass]
    links: list[TraceLink]
    warnings: list[str]
    modified: bool  # True if scenarios were applied to the working copy


# --- Scenarios and impact analysis ---

# 'deactivate' | 'modify' | 'add' change a use case (candidates are classes),
# 'code' changes a class or method (candidates are use cases).
ChangeType = Literal["deactivate", "modify", "add", "code"]
Decision = Literal["open", "accepted", "rejected"]


class ScenarioCreate(ApiModel):
    change_type: ChangeType
    use_case_id: str = ""  # changed use case; for "add" the id of the new one
    new_text: str = ""  # for "modify" and "add"
    title: str = ""  # optional, a title is generated otherwise
    class_ids: list[str] = []  # for "add": the classes to analyse, chosen by the user
    class_id: str = ""  # for "code": the changed class
    method_signature: str = ""  # for "code": the changed method, "" = whole class
    new_code: str = ""  # for "code": the changed code of that method or class


class Proposal(ApiModel):
    id: int
    target: str  # method signature, or the use case id for a code change
    assessment: str  # 'modify' | 'remove' | 'add' | 'no_change' | 'unclear' | 'deviation' | 'no_deviation'
    reason: str
    requirement_reference: str
    original_code: str  # current method code, or current use case text
    proposed_code: str  # proposed method code, or proposed use case text
    reference_problem: str  # '' if the reference was checked successfully
    decision: Decision
    decided_at: str | None


class Analysis(ApiModel):
    id: int
    status: str  # 'pending' | 'running' | 'done' | 'failed'
    status_message: str
    error: str
    class_note: str
    call_sites: list[CallSite]
    model: str
    prompt_version: str
    prompt: str
    raw_answer: str
    reasoning: str
    created_at: str
    started_at: str | None
    finished_at: str | None
    proposals: list[Proposal]


class Candidate(ApiModel):
    artifact_id: str  # class id, or use case id for a code change
    analysis: Analysis | None  # the latest analysis, None if never analysed


class ScenarioSummary(ApiModel):
    id: int
    project_id: str
    title: str
    change_type: ChangeType
    use_case_id: str
    class_id: str
    method_signature: str
    created_at: str
    applied_at: str | None  # when the scenario was applied to the working copy
    status: str  # 'created' | 'running' | 'review' | 'completed' | 'applied'
    candidate_count: int
    analysed_count: int
    open_count: int  # failed or missing analyses plus undecided proposals


class ScenarioDetail(ScenarioSummary):
    original_text: str
    new_text: str
    original_code: str
    new_code: str
    candidates: list[Candidate]


class DecisionUpdate(ApiModel):
    decision: Decision
