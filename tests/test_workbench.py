from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from pydantic import JsonValue

from wallet_evals.case_sets import DatasetCaseSource
from wallet_evals.runner import (
    CaseTrace,
    ExecutionContext,
    ObservableChangeTraceEvent,
    RunResult,
    WalletResponseTraceEvent,
)
from wallet_evals.workbench import WorkbenchConfigurationError, evaluate_execution, run_workbench
from wallet_evals.workbench.models import (
    CaseEvaluationDefinition,
    EvaluationBrief,
    EvaluationPlan,
    EvaluationPlanEnvelope,
    NoHttpErrorCheck,
    ObservableChangeCountCheck,
    OutcomeSequenceCheck,
    ResponseJsonEqualsCheck,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _context(case_set_id: str = "cohort-a") -> ExecutionContext:
    return ExecutionContext(
        wallet="wallet@revision",
        model="model-a",
        environment="test",
        settings={"case_set_id": case_set_id},
    )


def _trace(
    case_id: str,
    outcome: str,
    *,
    amount_minor: int = 100,
    http_status: int | None = None,
    changed: bool = False,
) -> CaseTrace:
    if http_status is None:
        response = cast(
            JsonValue,
            {
                "outcome": {
                    "kind": outcome,
                    "view": {"data": {"candidate": {"amount_minor": amount_minor}}},
                }
            },
        )
    else:
        response = cast(
            JsonValue,
            {"status_code": http_status, "body": {"detail": "failure"}},
        )
    response_event = WalletResponseTraceEvent(order=1, response=response)
    if changed:
        events = (
            response_event,
            ObservableChangeTraceEvent(
                order=2,
                subject="wallet_ledger",
                capture_point="after_action_1",
                value={"changed": True},
            ),
        )
    else:
        events = (response_event,)
    return CaseTrace(
        run_id="run-a",
        case_execution_id=f"execution-{case_id}",
        case_id=case_id,
        execution_context=_context(),
        events=events,
    )


def _definition(case_id: str, expected_outcome: str = "preview") -> CaseEvaluationDefinition:
    return CaseEvaluationDefinition(
        case_id=case_id,
        criterion_id=f"criterion-{case_id}",
        criterion="The observable response satisfies the declared scenario expectation.",
        checks=(
            NoHttpErrorCheck(
                check_id="no-error",
                description="There is no public HTTP error",
            ),
            OutcomeSequenceCheck(
                check_id="outcome",
                description="The response has the expected outcome",
                expected=(expected_outcome,),
            ),
            ResponseJsonEqualsCheck(
                check_id="amount",
                description="The structured candidate preserves the amount",
                response_index=0,
                path="/outcome/view/data/candidate/amount_minor",
                expected=100,
            ),
            ObservableChangeCountCheck(
                check_id="change-count",
                description="No effect occurs before confirmation",
                expected=0,
            ),
        ),
    )


def _plan(*definitions: CaseEvaluationDefinition, case_set_id: str = "cohort-a") -> EvaluationPlan:
    return EvaluationPlan(
        plan_id="plan-a",
        title="Small workbench evaluation",
        case_set_id=case_set_id,
        brief=EvaluationBrief(
            stakeholder="Product team",
            decision_need="Choose what to investigate next.",
            uncertainty="Behavior may not satisfy the selected scenarios.",
            governing_question="Does the behavior satisfy the selected scenarios?",
            sut_boundary="Wallet Assistant control and capability layer.",
            expected_behavior=("Selected requests produce the declared outcomes.",),
            scope="The exact synthetic cases and execution configuration in this artifact.",
            limitations=("This is not a representative sample.",),
        ),
        cases=definitions,
    )


def _run(*traces: CaseTrace, case_set_id: str = "cohort-a") -> RunResult:
    context = _context(case_set_id)
    normalized = tuple(trace.model_copy(update={"execution_context": context}) for trace in traces)
    return RunResult(run_id="run-a", execution_context=context, traces=normalized)


def test_shipped_workbench_plan_exactly_matches_shipped_scenario_cohort() -> None:
    plan = EvaluationPlanEnvelope.model_validate_json(
        (REPOSITORY_ROOT / "data/evaluation-plans/workbench-check-8.plan.v1.json").read_text(
            encoding="utf-8"
        )
    ).evaluation_plan
    source = DatasetCaseSource(REPOSITORY_ROOT / "data/dataset-1/workbench-check-8.v1.json")

    assert plan.case_set_id == source.case_set_id
    assert tuple(case.case_id for case in plan.cases) == source.case_ids
    assert len(plan.cases) == 8


def test_workbench_produces_case_judgments_summary_and_scoped_finding() -> None:
    plan = _plan(_definition("case-pass"), _definition("case-fail", "question"))
    execution = _run(_trace("case-pass", "preview"), _trace("case-fail", "preview"))

    completed = evaluate_execution(
        plan,
        execution,
        plan_source="plan.json",
        execution_source="run.json",
    )

    assert [judgment.outcome for judgment in completed.judgments] == ["pass", "fail"]
    assert completed.summary.model_dump() == {
        "case_count": 2,
        "passed": 1,
        "failed": 1,
        "unable_to_judge": 0,
        "pass_rate": 0.5,
    }
    assert completed.finding.answer_state == "behavior_gaps_found"
    assert completed.finding.failed_case_ids == ("case-fail",)
    failed_check = completed.judgments[1].checks[1]
    assert failed_check.status == "fail"
    assert failed_check.evidence_event_orders == (1,)


def test_missing_required_evidence_is_unable_to_judge() -> None:
    definition = _definition("case-a").model_copy(
        update={
            "checks": (
                ResponseJsonEqualsCheck(
                    check_id="missing",
                    description="A required field is available",
                    response_index=0,
                    path="/outcome/not-present",
                    expected="value",
                ),
            )
        }
    )

    completed = evaluate_execution(
        _plan(definition),
        _run(_trace("case-a", "preview")),
        plan_source="plan.json",
        execution_source="run.json",
    )

    assert completed.judgments[0].outcome == "unable_to_judge"
    assert completed.judgments[0].checks[0].note == (
        "response JSON path '/outcome/not-present' is not present"
    )
    assert completed.finding.answer_state == "insufficient_evidence"


def test_absent_wallet_response_cannot_pass_response_checks() -> None:
    definition = _definition("case-a").model_copy(
        update={"checks": _definition("case-a").checks[:2]}
    )
    trace = CaseTrace(
        run_id="run-a",
        case_execution_id="execution-case-a",
        case_id="case-a",
        execution_context=_context(),
        events=(
            ObservableChangeTraceEvent(
                order=1,
                subject="wallet_ledger",
                capture_point="bootstrap",
                value={},
            ),
        ),
    )

    completed = evaluate_execution(
        _plan(definition),
        _run(trace),
        plan_source="plan.json",
        execution_source="run.json",
    )

    assert completed.judgments[0].outcome == "unable_to_judge"
    assert [check.status for check in completed.judgments[0].checks] == [
        "unable_to_judge",
        "unable_to_judge",
    ]


def test_http_failure_is_behavioral_evidence_and_a_failed_judgment() -> None:
    completed = evaluate_execution(
        _plan(_definition("case-a", "question")),
        _run(_trace("case-a", "unknown", http_status=502)),
        plan_source="plan.json",
        execution_source="run.json",
    )

    judgment = completed.judgments[0]
    assert judgment.outcome == "fail"
    assert judgment.checks[0].observed == [502]
    assert judgment.checks[1].observed == ["http_error:502"]
    assert judgment.checks[2].status == "unable_to_judge"


@pytest.mark.parametrize(
    ("plan", "execution", "message"),
    [
        (
            _plan(_definition("case-a"), case_set_id="other-cohort"),
            _run(_trace("case-a", "preview")),
            "does not match execution case set",
        ),
        (
            _plan(_definition("case-a")),
            _run(_trace("different-case", "preview")),
            "must exactly match",
        ),
    ],
)
def test_plan_scope_must_match_execution_exactly(
    plan: EvaluationPlan,
    execution: RunResult,
    message: str,
) -> None:
    with pytest.raises(WorkbenchConfigurationError, match=message):
        evaluate_execution(
            plan,
            execution,
            plan_source="plan.json",
            execution_source="run.json",
        )


def test_file_workbench_saves_immutable_json_and_readable_report(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    execution_path = tmp_path / "run.json"
    output_directory = tmp_path / "evaluations"
    plan = _plan(_definition("case-a"))
    execution = _run(_trace("case-a", "preview"))
    plan_path.write_text(
        json.dumps(
            EvaluationPlanEnvelope(schema_version="0.1", evaluation_plan=plan).model_dump(
                mode="json"
            )
        ),
        encoding="utf-8",
    )
    execution_path.write_text(
        json.dumps({"schema_version": "0.1", "run_result": execution.model_dump(mode="json")}),
        encoding="utf-8",
    )

    saved = run_workbench(plan_path, execution_path, output_directory)

    assert saved.artifact_path.is_file()
    assert saved.report_path.is_file()
    artifact = json.loads(saved.artifact_path.read_text(encoding="utf-8"))
    assert artifact["completed_evaluation"]["finding"]["answer_state"] == "supported"
    report = saved.report_path.read_text(encoding="utf-8")
    assert "# Small workbench evaluation" in report
    assert "1/1 passed" in report
    assert "Trace event order(s): 1" in report
    with pytest.raises(WorkbenchConfigurationError, match="already exists"):
        run_workbench(plan_path, execution_path, output_directory)
