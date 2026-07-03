# Grill Loop

Grill Loop is a Codex skill for stress-testing and improving product, strategy, and experiment plans through an auditable review loop.

It extends the idea behind `grill-me`: keep asking the hard questions, but avoid forcing a human to sit in the loop for every small decision.

## Why not just use Grill Me?

`grill-me` is valuable because it asks detailed, one-question-at-a-time follow-ups. That is also the operational bottleneck: every question waits for a human response, including questions that are low-risk, reversible, or answerable from available evidence.

Grill Loop changes the operating model:

- simple and reversible questions can fast-pass;
- questions answerable from local evidence go through research;
- important or disputed questions go to an independent judge;
- only questions requiring unavailable business facts, authority, or risk acceptance escalate to the human.

The goal is not to replace human judgment. The goal is to reserve human attention for the decisions that actually need it.

## What it does

Grill Loop runs one plan through a stateful loop:

1. A Grill role finds the highest-impact unresolved issue.
2. The controller routes the issue as `FAST_PASS`, `RESEARCH`, `JUDGE`, or `ESCALATE`.
3. A candidate revision is prepared when appropriate.
4. A Judge role scores the retained artifact with a fixed rubric.
5. The state manager records the decision and decides whether the loop should continue.

The skill preserves:

- the original source plan;
- immutable draft snapshots;
- machine-readable state in `state.json`;
- a human-readable decision log in `decisions.md`;
- explicit terminal status and unresolved escalations.

## Modes

Grill Loop has one engine with two execution policies.

### Supervised

Use this when you want the loop to automate simple work but pause for human decisions.

```text
Use $grill-loop in supervised mode to stress-test and improve this plan.
```

### Autonomous

Use this when you explicitly authorize subagents and want the loop to continue without interrupting you unless no safe conservative branch exists.

```text
Use $grill-loop in autonomous mode with specialized subagents to improve this plan.
You may choose conservative reversible branches, but keep unresolved business decisions in the final escalation list.
```

Autonomous mode must not invent missing facts. If the loop cannot safely continue, it should stop with unresolved items rather than pretend certainty.

## Installation

Copy the skill folder into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R grill-loop ~/.codex/skills/grill-loop
```

Then restart Codex or start a new session so the skill is discovered.

## Repository layout

```text
grill-loop/
  SKILL.md
  agents/openai.yaml
  references/
    role-contracts.md
    rubric.md
  scripts/
    grill_state.py
    test_grill_state.py
  tests/
    fixtures/flawed-plan.md

grill-loop-visual/
  index.html
```

`grill-loop-visual/index.html` is an optional explainer page. It is not required for the skill to run.

## Validation

Run the deterministic state-manager tests:

```bash
python3 -m unittest grill-loop/scripts/test_grill_state.py
```

Expected result:

```text
Ran 12 tests
OK
```

## How to evaluate whether it is useful

The skill should be judged by measurable workflow impact, not by whether the idea sounds elegant.

Useful evaluation metrics:

- Human interruption rate: how many questions require user input per review.
- Review completion rate: how often the loop reaches `passed` or `conditional_pass`.
- Quality lift: score improvement from baseline to final draft.
- Decision auditability: whether another reviewer can understand why each branch was accepted, rejected, or escalated.
- False autonomy rate: how often autonomous mode makes assumptions that should have escalated.
- Time to decision: elapsed time from initial plan to final artifact.

The first success criterion is simple: compared with `grill-me`, the user should spend less active attention while still receiving a sharper, better-scored plan.

## Status

This is an experimental v0.1 skill. It is suitable for local use and method exploration. Treat autonomous runs as conservative review assistance, not as authority to launch, spend budget, change production systems, or make irreversible business decisions.

## License

MIT. See [LICENSE](LICENSE).
