from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pytest
from pydantic import JsonValue, ValidationError

from wallet_evals.runner import (
    AdaptiveChoice,
    AdaptiveChoiceViolationError,
    AdaptiveSelectionRequest,
    CaseDefinition,
    CaseExecution,
    EvaluationRunner,
    ExecutionContext,
    FixedSequenceActionPlan,
    InteractionResult,
    JsonFileRunResultStore,
    MissingAdaptiveSelectorError,
    ObservableChangeObservation,
    ParticipantAction,
    ParticipantVisibleFact,
    ResponseAdaptiveActionPlan,
    RunRequest,
    RunResult,
    SavedRunResultIdentity,
    StandaloneActionPlan,
    WalletExecution,
    WalletResponseObservation,
)


class DictionaryCaseSource:
    def __init__(self, cases: Iterable[CaseDefinition]) -> None:
        self.cases = {case.case_id: case for case in cases}
        self.requested: list[str] = []

    def get(self, case_id: str) -> CaseDefinition:
        self.requested.append(case_id)
        return self.cases[case_id]


class ScriptedWallet:
    def __init__(self, results: Iterable[InteractionResult]) -> None:
        self._results = iter(results)
        self.actions: list[ParticipantAction] = []
        self.closed = False

    def perform(self, action: ParticipantAction) -> InteractionResult:
        self.actions.append(action)
        return next(self._results)

    def close(self) -> None:
        self.closed = True


class RecordingWalletFactory:
    def __init__(self, wallets: Iterable[WalletExecution]) -> None:
        self._wallets = iter(wallets)
        self.executions: list[CaseExecution] = []

    def bootstrap(self, execution: CaseExecution) -> WalletExecution:
        self.executions.append(execution)
        return next(self._wallets)


class RecordingStore:
    def __init__(self) -> None:
        self.results: list[RunResult] = []

    def save(self, result: RunResult) -> SavedRunResultIdentity:
        self.results.append(result)
        return SavedRunResultIdentity(run_id=result.run_id, artifact_id=f"artifact:{result.run_id}")


class FailingStore:
    def __init__(self) -> None:
        self.results: list[RunResult] = []

    def save(self, result: RunResult) -> SavedRunResultIdentity:
        self.results.append(result)
        raise OSError("persistence unavailable")


class FailingWallet:
    def __init__(self) -> None:
        self.actions: list[ParticipantAction] = []
        self.closed = False

    def perform(self, action: ParticipantAction) -> InteractionResult:
        self.actions.append(action)
        raise RuntimeError("Wallet interaction failed")

    def close(self) -> None:
        self.closed = True


class DeterministicIdentities:
    def __init__(self, run_id: str = "run-001") -> None:
        self.run_id = run_id
        self.execution_ids_created: list[str] = []

    def new_run_id(self) -> str:
        return self.run_id

    def new_case_execution_id(self, run_id: str, case_id: str) -> str:
        execution_id = f"{run_id}:{case_id}"
        self.execution_ids_created.append(execution_id)
        return execution_id


class ScriptedSelector:
    def __init__(self, choices: Iterable[AdaptiveChoice | None]) -> None:
        self._choices = iter(choices)
        self.requests: list[AdaptiveSelectionRequest] = []

    def select_next(self, request: AdaptiveSelectionRequest) -> AdaptiveChoice | None:
        self.requests.append(request)
        return next(self._choices)


def context() -> ExecutionContext:
    return ExecutionContext(
        wallet="wallet@abc123",
        model="model-v1",
        environment="local-eval",
        settings={"temperature": 0, "feature_flags": ["capture"]},
    )


def response(
    payload: JsonValue,
    *,
    facts: tuple[ParticipantVisibleFact, ...] = (),
) -> WalletResponseObservation:
    return WalletResponseObservation(response=payload, participant_visible_facts=facts)


