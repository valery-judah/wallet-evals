{
  "blockers": [],
  "analysis": {
    "conditions": [
      {
        "id": "BC-1",
        "condition": "Recorded identities unambiguously associate each case trace and its evidence with the originating run, case execution, and case, while timestamps establish occurrence order only.",
        "supports": ["WF-1", "WF-2", "WF-3"]
      },
      {
        "id": "BC-2",
        "condition": "The evidence used for judgment is the evidence preserved in the saved trace; unsupported semantics, missing evidence, and unresolved joins remain identifiable rather than being reconstructed or invented.",
        "supports": ["WF-1", "WF-3"]
      },
      {
        "id": "BC-3",
        "condition": "The selected trace identifies one distinguishable case execution as the sole correctness judgment unit.",
        "supports": ["WF-2", "WF-3", "WF-4"]
      },
      {
        "id": "BC-4",
        "condition": "The selected case's purpose, dimensions, interaction form, declared initial conditions, and applicable evaluation basis are known for the judgment.",
        "supports": ["WF-3", "WF-4"]
      },
      {
        "id": "BC-5",
        "condition": "The trace evidence can be followed in occurrence order, and case context, participant actions, Wallet behavior and errors, adaptive choices, observations, and diagnostics remain distinguishable by evidence role and origin.",
        "supports": ["WF-3"]
      },
      {
        "id": "BC-6",
        "condition": "Each captured Wallet response available for judgment is complete, any response summary is identifiable as a derived view, and the exact captured evidence remains inspectable.",
        "supports": ["WF-3"]
      },
      {
        "id": "BC-7",
        "condition": "Each adaptive choice identifies its selected action and cited participant-visible response facts; each observation identifies its subject, capture point, boundary, and source; and each presented diagnostic is attributable to its originating step.",
        "supports": ["WF-3"]
      },
      {
        "id": "BC-8",
        "condition": "A pass or fail disposition is valid only when the saved trace supports an attributable whole-case judgment against the identified evaluation basis; otherwise the valid disposition is not judgeable.",
        "supports": ["WF-3", "WF-4", "OUTCOME"]
      },
      {
        "id": "BC-9",
        "condition": "At the point of saving, the review record identifies the run, selected trace, case execution, evaluation basis, judge, and exactly one whole-case disposition of pass, fail, or not judgeable.",
        "supports": ["WF-4", "OUTCOME"]
      },
      {
        "id": "BC-10",
        "condition": "For a fail disposition, the review record identifies the first observable failure in a short note and an evidence location that resolves to the relevant evidence in the selected trace.",
        "supports": ["WF-4", "OUTCOME"]
      },
      {
        "id": "BC-11",
        "condition": "The completed review record can be retained independently of the saved execution evidence, and retaining it leaves the saved trace unchanged.",
        "supports": ["WF-4", "OUTCOME"]
      }
    ]
  }
}
