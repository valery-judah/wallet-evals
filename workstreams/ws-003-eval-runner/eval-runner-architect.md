# Evaluation Runner High-Level Architecture

## Basis

### Derived inputs

- Primary workflow analysis
- Necessary behavioral conditions analysis
- System responsibilities analysis
- Interface requirements analysis

### Authoritative basis

- `docs/product/evaluation-subsystem-frame.md`
- `docs/product/spec.md`
- `docs/product/concepts.md`

## 1. System context and boundary

The evaluation running system begins when an evaluation operator supplies selected case identities and an execution configuration. It ends when one identifiable run result, containing every produced attributable case trace and its governing execution context, has been durably saved. Correctness judgment, scoring, diagnosis, publication, and alteration of traces by downstream verdicts remain outside the boundary.

The minimum architecture has one logical component, the **Evaluation Runner**. Case-scoped execution contexts are runtime instances controlled by that component, not additional logical components.

| External party or capability | Why it is outside the system | Boundary requirement | System dependence or exposure |
| --- | --- | --- | --- |
| Evaluation operator | The operator initiates the workflow rather than performing runner behavior. | IR-1 | Supplies selected case identities and the identified Wallet, model, environment, and other relevant settings; receives the saved run-result identity. |
| Evaluation-case definition source | Case definitions are selected inputs, not created by this workflow. | IR-2 | Supplies each case's identity, starting conditions, participant-action mode, role, allowed actions, and other declared bounds. |
| Wallet execution capability, including the identified Wallet, model, and relevant environment | This is the configured system under test and execution context whose behavior the runner exercises and observes. | IR-2, IR-3 | Must support separate controllable state, accept case-valid participant actions, and expose complete Wallet responses, participant-visible response facts, and relevant observable changes in distinguishable order. |
| Durable file persistence destination | The result must outlive the Wallet execution runtime; the product frame requires durable saving as files. This is a persistence boundary, not necessarily a separate process or service. | IR-4 | Accepts the complete identifiable run result and retains it for later interpretation without rerunning Wallet. |

Downstream experts, automated judges, and viewers are consumers of saved evidence, but this workflow requires no direct runner interface to them.

## 2. Logical component model

### Evaluation Runner

**Purpose:** Coordinate an identified evaluation run from case setup through durable evidence preservation.

**Responsibilities realized:** R-1 through R-7.

**Primary domain concepts:** evaluation case, evaluation run, case execution, case trajectory, case trace, and run result.

**Accountabilities:**

- establish run identity, governing execution context, and case-execution membership before evidence capture (R-1);
- prepare a distinct controllable Wallet state from each case's starting conditions (R-2);
- supply participant actions according to the case-declared standalone, fixed-sequence, or response-adaptive mode and bounds (R-3);
- observe and preserve attributable, ordered trajectory evidence, including complete Wallet responses and relevant resulting changes (R-4);
- for response-adaptive cases, preserve the chosen action and the participant-visible response facts used to choose it, excluding private reasoning (R-5);
- bind every trace to its case execution, run identity, and effective Wallet, model, environment, and other relevant settings (R-6); and
- collect produced traces and save them as one identifiable run result (R-7).

**Dependencies:** the four external parties or capabilities in the system context table.

No responsibility requires an independent internal state authority, deployment lifecycle, or cross-component contract. Splitting orchestration, action selection, capture, or result assembly into separate components would therefore add boundaries without satisfying additional supplied behavior.

## 3. Architectural interface model

| Architectural interface | Participants | Domain purpose and crossing information | Requirement |
| --- | --- | --- | --- |
| Run operation | Evaluation operator → Evaluation Runner | Start a run with selected case identities and execution configuration; return the saved result identity only when durable saving succeeds. | IR-1 |
| Case-definition acquisition | Evaluation-case definition source → Evaluation Runner | Supply the selected case definition, including starting conditions and participant-action declaration and bounds. | IR-2 |
| Isolated execution bootstrap | Evaluation Runner ↔ Wallet execution capability | Establish a distinguishable, controllable Wallet state under the run context that reflects the case starting conditions and is isolated from all other case executions. | IR-2 |
| Wallet exercise and observation | Evaluation Runner ↔ Wallet execution capability | Send case-valid participant actions; receive complete Wallet responses, participant-visible response facts needed for adaptive selection, and relevant observable Wallet or environment changes with distinguishable occurrence order. | IR-3 |
| Run-result persistence | Evaluation Runner → durable file persistence destination | Transfer the run identity and execution context together with every produced attributable case trace; establish the identity of the durably retained complete result. | IR-4 |

