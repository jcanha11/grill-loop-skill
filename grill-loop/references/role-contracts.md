# Role contracts and packets

Subagents return JSON-compatible content and do not edit shared files.

## Grill packet

Return exactly one issue:

```json
{
  "question": "One decision question",
  "why_it_matters": "Impact on the plan",
  "recommended_answer": "Grill agent recommendation",
  "affected_dimensions": ["measurement and experiment design"],
  "needs_research": false,
  "potential_veto": false
}
```

Choose the highest-impact unresolved branch. Do not repeat an issue already resolved in the decision log.

## Research packet

Return evidence, not a decision:

```json
{
  "question": "Question researched",
  "findings": [
    {
      "source": "/absolute/path/to/file.md:42",
      "fact": "Relevant fact",
      "reliability": "primary"
    }
  ],
  "conflicts": [],
  "unresolved": []
}
```

Use `primary`, `secondary`, or `inferred` reliability. Label inference explicitly.

## Decision packet

Write this packet to a temporary JSON file for `grill_state.py record`:

```json
{
  "question": "One decision question",
  "route": "JUDGE",
  "recommendation": "Recommended answer",
  "decision": "ACCEPT",
  "rationale": "Why the route and decision are justified",
  "impact": "What changes in the draft",
  "confidence": 0.86,
  "evidence": [
    {
      "source": "/absolute/path/to/file.md:42",
      "fact": "Supporting fact"
    }
  ],
  "score": 87,
  "dimension_scores": {
    "objective_target": 14,
    "evidence_denominator": 17,
    "mechanism": 13,
    "measurement": 14,
    "execution": 13,
    "risks": 8,
    "clarity": 8
  },
  "vetoes": [],
  "high_impact_open": [],
  "material_new_issue": true,
  "artifact_sha256": "64 lowercase hexadecimal characters"
}
```

Allowed routes: `FAST_PASS`, `RESEARCH`, `JUDGE`, `ESCALATE`.

Allowed decisions: `ACCEPT`, `REJECT`, `CONSERVATIVE`, `USER_REQUIRED`.

Rules:

- `FAST_PASS` requires confidence >= 0.90 and no vetoes.
- `ESCALATE` in supervised mode requires `USER_REQUIRED`.
- `ESCALATE` in autonomous mode uses `CONSERVATIVE` when a safe branch exists.
- Scores are for the complete current draft, not just the current issue.
- For `ACCEPT` or `CONSERVATIVE`, score the proposed candidate and set `artifact_sha256` to that candidate's SHA-256.
- For `REJECT` or `USER_REQUIRED`, score the unchanged current draft and set `artifact_sha256` to the current draft's SHA-256.
- Dimension scores must use the keys and maxima defined by the rubric and sum to `score`.
- Set `material_new_issue` to true when the iteration identifies a new high-impact defect or changes a core plan decision.
- Set `material_new_issue` to true for every accepted or conservative candidate on a non-`FAST_PASS` route. The state CLI rejects accepted candidates marked as non-material.
- `FAST_PASS` is non-material and must not include a candidate draft.

## User resolution packet

After a supervised pause, use the normal decision packet shape, replace the prior route with `JUDGE`, include the user's answer in `rationale`, and invoke `record --resume`.

## Agent isolation

- Grill sees the current draft, rubric, and resolved-question summaries. It does not see Judge hidden reasoning.
- Research sees the question and authorized source scope. It does not choose a plan branch.
- Judge sees the current draft, proposed candidate when present, issue packet, evidence packet, rubric, and unresolved constraints. It does not see the main agent's preferred answer beyond the explicit recommendation and candidate.
- The main agent alone writes candidates and invokes the state CLI.
