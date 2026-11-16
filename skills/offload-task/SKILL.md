---
name: offload-task
description: >-
  Delegate a task to one or two T3 Code subagents, verify their work, and score
  them so later choices improve. Use when the user says "offload" (optionally
  naming a model and reasoning effort), and proactively whenever delegating
  would finish the work faster, free you to do something else meanwhile, run
  pieces in parallel, or hand work needing less intelligence to a cheaper
  model.
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
model. It prints the branch. The script keeps a fixed 3:2 cycle, so 6 of every
10 calls exploit and 4 explore.

- **user**: use the model the user named. If they gave no effort, use high.
- **exploit**: run `python scripts/offload.py history` to see each model and
  effort's average scores and review. Pick the one that best fits the
  intelligence this task needs. Running tests or parsing logs needs little;
  debugging or browser use needs more. With no history yet, start with
  Sonnet 5.5 on high for code and technical work, or GPT-6.1 Sol on high for
  research and audits.
- **explore**: the script names two models from different providers at the
  same effort, favoring the least tried. Run both on the same task at the same
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

Score each child run from 0 to 5 on every dimension, in this order:

1. **Correctness**: the result is right.
2. **Completeness**: every acceptance criterion is met.
3. **Adherence**: it followed the brief and stayed in scope.
4. **Evidence**: its claims are backed by evidence you could verify.
5. **Clarity**: the report is clear and concise.
6. **Efficiency**: it finished quickly, without wasted steps.
7. **Independence**: it needed no follow-up or rework from you.

Each model and effort keeps one review. Run `history` and read the agent's
current review, if it has one. Then write an updated review of about 4 to 6
sentences. Merge what you knew before with what this run showed: the kinds of
task it handled well, where it struggled, and when to choose it. Then record:

```sh
python scripts/offload.py record <model> <effort> <s1,s2,s3,s4,s5,s6,s7> "<updated review>"
```

The script adds the agent if it is new. Otherwise it folds the scores into the
agent's averages and replaces the review. Record each explore run separately.
Do not record a run that infrastructure blocked; it says nothing about the
model.

The data lives outside this skill, in `~/.local/share/offload-task/`
(`$XDG_DATA_HOME/offload-task` if set, or `$OFFLOAD_DATA` to override), so
reinstalling or updating the skill keeps it. `state.json` holds the call
counters. `history.csv` holds one row per model and effort. Do not edit either
file by hand.
