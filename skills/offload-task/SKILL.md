---
name: offload-task
description: >-
  Offload work that needs less intelligence than the current model to a cheaper
  T3 Code subagent, then verify, score, and record the result. Use when the user
  says "offload" (optionally naming a model and reasoning effort). Also, before
  each task such as code changes, tests, browser use, research, or audits, ask
  yourself: "Should I delegate this task, or do it myself?" If the answer is
  delegate, use this skill. Starting defaults are Sonnet 5.5 on high for code
  and technical work, and GPT-6.1 Sol on high for research and audits. After
  that, recorded performance decides the defaults.
---

# Offload task

The parent keeps decisions, verification, and the final answer. The children do
the execution. `scripts/offload.py` below means the script in this skill's
folder.

## 1. Delegate, or do it myself?

Before each task, ask: "Can I delegate this task, or should I do it myself?"
Delegate only when all three are true:

- A lighter model can do it well.
- It fits in a short, self-contained brief.
- Checking the result costs less than doing the work.

Otherwise, do it yourself. When the user says "offload", always delegate.

## 2. Pick the agents

Choose a category. `code` covers code, tests, builds, debugging, and browser
use. `research` covers research, audits, reviews, and analysis.

- **The user named a model**: use it. If they gave no effort, use high. Skip
  `select` and record the run with `--branch user`.
- **Otherwise**: run
  `python scripts/offload.py select --category <code|research> --exclude <parent model>`.

The script tracks decisions in `state.json` and keeps a fixed 3:2 cycle, so 6 of
every 10 decisions exploit and 4 explore:

- **exploit** returns one agent: the current default for the category. Defaults
  start as Sonnet 5.5 on high for `code` and GPT-6.1 Sol on high for `research`.
  Once a model and effort have 3 or more scored runs, the one with the best
  average score becomes the default.
- **explore** returns two agents from different providers, favoring the least
  tried. Run both on the same task at the same time, then use the better
  result.

To change the model pool, edit `MODELS` in the script.

## 3. Delegate

1. Call `orchestrator_capabilities` once per thread. Resolve each label to its
   exact provider instance, model ID, and effort option. If something is
   unavailable, tell the user. Never substitute quietly.
2. Call `delegate_task` once per agent, with the effort in `target.options`. For
   explore, start both runs in the same turn. If they edit files, give each one
   `isolation: "worktree"`. The children cannot see this thread, so write a
   self-contained brief:

   ```text
   Goal: <one bounded task>
   Context: <key facts, absolute paths, commands>
   Scope: <allowed tools/paths; no commits, pushes, or sub-delegation unless stated>
   Done when: <acceptance criteria>
   Report: outcome, evidence (exit codes, citations, file paths), blockers. Be brief.
   ```

3. Follow the returned `next`. Do not poll. Cancel runs you no longer need with
   `task_cancel`.

## 4. Verify and report

- Check the evidence: the decisive test output, the diff, or the cited sources.
  A missing report, missing evidence, or a timeout counts as a failure.
- For explore, compare the two outputs and keep the better one. Discard the
  other run's changes.
- Report to the user: the outcome, the evidence, the child thread links, and
  any open issues. Do not forward raw logs.

## 5. Score and record

Score each child run from 0 to 10:

- **Correctness** (0–5): is the result right?
- **Completeness** (0–3): does it meet every acceptance criterion?
- **Report quality** (0–2): is the evidence verifiable and the report concise?

Then write a one-line review naming what the run did well and what it did badly.
Record every run, failures included. Use `-` as the score for runs that were
cancelled or blocked by infrastructure.

```sh
python scripts/offload.py record --branch <exploit|explore|user> --category <code|research> \
  --run <model> <effort> <score> "<review>" [--run <model> <effort> <score> "<review>"]
```

The script updates `state.json` and appends one row per run to the table below.
Do not edit the table by hand, and do not commit it unless the user asks.
`python scripts/offload.py status` shows the counters and the current defaults.

## Historical performance

| Date | Call | Branch | Category | Model | Effort | Score | Won | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