def test_runner_executes_cases_serially_and_saves_one_attributable_result() -> None:
    first_action = ParticipantAction(name="message", payload="Show my balance")
    second_actions = (
        ParticipantAction(name="message", payload="Start transfer"),
        ParticipantAction(name="message", payload="Cash account"),
    )
    standalone = CaseDefinition(
        case_id="case-standalone",
        starting_conditions={"balance": 100},
        case_context={"intent": "inspect balance"},
        action_plan=StandaloneActionPlan(action=first_action),
    )
    fixed = CaseDefinition(
        case_id="case-fixed",
        starting_conditions={"draft": None},
        case_context={"intent": "complete transfer"},
        action_plan=FixedSequenceActionPlan(actions=second_actions),
    )
    first_wallet = ScriptedWallet(
        [
            InteractionResult(
                observations=(
                    ObservableChangeObservation(
                        subject="wallet", capture_point="before_response", value={"read": True}
                    ),
                    response({"text": "Balance is 100", "buttons": []}),
                )
            )
        ]
    )
    second_wallet = ScriptedWallet(
        [
            InteractionResult(observations=(response({"text": "Destination?"}),)),
            InteractionResult(
                observations=(
                    response({"text": "Ready to confirm"}),
                    ObservableChangeObservation(
                        subject="transfer_draft",
                        capture_point="after_response",
                        value={"destination": "Cash account"},
                    ),
                )
            ),
        ]
    )
    source = DictionaryCaseSource([standalone, fixed])
    factory = RecordingWalletFactory([first_wallet, second_wallet])
    store = RecordingStore()
    identities = DeterministicIdentities()
    runner = EvaluationRunner(
        case_source=source,
        wallet_factory=factory,
        result_store=store,
        identity_generator=identities,
    )

    saved = runner.run(
        RunRequest(case_ids=("case-standalone", "case-fixed"), execution_context=context())
    )

    assert saved == SavedRunResultIdentity(run_id="run-001", artifact_id="artifact:run-001")
    assert source.requested == ["case-standalone", "case-fixed"]
    assert identities.execution_ids_created == [
        "run-001:case-standalone",
        "run-001:case-fixed",
    ]
    assert [execution.case_execution_id for execution in factory.executions] == (
        identities.execution_ids_created
    )
    assert first_wallet.closed and second_wallet.closed
    assert first_wallet.actions == [first_action]
    assert second_wallet.actions == list(second_actions)

    assert len(store.results) == 1
    result = store.results[0]
    assert result.run_id == "run-001"
    assert result.execution_context == context()
    assert [trace.case_id for trace in result.traces] == ["case-standalone", "case-fixed"]
    assert all(trace.execution_context == context() for trace in result.traces)
    assert result.traces[0].starting_conditions == {"balance": 100}
    assert result.traces[0].case_context == {"intent": "inspect balance"}
    assert [(event.order, event.kind) for event in result.traces[0].events] == [
        (1, "participant_action"),
        (2, "observable_change"),
        (3, "wallet_response"),
    ]
    assert [(event.order, event.kind) for event in result.traces[1].events] == [
        (1, "participant_action"),
        (2, "wallet_response"),
        (3, "participant_action"),
        (4, "wallet_response"),
        (5, "observable_change"),
    ]


def test_response_adaptive_execution_records_visible_basis_without_private_context() -> None:
    offered_actions = ParticipantVisibleFact(name="offered_actions", value=["confirm", "cancel"])
    plan = ResponseAdaptiveActionPlan(
        initial_action=ParticipantAction(name="message", payload="Transfer 20 to Alice"),
        role_context={"private_goal": "complete a valid transfer"},
        allowed_action_names=("message", "confirm", "cancel"),
        selection_bounds={"currency": "ARS", "maximum_amount": 20},
        max_actions=3,
    )
    case = CaseDefinition(case_id="adaptive", action_plan=plan)
    wallet = ScriptedWallet(
        [
            InteractionResult(
                observations=(
                    response(
                        {"text": "Transfer prepared", "actions": ["confirm", "cancel"]},
                        facts=(offered_actions,),
                    ),
                )
            ),
            InteractionResult(observations=(response({"text": "Transfer complete"}),)),
        ]
    )
    selector = ScriptedSelector(
        [
            AdaptiveChoice(
                action=ParticipantAction(name="confirm"), based_on_facts=(offered_actions,)
            ),
            None,
        ]
    )
    store = RecordingStore()
    runner = EvaluationRunner(
        case_source=DictionaryCaseSource([case]),
        wallet_factory=RecordingWalletFactory([wallet]),
        result_store=store,
        adaptive_selector=selector,
        identity_generator=DeterministicIdentities(),
    )

    runner.run(RunRequest(case_ids=("adaptive",), execution_context=context()))

    assert len(selector.requests) == 2
    assert selector.requests[0].role_context == {"private_goal": "complete a valid transfer"}
    assert selector.requests[0].selection_bounds == {
        "currency": "ARS",
        "maximum_amount": 20,
    }
    assert selector.requests[0].participant_visible_facts == (offered_actions,)
    assert selector.requests[0].action_history == (plan.initial_action,)
    trace = store.results[0].traces[0]
    adaptive_event = trace.events[2]
    assert adaptive_event.kind == "participant_action"
    assert adaptive_event.adaptive_basis == (offered_actions,)
    serialized_trace = json.dumps(trace.model_dump(mode="json"))
    assert "private_goal" not in serialized_trace
    assert "complete a valid transfer" not in serialized_trace


