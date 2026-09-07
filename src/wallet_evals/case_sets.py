from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal, TypeAlias, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError, field_validator

from wallet_evals.runner import (
    AdaptiveChoice,
    AdaptiveSelectionRequest,
    CaseDefinition,
    FixedSequenceActionPlan,
    ParticipantAction,
    ParticipantVisibleFact,
    ResponseAdaptiveActionPlan,
    StandaloneActionPlan,
)

NonEmptyString: TypeAlias = Annotated[str, Field(min_length=1)]
RecordT = TypeVar("RecordT", bound="DimensionRecord | TupleRecord | ExampleRecord")
ModelT = TypeVar("ModelT", bound=BaseModel)

FIXTURES_FILENAME = "wallet_v1_case_fixtures.json"
TUPLES_FILENAME = "wallet_v1_evaluation_tuples_aligned.json"
DIMENSIONS_FILENAME = "wallet_user_query_dimensions_v1_1.json"
EXAMPLES_FILENAME_TEMPLATE = "wallet_v1_examples_{tuple_id}.json"


class CaseSetError(ValueError):
    """Raised when a case set or one of its companion files is invalid."""


class AdaptivePreludeError(RuntimeError):
    """Raised when Wallet does not expose the facts required by a declared prelude."""


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CaseSetDocument(InputModel):
    schema_version: Literal["1.0"]
    id: NonEmptyString
    description: NonEmptyString
    cases: tuple[NonEmptyString, ...] = Field(min_length=1)

    @field_validator("cases")
    @classmethod
    def cases_are_unique(cls, cases: tuple[str, ...]) -> tuple[str, ...]:
        if any(not case_id.strip() for case_id in cases):
            raise ValueError("case identities must not be blank")
        if len(cases) != len(set(cases)):
            raise ValueError("case identities must be unique")
        return cases


class WalletFixtureAccount(InputModel):
    id: NonEmptyString
    name: NonEmptyString
    type: Literal["cash", "debit_card", "credit_card", "bank_account", "wallet"]
    currency: NonEmptyString
    opening_balance_minor: int


class WalletFixture(InputModel):
    accounts: tuple[WalletFixtureAccount, ...]
    spending_category_paths: tuple[str, ...]
    income_category_paths: tuple[str, ...]
    transactions: tuple[JsonValue, ...]
    include_default_categories: bool

    @field_validator("include_default_categories")
    @classmethod
    def default_categories_are_required(cls, enabled: bool) -> bool:
        if not enabled:
            raise ValueError("the local Wallet adapter requires default categories")
        return enabled

    @field_validator("spending_category_paths", "income_category_paths", "transactions")
    @classmethod
    def unsupported_fixture_collections_are_empty(
        cls, values: tuple[JsonValue, ...]
    ) -> tuple[JsonValue, ...]:
        if values:
            raise ValueError("the local Wallet adapter does not support this fixture content yet")
        return values


class MessagePrelude(InputModel):
    kind: Literal["message"]
    content: NonEmptyString


class OfferedActionPrelude(InputModel):
    kind: Literal["offered_action"]
    action: NonEmptyString


class AssertIdlePrelude(InputModel):
    kind: Literal["assert_idle"]


PreludeStep: TypeAlias = Annotated[
    MessagePrelude | OfferedActionPrelude | AssertIdlePrelude,
    Field(discriminator="kind"),
]


class FixtureCase(InputModel):
    fixture: WalletFixture
    prelude: tuple[PreludeStep, ...]


class FixturesDocument(InputModel):
    schema_version: Literal["1.0"]
    shared_fixture: JsonValue
    cases: dict[str, FixtureCase]


