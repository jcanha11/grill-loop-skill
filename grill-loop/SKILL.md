---
name: grill-loop
description: Stress-test and iteratively improve product, strategy, and experiment plans with a stateful scored loop, independent Grill and Judge roles, optional evidence research, supervised or autonomous escalation, versioned drafts, and explicit stopping rules. Use when the user asks for a grill loop, autonomous plan review, repeated plan refinement, loop engineering for a proposal, or a multi-agent critique-and-revision workflow.
---

# Grill Loop

Run an auditable improvement loop around one plan. Preserve the original, resolve one design branch per iteration, and stop only through deterministic quality rules.

## Preconditions

1. Accept product, strategy, or experiment plans. For another domain, state that the bundled rubric is not calibrated and use `supervised` mode unless the user supplies a replacement rubric.
2. Require an explicit mode: `supervised` or `autonomous`. If absent, use `supervised` and say so.
3. Verify that the user explicitly authorized subagents. Autonomous mode requires this authorization. If it is missing, ask once; do not simulate independent agents while claiming multi-agent review.
4. Normalize pasted or non-Markdown input into a Markdown working source. Do not edit the user's original file.
5. Read [references/rubric.md](references/rubric.md) and [references/role-contracts.md](references/role-contracts.md) before the first run.

## Initialize

Run:

```bash
python3 <skill-dir>/scripts/grill_state.py init \
  --source <normalized-plan.md> \
  --mode <supervised|autonomous> \
  --run-dir <workspace>/.grill-loop
```

If that run directory already contains a state file, resume it or select another explicit run directory. Never replace an active run.

The command creates:

- `state.json`: machine-readable run state and score history.
- `decisions.md`: append-only human-readable decision log.
- `drafts/000-baseline.md`: immutable normalized baseline.

## Iterate

Repeat one branch at a time. Never batch several questions into one iteration.

### 1. Grill

Spawn a fresh Grill subagent with only the current draft, rubric, and unresolved-item list. Ask for the single highest-impact unresolved problem in the structured format from `role-contracts.md`.

If no subagent capability is available:

- In `supervised` mode, disclose the limitation and continue one question at a time with the user.
- In `autonomous` mode, stop. Independent adjudication is a required capability, not an optional presentation style.

If a subagent call fails due to tooling or model/runtime errors, retry that same role once with a fresh subagent and the same allowed context. If the same role fails twice:

- In `supervised` mode, pause and ask the user whether to retry, switch to manual review, or stop.
- In `autonomous` mode, run `grill_state.py abort --reason subagent_failure --detail <role-and-error-summary>` and stop. Do not let the main agent silently replace an independent Judge or Research role.

### 2. Route

Classify the question by consequence, uncertainty, and reversibility—not by how simple it sounds.

- `FAST_PASS`: all fast-pass conditions in the rubric hold. Record it without invoking Judge.
- `RESEARCH`: evidence is discoverable in authorized local files, code, SQL, configuration, or provided sources. Spawn a read-only Research subagent, then continue to Judge.
- `JUDGE`: the issue is disputed, high-impact, evidence-conflicted, or changes goals, mechanics, metrics, guardrails, or meaningful resources.
- `ESCALATE`: required business facts or authority are unavailable.

Never fast-pass a veto candidate.

### 3. Prepare a candidate

For `RESEARCH`, `JUDGE`, or autonomous `ESCALATE`, copy the current snapshot to a temporary candidate and apply only the proposed branch. Do not add it to the version history yet.

For supervised `ESCALATE`, keep the current draft unchanged until the user decides.

### 4. Judge

Spawn a fresh Judge subagent for every non-fast-pass route. Do not give it the Grill agent's hidden reasoning or the main agent's preferred answer. Give it only:

- current draft;
- proposed candidate when one exists;
- one issue packet;
- Research evidence when present;
- fixed rubric;
- unresolved constraints.

Require the Judge to decide whether the candidate should replace the current draft and score the artifact that would remain after its decision:

- `ACCEPT` or `CONSERVATIVE`: score the candidate.
- `REJECT` or `USER_REQUIRED`: score the current draft.

Require rubric scores, vetoes, confidence, decision, rationale, and the scored artifact's SHA-256 in the structured format from `role-contracts.md`. The state CLI rejects stale scores whose hash does not match the retained artifact.

For `FAST_PASS`, reuse the last complete score because the change is non-material. If no complete score exists yet, route to Judge instead.

### 5. Handle escalation

- `supervised`: record `ESCALATE`, pause, and ask the user exactly one concise question with a recommended answer. After the response, resume with `record --resume`.
- `autonomous`: choose the least-assumptive reversible branch, mark it `CONSERVATIVE`, keep the item in the final escalation list, and continue. Never invent missing facts.

### 6. Accept or discard the candidate

When the decision accepts a candidate:

1. Preserve explicit unknowns and conditional language.
2. Pass the candidate to the state CLI so it becomes the next immutable snapshot.
3. Discard a rejected candidate.
4. Do not overwrite the original source.
5. Ensure the decision packet sets `material_new_issue=true` for any accepted or conservative non-`FAST_PASS` candidate.

### 7. Record

Write one decision packet JSON using `role-contracts.md`, then run:

```bash
python3 <skill-dir>/scripts/grill_state.py record \
  --run-dir <workspace>/.grill-loop \
  --input <decision-packet.json> \
  --candidate <candidate.md>
```

Omit `--candidate` when no draft change was accepted. Add `--resume` only after resolving a supervised pause.

Never pass `--candidate` for `FAST_PASS`; a fast pass is non-material by definition.

Inspect the command's JSON output. Continue only while `status` is `active`.

## Stop and deliver

The state CLI owns the stopping decision. Defaults:

- no vetoes;
- score at least 85/100;
- no open high-impact item;
- two consecutive iterations with no material new issue;
- stagnation when improvement is under 3 points across two intervals;
- hard limit of 10 iterations.

On completion, run:

```bash
python3 <skill-dir>/scripts/grill_state.py finalize \
  --run-dir <workspace>/.grill-loop
```

Deliver:

- `final.md`;
- score and terminal status (`passed`, `conditional_pass`, or `stopped`);
- concise major-change summary;
- unresolved escalations and vetoes;
- link to `decisions.md`.

Do not apply `final.md` back to the original unless the user explicitly requests it.

## Invariants

- Keep the Controller deterministic; do not let an agent declare itself finished outside the state rules.
- Keep Grill and Judge contexts independent.
- Let subagents research and judge; do not let them concurrently edit shared state or drafts.
- Record every fast pass, rejection, conservative choice, and escalation.
- Cite evidence by local path and location when available.
- Never convert missing evidence into certainty.
- Preserve both modes permanently: they are execution policies over one engine, not separate implementations.