@pytest.mark.parametrize(
    "choice",
    [
        AdaptiveChoice(
            action=ParticipantAction(name="delete"),
            based_on_facts=(ParticipantVisibleFact(name="offered", value=True),),
        ),
        AdaptiveChoice(
            action=ParticipantAction(name="confirm"),
            based_on_facts=(ParticipantVisibleFact(name="invented", value=True),),
        ),
    ],
)
def test_adaptive_choice_must_stay_within_action_and_evidence_bounds(
    choice: AdaptiveChoice,
) -> None:
    offered = ParticipantVisibleFact(name="offered", value=True)
    case = CaseDefinition(
        case_id="adaptive",
        action_plan=ResponseAdaptiveActionPlan(
            initial_action=ParticipantAction(name="message"),
            allowed_action_names=("message", "confirm"),
            max_actions=2,
        ),
    )
    wallet = ScriptedWallet(
        [InteractionResult(observations=(response("confirm?", facts=(offered,)),))]
    )
    factory = RecordingWalletFactory([wallet])
    store = RecordingStore()
    runner = EvaluationRunner(
        case_source=DictionaryCaseSource([case]),
        wallet_factory=factory,
        result_store=store,
        adaptive_selector=ScriptedSelector([choice]),
        identity_generator=DeterministicIdentities(),
    )

    with pytest.raises(AdaptiveChoiceViolationError):
        runner.run(RunRequest(case_ids=("adaptive",), execution_context=context()))

    assert wallet.closed
    assert wallet.actions == [ParticipantAction(name="message")]
    assert store.results == []


def test_missing_adaptive_selector_is_rejected_before_wallet_bootstrap() -> None:
    case = CaseDefinition(
        case_id="adaptive",
        action_plan=ResponseAdaptiveActionPlan(
            initial_action=ParticipantAction(name="message"),
            allowed_action_names=("message",),
            max_actions=1,
        ),
    )
    factory = RecordingWalletFactory([])
    runner = EvaluationRunner(
        case_source=DictionaryCaseSource([case]),
        wallet_factory=factory,
        result_store=RecordingStore(),
        identity_generator=DeterministicIdentities(),
    )

    with pytest.raises(MissingAdaptiveSelectorError):
        runner.run(RunRequest(case_ids=("adaptive",), execution_context=context()))

    assert factory.executions == []


def test_interaction_failure_closes_case_state_and_does_not_persist() -> None:
    action = ParticipantAction(name="message", payload="Hello")
    case = CaseDefinition(case_id="case-1", action_plan=StandaloneActionPlan(action=action))
    wallet = FailingWallet()
    store = RecordingStore()
    runner = EvaluationRunner(
        case_source=DictionaryCaseSource([case]),
        wallet_factory=RecordingWalletFactory([wallet]),
        result_store=store,
        identity_generator=DeterministicIdentities(),
    )

    with pytest.raises(RuntimeError, match="Wallet interaction failed"):
        runner.run(RunRequest(case_ids=("case-1",), execution_context=context()))

    assert wallet.closed
    assert wallet.actions == [action]
    assert store.results == []


