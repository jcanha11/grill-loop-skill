# Promotion kit

Use this page when launching Grill Loop publicly. The goal is to send people to the visual explainer first, then let the README convert them into installers.

Primary links:

- Visual explainer: <https://jcanha11.github.io/grill-loop-skill/grill-loop-visual/>
- Repository: <https://github.com/jcanha11/grill-loop-skill>
- One-line install:

```bash
curl -fsSL https://raw.githubusercontent.com/jcanha11/grill-loop-skill/main/install.sh | bash
```

## Positioning

One sentence:

> Grill Loop turns deep AI questioning into an auditable self-running review loop, so humans only answer the hard questions.

Chinese:

> Grill Loop 把 AI 的连续拷问变成可自循环、可审计的方案评审系统，让人只处理真正需要人的问题。

Avoid positioning it as just "a Codex skill." That is implementation detail. The public value is the workflow: less human babysitting, better plan review, explicit logs, independent judgment, safe stopping.

## Short launch copy

### English

I built Grill Loop: a self-running critique loop for AI agents.

The problem: `grill-me` style review is valuable because it asks detailed questions, but every question waits for a human. That means even simple, reversible, researchable questions consume attention.

Grill Loop routes each question:

- `FAST_PASS` for simple reversible items
- `RESEARCH` when evidence is available
- `JUDGE` for important or disputed decisions
- `ESCALATE` only when a human has the missing fact or authority

It keeps versioned drafts, `state.json`, `decisions.md`, scoring, vetoes, and stop rules.

Demo: https://jcanha11.github.io/grill-loop-skill/grill-loop-visual/
Repo: https://github.com/jcanha11/grill-loop-skill

### 中文

我做了一个 Grill Loop：让 AI 的连续拷问自循环起来。

问题是：`grill-me` 这类方案拷问很有价值，因为它问得细；但每一问都等人回答。重要问题值得人判断，但大量简单、可逆、可查证的问题也会持续占用人的注意力。

Grill Loop 会自动分流每个问题：

- `FAST_PASS`：简单、可逆、高置信，自动通过
- `RESEARCH`：资料里有答案，先查证
- `JUDGE`：重要或有争议，交给独立 Agent 裁决
- `ESCALATE`：只有人知道事实或有权限时，才打断人

它会保留版本草稿、`state.json`、`decisions.md`、评分、否决项和停止规则。

可视化说明： https://jcanha11.github.io/grill-loop-skill/grill-loop-visual/
GitHub： https://github.com/jcanha11/grill-loop-skill

## Hacker News / Reddit title options

- Show HN: Grill Loop – self-running critique loops for AI agents
- Show HN: I built an auditable AI review loop that only asks humans for exceptions
- I built a multi-agent plan review loop with fast-pass, research, judge, and escalation routes

## X / Twitter thread

1. I built Grill Loop: a self-running critique loop for AI agents.
2. `grill-me` style workflows are powerful because they ask detailed questions. But every question waits for a human.
3. Grill Loop routes each issue: `FAST_PASS`, `RESEARCH`, `JUDGE`, or `ESCALATE`.
4. The key design choice: keep Grill, Research, Judge, and State separate. The critic does not approve its own work.
5. It writes versioned drafts, `state.json`, `decisions.md`, scores, vetoes, and stop reasons.
6. The goal is not to replace human judgment. It is to reserve human attention for decisions that actually need it.
7. Demo: https://jcanha11.github.io/grill-loop-skill/grill-loop-visual/
8. Repo: https://github.com/jcanha11/grill-loop-skill

## LinkedIn post

I open-sourced Grill Loop, a small experiment in AI workflow design.

The insight is simple: deep AI questioning is useful, but the human should not have to answer every single question. Some questions are simple and reversible. Some can be answered from evidence. Some need independent judgment. Only a smaller set truly requires business authority or missing context from a person.

Grill Loop turns that into a stateful review loop:

- Grill finds the highest-impact unresolved issue.
- Research checks available evidence.
- Judge independently scores the retained artifact.
- State records every decision and decides when to stop.

It is experimental, but the goal is practical: reduce human babysitting while making product, strategy, and experiment plans more decision-ready.

Visual explainer: https://jcanha11.github.io/grill-loop-skill/grill-loop-visual/
GitHub: https://github.com/jcanha11/grill-loop-skill

## 中文社群发布稿

我开源了一个 Codex skill：Grill Loop。

它不是想让 AI 替人拍板，而是解决一个很具体的问题：Grill Me 这类方案拷问很有价值，因为它问得细；但它每一问都要等人回复，人必须一直盯着。

Grill Loop 的思路是把问题自动分流：

- 简单可逆的问题自动通过；
- 能从材料中查到的问题先研究；
- 重要或有争议的问题交给独立 Agent 裁决；
- 只有缺业务事实、权限或风险偏好时才升级给人。

所以它的目标不是“全自动取代人”，而是“系统先自循环，人只处理例外”。

可视化说明： https://jcanha11.github.io/grill-loop-skill/grill-loop-visual/
GitHub： https://github.com/jcanha11/grill-loop-skill

## Channel checklist

Use the visual explainer as the first link when the audience is not already inside GitHub.

- GitHub repo: add topics, description, homepage, README preview image.
- Hacker News: post as "Show HN" only after the README and demo page are stable.
- Reddit: post to targeted AI agent / developer productivity communities; avoid generic spam.
- X / Twitter: use the thread above, include the preview image.
- LinkedIn: use the workflow/productivity angle.
- Chinese communities: emphasize "释放人力" and "人只处理例外."
- Newsletters / curators: send one concise email with demo, repo, one-line install, and why it matters.
- Awesome lists: submit only after there is a clear category fit.

## 14-day measurement plan

Track these in GitHub Insights -> Traffic:

- Views and unique visitors.
- Clones.
- Referring sites.
- Popular content.

Track these manually:

- Stars per channel/post.
- Install attempts or issues mentioning install.
- First real user feedback.
- Questions that reveal README confusion.
- Whether visitors land on the visual page or repository first.

Decision rules:

- If visual page views are high but repo stars are low, strengthen the install CTA.
- If repo views are high but clones are low, simplify the README first screen.
- If people ask what it is for, sharpen positioning.
- If people ask how to install, move the one-line install higher.
- If people ask whether it replaces human judgment, make the escalation boundary more prominent.
