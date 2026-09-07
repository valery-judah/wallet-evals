from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from wallet_evals.runner.errors import (
    AdaptiveChoiceViolationError,
    CaseDefinitionIdentityError,
    IdentityCollisionError,
    MissingAdaptiveSelectorError,
    PersistenceContractError,
)
from wallet_evals.runner.models import (
    AdaptiveChoice,
    AdaptiveSelectionRequest,
    CaseDefinition,
    CaseExecution,
    CaseTrace,
    FixedSequenceActionPlan,
    InteractionResult,
    ObservableChangeTraceEvent,
    ParticipantAction,
    ParticipantActionTraceEvent,
    ParticipantVisibleFact,
    ResponseAdaptiveActionPlan,
    RunRequest,
    RunResult,
    SavedRunResultIdentity,
    StandaloneActionPlan,
    TraceEvent,
    WalletResponseObservation,
    WalletResponseTraceEvent,
)
from wallet_evals.runner.ports import (
    AdaptiveActionSelector,
    CaseDefinitionSource,
    IdentityGenerator,
    RunResultStore,
    WalletExecution,
    WalletExecutionFactory,
)


class UUIDIdentityGenerator:
    def new_run_id(self) -> str:
        return str(uuid4())

    def new_case_execution_id(self, run_id: str, case_id: str) -> str:
        del run_id, case_id
        return str(uuid4())


