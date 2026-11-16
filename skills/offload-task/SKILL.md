---
name: offload-task
description: >-
  Offload work that needs less intelligence than the current model to a cheaper
  T3 Code subagent, then verify, score, and report the result. Use when the user
  says "offload" (optionally naming a model and reasoning effort; default
  GPT-6.1 Sol on high), and proactively whenever the parent agent (e.g. Opus)
  has a task a lighter model can handle, such as running tests, research,
  browser use, log digging, or mechanical edits.
---

# Offload task

The parent keeps decisions, verification, and the final answer. The child does
the execution.

## When to offload

- **User asks**: "offload ..." with an optional model and effort. Missing model
  defaults to **GPT-6.1 Sol**, missing effort to **high**. Never override what
  the user named.
- **Parent decides**: the task needs less intelligence than the parent model.
  Examples: Opus offloads test runs to Sonnet 5.5, or research to GPT-6.1 Sol.
  Skip it when the brief would cost more than doing the task directly.

## Pick the model

1. Read **Historical performance** below. Find rows with a similar task type.
2. **Exploit**: choose the cheapest model and effort that scored 8 or more on
   similar work. With no data, use GPT-6.1 Sol on high.
3. **Explore**: about 1 in every 10 parent-chosen offloads, try a model or
   effort with little or no history. Only explore on low-risk tasks.
4. **Dual run** (optional): send the same task to two models from different
   providers (e.g. Sonnet 5.5 and GPT-6.1 Sol), and keep the better result.
   Use it for exploring, or when a wrong result is costly. Run edits in
   separate worktrees. Never run two editors in the same checkout.

Candidates: Sonnet 5.5, GPT-6.1 Sol, Haiku 5.5, plus any other models
`orchestrator_capabilities` lists.

## Delegate

1. Call `orchestrator_capabilities` once per thread. Resolve the exact provider
   instance, model ID, and effort option. If something is unavailable, tell the
   user. Never substitute quietly.
2. Call `delegate_task`, with the effort in `target.options`. Use
   `isolation: "worktree"` when the task edits files in parallel with other
   work. The child does not see this thread, so write a self-contained brief:

   ```text
   Goal: <one bounded task>
   Context: <key facts, absolute paths, commands>
   Scope: <allowed tools/paths; no commits, pushes, or sub-delegation unless stated>
   Done when: <acceptance criteria>
   Report: outcome, evidence (exit codes, citations, file paths), blockers. Be brief.
   ```

3. Follow the returned `next`. Do not poll. Cancel runs you no longer need with
   `task_cancel`.

## Verify and report

- Check the evidence: the decisive test output, the diff, or the cited sources.
  A missing report, missing evidence, or a timeout counts as failure.
- Report to the user: the outcome, the evidence, the child thread link, and any
  open issues. Do not forward raw logs.

## Score and record

After every finished offload, score each child run from 0 to 10:

- **Correctness** (0–5): is the result right?
- **Completeness** (0–3): does it meet every acceptance criterion?
- **Report quality** (0–2): is the evidence verifiable and the report concise?

Then append one row per child run to the table below. Use `—` for runs that
were cancelled or blocked by infrastructure, and give the reason in Notes. Never
add made-up or example rows. Edit only this source file
(`dicey-skills/skills/offload-task/SKILL.md`), and do not commit it unless the
user asks.

| Column | Value |
| --- | --- |
| Date | UTC date, `YYYY-MM-DD` |
| Task type | `tests`, `research`, `browser`, `edit`, `analysis`, or `other` |
| Model | the resolved model name |
| Effort | the effort actually used |
| Mode | `single`, or `dual:<other model>` |
| Selection | `user`, `default`, `exploit`, or `explore` |
| Score | 0–10, or `—` |
| Notes | under 15 words: what went well or wrong; for dual runs, which won |

## Historical performance

| Date | Task type | Model | Effort | Mode | Selection | Score | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
