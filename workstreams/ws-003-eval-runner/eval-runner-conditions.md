{
  "blockers": [],
  "analysis": {
    "conditions": [
      {
        "id": "BC-1",
        "condition": "The identified Wallet can be instantiated in a separate controllable state for each selected case.",
        "supports": ["WF-1"]
      },
      {
        "id": "BC-2",
        "condition": "Each selected case defines the starting conditions needed for its Wallet setup.",
        "supports": ["WF-1"]
      },
      {
        "id": "BC-3",
        "condition": "The identified Wallet and model are available for interaction under the selected run configuration.",
        "supports": ["WF-2"]
      },
      {
        "id": "BC-4",
        "condition": "Each selected case defines how its participant actions are supplied, including the role, allowed actions, and other bounds for response-adaptive cases.",
        "supports": ["WF-2"]
      },
      {
        "id": "BC-5",
        "condition": "Before a case execution begins, its Wallet state reflects the case starting conditions and is isolated from every other case execution.",
        "supports": ["WF-2"]
      },
      {
        "id": "BC-6",
        "condition": "The participant actions, Wallet responses, and relevant resulting changes are observable with their occurrence order distinguishable.",
        "supports": ["WF-3"]
      },
      {
        "id": "BC-7",
        "condition": "Each case execution has a distinguishable case identity and run membership before evidence from its trajectory is captured.",
        "supports": ["WF-3"]
      },
      {
        "id": "BC-8",
        "condition": "For each executed case, an attributable trace exists that preserves the captured observable trajectory in occurrence order and, for a response-adaptive case, the selected actions and participant-visible response facts on which they were based.",
        "supports": ["WF-4", "WF-5", "OUTCOME"]
      },
      {
        "id": "BC-9",
        "condition": "The Wallet, model, environment, and other relevant settings that governed each case execution are known when its trace is associated.",
        "supports": ["WF-4"]
      },
      {
        "id": "BC-10",
        "condition": "Every produced case trace is associated with its originating case execution, the run identity, and the execution configuration that produced it.",
        "supports": ["WF-5", "OUTCOME"]
      },
      {
        "id": "BC-11",
        "condition": "A persistence destination is available that can retain the complete run result independently of the Wallet execution runtime.",
        "supports": ["WF-5", "OUTCOME"]
      }
    ]
  }
}
