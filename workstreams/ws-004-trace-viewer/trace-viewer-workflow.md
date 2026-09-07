# Primary end-to-end workflow

**Principal actor:** Domain expert acting as the judge

**Initiating trigger:** The judge starts a review of one previously saved evaluation run in order to judge a contained case execution.

| ID | Workflow step |
| --- | --- |
| `WF-1` | **Open the saved run for review.** Make its recorded case traces available while retaining the identities and provenance carried by the saved evidence. |
| `WF-2` | **Select one case trace.** Choose the case execution to judge using its recorded trace and case identity. |
| `WF-3` | **Review the case execution as a whole.** Apply the visible evaluation basis to the case context and the attributable, ordered evidence, including participant actions, complete Wallet responses, adaptive choices, named observations, and Wallet errors. Keep those evidence roles distinct and inspect exact captured evidence or step-linked diagnostics when needed to support the judgment. |
| `WF-4` | **Record one whole-case disposition.** Save pass, fail, or not judgeable as a review record keyed to the selected saved trace and separate from its execution evidence. Identify the run, trace, case execution, evaluation basis, and judge; for a fail disposition, also record a short first-observable-failure note linked to the relevant trace evidence. |

**Successful outcome:** One attributable review record is saved for the selected case execution, containing its pass, fail, or not-judgeable disposition and the required evidence-linked first-failure explanation when it failed, while the saved trace remains unchanged.

## Result provenance

### Derived inputs

- None.

### Authoritative basis

- `docs/product/evaluation-trace-viewer-frame.md`
