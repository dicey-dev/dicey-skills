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

Before each task, ask: "Should I delegate this task, or do it myself?" Think
about:

- Would delegating get the whole job done faster?
- Can I work on something else while the child runs?
- Can several pieces run in parallel as separate children?
- Does the task need less intelligence than I have?

If any answer is yes, delegate. When the user says "offload", always delegate.

## 2. Pick the agents

Run `python scripts/offload.py next`. Add `--user` when the user named the
model. It prints a call number and a branch. The script keeps a fixed 3:2
cycle, so 6 of every 10 calls exploit and 4 explore.

- **user**: use the model the user named. If they gave no effort, use high.
- **exploit**: pick one agent yourself. Run
  `python scripts/offload.py history --grep <word>` to see how each model and
  effort scored on similar tasks, and choose the best fit. Match the agent to
  the intelligence the task needs: running tests or parsing logs needs little,
  debugging or browser use needs more. With no similar history, start with
  Sonnet 5.5 on high for code and technical work, or GPT-6.1 Sol on high for
  research and audits.
- **explore**: the script names two agents (model and effort) from different
  providers, favoring the least tried. Run both on the same task at the same
  time, then use the better result.

To change the explore pool, edit `MODELS` and `EFFORTS` in the script.

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

Score each child run from 0 to 5 on every dimension. The scores are stored
separately, in this order:

1. **Correctness**: the result is right.
2. **Completeness**: every acceptance criterion is met.
3. **Adherence**: it followed the brief and stayed in scope.
4. **Evidence**: its claims are backed by evidence you could verify.
5. **Clarity**: the report is clear and concise.
6. **Efficiency**: it finished quickly, without wasted steps.
7. **Independence**: it needed no follow-up or rework from you.

Add a one-line review naming what the run did well and what it did badly. Then
record every run, failures included:

```sh
python scripts/offload.py record --call <number> --task "<one-line task description>" \
  --run <model> <effort> <s1,s2,s3,s4,s5,s6,s7> "<review>" \
  [--run <model> <effort> <s1,...,s7> "<review>"]
```

Use `-` in place of the scores for a run that was cancelled or blocked by
infrastructure. The script appends one row per run to `history.csv` in this
skill's folder. Do not edit that file by hand.