These are domain contracts only. No supplied requirement selects methods, DTOs, serialized schemas, transport protocols, or tracing technology.

## 4. Runtime interaction model

### Run establishment and case execution

1. The operator supplies selected case identities and execution configuration. The Evaluation Runner establishes the run identity and governing context, obtains the selected case definitions, and assigns each case execution an identity and run membership before any trajectory evidence is captured. This makes attribution available at capture time rather than reconstructing it afterward. (WF-1; BC-2, BC-7, BC-9; R-1)
2. For each selected case, the runner asks the Wallet execution capability for fresh controllable state under the governing context and applies the case starting conditions. The execution does not begin unless that state reflects those conditions and is isolated from every other case execution. (WF-1; BC-1, BC-5; R-2; IR-2)
3. The runner supplies actions according to the case declaration while observing the same boundary through which the trajectory becomes visible. For a standalone case it sends the single declared action. For a fixed sequence it sends the declared actions without using responses to choose later actions. For a response-adaptive sequence it uses only declared private role context and participant-visible Wallet response facts, within the declared bounds, to choose the next action. (WF-2; BC-3, BC-4; R-3; IR-3)
4. As interaction occurs, the runner adds observable participant actions, complete Wallet responses, and relevant observable changes to the case trace in distinguishable occurrence order, already associated with the case-execution identity. For every adaptive choice it adds the selected action and the participant-visible response facts used as its basis, but not private reasoning. (WF-3, WF-4; BC-6 through BC-10; R-4 through R-6)
5. After the selected case executions finish, the runner assembles their produced traces with the run identity and effective execution context and passes the complete result to durable file persistence. The workflow succeeds only when persistence confirms a durable identifiable result, whose identity is then exposed to the operator. (WF-5; BC-11; R-7; IR-1, IR-4)

The minimum execution baseline processes cases serially. Parallel execution and production-scale orchestration are explicitly deferred, while a fresh case-scoped Wallet state still provides the required isolation. The architecture does not impose an order among selected cases as a product semantic.

## 5. Information and ownership model

| Domain information | Established by | Use and integrity authority while in scope | Survival requirement |
| --- | --- | --- | --- |
| Evaluation case definition | Evaluation-case definition source | The source is authoritative for the selected definition. The runner consumes it without changing its declared starting conditions or participant-action semantics. | The saved evidence retains the originating case identity and the case context required by the shared trace semantics; the full source representation is not required by the supplied inputs. |
| Evaluation run identity and governing context | Evaluation Runner from the operator's selection | The runner maintains the run identity and the effective Wallet, model, environment, and other relevant settings and applies them to every member case execution. | Must be part of the durable run result. |
| Case-execution identity and run membership | Evaluation Runner before capture | The runner is authoritative for the relationship among the selected case, its execution, and its run and preserves it throughout capture and assembly. | Must survive in the attributable trace and run result. |
| Live case-scoped Wallet and environment state | Wallet execution capability, under setup controlled by the Evaluation Runner | The Wallet execution capability is authoritative for live state; the runner is accountable for establishing the required starting conditions and preventing state sharing between case executions. | No live state is required to survive execution. Only relevant observable changes captured as evidence survive. |
| Case trajectory | Occurs through participant and Wallet interaction | It is an occurrence, not a stored authoritative object. The Wallet execution capability exposes observable parts; the runner does not claim unobserved behavior. | The trajectory itself need not survive. Its captured evidence does. |
| Case trace, including adaptive-choice evidence | Evaluation Runner during observation | The runner maintains ordering, attribution, complete observed Wallet responses, relevant resulting changes, and adaptive evidence while assembling the run. | Must survive as part of the durable run result. After successful saving, the persisted artifact is the authoritative durable evidence record. |
| Run result | Evaluation Runner from produced traces and run context | The runner maintains completeness and identity during assembly; the persistence destination becomes authoritative for the durable saved result after successful persistence. | Must survive independently of the Wallet execution runtime. |

Recorded execution context is immutable provenance for the evidence, not a synchronized replica of mutable live Wallet or environment state. No additional cache, replica, or independently synchronized state is required.

## 6. Isolation and execution topology

The runner creates or obtains one case-scoped Wallet execution context for each selected case. That context starts from the case-defined conditions and must not expose or reuse mutable Wallet or environment state from another case execution. Serial scheduling does not relax this requirement: each case still receives fresh, separately controllable state.

The isolation mechanism may be an in-process resettable instance, a separate process, a container, or another mechanism only if it provides the stated state separation and controllability. The supplied conditions do not choose among them, so the physical mechanism remains unspecified.

