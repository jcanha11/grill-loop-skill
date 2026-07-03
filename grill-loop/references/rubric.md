# Product, strategy, and experiment rubric

Score the complete current draft after every material iteration. Use integer scores and explain every deduction that changes the decision.

## Dimensions (100 points)

| Dimension | Points | Required evidence |
| --- | ---: | --- |
| Objective and target population | 15 | Explicit problem, target users, desired outcome, and exclusions |
| Evidence, denominator, and opportunity size | 20 | Source-backed baseline, denominator, affected population, and uncertainty |
| Mechanism and causal chain | 15 | Credible path from intervention to outcome, with key assumptions |
| Measurement and experiment design | 15 | Primary metric, guardrails, definitions, comparison strategy, and decision rule |
| Execution and resources | 15 | Scope, dependencies, owner assumptions, operational path, and rollback |
| Risks and constraints | 10 | User, business, safety, compliance, supply, and concentration risks as applicable |
| Decision clarity | 10 | MVP boundary, alternatives rejected, unknowns, and next decision are explicit |

Do not reward prose volume. A short plan with precise evidence can outscore a long speculative plan.

## Vetoes

Return a veto when any applicable condition holds:

1. The objective or target population is absent or internally contradictory.
2. A central factual claim conflicts with available evidence or cites invented evidence.
3. An experiment has no primary metric, metric definition, denominator, or decision rule.
4. A material irreversible or high-risk action lacks authorization, guardrails, or rollback.
5. A required business fact is unknown but the plan presents it as certain.
6. A known safety, compliance, abuse, or severe user-harm path is ignored.

A veto cannot enter `FAST_PASS`. A terminal `passed` result requires zero vetoes.

## Routing rules

### FAST_PASS

Use only when every condition holds:

- reversible;
- does not change the objective, target population, metric definition, strategy boundary, launch authority, or material resources;
- needs no user-only or unavailable fact;
- evidence is consistent;
- confidence is at least 0.90;
- cannot trigger a veto.

Examples include terminology normalization, adding an already-established source citation, or moving an accepted constraint into the correct section.

### RESEARCH

Use when authorized sources can answer the question. Research before asking the user. Report conflicts and absence of evidence; do not infer agreement from silence.

### JUDGE

Use when the branch may alter a core conclusion, target, mechanism, metric, risk acceptance, or meaningful resource commitment, or when evidence conflicts.

### ESCALATE

Use when the answer requires unavailable facts, business authority, risk acceptance, or a preference the rubric cannot supply.

## Conservative branch

Autonomous mode may continue after escalation only by selecting a branch that is:

- reversible;
- lower exposure or narrower scope;
- explicit about uncertainty;
- non-committal about external launch or resource authorization;
- preserved in the final escalation list.

If no such branch exists, stop with unresolved status rather than fabricate a decision.
