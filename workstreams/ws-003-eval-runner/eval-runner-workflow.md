{
  "blockers": [],
  "workflow": {
    "initiating_trigger": "An evaluation operator starts a run by choosing a test-run configuration that specifies the synthetic case set or run scope and the Wallet and model configuration to exercise.",
    "mvp_value": "Turn a chosen configuration of synthetic test cases into saved execution results that establish what ran and what Wallet did, so the behavior can be assessed later without rerunning the original execution.",
    "name": "Run configured Wallet evaluation cases and save their results",
    "principal_actor": "Evaluation operator",
    "source_refs": [
      {
        "line_end": 11,
        "line_start": 5,
        "path": "docs/product/evaluation-subsystem-frame.md",
        "supports": "Places the workflow start at case and Wallet/model configuration selection and states that the subsystem records what was exercised and what Wallet did without deciding correctness."
      },
      {
        "line_end": 20,
        "line_start": 17,
        "path": "docs/product/evaluation-subsystem-frame.md",
        "supports": "Observes selected or full-corpus execution against identified inputs, isolated case state, and preservation of inputs, outputs, final state, runtime events, and telemetry."
      },
      {
        "line_end": 68,
        "line_start": 60,
        "path": "docs/product/evaluation-subsystem-frame.md",
        "supports": "Shows the operator can execute isolated cases with a targeted cohort or full dataset and retain responses, errors, final state, runtime evidence, and provenance."
      },
      {
        "line_end": 139,
        "line_start": 127,
        "path": "docs/product/evaluation-subsystem-frame.md",
        "supports": "Defines selection of cases and Wallet/model configuration, clean state between cases, fixed or response-adaptive execution, and capture of observable behavior and provenance."
      },
      {
        "line_end": 190,
        "line_start": 181,
        "path": "docs/product/evaluation-subsystem-frame.md",
        "supports": "Excludes correctness grading and avoids committing the result-saving workflow to a particular storage layout or viewer mechanism."
      }
    ],
    "steps": [
      {
        "action": "Choose the run configuration that determines which synthetic test cases will execute, such as a targeted set or broader corpus, together with the Wallet and model inputs for that run.",
        "id": "S1"
      },
      {
        "action": "Execute each configured case against Wallet in clean, isolated state, following its fixed interaction sequence or its bounded response-adaptive choices.",
        "id": "S2"
      },
      {
        "action": "Capture each case's inputs, Wallet public responses, response-dependent choices when applicable, final public state, errors, runtime evidence, and Wallet, model, and run-configuration provenance as the execution proceeds.",
        "id": "S3"
      },
      {
        "action": "Collect the captured case records for the run and save them as durable, inspectable result artifacts associated with the run and case identities.",
        "id": "S4"
      }
    ],
    "successful_outcome": {
      "description": "The configured case set has been executed, and its captured per-case results have been collected and saved as an identifiable run result that shows what was exercised and what Wallet did without assigning a behavioral verdict.",
      "id": "O1"
    }
  }
}