The only required physical separation is semantic: durable result files must survive termination of the Wallet execution runtime. The Evaluation Runner, Wallet execution contexts, and file persistence need not be separate services or repositories.

## 7. Consequential failure semantics

| Failure point | Detection or containment | Can the workflow continue? | Remaining valid evidence | Required recovery behavior |
| --- | --- | --- | --- | --- |
| A selected case definition, governing configuration, identified Wallet, model, or environment is unavailable before execution | Evaluation Runner detects that it cannot establish the run or affected case context. No affected case execution begins. | Not specified. | No trace exists for the unstarted execution. Any already completed attributable trace remains evidence of its own execution, but the inputs do not say whether an incomplete run may be a successful result. | Retry, skip, abort, and partial-run policies are unspecified. |
| Case bootstrap cannot establish the declared starting conditions or isolation | Evaluation Runner contains the failure to that case-scoped context and does not treat it as ready for execution. | Not specified. | No requirement-compliant trace of an actual case trajectory is produced for that case. Earlier complete traces retain their own evidentiary meaning. | Recovery and continuation are unspecified. |
| Wallet/model interaction or adaptive action selection cannot proceed after a trajectory has begun | Evaluation Runner detects the missing required interaction at the exercise boundary and contains live state to that case context. | Not specified. | An ordered attributable prefix may have been observed, but the supplied requirements do not decide whether it is saved or qualifies as a produced case trace. Other complete traces remain attributable evidence. | Retry, resume, and partial-trace persistence are unspecified. |
| Ordered capture or attribution fails | Evaluation Runner detects that it cannot satisfy R-4, R-5, or R-6 and must not represent the affected evidence as a requirement-compliant attributable trace. | Not specified. | Any evidence whose order, identity, or required adaptive basis is missing is insufficient for the required trace contract. Unaffected complete traces remain valid. | Retry and incomplete-result behavior are unspecified. |
| Durable run-result saving fails or does not establish a complete identifiable result | Evaluation Runner detects failure at the persistence boundary. | The primary workflow cannot complete successfully. | In-memory or partially written material does not establish the required durable run result. Previously saved independent results are unaffected. | Retry, atomic-write, cleanup, and resume semantics are unspecified. |

An undesirable or incorrect Wallet response is not, by itself, a runner failure. If the interaction and capture contracts remain available, that response and its observable consequences are evidence to preserve; judging them is downstream.

The unspecified continuation, retry, resume, partial-trace, and partial-result policies are not blockers to this HLD because the successful path and the conditions for claiming its successful outcome are coherent without selecting those policies.

## 8. Architectural decisions and unresolved blockers

### Decisions forced by supplied requirements

| Decision | Driver |
| --- | --- |
| Establish run and case-execution identity before capturing evidence. | WF-3 through WF-5; BC-7, BC-10; R-1, R-4, R-6 |
| Give every case execution fresh, controllable Wallet state isolated from all other case executions. | WF-1, WF-2; BC-1, BC-5; R-2; IR-2 |
| Capture evidence at the Wallet exercise boundary in distinguishable occurrence order and preserve complete Wallet responses and relevant observable changes. | WF-2 through WF-4; BC-6, BC-8; R-3, R-4; IR-3 |
| Preserve adaptive selections and their participant-visible factual basis, while excluding private reasoning. | BC-4, BC-8; R-3, R-5; IR-3 |
| Bind each trace to the effective execution context that produced it. | WF-4, WF-5; BC-9, BC-10; R-6 |
| Persist one identifiable run result as files outside the Wallet execution runtime. | WF-5; BC-11; R-7; IR-4; proposed MVP boundary |

### Minimal design choices

| Choice | Concrete driver |
| --- | --- |
| Keep R-1 through R-7 in one Evaluation Runner component. | Their state and control flow form one run lifecycle, and no supplied behavior requires independent ownership, deployment, or synchronization. |
| Use serial case scheduling as the baseline. | One-or-more-case execution is satisfied without production-scale orchestration or parallel execution, both of which are explicitly deferred. |
| Treat case-scoped execution contexts as runtime isolation units rather than logical components. | BC-5 requires state isolation, not a separately accountable service or subsystem. |

### Intentionally unresolved choices

- physical isolation mechanism;
- exact observation and tracing mechanism;
- serialized trace schema, file layout, and compatibility policy;
- persistence completion or atomicity mechanism; and
- retry, skip, abort, resume, partial-trace, and incomplete-run behavior.

These choices are not required to allocate responsibilities or explain the successful workflow. They must not be inferred from generic operational practice.

### Blockers

None.
