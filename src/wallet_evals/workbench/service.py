from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, TypeVar, cast
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

from wallet_evals.runner import (
    CaseTrace,
    ObservableChangeTraceEvent,
    RunResult,
    WalletResponseTraceEvent,
)
from wallet_evals.workbench.models import (
    CaseEvaluationDefinition,
    CaseJudgment,
    CheckAssessment,
    CheckDefinition,
    CompletedEvaluation,
    CompletedEvaluationEnvelope,
    EvaluationPlan,
    EvaluationPlanEnvelope,
    EvaluationSummary,
    NoHttpErrorCheck,
    OutcomeSequenceCheck,
    ResponseJsonEqualsCheck,
    ScopedFinding,
)

JUDGE_ID = "wallet-evals/deterministic-checks@0.1"
_MISSING = object()
ModelT = TypeVar("ModelT", bound=BaseModel)


class WorkbenchConfigurationError(ValueError):
    """Raised when an evaluation plan and execution cannot form one scoped investigation."""


class WorkbenchExecutionError(RuntimeError):
    """Raised when a valid completed evaluation cannot be persisted."""


class RunResultEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["0.1"]
    run_result: RunResult


@dataclass(frozen=True)
class SavedEvaluation:
    evaluation_id: str
    artifact_path: Path
    report_path: Path
    summary: EvaluationSummary
    finding: ScopedFinding


def run_workbench(plan_path: Path, execution_path: Path, output_directory: Path) -> SavedEvaluation:
    resolved_plan_path = plan_path.expanduser().resolve()
    resolved_execution_path = execution_path.expanduser().resolve()
    plan = _load_model(resolved_plan_path, EvaluationPlanEnvelope, label="evaluation plan")
    execution = _load_model(resolved_execution_path, RunResultEnvelope, label="execution result")
    completed = evaluate_execution(
        plan.evaluation_plan,
        execution.run_result,
        plan_source=str(resolved_plan_path),
        execution_source=str(resolved_execution_path),
    )
    try:
        return _save_evaluation(completed, output_directory.expanduser().resolve())
    except OSError as exc:
        raise WorkbenchExecutionError(f"cannot save completed evaluation: {exc}") from exc


def evaluate_execution(
    plan: EvaluationPlan,
    run_result: RunResult,
    *,
    plan_source: str,
    execution_source: str,
) -> CompletedEvaluation:
    _validate_scope(plan, run_result)
    traces_by_case = {trace.case_id: trace for trace in run_result.traces}
    judgments = tuple(_judge_case(case, traces_by_case[case.case_id]) for case in plan.cases)
    passed = sum(judgment.outcome == "pass" for judgment in judgments)
    failed = sum(judgment.outcome == "fail" for judgment in judgments)
    unable = sum(judgment.outcome == "unable_to_judge" for judgment in judgments)
    summary = EvaluationSummary(
        case_count=len(judgments),
        passed=passed,
        failed=failed,
        unable_to_judge=unable,
        pass_rate=passed / len(judgments),
    )
    finding = _finding(plan, summary, judgments)
    evaluation_id = f"{plan.plan_id}--{run_result.run_id}"
    return CompletedEvaluation(
        evaluation_id=evaluation_id,
        created_at=datetime.now(UTC).isoformat(),
        plan_source=plan_source,
        execution_source=execution_source,
        plan=plan,
        run_id=run_result.run_id,
        execution_context=run_result.execution_context,
        judge_id=JUDGE_ID,
        judgments=judgments,
        summary=summary,
        finding=finding,
    )


def _validate_scope(plan: EvaluationPlan, run_result: RunResult) -> None:
    recorded_case_set = run_result.execution_context.settings.get("case_set_id")
    if recorded_case_set != plan.case_set_id:
        raise WorkbenchConfigurationError(
            f"plan case set {plan.case_set_id!r} does not match execution case set "
            f"{recorded_case_set!r}"
        )
    planned_cases = tuple(case.case_id for case in plan.cases)
    executed_cases = tuple(trace.case_id for trace in run_result.traces)
    if executed_cases != planned_cases:
        raise WorkbenchConfigurationError(
            "execution cases must exactly match the evaluation plan in declared order; "
            f"planned {planned_cases!r}, executed {executed_cases!r}"
        )


def _judge_case(definition: CaseEvaluationDefinition, trace: CaseTrace) -> CaseJudgment:
    assessments = tuple(_assess(check, trace) for check in definition.checks)
    statuses = {assessment.status for assessment in assessments}
    if "fail" in statuses:
        outcome = "fail"
    elif "unable_to_judge" in statuses:
        outcome = "unable_to_judge"
    else:
        outcome = "pass"
    return CaseJudgment(
        judgment_id=f"{trace.case_execution_id}:{definition.criterion_id}:{JUDGE_ID}",
        case_id=trace.case_id,
        case_execution_id=trace.case_execution_id,
        criterion_id=definition.criterion_id,
        criterion=definition.criterion,
        judge_id=JUDGE_ID,
        outcome=outcome,
        checks=assessments,
    )


