from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

from wallet_evals.runner import ExecutionContext

NonEmptyString: TypeAlias = Annotated[str, Field(min_length=1)]


class WorkbenchModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvaluationBrief(WorkbenchModel):
    stakeholder: NonEmptyString
    decision_need: NonEmptyString
    uncertainty: NonEmptyString
    governing_question: NonEmptyString
    sut_boundary: NonEmptyString
    expected_behavior: tuple[NonEmptyString, ...] = Field(min_length=1)
    scope: NonEmptyString
    limitations: tuple[NonEmptyString, ...] = ()


class OutcomeSequenceCheck(WorkbenchModel):
    kind: Literal["outcome_sequence"] = "outcome_sequence"
    check_id: NonEmptyString
    description: NonEmptyString
    expected: tuple[NonEmptyString, ...] = Field(min_length=1)


class ResponseJsonEqualsCheck(WorkbenchModel):
    kind: Literal["response_json_equals"] = "response_json_equals"
    check_id: NonEmptyString
    description: NonEmptyString
    response_index: int = Field(ge=0)
    path: NonEmptyString
    expected: JsonValue

    @field_validator("path")
    @classmethod
    def path_is_json_pointer(cls, path: str) -> str:
        if path != "/" and not path.startswith("/"):
            raise ValueError("response JSON path must be a JSON Pointer")
        return path


class NoHttpErrorCheck(WorkbenchModel):
    kind: Literal["no_http_error"] = "no_http_error"
    check_id: NonEmptyString
    description: NonEmptyString


class ObservableChangeCountCheck(WorkbenchModel):
    kind: Literal["observable_change_count"] = "observable_change_count"
    check_id: NonEmptyString
    description: NonEmptyString
    expected: int = Field(ge=0)


CheckDefinition: TypeAlias = Annotated[
    OutcomeSequenceCheck | ResponseJsonEqualsCheck | NoHttpErrorCheck | ObservableChangeCountCheck,
    Field(discriminator="kind"),
]


class CaseEvaluationDefinition(WorkbenchModel):
    case_id: NonEmptyString
    criterion_id: NonEmptyString
    criterion: NonEmptyString
    checks: tuple[CheckDefinition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def check_identities_are_unique(self) -> CaseEvaluationDefinition:
        check_ids = tuple(check.check_id for check in self.checks)
        if len(check_ids) != len(set(check_ids)):
            raise ValueError("check identities must be unique within a case")
        return self


class EvaluationPlan(WorkbenchModel):
    plan_id: NonEmptyString
    title: NonEmptyString
    case_set_id: NonEmptyString
    brief: EvaluationBrief
    cases: tuple[CaseEvaluationDefinition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def case_identities_are_unique(self) -> EvaluationPlan:
        case_ids = tuple(case.case_id for case in self.cases)
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case identities must be unique within an evaluation plan")
        return self


class EvaluationPlanEnvelope(WorkbenchModel):
    schema_version: Literal["0.1"]
    evaluation_plan: EvaluationPlan


class CheckAssessment(WorkbenchModel):
    check_id: NonEmptyString
    description: NonEmptyString
    status: Literal["pass", "fail", "unable_to_judge"]
    expected: JsonValue
    observed: JsonValue
    evidence_event_orders: tuple[int, ...] = ()
    note: str | None = None


class CaseJudgment(WorkbenchModel):
    judgment_id: NonEmptyString
    case_id: NonEmptyString
    case_execution_id: NonEmptyString
    criterion_id: NonEmptyString
    criterion: NonEmptyString
    judge_id: NonEmptyString
    outcome: Literal["pass", "fail", "unable_to_judge"]
    checks: tuple[CheckAssessment, ...] = Field(min_length=1)


class EvaluationSummary(WorkbenchModel):
    case_count: int = Field(ge=1)
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    unable_to_judge: int = Field(ge=0)
    pass_rate: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def counts_cover_all_cases(self) -> EvaluationSummary:
        if self.passed + self.failed + self.unable_to_judge != self.case_count:
            raise ValueError("judgment counts must cover all evaluated cases")
        return self


class ScopedFinding(WorkbenchModel):
    answer_state: Literal["supported", "behavior_gaps_found", "insufficient_evidence"]
    governing_question: NonEmptyString
    answer: NonEmptyString
    scope: NonEmptyString
    limitations: tuple[NonEmptyString, ...]
    failed_case_ids: tuple[str, ...] = ()
    unable_case_ids: tuple[str, ...] = ()


class CompletedEvaluation(WorkbenchModel):
    evaluation_id: NonEmptyString
    created_at: NonEmptyString
    plan_source: NonEmptyString
    execution_source: NonEmptyString
    plan: EvaluationPlan
    run_id: NonEmptyString
    execution_context: ExecutionContext
    judge_id: NonEmptyString
    judgments: tuple[CaseJudgment, ...] = Field(min_length=1)
    summary: EvaluationSummary
    finding: ScopedFinding


class CompletedEvaluationEnvelope(WorkbenchModel):
    schema_version: Literal["0.1"]
    completed_evaluation: CompletedEvaluation


__all__ = [
    "CaseEvaluationDefinition",
    "CaseJudgment",
    "CheckAssessment",
    "CheckDefinition",
    "CompletedEvaluation",
    "CompletedEvaluationEnvelope",
    "EvaluationBrief",
    "EvaluationPlan",
    "EvaluationPlanEnvelope",
    "EvaluationSummary",
    "NoHttpErrorCheck",
    "ObservableChangeCountCheck",
    "OutcomeSequenceCheck",
    "ResponseJsonEqualsCheck",
    "ScopedFinding",
]
