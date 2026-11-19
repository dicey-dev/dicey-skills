---
name: offload-task
description: Trigger this if the user says 'big task'. They may also name a model and reasoning effort.
---

# Big Task

Split the work across subagents to finish sooner and to record how each model
performs. You plan, decide, verify, and report. The children execute.

`scripts/offload.py` below means the script in this skill's folder.

## Steps

1. **Break the task down.** Answer these before doing any of the work yourself:
   - Can I break this task into smaller tasks? If not, it is one piece. Keep
     going with the questions below.
   - If yes, how? Split along lines that don't overlap:
     - by question: separate things to find out, each a read-only search or audit;
     - by area: changes to files or modules that don't touch each other;
     - by phase: investigate, implement, test, review.
   - Which pieces don't depend on each other? Those run in parallel.
   - Which pieces need another piece's result first? Those wait for it.
   - Which pieces are mine? Keep decisions, work that needs the user, and small
     steps that would take longer to brief than to do. Delegate the rest. If the
     task can't be split, delegate it as one piece and keep the verification.
   - Which pieces need less intelligence? Searches, test runs, log triage and
     short scripts can go to a smaller model.
   - Can I write a "done when" for each piece? If not, clarify its outcome or
     split it further.

   Post the plan as a short list: each piece, who does it, and what it waits on.
   Then carry on without waiting, unless a piece needs a decision from the user.
   If new work turns up later in the task, break it down the same way.

2. **Pick an agent for each delegated attempt.** Run
   `python scripts/offload.py next` once per attempt, retries included, before
   choosing a model. Add `--user` when the user named the model. It prints the
   branch:
   - **user**: use the model the user named. If they gave no effort, use high.
   - **exploit**: run `python scripts/offload.py history` and pick the agent
     whose review best fits this piece. With no history yet, use Sonnet 5.5 on
     high for code and technical work, or GPT-6.2 Sol on high for research and
     audits.
   - **explore**: the script names two models from different providers at the
     same effort. Run both on the same piece, from the same starting state.
     Never skip explore.

3. **Start the pieces.**
   - Call `orchestrator_capabilities` once per thread. Resolve each label to its
     exact provider instance, model ID and effort option. If one is unavailable,
     tell the user. Never substitute quietly.
   - Call `delegate_task` once per agent, with the effort in `target.options`.
     Start every piece whose inputs are ready in the same turn.
   - Give `isolation: "worktree"` to both explore runs when they edit files, and
     to any child that edits files while another child runs. A worktree starts
     from the last commit, so make sure the changes a piece depends on are
     there first.
   - The children can't see this thread, so write a self-contained brief:

     ```text
     Goal: <one piece>
     Context: <key facts, absolute paths in the child's own checkout, commands>
     Scope: <allowed tools and paths; no commits, pushes or sub-delegation unless stated>
     Done when: <acceptance criteria>
     Report: outcome, evidence (exit codes, citations, file paths), blockers. Be brief.
     ```

4. **Work while they run.** Do your own pieces. Follow the returned `next`
   exactly, including ending your turn when it says to; a child's completion
   wakes you. Cancel runs you no longer need with `task_cancel`.

5. **Verify each result as it arrives.**
   - Check the evidence: the decisive test output, the diff, or the cited
     sources. A failed run, or a finished run missing its report or required
     evidence, is a failure. A wait timeout is not; the child is still running.
   - Score every run in step 6 before you repair anything.
   - For explore, wait for both results. Keep the better acceptable one and
     discard the other run's changes.
   - If no result for the piece is acceptable, retry it once through steps 2
     to 6, with a corrected brief if needed. If the retry also fails, finish the
     piece yourself.
   - Apply each accepted worktree diff to your checkout. A dependent piece that
     edits files must see those changes: commit them first if it runs in a
     worktree, or run it in your checkout when no other child is running.

6. **Score and record each child attempt.** Score each attempt exactly once, on
   what it delivered before your fixes. Rework you had to do lowers
   independence. Score it 0 to 5 on each dimension, in this order: correctness,
   completeness, adherence (followed the brief, stayed in scope), evidence,
   clarity, efficiency, independence (needed no follow-up or rework).

   Run `history` and read the agent's current review. Write an updated review of
   about 4 to 6 sentences that merges it with this run, in this shape:

   ```text
   <task shape>, <size>. Good at: … Weak at: … Pick it for: … Guard against: …
   ```

   - Task shapes: read-only audit, debugging, multi-file implementation, small
     edit, test triage, diff review, web research, script or query, browser or UI.
   - Worth noting: report length, scope discipline, honesty about limits, side
     effects, test isolation, how precise the brief had to be, and how it did
     against its explore peer.
   - Write for someone choosing a model on a different project. No file,
     function, product or company names, and no findings from the task.

   Record with the script's model label (such as `sonnet-5.5`), not the
   provider's model ID, and the effort actually used. For a model outside the
   pool, reuse its existing label in `history` if it has one.

   ```sh
   python scripts/offload.py record <model> <effort> <s1,...,s7> "<updated review>"
   ```

   Record each explore run separately. Do not record a run that infrastructure
   blocked, or one that failed because your brief was wrong.

7. **Put it together and report.** Run the final checks on the combined result.
   Report the outcome, the evidence, the child thread links and any open issues.
   Do not forward raw logs.

## Data

The data lives in `~/.local/share/offload-task/` (`$XDG_DATA_HOME/offload-task`
if set, or `$OFFLOAD_DATA` to override), so updating the skill keeps it.
`state.json` holds the call counters. `history.csv` holds one row per model and
effort. Do not edit either file by hand.