def _assess(check: CheckDefinition, trace: CaseTrace) -> CheckAssessment:
    if isinstance(check, OutcomeSequenceCheck):
        responses = _responses(trace)
        if not responses:
            return _unable(
                check,
                expected=list(check.expected),
                note="trace has no Wallet response evidence",
            )
        outcomes = tuple(_outcome_label(event.response) for event in responses)
        return _comparison(
            check,
            expected=list(check.expected),
            observed=list(outcomes),
            event_orders=tuple(event.order for event in responses),
        )
    if isinstance(check, ResponseJsonEqualsCheck):
        responses = _responses(trace)
        if check.response_index >= len(responses):
            return _unable(
                check,
                expected=check.expected,
                note=f"response index {check.response_index} is not present",
            )
        response = responses[check.response_index]
        observed = _resolve_pointer(response.response, check.path)
        if observed is _MISSING:
            return _unable(
                check,
                expected=check.expected,
                event_orders=(response.order,),
                note=f"response JSON path {check.path!r} is not present",
            )
        return _comparison(
            check,
            expected=check.expected,
            observed=cast(JsonValue, observed),
            event_orders=(response.order,),
        )
    if isinstance(check, NoHttpErrorCheck):
        responses = _responses(trace)
        if not responses:
            return _unable(
                check,
                expected="no HTTP response status of 400 or greater",
                note="trace has no Wallet response evidence",
            )
        statuses = [_http_status(event.response) for event in responses]
        observed_statuses = [status for status in statuses if status is not None]
        passed = not any(status >= 400 for status in observed_statuses)
        return CheckAssessment(
            check_id=check.check_id,
            description=check.description,
            status="pass" if passed else "fail",
            expected="no HTTP response status of 400 or greater",
            observed=cast(JsonValue, observed_statuses),
            evidence_event_orders=tuple(event.order for event in responses),
        )
    changes = tuple(
        event for event in trace.events if isinstance(event, ObservableChangeTraceEvent)
    )
    return _comparison(
        check,
        expected=check.expected,
        observed=len(changes),
        event_orders=tuple(event.order for event in changes),
    )


def _comparison(
    check: CheckDefinition,
    *,
    expected: JsonValue,
    observed: JsonValue,
    event_orders: tuple[int, ...],
) -> CheckAssessment:
    return CheckAssessment(
        check_id=check.check_id,
        description=check.description,
        status="pass" if observed == expected else "fail",
        expected=expected,
        observed=observed,
        evidence_event_orders=event_orders,
    )


def _unable(
    check: CheckDefinition,
    *,
    expected: JsonValue,
    note: str,
    event_orders: tuple[int, ...] = (),
) -> CheckAssessment:
    return CheckAssessment(
        check_id=check.check_id,
        description=check.description,
        status="unable_to_judge",
        expected=expected,
        observed=None,
        evidence_event_orders=event_orders,
        note=note,
    )


def _responses(trace: CaseTrace) -> tuple[WalletResponseTraceEvent, ...]:
    return tuple(event for event in trace.events if isinstance(event, WalletResponseTraceEvent))


def _outcome_label(response: JsonValue) -> str:
    if not isinstance(response, dict):
        return "unknown"
    outcome = response.get("outcome")
    if isinstance(outcome, dict) and isinstance(outcome.get("kind"), str):
        return cast(str, outcome["kind"])
    status = _http_status(response)
    return f"http_error:{status}" if status is not None else "unknown"


def _http_status(response: JsonValue) -> int | None:
    if not isinstance(response, dict):
        return None
    status = response.get("status_code")
    return status if isinstance(status, int) and not isinstance(status, bool) else None


def _resolve_pointer(value: JsonValue, pointer: str) -> object:
    if pointer == "":
        return value
    current: object = value
    for raw_part in pointer.split("/")[1:]:
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if part not in current:
                return _MISSING
            current = current[part]
            continue
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                return _MISSING
            if index < 0 or index >= len(current):
                return _MISSING
            current = current[index]
            continue
        return _MISSING
    return current