class DimensionValueRecord(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    value: NonEmptyString


class DimensionRecord(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    id: NonEmptyString
    name: NonEmptyString
    values: tuple[DimensionValueRecord, ...]


class DimensionsDocument(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    schema_version: Literal["1.0"]
    name: NonEmptyString
    purpose: NonEmptyString
    dimension_set_version: NonEmptyString
    dimensions: tuple[DimensionRecord, ...]


class TupleRecord(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    id: NonEmptyString
    purpose: NonEmptyString
    failure_surface: NonEmptyString
    dimensions: dict[str, JsonValue]


class TuplesDocument(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    schema_version: Literal["1.0"]
    dimension_set_version: NonEmptyString
    tuple_count: int = Field(ge=0)
    tuples: tuple[TupleRecord, ...]


class ExampleRecord(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    id: NonEmptyString
    interaction_form: Literal["standalone", "sequence", "adaptive_sequence_candidate"]
    user_messages: tuple[NonEmptyString, ...] = Field(min_length=1)
    focal_message_index: int | None


class ExamplesDocument(InputModel):
    status: Literal["ok"]
    tuple_id: NonEmptyString
    examples: tuple[ExampleRecord, ...]


class DatasetBundle:
    """A fully validated and joined current-layout evaluation dataset."""

    directory: Path
    dimensions_document: DimensionsDocument
    tuples_document: TuplesDocument
    fixtures_document: FixturesDocument
    tuple_records: dict[str, TupleRecord]
    example_documents: dict[str, ExamplesDocument]
    examples_by_tuple: dict[str, dict[str, ExampleRecord]]
    fixture_cases: dict[str, FixtureCase]
    case_definitions: dict[str, CaseDefinition]
    cohorts: dict[str, CaseSetDocument]
    cohort_filenames: dict[str, str]
    source_documents: dict[str, dict[str, JsonValue]]

    def __init__(self, directory: Path) -> None:
        self.directory = directory.expanduser().resolve()
        if not self.directory.is_dir():
            raise CaseSetError(
                f"dataset directory does not exist or is not a directory: {self.directory}"
            )

        self.source_documents = {}
        self.dimensions_document = self._load_source(
            DIMENSIONS_FILENAME,
            DimensionsDocument,
            label="query dimensions",
        )
        self.tuples_document = self._load_source(
            TUPLES_FILENAME,
            TuplesDocument,
            label="evaluation tuples",
        )
        self.fixtures_document = self._load_source(
            FIXTURES_FILENAME,
            FixturesDocument,
            label="case fixtures",
        )

        self._validate_dimensions()
        self.tuple_records = _unique_by_id(
            self.tuples_document.tuples,
            label="evaluation tuple",
        )
        if self.tuples_document.tuple_count != len(self.tuple_records):
            raise CaseSetError(
                f"invalid evaluation tuples file {self.directory / TUPLES_FILENAME}: "
                f"tuple_count declares {self.tuples_document.tuple_count}, "
                f"but {len(self.tuple_records)} tuples are present"
            )
        self._validate_tuple_dimensions()

        self.example_documents = {}
        self.examples_by_tuple = {}
        for tuple_id in self.tuple_records:
            filename = EXAMPLES_FILENAME_TEMPLATE.format(tuple_id=tuple_id)
            examples_document = self._load_source(
                filename,
                ExamplesDocument,
                label=f"examples for {tuple_id}",
            )
            if examples_document.tuple_id != tuple_id:
                raise CaseSetError(
                    f"example file {filename} declares tuple {examples_document.tuple_id}, "
                    f"expected {tuple_id}"
                )
            self.example_documents[tuple_id] = examples_document
            self.examples_by_tuple[tuple_id] = _unique_by_id(
                examples_document.examples,
                label=f"example for {tuple_id}",
            )
        self._reject_orphan_example_files()

        expected_case_ids = {
            f"{tuple_id}/{example_id}"
            for tuple_id, examples in self.examples_by_tuple.items()
            for example_id in examples
        }
        fixture_case_ids = set(self.fixtures_document.cases)
        missing_fixtures = sorted(expected_case_ids - fixture_case_ids)
        orphan_fixtures = sorted(fixture_case_ids - expected_case_ids)
        if missing_fixtures:
            raise CaseSetError(
                f"invalid case fixtures file {self.directory / FIXTURES_FILENAME}: "
                f"missing fixtures for {', '.join(missing_fixtures)}"
            )
        if orphan_fixtures:
            raise CaseSetError(
                f"invalid case fixtures file {self.directory / FIXTURES_FILENAME}: "
                f"orphan fixtures for {', '.join(orphan_fixtures)}"
            )
        self.fixture_cases = self.fixtures_document.cases

        self.case_definitions = {}
        for tuple_id, examples in self.examples_by_tuple.items():
            tuple_record = self.tuple_records[tuple_id]
            for example_id, example in examples.items():
                case_id = f"{tuple_id}/{example_id}"
                self.case_definitions[case_id] = _build_case(
                    case_id,
                    self.fixture_cases[case_id],
                    tuple_record,
                    example,
                )

        self.cohorts = {}
        self.cohort_filenames = {}
        self._load_cohorts()

    @property
    def case_ids(self) -> tuple[str, ...]:
        return tuple(self.case_definitions)

    def get(self, case_id: str) -> CaseDefinition:
        try:
            return self.case_definitions[case_id]
        except KeyError as exc:
            raise CaseSetError(f"dataset has no case: {case_id}") from exc

    def _load_source(
        self,
        filename: str,
        model: type[ModelT],
        *,
        label: str,
    ) -> ModelT:
        path = self.directory / filename
        payload = _load_json_object(path, label=label)
        try:
            document = model.model_validate(payload)
        except ValidationError as exc:
            raise CaseSetError(f"invalid {label} file {path}: {exc}") from exc
        self.source_documents[filename] = payload
        return document

    def _validate_dimensions(self) -> None:
        dimensions = _unique_by_id(
            self.dimensions_document.dimensions,
            label="query dimension",
        )
        names: set[str] = set()
        for dimension in dimensions.values():
            if dimension.name in names:
                raise CaseSetError(f"duplicate query dimension name: {dimension.name}")
            names.add(dimension.name)
            values: set[str] = set()
            for value in dimension.values:
                if value.value in values:
                    raise CaseSetError(
                        f"duplicate value {value.value!r} in query dimension {dimension.name}"
                    )
                values.add(value.value)

    def _validate_tuple_dimensions(self) -> None:
        if (
            self.tuples_document.dimension_set_version
            != self.dimensions_document.dimension_set_version
        ):
            raise CaseSetError(
                "evaluation tuple dimension_set_version does not match query dimensions: "
                f"{self.tuples_document.dimension_set_version!r} != "
                f"{self.dimensions_document.dimension_set_version!r}"
            )
        dimensions_by_name = {
            dimension.name: dimension for dimension in self.dimensions_document.dimensions
        }
        for tuple_record in self.tuples_document.tuples:
            for dimension_name, assigned in tuple_record.dimensions.items():
                dimension = dimensions_by_name.get(dimension_name)
                if dimension is None:
                    raise CaseSetError(
                        f"tuple {tuple_record.id} uses unknown dimension {dimension_name!r}"
                    )
                assigned_values: list[str]
                if isinstance(assigned, str):
                    assigned_values = [assigned]
                elif isinstance(assigned, list) and all(isinstance(item, str) for item in assigned):
                    assigned_values = cast(list[str], assigned)
                else:
                    raise CaseSetError(
                        f"tuple {tuple_record.id} dimension {dimension_name!r} "
                        "must be a string or array of strings"
                    )
                if not assigned_values:
                    raise CaseSetError(
                        f"tuple {tuple_record.id} dimension {dimension_name!r} has no values"
                    )
                if len(assigned_values) != len(set(assigned_values)):
                    raise CaseSetError(
                        f"tuple {tuple_record.id} dimension {dimension_name!r} "
                        "contains duplicate values"
                    )
                allowed = {value.value for value in dimension.values}
                unknown = sorted(set(assigned_values) - allowed)
                if unknown:
                    raise CaseSetError(
                        f"tuple {tuple_record.id} dimension {dimension_name!r} uses "
                        f"unknown value(s): {', '.join(unknown)}"
                    )

    def _reject_orphan_example_files(self) -> None:
        expected = {
            EXAMPLES_FILENAME_TEMPLATE.format(tuple_id=tuple_id) for tuple_id in self.tuple_records
        }
        discovered = {path.name for path in self.directory.glob("wallet_v1_examples_*.json")}
        orphaned = sorted(discovered - expected)
        if orphaned:
            raise CaseSetError(f"orphan example files: {', '.join(orphaned)}")

    def _load_cohorts(self) -> None:
        reserved = set(self.source_documents)
        for path in sorted(self.directory.glob("*.json")):
            if path.name in reserved:
                continue
            payload = _load_json_object(path, label="dataset JSON")
            try:
                cohort = CaseSetDocument.model_validate(payload)
            except ValidationError as exc:
                raise CaseSetError(f"invalid case set file {path}: {exc}") from exc
            if cohort.id in self.cohorts:
                raise CaseSetError(f"duplicate case-set identity: {cohort.id}")
            unknown_cases = sorted(set(cohort.cases) - set(self.case_definitions))
            if unknown_cases:
                raise CaseSetError(
                    f"case set {cohort.id} references unknown cases: {', '.join(unknown_cases)}"
                )
            self.cohorts[cohort.id] = cohort
            self.cohort_filenames[cohort.id] = path.name
            self.source_documents[path.name] = payload


class DatasetCaseSource:
    """Resolve selected cases from a case set and its co-located dataset files."""

    def __init__(self, case_set_path: Path) -> None:
        self.path = case_set_path.expanduser().resolve()
        self.document = _load_model(self.path, CaseSetDocument, label="case set")
        self.dataset = DatasetBundle(self.path.parent)
        cases: dict[str, CaseDefinition] = {}
        for case_id in self.document.cases:
            try:
                cases[case_id] = self.dataset.case_definitions[case_id]
            except KeyError as exc:
                raise CaseSetError(f"selected case is not in the dataset: {case_id}") from exc

        self._cases = cases

    @property
    def case_set_id(self) -> str:
        return self.document.id

    @property
    def case_ids(self) -> tuple[str, ...]:
        return self.document.cases

    def get(self, case_id: str) -> CaseDefinition:
        return self._cases[case_id]


class DatasetAdaptiveSelector:
    """Execute the current dataset's declared response-adaptive prelude."""

    def select_next(self, request: AdaptiveSelectionRequest) -> AdaptiveChoice | None:
        http_status = next(
            (
                fact.value
                for fact in request.participant_visible_facts
                if fact.name == "http_status"
            ),
            None,
        )
        if (
            isinstance(http_status, int)
            and not isinstance(http_status, bool)
            and http_status >= 400
        ):
            return None

        bounds = request.selection_bounds
        if len(request.action_history) == 1:
            fact = _find_fact(request, "available_actions")
            if not isinstance(fact.value, list):
                raise AdaptivePreludeError("Wallet available actions are not a JSON array")
            required_action = bounds.get("required_offered_action")
            if not isinstance(required_action, str) or not required_action:
                raise AdaptivePreludeError("adaptive case has no required offered action")
            offer = next(
                (
                    item
                    for item in fact.value
                    if isinstance(item, dict) and item.get("action") == required_action
                ),
                None,
            )
            if offer is None:
                raise AdaptivePreludeError(
                    f"Wallet did not offer required action: {required_action}"
                )
            return AdaptiveChoice(
                action=ParticipantAction(name="task_action", payload=offer),
                based_on_facts=(fact,),
            )

        if len(request.action_history) == 2:
            active_fact = _find_fact(request, "active_task")
            if bounds.get("require_idle_before_next_message") is True and active_fact.value is True:
                raise AdaptivePreludeError("adaptive prelude did not return Wallet to idle")
            outcome_fact = _find_fact(request, "outcome_kind")
            next_message = bounds.get("next_message_after_confirmation")
            if not isinstance(next_message, str) or not next_message:
                raise AdaptivePreludeError("adaptive case has no next message")
            return AdaptiveChoice(
                action=ParticipantAction(name="message", payload=next_message),
                based_on_facts=(active_fact, outcome_fact),
            )
        return None


def _build_case(
    case_id: str,
    fixture_case: FixtureCase,
    tuple_record: TupleRecord,
    example: ExampleRecord,
) -> CaseDefinition:
    action_plan = _build_action_plan(case_id, fixture_case.prelude, example)
    return CaseDefinition(
        case_id=case_id,
        starting_conditions=fixture_case.fixture.model_dump(mode="json"),
        case_context={
            "tuple_id": tuple_record.id,
            "example_id": example.id,
            "interaction_form": example.interaction_form,
            "focal_message_index": example.focal_message_index,
            "purpose": tuple_record.purpose,
            "failure_surface": tuple_record.failure_surface,
            "dimensions": tuple_record.dimensions,
            "declared_prelude": [step.model_dump(mode="json") for step in fixture_case.prelude],
        },
        action_plan=action_plan,
    )


def _build_action_plan(
    case_id: str,
    prelude: tuple[PreludeStep, ...],
    example: ExampleRecord,
) -> StandaloneActionPlan | FixedSequenceActionPlan | ResponseAdaptiveActionPlan:
    messages = example.user_messages
    if example.interaction_form == "standalone":
        if prelude or len(messages) != 1 or example.focal_message_index != 0:
            raise CaseSetError(f"invalid standalone execution declaration: {case_id}")
        return StandaloneActionPlan(action=ParticipantAction(name="message", payload=messages[0]))

    if example.interaction_form == "sequence":
        if prelude or len(messages) < 2:
            raise CaseSetError(f"invalid fixed-sequence execution declaration: {case_id}")
        if example.focal_message_index is None or not 0 <= example.focal_message_index < len(
            messages
        ):
            raise CaseSetError(f"invalid focal message index: {case_id}")
        return FixedSequenceActionPlan(
            actions=tuple(
                ParticipantAction(name="message", payload=message) for message in messages
            )
        )

    if len(prelude) != 3 or len(messages) != 1 or example.focal_message_index is not None:
        raise CaseSetError(f"invalid adaptive execution declaration: {case_id}")
    first, second, third = prelude
    if not (
        isinstance(first, MessagePrelude)
        and isinstance(second, OfferedActionPrelude)
        and isinstance(third, AssertIdlePrelude)
    ):
        raise CaseSetError(
            f"adaptive prelude must be message, offered_action, assert_idle: {case_id}"
        )
    return ResponseAdaptiveActionPlan(
        initial_action=ParticipantAction(name="message", payload=first.content),
        role_context={"case_id": case_id, "purpose": "satisfy the declared prelude"},
        allowed_action_names=("message", "task_action"),
        selection_bounds={
            "required_offered_action": second.action,
            "next_message_after_confirmation": messages[0],
            "require_idle_before_next_message": True,
        },
        max_actions=3,
    )


def _find_fact(request: AdaptiveSelectionRequest, name: str) -> ParticipantVisibleFact:
    fact = next(
        (fact for fact in request.participant_visible_facts if fact.name == name),
        None,
    )
    if fact is None:
        raise AdaptivePreludeError(f"Wallet response did not expose required fact: {name}")
    return fact


def _unique_by_id(records: tuple[RecordT, ...], *, label: str) -> dict[str, RecordT]:
    indexed: dict[str, RecordT] = {}
    for record in records:
        if record.id in indexed:
            raise CaseSetError(f"duplicate {label} identity: {record.id}")
        indexed[record.id] = record
    return indexed


def _load_model(path: Path, model: type[ModelT], *, label: str) -> ModelT:
    payload = _load_json_object(path, label=label)
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise CaseSetError(f"invalid {label} file {path}: {exc}") from exc


def _load_json_object(path: Path, *, label: str) -> dict[str, JsonValue]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CaseSetError(f"cannot read {label} file {path}: {exc.strerror or exc}") from exc
    try:
        parsed: object = json.loads(content)
    except json.JSONDecodeError as exc:
        raise CaseSetError(f"invalid JSON in {label} file {path}: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise CaseSetError(f"invalid {label} file {path}: document root must be an object")
    parsed_mapping = cast(dict[object, object], parsed)
    if not all(isinstance(key, str) for key in parsed_mapping):
        raise CaseSetError(f"invalid {label} file {path}: document root must be an object")
    return cast(dict[str, JsonValue], parsed_mapping)


__all__ = [
    "AdaptivePreludeError",
    "CaseSetDocument",
    "CaseSetError",
    "DatasetBundle",
    "DatasetAdaptiveSelector",
    "DatasetCaseSource",
    "DimensionRecord",
    "DimensionsDocument",
    "ExampleRecord",
    "ExamplesDocument",
    "FixtureCase",
    "TupleRecord",
]
