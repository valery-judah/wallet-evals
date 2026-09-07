from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue
from wallet.ai.control.domain import MessageSubmission, TaskActionSubmission, TurnRequest
from wallet.ai.control.engine import (
    ConversationProcessingError,
    InvalidTurnRequestError,
    TurnGuardConflictError,
)
from wallet.ai.control.registry import ConversationNotFoundError, RequestIdConflictError
from wallet.ai.llm import StructuredChatError
from wallet.api.deps import AppContainer, build_app_container
from wallet.api.schemas import AccountResponse, SubmitTurnResponse, TransactionResponse
from wallet.application.accounts import AccountService, OpenAccount
from wallet.config import Settings
from wallet.domain.accounts import AccountType
from wallet.observability import configure_logging

from wallet_evals.case_sets import CaseSetError, DatasetAdaptiveSelector, DatasetCaseSource
from wallet_evals.runner import (
    CaseExecution,
    EvaluationRunner,
    ExecutionContext,
    InteractionResult,
    JsonFileRunResultStore,
    ObservableChangeObservation,
    ParticipantAction,
    ParticipantVisibleFact,
    RunRequest,
    WalletResponseObservation,
)


class LocalWalletExecutionFactory:
    def __init__(self, settings: Settings, *, case_count: int) -> None:
        self._settings = settings
        self._case_count = case_count
        self._case_number = 0

    def bootstrap(self, execution: CaseExecution) -> LocalWalletExecution:
        self._case_number += 1
        print(
            f"[{self._case_number}/{self._case_count}] {execution.case.case_id}",
            flush=True,
        )
        fixture = _json_object(
            execution.case.starting_conditions,
            label=f"starting conditions {execution.case.case_id}",
        )
        container = build_app_container(self._settings)
        accounts = _json_array(fixture.get("accounts"), label="fixture accounts")
        for account_value in accounts:
            account = _json_object(account_value, label="fixture account")
            account_id = _required_string(account.get("id"), label="account id")
            seeding_service = AccountService(
                accounts=container.accounts,
                transactions=container.transactions,
                generate_account_id=lambda account_id=account_id: account_id,
            )
            seeding_service.open_account(
                OpenAccount(
                    name=_required_string(account.get("name"), label="account name"),
                    type=AccountType(_required_string(account.get("type"), label="account type")),
                    currency=_required_string(account.get("currency"), label="account currency"),
                    opening_balance_minor=_required_int(
                        account.get("opening_balance_minor"), label="opening balance"
                    ),
                )
            )
        return LocalWalletExecution(execution.case.case_id, container)


class LocalWalletExecution:
    def __init__(self, case_id: str, container: AppContainer) -> None:
        self._case_id = case_id
        self._container = container
        self._conversation_id: str | None = None
        self._turn = 0
        self._state = self._snapshot_state()

    def perform(self, action: ParticipantAction) -> InteractionResult:
        self._turn += 1
        submission = self._submission(action)
        request_id = f"eval-{self._case_id.replace('/', '-')}-{self._turn}"
        try:
            response = self._container.conversation_controller.submit_turn(
                TurnRequest(
                    request_id=request_id,
                    conversation_id=self._conversation_id,
                    input=submission,
                )
            )
        except (
            ConversationNotFoundError,
            RequestIdConflictError,
            TurnGuardConflictError,
            InvalidTurnRequestError,
            ConversationProcessingError,
            StructuredChatError,
        ) as exc:
            status_code, detail = _public_conversation_error(exc)
            public_response: dict[str, Any] = {
                "status_code": status_code,
                "body": {"detail": detail},
                "request_id": request_id,
            }
            facts = (
                ParticipantVisibleFact(name="active_task", value=False),
                ParticipantVisibleFact(name="outcome_kind", value="http_error"),
                ParticipantVisibleFact(name="outcome_message", value=detail),
                ParticipantVisibleFact(name="available_actions", value=[]),
                ParticipantVisibleFact(name="http_status", value=status_code),
            )
        else:
            self._conversation_id = response.conversation.id
            public_response = SubmitTurnResponse.from_domain(response).model_dump(mode="json")
            facts = self._visible_facts(public_response)

        observations: list[WalletResponseObservation | ObservableChangeObservation] = [
            WalletResponseObservation(
                response=cast(JsonValue, public_response),
                participant_visible_facts=facts,
            )
        ]
        state = self._snapshot_state()
        if state != self._state:
            observations.append(
                ObservableChangeObservation(
                    subject="wallet_ledger",
                    capture_point=f"after_action_{self._turn}",
                    value=state,
                )
            )
        self._state = state
        return InteractionResult(observations=tuple(observations))

    def close(self) -> None:
        """The case-scoped container owns only in-memory state and needs no explicit shutdown."""

    def _submission(self, action: ParticipantAction) -> MessageSubmission | TaskActionSubmission:
        if action.name == "message":
            return MessageSubmission(_required_string(action.payload, label="message payload"))
        if action.name == "task_action":
            payload = _json_object(action.payload, label="task action payload")
            action_payload = payload.get("payload")
            return TaskActionSubmission(
                expected_task_id=_required_string(
                    payload.get("expected_task_id"), label="expected task id"
                ),
                expected_conversation_version=_required_int(
                    payload.get("expected_conversation_version"),
                    label="expected conversation version",
                ),
                action=_required_string(payload.get("action"), label="task action"),
                payload=(
                    {}
                    if action_payload is None
                    else cast(
                        dict[str, object], _json_object(action_payload, label="action payload")
                    )
                ),
            )
        raise ValueError(f"unsupported participant action: {action.name}")

    def _snapshot_state(self) -> dict[str, JsonValue]:
        return {
            "accounts": cast(
                JsonValue,
                [
                    AccountResponse.from_snapshot(snapshot).model_dump(mode="json")
                    for snapshot in self._container.account_service.list_accounts()
                ],
            ),
            "transactions": cast(
                JsonValue,
                [
                    TransactionResponse.from_domain(transaction).model_dump(mode="json")
                    for transaction in self._container.transaction_service.list_transactions()
                ],
            ),
        }

    @staticmethod
    def _visible_facts(response: dict[str, Any]) -> tuple[ParticipantVisibleFact, ...]:
        conversation = cast(dict[str, Any], response["conversation"])
        outcome = cast(dict[str, Any], response["outcome"])
        active_task = conversation.get("active_task")
        offers: JsonValue = []
        if isinstance(active_task, dict):
            view = active_task.get("view")
            if isinstance(view, dict) and isinstance(view.get("available_actions"), list):
                offers = cast(JsonValue, view["available_actions"])
        return (
            ParticipantVisibleFact(name="active_task", value=active_task is not None),
            ParticipantVisibleFact(name="outcome_kind", value=cast(JsonValue, outcome["kind"])),
            ParticipantVisibleFact(
                name="outcome_message", value=cast(JsonValue, outcome["message"])
            ),
            ParticipantVisibleFact(name="available_actions", value=offers),
        )


