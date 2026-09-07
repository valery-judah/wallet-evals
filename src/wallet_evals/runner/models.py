from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

NonEmptyString: TypeAlias = Annotated[str, Field(min_length=1)]


class RunnerModel(BaseModel):
    """Base for validated, immutable runner values."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ExecutionContext(RunnerModel):
    """The effective Wallet, model, environment, and settings for a run."""

    wallet: NonEmptyString
    model: NonEmptyString
    environment: NonEmptyString
    settings: dict[str, JsonValue] = Field(default_factory=dict)


class ParticipantAction(RunnerModel):
    """A participant action sent across the Wallet exercise boundary."""

    name: NonEmptyString
    payload: JsonValue = None


class ParticipantVisibleFact(RunnerModel):
    """One response fact visible to an adaptive participant."""

    name: NonEmptyString
    value: JsonValue


class StandaloneActionPlan(RunnerModel):
    mode: Literal["standalone"] = "standalone"
    action: ParticipantAction


class FixedSequenceActionPlan(RunnerModel):
    mode: Literal["fixed_sequence"] = "fixed_sequence"
    actions: tuple[ParticipantAction, ...] = Field(min_length=1)


class ResponseAdaptiveActionPlan(RunnerModel):
    mode: Literal["response_adaptive"] = "response_adaptive"
    initial_action: ParticipantAction
    role_context: JsonValue = Field(default_factory=dict)
    allowed_action_names: tuple[NonEmptyString, ...] = Field(min_length=1)
    selection_bounds: dict[str, JsonValue] = Field(default_factory=dict)
    max_actions: int = Field(ge=1)

    @field_validator("allowed_action_names")
    @classmethod
    def action_names_are_unique(cls, names: tuple[str, ...]) -> tuple[str, ...]:
        if len(names) != len(set(names)):
            raise ValueError("allowed action names must be unique")
        return names

    @model_validator(mode="after")
    def initial_action_is_allowed(self) -> ResponseAdaptiveActionPlan:
        if self.initial_action.name not in self.allowed_action_names:
            raise ValueError("initial action must be allowed by the adaptive plan")
        return self


ActionPlan: TypeAlias = Annotated[
    StandaloneActionPlan | FixedSequenceActionPlan | ResponseAdaptiveActionPlan,
    Field(discriminator="mode"),
]


class CaseDefinition(RunnerModel):
    """The case information required to prepare and conduct one execution."""

    case_id: NonEmptyString
    starting_conditions: JsonValue = Field(default_factory=dict)
    case_context: dict[str, JsonValue] = Field(default_factory=dict)
    action_plan: ActionPlan


class RunRequest(RunnerModel):
    case_ids: tuple[NonEmptyString, ...] = Field(min_length=1)
    execution_context: ExecutionContext

    @field_validator("case_ids")
    @classmethod
    def selected_cases_are_unique(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("selected case identities must be unique")
        return case_ids


class CaseExecution(RunnerModel):
    """Identity and inputs established before a case trajectory starts."""

    run_id: NonEmptyString
    case_execution_id: NonEmptyString
    case: CaseDefinition
    execution_context: ExecutionContext


class WalletResponseObservation(RunnerModel):
    kind: Literal["wallet_response"] = "wallet_response"
    response: JsonValue
    participant_visible_facts: tuple[ParticipantVisibleFact, ...] = ()


class ObservableChangeObservation(RunnerModel):
    kind: Literal["observable_change"] = "observable_change"
    subject: NonEmptyString
    capture_point: NonEmptyString
    value: JsonValue


WalletObservation: TypeAlias = Annotated[
    WalletResponseObservation | ObservableChangeObservation,
    Field(discriminator="kind"),
]


class InteractionResult(RunnerModel):
    """Ordered observations exposed by Wallet for one participant action."""

    observations: tuple[WalletObservation, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def includes_complete_wallet_response(self) -> InteractionResult:
        if not any(
            isinstance(observation, WalletResponseObservation) for observation in self.observations
        ):
            raise ValueError("an interaction result must include a complete Wallet response")
        return self

    def visible_facts(self) -> tuple[ParticipantVisibleFact, ...]:
        return tuple(
            fact
            for observation in self.observations
            if isinstance(observation, WalletResponseObservation)
            for fact in observation.participant_visible_facts
        )


class AdaptiveSelectionRequest(RunnerModel):
    """The bounded information available when selecting a later adaptive action."""

    run_id: NonEmptyString
    case_execution_id: NonEmptyString
    case_id: NonEmptyString
    role_context: JsonValue
    allowed_action_names: tuple[NonEmptyString, ...]
    selection_bounds: dict[str, JsonValue]
    action_history: tuple[ParticipantAction, ...]
    participant_visible_facts: tuple[ParticipantVisibleFact, ...]


class AdaptiveChoice(RunnerModel):
    action: ParticipantAction
    based_on_facts: tuple[ParticipantVisibleFact, ...] = Field(min_length=1)


class ParticipantActionTraceEvent(RunnerModel):
    kind: Literal["participant_action"] = "participant_action"
    order: int = Field(ge=1)
    action: ParticipantAction
    adaptive_basis: tuple[ParticipantVisibleFact, ...] | None = None

    @field_validator("adaptive_basis")
    @classmethod
    def adaptive_basis_is_not_empty(
        cls, basis: tuple[ParticipantVisibleFact, ...] | None
    ) -> tuple[ParticipantVisibleFact, ...] | None:
        if basis == ():
            raise ValueError("an adaptive basis must contain at least one visible fact")
        return basis


class WalletResponseTraceEvent(RunnerModel):
    kind: Literal["wallet_response"] = "wallet_response"
    order: int = Field(ge=1)
    response: JsonValue
    participant_visible_facts: tuple[ParticipantVisibleFact, ...] = ()


class ObservableChangeTraceEvent(RunnerModel):
    kind: Literal["observable_change"] = "observable_change"
    order: int = Field(ge=1)
    subject: NonEmptyString
    capture_point: NonEmptyString
    value: JsonValue


TraceEvent: TypeAlias = Annotated[
    ParticipantActionTraceEvent | WalletResponseTraceEvent | ObservableChangeTraceEvent,
    Field(discriminator="kind"),
]


class CaseTrace(RunnerModel):
    run_id: NonEmptyString
    case_execution_id: NonEmptyString
    case_id: NonEmptyString
    execution_context: ExecutionContext
    case_context: dict[str, JsonValue] = Field(default_factory=dict)
    starting_conditions: JsonValue = Field(default_factory=dict)
    events: tuple[TraceEvent, ...] = Field(min_length=1)

    @field_validator("events")
    @classmethod
    def event_order_is_contiguous(cls, events: tuple[TraceEvent, ...]) -> tuple[TraceEvent, ...]:
        if tuple(event.order for event in events) != tuple(range(1, len(events) + 1)):
            raise ValueError("trace event order must be contiguous and start at one")
        return events


class RunResult(RunnerModel):
    run_id: NonEmptyString
    execution_context: ExecutionContext
    traces: tuple[CaseTrace, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def traces_belong_to_run(self) -> RunResult:
        execution_ids: set[str] = set()
        for trace in self.traces:
            if trace.run_id != self.run_id:
                raise ValueError("every trace must belong to the result run")
            if trace.execution_context != self.execution_context:
                raise ValueError("every trace must carry the governing execution context")
            if trace.case_execution_id in execution_ids:
                raise ValueError("case execution identities must be unique within a run")
            execution_ids.add(trace.case_execution_id)
        return self


class SavedRunResultIdentity(RunnerModel):
    """Identity established by persistence only after a complete save succeeds."""

    run_id: NonEmptyString
    artifact_id: NonEmptyString
