from __future__ import annotations

from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict, JsonValue

from wallet_evals.case_sets import DatasetBundle


class DatasetSourceNotFoundError(LookupError):
    """Raised when a requested source is not part of the validated dataset."""


class ViewerModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DatasetTotals(ViewerModel):
    dimensions: int
    tuples: int
    cases: int
    cohorts: int
    interaction_forms: dict[str, int]


class CoverageValue(ViewerModel):
    value: str
    tuple_count: int
    case_count: int


class DimensionCoverage(ViewerModel):
    dimension_id: str
    dimension_name: str
    values: tuple[CoverageValue, ...]
    omitted_tuple_count: int
    omitted_case_count: int


class DatasetTupleView(ViewerModel):
    tuple_id: str
    record: dict[str, JsonValue]
    case_ids: tuple[str, ...]


class DatasetCaseView(ViewerModel):
    case_id: str
    tuple_id: str
    example_id: str
    interaction_form: str
    example: dict[str, JsonValue]
    fixture: dict[str, JsonValue]
    prelude: tuple[dict[str, JsonValue], ...]
    cohort_ids: tuple[str, ...]


class DatasetCohortView(ViewerModel):
    cohort_id: str
    filename: str
    description: str
    case_ids: tuple[str, ...]


class DatasetSnapshot(ViewerModel):
    dataset_directory: str
    dimension_set_name: str
    dimension_set_version: str
    purpose: str
    totals: DatasetTotals
    coverage: tuple[DimensionCoverage, ...]
    dimensions: tuple[dict[str, JsonValue], ...]
    tuples: tuple[DatasetTupleView, ...]
    cases: tuple[DatasetCaseView, ...]
    cohorts: tuple[DatasetCohortView, ...]
    shared_fixture: JsonValue
    source_files: tuple[str, ...]


class LoadedDatasetSource(ViewerModel):
    filename: str
    document: dict[str, JsonValue]


class DatasetRepository:
    """Load one complete dataset and expose its joined review projection."""

    def __init__(self, directory: Path) -> None:
        self.bundle = DatasetBundle(directory)
        self.directory = self.bundle.directory
        self._snapshot = self._build_snapshot()

    def snapshot(self) -> DatasetSnapshot:
        return self._snapshot

    def load_source(self, filename: str) -> LoadedDatasetSource:
        document = self.bundle.source_documents.get(filename)
        if document is None:
            raise DatasetSourceNotFoundError(f"dataset source not found: {filename}")
        return LoadedDatasetSource(filename=filename, document=document)

    def _build_snapshot(self) -> DatasetSnapshot:
        cases_by_tuple = {
            tuple_id: tuple(f"{tuple_id}/{example_id}" for example_id in examples)
            for tuple_id, examples in self.bundle.examples_by_tuple.items()
        }
        cohorts_by_case: dict[str, list[str]] = {case_id: [] for case_id in self.bundle.case_ids}
        cohorts: list[DatasetCohortView] = []
        for cohort_id, cohort in sorted(self.bundle.cohorts.items()):
            for case_id in cohort.cases:
                cohorts_by_case[case_id].append(cohort_id)
            cohorts.append(
                DatasetCohortView(
                    cohort_id=cohort_id,
                    filename=self.bundle.cohort_filenames[cohort_id],
                    description=cohort.description,
                    case_ids=cohort.cases,
                )
            )

        interaction_forms: dict[str, int] = {}
        cases: list[DatasetCaseView] = []
        for tuple_id, examples in self.bundle.examples_by_tuple.items():
            for example_id, example in examples.items():
                case_id = f"{tuple_id}/{example_id}"
                interaction_forms[example.interaction_form] = (
                    interaction_forms.get(example.interaction_form, 0) + 1
                )
                fixture_case = self.bundle.fixture_cases[case_id]
                cases.append(
                    DatasetCaseView(
                        case_id=case_id,
                        tuple_id=tuple_id,
                        example_id=example_id,
                        interaction_form=example.interaction_form,
                        example=_json_mapping(example.model_dump(mode="json")),
                        fixture=_json_mapping(fixture_case.fixture.model_dump(mode="json")),
                        prelude=tuple(
                            _json_mapping(step.model_dump(mode="json"))
                            for step in fixture_case.prelude
                        ),
                        cohort_ids=tuple(cohorts_by_case[case_id]),
                    )
                )

        tuples = tuple(
            DatasetTupleView(
                tuple_id=tuple_id,
                record=_json_mapping(record.model_dump(mode="json")),
                case_ids=cases_by_tuple[tuple_id],
            )
            for tuple_id, record in self.bundle.tuple_records.items()
        )
        dimensions = tuple(
            _json_mapping(dimension.model_dump(mode="json"))
            for dimension in self.bundle.dimensions_document.dimensions
        )
        return DatasetSnapshot(
            dataset_directory=str(self.directory),
            dimension_set_name=self.bundle.dimensions_document.name,
            dimension_set_version=self.bundle.dimensions_document.dimension_set_version,
            purpose=self.bundle.dimensions_document.purpose,
            totals=DatasetTotals(
                dimensions=len(dimensions),
                tuples=len(tuples),
                cases=len(cases),
                cohorts=len(cohorts),
                interaction_forms=dict(sorted(interaction_forms.items())),
            ),
            coverage=self._build_coverage(cases_by_tuple),
            dimensions=dimensions,
            tuples=tuples,
            cases=tuple(cases),
            cohorts=tuple(cohorts),
            shared_fixture=self.bundle.fixtures_document.shared_fixture,
            source_files=tuple(sorted(self.bundle.source_documents)),
        )

    def _build_coverage(
        self,
        cases_by_tuple: dict[str, tuple[str, ...]],
    ) -> tuple[DimensionCoverage, ...]:
        coverage: list[DimensionCoverage] = []
        for dimension in self.bundle.dimensions_document.dimensions:
            counts = {value.value: [0, 0] for value in dimension.values}
            omitted_tuple_count = 0
            omitted_case_count = 0
            for tuple_id, tuple_record in self.bundle.tuple_records.items():
                assigned = tuple_record.dimensions.get(dimension.name)
                case_count = len(cases_by_tuple[tuple_id])
                if assigned is None:
                    omitted_tuple_count += 1
                    omitted_case_count += case_count
                    continue
                assigned_values = [assigned] if isinstance(assigned, str) else assigned
                for value in cast(list[JsonValue], assigned_values):
                    if not isinstance(value, str):
                        continue
                    counts[value][0] += 1
                    counts[value][1] += case_count
            coverage.append(
                DimensionCoverage(
                    dimension_id=dimension.id,
                    dimension_name=dimension.name,
                    values=tuple(
                        CoverageValue(
                            value=value.value,
                            tuple_count=counts[value.value][0],
                            case_count=counts[value.value][1],
                        )
                        for value in dimension.values
                    ),
                    omitted_tuple_count=omitted_tuple_count,
                    omitted_case_count=omitted_case_count,
                )
            )
        return tuple(coverage)


def _json_mapping(value: object) -> dict[str, JsonValue]:
    return cast(dict[str, JsonValue], value)


__all__ = [
    "DatasetRepository",
    "DatasetSnapshot",
    "DatasetSourceNotFoundError",
    "LoadedDatasetSource",
]
