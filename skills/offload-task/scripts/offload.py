#!/usr/bin/env python3
"""Keep the offload-task skill's 3:2 exploit/explore ratio and its run history.

  offload.py next [--user]      # start a call: prints its number, branch, and agents
  offload.py record --call 7 --task "Run the unit tests and report failures" \
      --run sonnet-5.5 high 5,4,5,4,4,3,5 "All failures found; slow to finish" \
      --run gpt-6.1-sol medium 3,3,4,2,4,5,2 "Missed two failures; no logs cited"
  offload.py history [--grep tests]

Data lives next to SKILL.md (override the folder with OFFLOAD_DATA):
state.json holds the call counters, history.csv holds one row per child run.
"""
import argparse
import csv
import fcntl
import json
import os
import random
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(os.environ.get("OFFLOAD_DATA", Path(__file__).resolve().parent.parent))
STATE = DATA / "state.json"
HISTORY = DATA / "history.csv"

# Explore pool, grouped by provider. Names are labels: resolve exact IDs with
# orchestrator_capabilities. Edit these lists to change the pool.
MODELS = {
    "anthropic": ["opus-5.5", "sonnet-5.5", "haiku-5.5"],
    "openai": ["gpt-6.1-sol", "gpt-6.1-terra"],
}
EFFORTS = ["medium", "high"]
CYCLE = ["exploit", "explore", "exploit", "explore", "exploit"]  # 3:2
SCORES = ["correctness", "completeness", "adherence", "evidence", "clarity",
          "efficiency", "independence"]  # each 0-5, in this order
COLUMNS = ["date", "call", "branch", "task", "model", "effort", *SCORES, "review"]


@contextmanager
def locked():
    fd = os.open(DATA, os.O_RDONLY)  # lock the folder; no lock file left behind
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def load_state():
    if not STATE.exists():
        return {"calls": 0, "decisions": 0, "pending": {}}
    return json.loads(STATE.read_text())


def save_state(state):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    tmp.replace(STATE)


def load_history():
    if not HISTORY.exists():
        return []
    with open(HISTORY, newline="") as f:
        return list(csv.DictReader(f))


def explore_agents():
    """One least-tried model + effort from each of two different providers."""
    tried = {}
    for row in load_history():
        key = (row["model"], row["effort"])
        tried[key] = tried.get(key, 0) + 1
    picks = []
    for models in MODELS.values():
        options = [(m, e) for m in models for e in EFFORTS]
        fewest = min(tried.get(o, 0) for o in options)
        picks.append(random.choice([o for o in options if tried.get(o, 0) == fewest]))
    return [{"model": m, "effort": e} for m, e in random.sample(picks, 2)]


def cmd_next(args):
    with locked():
        state = load_state()
        state["calls"] += 1
        if args.user:
            branch = "user"
        else:
            branch = CYCLE[state["decisions"] % len(CYCLE)]
            state["decisions"] += 1
        out = {"call": state["calls"], "branch": branch}
        if branch == "explore":
            out["agents"] = explore_agents()
        state["pending"][str(state["calls"])] = branch
        save_state(state)
    print(json.dumps(out, indent=2))


def parse_scores(raw):
    if raw == "-":
        return [""] * len(SCORES)
    values = [int(v) for v in raw.split(",")]
    if len(values) != len(SCORES) or not all(0 <= v <= 5 for v in values):
        raise ValueError
    return values


def cmd_record(args):
    try:
        runs = [(m, e, parse_scores(s), review.strip()) for m, e, s, review in args.run]
    except ValueError:
        sys.exit(f"error: scores must be {len(SCORES)} integers 0-5 in the order "
                 f"{','.join(SCORES)}, or '-' if the run could not be scored")
    with locked():
        state = load_state()
        branch = state["pending"].get(str(args.call))
        if branch is None:
            sys.exit(f"error: call {args.call} is not open; run 'next' first")
        if branch == "explore" and len(runs) != 2:
            sys.exit("error: an explore call needs exactly two --run entries")
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        new_file = not HISTORY.exists()
        with open(HISTORY, "a", newline="") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(COLUMNS)
            for model, effort, scores, review in runs:
                writer.writerow([date, args.call, branch, args.task.strip(), model,
                                 effort, *scores, review])
        del state["pending"][str(args.call)]
        save_state(state)
    print(f"recorded call {args.call} ({branch}): {len(runs)} run(s)")


def cmd_history(args):
    state = load_state()
    done = state["decisions"]
    print(f"calls: {state['calls']}, next branch: {CYCLE[done % len(CYCLE)]}")
    rows = load_history()
    if args.grep:
        needle = args.grep.lower()
        rows = [r for r in rows if needle in (r["task"] + " " + r["review"]).lower()]
    if not rows:
        print("no matching runs recorded")
        return

    agents = {}
    for r in rows:
        if r[SCORES[0]] != "":
            agents.setdefault(f"{r['model']}/{r['effort']}", []).append(r)
    if agents:
        short = [s[:5] for s in SCORES]
        print(f"\n{'average scores (0-5)':<24}{'runs':>5} " + " ".join(f"{s:>5}" for s in short))
    for agent, scored in sorted(agents.items()):
        means = [sum(int(r[s]) for r in scored) / len(scored) for s in SCORES]
        print(f"{agent:<24}{len(scored):>5} " + " ".join(f"{m:>5.1f}" for m in means))

    print("\nruns")
    for r in rows:
        scores = ",".join(r[s] for s in SCORES) if r[SCORES[0]] != "" else "unscored"
        print(f"{r['date']} #{r['call']} {r['branch']} {r['model']}/{r['effort']} "
              f"[{scores}] {r['task']} -- {r['review']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    nxt = sub.add_parser("next", help="start a call and get its branch")
    nxt.add_argument("--user", action="store_true", help="the user named the model")
    nxt.set_defaults(func=cmd_next)

    rec = sub.add_parser("record", help="save scored runs once the call is finished")
    rec.add_argument("--call", type=int, required=True, help="number printed by 'next'")
    rec.add_argument("--task", required=True, help="one line describing the task")
    rec.add_argument("--run", nargs=4, action="append", required=True,
                     metavar=("MODEL", "EFFORT", "SCORES", "REVIEW"))
    rec.set_defaults(func=cmd_record)

    hist = sub.add_parser("history", help="show average scores and past runs")
    hist.add_argument("--grep", help="only runs whose task or review contains this text")
    hist.set_defaults(func=cmd_history)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
