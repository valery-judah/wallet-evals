from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from wallet_evals.case_sets import CaseSetError
from wallet_evals.dataset_viewer.repository import (
    DatasetRepository,
    DatasetSourceNotFoundError,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIRECTORY = REPOSITORY_ROOT / "data/dataset-1"


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _account_fixture() -> dict[str, object]:
    return {
        "fixture": {
            "accounts": [
                {
                    "id": "account-main",
                    "name": "Main",
                    "type": "wallet",
                    "currency": "ARS",
                    "opening_balance_minor": 10000,
                }
            ],
            "spending_category_paths": [],
            "income_category_paths": [],
            "transactions": [],
            "include_default_categories": True,
        },
        "prelude": [],
    }


def _write_dataset(directory: Path) -> None:
    _write_json(
        directory / "wallet_user_query_dimensions_v1_1.json",
        {
            "schema_version": "1.0",
            "name": "test-dimensions",
            "purpose": "Review test coverage",
            "dimension_set_version": "v1",
            "dimensions": [
                {
                    "id": "job",
                    "name": "Job",
                    "definition": "Requested job",
                    "values": [
                        {"value": "expense", "definition": "Expense"},
                        {"value": "income", "definition": "Income"},
                        {"value": "transfer", "definition": "Transfer"},
                    ],
                },
                {
                    "id": "context",
                    "name": "Context",
                    "definition": "Context requirement",
                    "values": [
                        {"value": "self", "definition": "Self contained"},
                        {"value": "linked", "definition": "Context linked"},
                    ],
                },
            ],
        },
    )
    _write_json(
        directory / "wallet_v1_evaluation_tuples_aligned.json",
        {
            "schema_version": "1.0",
            "dimension_set_version": "v1",
            "tuple_count": 2,
            "dataset": "test",
            "tuples": [
                {
                    "id": "T001",
                    "purpose": "Exercise multi-job assignment",
                    "failure_surface": "A job could be forced",
                    "dimensions": {"Job": ["expense", "income"]},
                },
                {
                    "id": "T002",
                    "purpose": "Exercise context",
                    "failure_surface": "Context could be ignored",
                    "dimensions": {"Job": "transfer", "Context": "self"},
                },
            ],
        },
    )
    for tuple_id, message in (("T001", "Money arrived or left"), ("T002", "Move money")):
        _write_json(
            directory / f"wallet_v1_examples_{tuple_id}.json",
            {
                "status": "ok",
                "tuple_id": tuple_id,
                "examples": [
                    {
                        "id": "E01",
                        "interaction_form": "standalone",
                        "user_messages": [message],
                        "focal_message_index": 0,
                        "review_note": "Preserved extra field",
                    }
                ],
            },
        )
    _write_json(
        directory / "wallet_v1_case_fixtures.json",
        {
            "schema_version": "1.0",
            "shared_fixture": {"note": "kept separate"},
            "cases": {
                "T001/E01": _account_fixture(),
                "T002/E01": _account_fixture(),
            },
        },
    )
    _write_json(
        directory / "review-set.json",
        {
            "schema_version": "1.0",
            "id": "review-set",
            "description": "One selected case",
            "cases": ["T001/E01"],
        },
    )


def _read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def test_current_dataset_is_fully_joined_with_expected_totals() -> None:
    snapshot = DatasetRepository(DATASET_DIRECTORY).snapshot()

    assert snapshot.totals.dimensions == 8
    assert snapshot.totals.tuples == 22
    assert snapshot.totals.cases == 440
    assert snapshot.totals.cohorts == 2
    assert snapshot.totals.interaction_forms == {
        "adaptive_sequence_candidate": 20,
        "sequence": 100,
        "standalone": 320,
    }
    cohorts = {cohort.cohort_id: cohort for cohort in snapshot.cohorts}
    assert len(cohorts["harness-check-10"].case_ids) == 10
    assert len(cohorts["workbench-check-8"].case_ids) == 8


def test_coverage_counts_multi_values_omissions_zeroes_and_cohorts(tmp_path: Path) -> None:
    _write_dataset(tmp_path)

    snapshot = DatasetRepository(tmp_path).snapshot()
    job = next(item for item in snapshot.coverage if item.dimension_name == "Job")
    context = next(item for item in snapshot.coverage if item.dimension_name == "Context")

    assert [(value.value, value.tuple_count, value.case_count) for value in job.values] == [
        ("expense", 1, 1),
        ("income", 1, 1),
        ("transfer", 1, 1),
    ]
    assert [(value.value, value.tuple_count, value.case_count) for value in context.values] == [
        ("self", 1, 1),
        ("linked", 0, 0),
    ]
    assert (context.omitted_tuple_count, context.omitted_case_count) == (1, 1)
    assert snapshot.cases[0].cohort_ids == ("review-set",)
    assert snapshot.cases[0].example["review_note"] == "Preserved extra field"
    assert snapshot.shared_fixture == {"note": "kept separate"}


def test_exact_sources_are_available_only_by_discovered_filename(tmp_path: Path) -> None:
    _write_dataset(tmp_path)
    repository = DatasetRepository(tmp_path)

    source = repository.load_source("wallet_v1_examples_T001.json")

    assert source.document["tuple_id"] == "T001"
    with pytest.raises(DatasetSourceNotFoundError):
        repository.load_source("../wallet_v1_examples_T001.json")
    with pytest.raises(DatasetSourceNotFoundError):
        repository.load_source(str((tmp_path / "wallet_v1_examples_T001.json").resolve()))


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("duplicate tuple", "duplicate evaluation tuple identity"),
        ("unknown dimension", "uses unknown dimension"),
        ("unknown value", "uses unknown value"),
        ("missing example", "wallet_v1_examples_T002.json"),
        ("missing fixture", "missing fixtures for T002/E01"),
        ("invalid interaction", "invalid standalone execution declaration"),
        ("unknown cohort case", "references unknown cases"),
    ],
)
def test_invalid_cross_file_relationships_fail_startup(
    tmp_path: Path,
    mutation: str,
    match: str,
) -> None:
    _write_dataset(tmp_path)
    tuples_path = tmp_path / "wallet_v1_evaluation_tuples_aligned.json"
    fixtures_path = tmp_path / "wallet_v1_case_fixtures.json"
    examples_path = tmp_path / "wallet_v1_examples_T002.json"
    cohort_path = tmp_path / "review-set.json"

    if mutation == "duplicate tuple":
        document = _read_object(tuples_path)
        tuples = document["tuples"]
        assert isinstance(tuples, list)
        tuple_records = cast(list[object], tuples)
        tuple_records.append(
            {
                "id": "T001",
                "purpose": "Duplicate",
                "failure_surface": "Duplicate",
                "dimensions": {},
            }
        )
        _write_json(tuples_path, document)
    elif mutation == "unknown dimension":
        document = _read_object(tuples_path)
        tuples = document["tuples"]
        assert isinstance(tuples, list) and isinstance(tuples[0], dict)
        tuples[0]["dimensions"] = {"Missing": "value"}
        _write_json(tuples_path, document)
    elif mutation == "unknown value":
        document = _read_object(tuples_path)
        tuples = document["tuples"]
        assert isinstance(tuples, list) and isinstance(tuples[0], dict)
        tuples[0]["dimensions"] = {"Job": "unknown"}
        _write_json(tuples_path, document)
    elif mutation == "missing example":
        examples_path.unlink()
    elif mutation == "missing fixture":
        document = _read_object(fixtures_path)
        cases = document["cases"]
        assert isinstance(cases, dict)
        del cases["T002/E01"]
        _write_json(fixtures_path, document)
    elif mutation == "invalid interaction":
        document = _read_object(examples_path)
        examples = document["examples"]
        assert isinstance(examples, list) and isinstance(examples[0], dict)
        examples[0]["user_messages"] = ["first", "second"]
        _write_json(examples_path, document)
    else:
        document = _read_object(cohort_path)
        document["cases"] = ["T999/E01"]
        _write_json(cohort_path, document)

    with pytest.raises(CaseSetError, match=match):
        DatasetRepository(tmp_path)