def _json_object(value: object, *, label: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be a JSON object")
    return cast(dict[str, JsonValue], value)


def _json_array(value: object, *, label: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array")
    return cast(list[JsonValue], value)


def _required_string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _required_int(value: object, *, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    return value


def _public_conversation_error(exc: Exception) -> tuple[int, str]:
    if isinstance(exc, ConversationNotFoundError):
        conversation_id = exc.args[0] if exc.args else "unknown"
        return 404, f"conversation not found: {conversation_id}"
    if isinstance(exc, RequestIdConflictError | TurnGuardConflictError):
        return 409, str(exc)
    if isinstance(exc, InvalidTurnRequestError):
        return 422, str(exc)
    return 502, "Conversation processing is temporarily unavailable."


def _git_revision(repository: Path) -> str:
    return _git(repository, "rev-parse", "HEAD")


def _git_is_dirty(repository: Path) -> bool:
    return bool(_git(repository, "status", "--porcelain"))


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Internal managed Wallet evaluation worker.")
    parser.add_argument("--case-set", type=Path, required=True)
    parser.add_argument("--wallet-repo", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--ollama-base-url", required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    configure_logging("WARNING", environment="test")
    source = DatasetCaseSource(args.case_set)
    wallet_repository = args.wallet_repo.expanduser().resolve()
    settings = Settings(
        environment="test",
        log_level="WARNING",
        seed_sample_data=False,
        ollama_model=args.model,
        ollama_base_url=args.ollama_base_url,
        ollama_timeout_seconds=120,
    )
    context = ExecutionContext(
        wallet=f"wallet@{_git_revision(wallet_repository)}",
        model=args.model,
        environment="local-in-process",
        settings={
            "case_set_id": source.case_set_id,
            "case_set_path": str(source.path),
            "case_count": len(source.case_ids),
            "ollama_base_url": args.ollama_base_url,
            "sut_worktree_dirty": _git_is_dirty(wallet_repository),
            "isolation_mode": "fresh in-memory dependency graph per case",
        },
    )
    runner = EvaluationRunner(
        case_source=source,
        wallet_factory=LocalWalletExecutionFactory(settings, case_count=len(source.case_ids)),
        result_store=JsonFileRunResultStore(args.results_dir.expanduser().resolve()),
        adaptive_selector=DatasetAdaptiveSelector(),
    )
    identity = runner.run(RunRequest(case_ids=source.case_ids, execution_context=context))
    print(f"Run ID: {identity.run_id}", flush=True)
    print(f"Result: {identity.artifact_id}", flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        run(argv)
    except (CaseSetError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: evaluation run failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