def test_persistence_failure_does_not_return_a_saved_identity() -> None:
    case = CaseDefinition(
        case_id="case-1",
        action_plan=StandaloneActionPlan(action=ParticipantAction(name="message")),
    )
    wallet = ScriptedWallet([InteractionResult(observations=(response({"text": "observed"}),))])
    store = FailingStore()
    runner = EvaluationRunner(
        case_source=DictionaryCaseSource([case]),
        wallet_factory=RecordingWalletFactory([wallet]),
        result_store=store,
        identity_generator=DeterministicIdentities(),
    )

    with pytest.raises(OSError, match="persistence unavailable"):
        runner.run(RunRequest(case_ids=("case-1",), execution_context=context()))

    assert wallet.closed
    assert len(store.results) == 1


def test_public_wallet_error_is_preserved_as_trace_evidence() -> None:
    case = CaseDefinition(
        case_id="case-502",
        action_plan=StandaloneActionPlan(action=ParticipantAction(name="message", payload="Hi")),
    )
    public_error: dict[str, JsonValue] = {
        "status_code": 502,
        "body": {"detail": "Conversation processing is temporarily unavailable."},
        "request_id": "eval-case-502-1",
    }
    status_fact = ParticipantVisibleFact(name="http_status", value=502)
    wallet = ScriptedWallet(
        [InteractionResult(observations=(response(public_error, facts=(status_fact,)),))]
    )
    store = RecordingStore()
    runner = EvaluationRunner(
        case_source=DictionaryCaseSource([case]),
        wallet_factory=RecordingWalletFactory([wallet]),
        result_store=store,
        identity_generator=DeterministicIdentities(),
    )

    runner.run(RunRequest(case_ids=("case-502",), execution_context=context()))

    error_event = store.results[0].traces[0].events[1]
    assert error_event.kind == "wallet_response"
    assert error_event.response == public_error
    assert error_event.participant_visible_facts == (status_fact,)


def test_json_store_returns_identity_after_writing_complete_result(tmp_path: Path) -> None:
    first_case = CaseDefinition(
        case_id="case-1",
        action_plan=StandaloneActionPlan(action=ParticipantAction(name="message", payload="Hi")),
    )
    second_case = CaseDefinition(
        case_id="case-2",
        action_plan=StandaloneActionPlan(
            action=ParticipantAction(name="message", payload="Balance?")
        ),
    )
    first_wallet = ScriptedWallet(
        [InteractionResult(observations=(response({"text": "Hello", "metadata": {}}),))]
    )
    second_wallet = ScriptedWallet(
        [InteractionResult(observations=(response({"text": "Balance is 100"}),))]
    )
    runner = EvaluationRunner(
        case_source=DictionaryCaseSource([first_case, second_case]),
        wallet_factory=RecordingWalletFactory([first_wallet, second_wallet]),
        result_store=JsonFileRunResultStore(tmp_path / "results"),
        identity_generator=DeterministicIdentities(run_id="run/with/slashes"),
    )

    saved = runner.run(RunRequest(case_ids=("case-1", "case-2"), execution_context=context()))

    artifact = Path(saved.artifact_id)
    assert saved.run_id == "run/with/slashes"
    assert artifact.name == "run%2Fwith%2Fslashes.json"
    document = json.loads(artifact.read_text(encoding="utf-8"))
    assert document["schema_version"] == "0.1"
    assert document["run_result"]["run_id"] == saved.run_id
    assert [trace["case_id"] for trace in document["run_result"]["traces"]] == [
        "case-1",
        "case-2",
    ]
    assert document["run_result"]["traces"][0]["events"][1]["response"] == {
        "text": "Hello",
        "metadata": {},
    }
    assert document["run_result"]["traces"][1]["events"][1]["response"] == {
        "text": "Balance is 100"
    }
    assert not list(artifact.parent.glob("*.tmp"))

    result = RunResult.model_validate(document["run_result"])
    with pytest.raises(FileExistsError):
        JsonFileRunResultStore(artifact.parent).save(result)


def test_models_reject_ambiguous_membership_and_incomplete_observations() -> None:
    with pytest.raises(ValidationError, match="selected case identities must be unique"):
        RunRequest(case_ids=("same", "same"), execution_context=context())

    with pytest.raises(ValidationError, match="complete Wallet response"):
        InteractionResult(
            observations=(
                ObservableChangeObservation(
                    subject="wallet", capture_point="after_action", value={"changed": True}
                ),
            )
        )
