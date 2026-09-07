from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from pydantic import JsonValue

from wallet_evals.case_sets import (
    AdaptivePreludeError,
    CaseSetError,
    DatasetAdaptiveSelector,
    DatasetCaseSource,
)
from wallet_evals.runner import (
    AdaptiveSelectionRequest,
    FixedSequenceActionPlan,
    ParticipantAction,
    ParticipantVisibleFact,
    ResponseAdaptiveActionPlan,
    StandaloneActionPlan,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
COHORT_PATH = REPOSITORY_ROOT / "data/dataset-1/harness-check-10.v1.json"


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _fixture(prelude: list[dict[str, JsonValue]] | None = None) -> dict[str, object]:
    return {
        "fixture": {
            "accounts": [
                {
                    "id": "account-cash",
                    "name": "Cash",
                    "type": "cash",
                    "currency": "ARS",
                    "opening_balance_minor": 10000,
                }
            ],
            "spending_category_paths": [],
            "income_category_paths": [],
            "transactions": [],
            "include_default_categories": True,
        },
        "prelude": [] if prelude is None else prelude,
    }


def _write_minimal_dataset(
    directory: Path,
    *,
    selected_cases: list[str] | None = None,
    fixture_cases: dict[str, object] | None = None,
    example: dict[str, object] | None = None,
) -> Path:
    case_set = directory / "case-set.json"
    selected = ["T001/E01"] if selected_cases is None else selected_cases
    fixtures = {"T001/E01": _fixture()} if fixture_cases is None else fixture_cases
    example_record = (
        {
            "id": "E01",
            "interaction_form": "standalone",
            "user_messages": ["Show my balance"],
            "focal_message_index": 0,
        }
        if example is None
        else example
    )
    _write_json(
        case_set,
        {
            "schema_version": "1.0",
            "id": "test-set",
            "description": "Test case set",
            "cases": selected,
        },
    )
    _write_json(
        directory / "wallet_user_query_dimensions_v1_1.json",
        {
            "schema_version": "1.0",
            "name": "test-dimensions",
            "purpose": "Test dimension model",
            "dimension_set_version": "v1",
            "dimensions": [],
        },
    )
    _write_json(
        directory / "wallet_v1_case_fixtures.json",
        {"schema_version": "1.0", "shared_fixture": {}, "cases": fixtures},
    )
    _write_json(
        directory / "wallet_v1_evaluation_tuples_aligned.json",
        cast(
            JsonValue,
            {
                "schema_version": "1.0",
                "dimension_set_version": "v1",
                "tuple_count": 1,
                "tuples": [
                    {
                        "id": "T001",
                        "purpose": "Test purpose",
                        "failure_surface": "Test failure",
                        "dimensions": {},
                    }
                ],
            },
        ),
    )
    _write_json(
        directory / "wallet_v1_examples_T001.json",
        {"status": "ok", "tuple_id": "T001", "examples": [example_record]},
    )
    return case_set


def test_ten_case_cohort_loads_all_supported_interaction_forms() -> None:
    source = DatasetCaseSource(COHORT_PATH)

    assert len(source.case_ids) == 10
    assert len(set(source.case_ids)) == 10
    assert isinstance(source.get("T001/E01").action_plan, StandaloneActionPlan)
    assert isinstance(source.get("T007/E01").action_plan, FixedSequenceActionPlan)
    assert isinstance(source.get("T020/E01").action_plan, ResponseAdaptiveActionPlan)


def test_missing_companion_file_is_reported_before_execution(tmp_path: Path) -> None:
    case_set = tmp_path / "case-set.json"
    _write_json(
        case_set,
        {
            "schema_version": "1.0",
            "id": "missing-companion",
            "description": "Missing companions",
            "cases": ["T001/E01"],
        },
    )

    with pytest.raises(CaseSetError, match="wallet_user_query_dimensions_v1_1.json"):
        DatasetCaseSource(case_set)


@pytest.mark.parametrize(
    ("selected_cases", "match"),
    [
        (["T001/E01", "T001/E01"], "case identities must be unique"),
        (["   "], "case identities must not be blank"),
        (["T001/E99"], "references unknown cases"),
    ],
)
def test_invalid_case_selection_is_rejected(
    tmp_path: Path, selected_cases: list[str], match: str
) -> None:
    case_set = _write_minimal_dataset(tmp_path, selected_cases=selected_cases)

    with pytest.raises(CaseSetError, match=match):
        DatasetCaseSource(case_set)


def test_malformed_example_is_rejected(tmp_path: Path) -> None:
    case_set = _write_minimal_dataset(
        tmp_path,
        example={
            "id": "E01",
            "interaction_form": "standalone",
            "user_messages": [],
            "focal_message_index": 0,
        },
    )

    with pytest.raises(CaseSetError, match="invalid examples for T001"):
        DatasetCaseSource(case_set)


def test_unknown_prelude_kind_is_rejected(tmp_path: Path) -> None:
    fixtures: dict[str, object] = {
        "T001/E01": _fixture(
            [cast(dict[str, JsonValue], {"kind": "private_state", "content": "secret"})]
        )
    }
    case_set = _write_minimal_dataset(tmp_path, fixture_cases=fixtures)

    with pytest.raises(CaseSetError, match="private_state"):
        DatasetCaseSource(case_set)


def test_adaptive_selector_uses_offered_action_then_observed_idle_state() -> None:
    selector = DatasetAdaptiveSelector()
    initial = ParticipantAction(name="message", payload="Create an account")
    available = ParticipantVisibleFact(
        name="available_actions",
        value=[
            {
                "action": "confirm",
                "expected_task_id": "task-1",
                "expected_conversation_version": 1,
                "payload": {},
            }
        ],
    )
    first = selector.select_next(
        AdaptiveSelectionRequest(
            run_id="run-1",
            case_execution_id="execution-1",
            case_id="T020/E01",
            action_history=(initial,),
            participant_visible_facts=(available,),
            role_context={},
            allowed_action_names=("message", "task_action"),
            selection_bounds={
                "required_offered_action": "confirm",
                "next_message_after_confirmation": "Now show the balance",
                "require_idle_before_next_message": True,
            },
        )
    )
    assert first is not None
    assert first.action.name == "task_action"
    assert first.based_on_facts == (available,)

    active = ParticipantVisibleFact(name="active_task", value=False)
    outcome = ParticipantVisibleFact(name="outcome_kind", value="completed")
    second = selector.select_next(
        AdaptiveSelectionRequest(
            run_id="run-1",
            case_execution_id="execution-1",
            case_id="T020/E01",
            action_history=(initial, first.action),
            participant_visible_facts=(active, outcome),
            role_context={},
            allowed_action_names=("message", "task_action"),
            selection_bounds={
                "required_offered_action": "confirm",
                "next_message_after_confirmation": "Now show the balance",
                "require_idle_before_next_message": True,
            },
        )
    )
    assert second is not None
    assert second.action == ParticipantAction(name="message", payload="Now show the balance")
    assert second.based_on_facts == (active, outcome)


def test_adaptive_selector_rejects_an_unoffered_confirmation() -> None:
    selector = DatasetAdaptiveSelector()
    request = AdaptiveSelectionRequest(
        run_id="run-1",
        case_execution_id="execution-1",
        case_id="T020/E01",
        action_history=(ParticipantAction(name="message"),),
        participant_visible_facts=(ParticipantVisibleFact(name="available_actions", value=[]),),
        role_context={},
        allowed_action_names=("message", "task_action"),
        selection_bounds={"required_offered_action": "confirm"},
    )

    with pytest.raises(AdaptivePreludeError, match="did not offer required action"):
        selector.select_next(request)


def test_adaptive_selector_stops_after_a_public_wallet_error() -> None:
    request = AdaptiveSelectionRequest(
        run_id="run-1",
        case_execution_id="execution-1",
        case_id="T020/E01",
        action_history=(ParticipantAction(name="message"),),
        participant_visible_facts=(ParticipantVisibleFact(name="http_status", value=502),),
        role_context={},
        allowed_action_names=("message", "task_action"),
        selection_bounds={"required_offered_action": "confirm"},
    )

    assert DatasetAdaptiveSelector().select_next(request) is None