class EvaluationRunner:
    """Coordinate one evaluation run from identity establishment through persistence."""

    def __init__(
        self,
        *,
        case_source: CaseDefinitionSource,
        wallet_factory: WalletExecutionFactory,
        result_store: RunResultStore,
        adaptive_selector: AdaptiveActionSelector | None = None,
        identity_generator: IdentityGenerator | None = None,
    ) -> None:
        self._case_source = case_source
        self._wallet_factory = wallet_factory
        self._result_store = result_store
        self._adaptive_selector = adaptive_selector
        self._identity_generator = identity_generator or UUIDIdentityGenerator()

    def run(self, request: RunRequest) -> SavedRunResultIdentity:
        run_id = self._identity_generator.new_run_id()
        governing_context = request.execution_context.model_copy(deep=True)
        cases = tuple(self._get_selected_case(case_id) for case_id in request.case_ids)
        self._require_adaptive_selector(cases)

        executions = tuple(
            CaseExecution(
                run_id=run_id,
                case_execution_id=self._identity_generator.new_case_execution_id(
                    run_id, case.case_id
                ),
                case=case.model_copy(deep=True),
                execution_context=governing_context.model_copy(deep=True),
            )
            for case in cases
        )
        execution_ids = tuple(execution.case_execution_id for execution in executions)
        if len(execution_ids) != len(set(execution_ids)):
            raise IdentityCollisionError(
                "case execution identities must be distinct before evidence capture"
            )

        traces = tuple(self._execute_case(execution) for execution in executions)
        result = RunResult(
            run_id=run_id,
            execution_context=governing_context,
            traces=traces,
        )
        saved_identity = self._result_store.save(result)
        if saved_identity.run_id != run_id:
            raise PersistenceContractError(
                "persistence returned an identity for a different evaluation run"
            )
        return saved_identity

    def _get_selected_case(self, case_id: str) -> CaseDefinition:
        case = self._case_source.get(case_id)
        if case.case_id != case_id:
            raise CaseDefinitionIdentityError(
                f"selected case {case_id!r} resolved to definition {case.case_id!r}"
            )
        return case

    def _require_adaptive_selector(self, cases: tuple[CaseDefinition, ...]) -> None:
        if self._adaptive_selector is not None:
            return
        if any(isinstance(case.action_plan, ResponseAdaptiveActionPlan) for case in cases):
            raise MissingAdaptiveSelectorError(
                "a response-adaptive case was selected but no adaptive selector was configured"
            )

    def _execute_case(self, execution: CaseExecution) -> CaseTrace:
        trace_case = execution.case.model_copy(deep=True)
        trace_context = execution.execution_context.model_copy(deep=True)
        wallet = self._wallet_factory.bootstrap(execution)
        events: list[TraceEvent] = []
        try:
            plan = execution.case.action_plan
            if isinstance(plan, StandaloneActionPlan):
                self._perform_action(wallet, events, plan.action)
            elif isinstance(plan, FixedSequenceActionPlan):
                for action in plan.actions:
                    self._perform_action(wallet, events, action)
            else:
                self._execute_adaptive(execution, wallet, events, plan)
        finally:
            wallet.close()

        return CaseTrace(
            run_id=execution.run_id,
            case_execution_id=execution.case_execution_id,
            case_id=trace_case.case_id,
            execution_context=trace_context,
            case_context=trace_case.case_context,
            starting_conditions=trace_case.starting_conditions,
            events=tuple(events),
        )

    def _execute_adaptive(
        self,
        execution: CaseExecution,
        wallet: WalletExecution,
        events: list[TraceEvent],
        plan: ResponseAdaptiveActionPlan,
    ) -> None:
        selector = self._adaptive_selector
        if selector is None:  # Guarded before any case is bootstrapped.
            raise MissingAdaptiveSelectorError("adaptive selector is unavailable")

        actions = [plan.initial_action]
        visible_facts = self._perform_action(wallet, events, plan.initial_action)
        while len(actions) < plan.max_actions:
            choice = selector.select_next(
                AdaptiveSelectionRequest(
                    run_id=execution.run_id,
                    case_execution_id=execution.case_execution_id,
                    case_id=execution.case.case_id,
                    role_context=plan.role_context,
                    allowed_action_names=plan.allowed_action_names,
                    selection_bounds=plan.selection_bounds,
                    action_history=tuple(actions),
                    participant_visible_facts=visible_facts,
                )
            )
            if choice is None:
                return
            self._validate_adaptive_choice(choice, plan, visible_facts)
            actions.append(choice.action)
            visible_facts = self._perform_action(
                wallet,
                events,
                choice.action,
                adaptive_basis=choice.based_on_facts,
            )

    @staticmethod
    def _validate_adaptive_choice(
        choice: AdaptiveChoice,
        plan: ResponseAdaptiveActionPlan,
        visible_facts: tuple[ParticipantVisibleFact, ...],
    ) -> None:
        if choice.action.name not in plan.allowed_action_names:
            raise AdaptiveChoiceViolationError(
                f"adaptive action {choice.action.name!r} is outside the case-declared bounds"
            )
        unavailable_facts = tuple(
            fact for fact in choice.based_on_facts if fact not in visible_facts
        )
        if unavailable_facts:
            raise AdaptiveChoiceViolationError(
                "adaptive choice cited facts that were not visible in the preceding Wallet response"
            )

    @staticmethod
    def _perform_action(
        wallet: WalletExecution,
        events: list[TraceEvent],
        action: ParticipantAction,
        *,
        adaptive_basis: tuple[ParticipantVisibleFact, ...] | None = None,
    ) -> tuple[ParticipantVisibleFact, ...]:
        events.append(
            ParticipantActionTraceEvent(
                order=len(events) + 1,
                action=action.model_copy(deep=True),
                adaptive_basis=(
                    tuple(fact.model_copy(deep=True) for fact in adaptive_basis)
                    if adaptive_basis is not None
                    else None
                ),
            )
        )
        result = wallet.perform(action.model_copy(deep=True))
        EvaluationRunner._capture_observations(events, result)
        return tuple(fact.model_copy(deep=True) for fact in result.visible_facts())

    @staticmethod
    def _capture_observations(events: list[TraceEvent], result: InteractionResult) -> None:
        for observation in result.observations:
            if isinstance(observation, WalletResponseObservation):
                event: TraceEvent = WalletResponseTraceEvent(
                    order=len(events) + 1,
                    response=deepcopy(observation.response),
                    participant_visible_facts=tuple(
                        fact.model_copy(deep=True) for fact in observation.participant_visible_facts
                    ),
                )
            else:
                event = ObservableChangeTraceEvent(
                    order=len(events) + 1,
                    subject=observation.subject,
                    capture_point=observation.capture_point,
                    value=deepcopy(observation.value),
                )
            events.append(event)