def _finding(
    plan: EvaluationPlan,
    summary: EvaluationSummary,
    judgments: tuple[CaseJudgment, ...],
) -> ScopedFinding:
    failed_case_ids = tuple(
        judgment.case_id for judgment in judgments if judgment.outcome == "fail"
    )
    unable_case_ids = tuple(
        judgment.case_id for judgment in judgments if judgment.outcome == "unable_to_judge"
    )
    if failed_case_ids:
        answer_state = "behavior_gaps_found"
        answer = (
            f"No. {summary.passed} of {summary.case_count} selected scenarios passed; "
            f"{summary.failed} exposed behavior gaps and {summary.unable_to_judge} could not be "
            "judged from the captured evidence."
        )
    elif unable_case_ids:
        answer_state = "insufficient_evidence"
        answer = (
            f"The question cannot be answered completely: {summary.passed} of "
            f"{summary.case_count} selected scenarios passed and {summary.unable_to_judge} "
            "could not be judged from the captured evidence."
        )
    else:
        answer_state = "supported"
        answer = f"Yes, within this scope: all {summary.case_count} selected scenarios passed."
    return ScopedFinding(
        answer_state=answer_state,
        governing_question=plan.brief.governing_question,
        answer=answer,
        scope=plan.brief.scope,
        limitations=plan.brief.limitations,
        failed_case_ids=failed_case_ids,
        unable_case_ids=unable_case_ids,
    )


def _load_model(path: Path, model: type[ModelT], *, label: str) -> ModelT:
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkbenchConfigurationError(f"{label} does not exist: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkbenchConfigurationError(f"cannot read {label} {path}: {exc}") from exc
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise WorkbenchConfigurationError(f"invalid {label} {path}: {exc}") from exc


def _save_evaluation(completed: CompletedEvaluation, directory: Path) -> SavedEvaluation:
    directory.mkdir(parents=True, exist_ok=True)
    stem = quote(completed.evaluation_id, safe="-")
    artifact_path = directory / f"{stem}.evaluation.json"
    report_path = directory / f"{stem}.md"
    if artifact_path.exists() or report_path.exists():
        raise WorkbenchConfigurationError(
            f"completed evaluation already exists for this plan and run: {artifact_path}"
        )
    envelope = CompletedEvaluationEnvelope(schema_version="0.1", completed_evaluation=completed)
    _atomic_write(
        artifact_path,
        json.dumps(envelope.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
    )
    try:
        _atomic_write(report_path, _render_report(completed))
    except Exception:
        artifact_path.unlink(missing_ok=True)
        raise
    return SavedEvaluation(
        evaluation_id=completed.evaluation_id,
        artifact_path=artifact_path,
        report_path=report_path,
        summary=completed.summary,
        finding=completed.finding,
    )


def _atomic_write(destination: Path, content: str) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.link(temporary_path, destination)
        temporary_path.unlink()
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _render_report(completed: CompletedEvaluation) -> str:
    summary = completed.summary
    lines = [
        f"# {completed.plan.title}",
        "",
        f"Evaluation ID: `{completed.evaluation_id}`  ",
        f"Execution run: `{completed.run_id}`  ",
        f"Judge: `{completed.judge_id}`",
        "",
        "## Evaluation brief",
        "",
        f"**Stakeholder:** {completed.plan.brief.stakeholder}",
        "",
        f"**Decision need:** {completed.plan.brief.decision_need}",
        "",
        f"**Uncertainty:** {completed.plan.brief.uncertainty}",
        "",
        f"**Governing question:** {completed.plan.brief.governing_question}",
        "",
        f"**SUT boundary:** {completed.plan.brief.sut_boundary}",
        "",
        f"**Scope:** {completed.plan.brief.scope}",
        "",
        "## Result",
        "",
        f"{summary.passed}/{summary.case_count} passed, {summary.failed} failed, "
        f"and {summary.unable_to_judge} were unable to judge "
        f"({summary.pass_rate:.1%} pass rate).",
        "",
        f"**Scoped answer:** {completed.finding.answer}",
        "",
        "## Case judgments",
        "",
    ]
    for judgment in completed.judgments:
        lines.extend(
            [
                f"### {judgment.case_id}: {judgment.outcome.replace('_', ' ')}",
                "",
                f"Criterion: {judgment.criterion}",
                "",
            ]
        )
        for check in judgment.checks:
            evidence = ", ".join(str(order) for order in check.evidence_event_orders) or "none"
            lines.extend(
                [
                    f"- **{check.status.replace('_', ' ')} — {check.description}.** "
                    f"Expected `{_compact(check.expected)}`; observed "
                    f"`{_compact(check.observed)}`. Trace event order(s): {evidence}."
                    + (f" {check.note}" if check.note else ""),
                    "",
                ]
            )
    lines.extend(["## Limitations", ""])
    if completed.finding.limitations:
        for limitation in completed.finding.limitations:
            lines.extend([f"- {limitation}", ""])
    else:
        lines.extend(["- None recorded.", ""])
    lines.extend(
        [
            "## Sources",
            "",
            f"- Evaluation plan: `{completed.plan_source}`",
            "",
            f"- Execution evidence: `{completed.execution_source}`",
            "",
        ]
    )
    return "\n".join(lines)


def _compact(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


__all__ = [
    "JUDGE_ID",
    "SavedEvaluation",
    "WorkbenchConfigurationError",
    "WorkbenchExecutionError",
    "evaluate_execution",
    "run_workbench",
]
