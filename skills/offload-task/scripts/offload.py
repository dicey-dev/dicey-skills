#!/usr/bin/env python3
"""Keep the offload-task skill's 3:2 exploit/explore ratio and per-agent scores.

  offload.py next [--user]   # count a call; print its branch (and agents on explore)
  offload.py history         # print every agent's average scores and review
  offload.py record sonnet-5.5 high 5,4,5,4,4,3,5 "<updated review>"

Data lives in $OFFLOAD_DATA, else $XDG_DATA_HOME/offload-task, else
~/.local/share/offload-task. state.json holds the call counters. history.csv
holds one row per model and effort: run count, average scores, and a review.
"""
import argparse
import csv
import fcntl
import io
import json
import os
import random
import sys
from contextlib import contextmanager
from pathlib import Path

DATA = Path(os.environ.get("OFFLOAD_DATA") or Path(
    os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "offload-task")
STATE = DATA / "state.json"
HISTORY = DATA / "history.csv"

# Explore pool, grouped by provider. Names are labels: resolve exact IDs with
# orchestrator_capabilities. Edit these lists to change the pool.
MODELS = {
    "anthropic": ["opus-5.5", "sonnet-5.5", "haiku-5.5"],
    "openai": ["gpt-6.2-sol", "gpt-6.2-terra"],
}
EFFORTS = ["medium", "high"]
CYCLE = ["exploit", "explore", "exploit", "explore", "exploit"]  # 3:2
SCORES = ["correctness", "completeness", "adherence", "evidence", "clarity",
          "efficiency", "independence"]  # each 0-5, in this order
COLUMNS = ["model", "effort", "runs", *SCORES, "review"]


@contextmanager
def locked():
    DATA.mkdir(parents=True, exist_ok=True)
    fd = os.open(DATA, os.O_RDONLY)  # lock the folder; no lock file left behind
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def write_atomic(path, text):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text)
    tmp.replace(path)


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"calls": 0, "decisions": 0}


def load_history():
    if not HISTORY.exists():
        return {}
    with open(HISTORY, newline="") as f:
        return {(r["model"], r["effort"]): r for r in csv.DictReader(f)}


def save_history(rows):
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(COLUMNS)
    writer.writerows([rows[key][c] for c in COLUMNS] for key in sorted(rows))
    write_atomic(HISTORY, buf.getvalue())


def explore_agents():
    """Two models from different providers at the same effort, least tried first."""
    runs = {k: int(r["runs"]) for k, r in load_history().items()}
    options = []
    for effort in EFFORTS:
        picks = []
        for models in MODELS.values():
            fewest = min(runs.get((m, effort), 0) for m in models)
            picks.append(random.choice(
                [m for m in models if runs.get((m, effort), 0) == fewest]))
        tried = sum(runs.get((m, effort), 0) for m in picks)
        options.append((tried, random.random(), effort, random.sample(picks, 2)))
    _, _, effort, models = min(options)
    return [{"model": m, "effort": effort} for m in models]


def cmd_next(args):
    with locked():
        state = load_state()
        state["calls"] += 1
        if args.user:
            branch = "user"
        else:
            branch = CYCLE[state["decisions"] % len(CYCLE)]
            state["decisions"] += 1
        write_atomic(STATE, json.dumps(state, indent=2) + "\n")
    out = {"call": state["calls"], "branch": branch}
    if branch == "explore":
        out["agents"] = explore_agents()
    print(json.dumps(out, indent=2))


def cmd_history(_args):
    state = load_state()
    print(f"calls: {state['calls']}, next branch: "
          f"{CYCLE[state['decisions'] % len(CYCLE)]}, data: {DATA}")
    rows = load_history()
    if not rows:
        print("no runs recorded yet")
        return
    for (model, effort), r in sorted(rows.items()):
        scores = ", ".join(f"{s} {float(r[s]):.1f}" for s in SCORES)
        print(f"\n{model} / {effort} ({r['runs']} runs)\n  {scores}\n  {r['review']}")


def cmd_record(args):
    try:
        scores = [int(v) for v in args.scores.split(",")]
        if len(scores) != len(SCORES) or not all(0 <= v <= 5 for v in scores):
            raise ValueError
    except ValueError:
        sys.exit(f"error: scores must be {len(SCORES)} integers 0-5, in the order "
                 + ",".join(SCORES))
    review = " ".join(args.review.split())
    if not review:
        sys.exit("error: the review cannot be empty")
    with locked():
        rows = load_history()
        key = (args.model, args.effort)
        old = rows.get(key)
        n = int(old["runs"]) if old else 0
        row = {"model": args.model, "effort": args.effort, "runs": n + 1, "review": review}
        for s, v in zip(SCORES, scores):
            prev = float(old[s]) if old else 0.0
            row[s] = f"{(prev * n + v) / (n + 1):.2f}"
        rows[key] = row
        save_history(rows)
    print(f"{'updated' if old else 'added'} {args.model} / {args.effort}: {n + 1} runs")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    nxt = sub.add_parser("next", help="count a call and get its branch")
    nxt.add_argument("--user", action="store_true", help="the user named the model")
    nxt.set_defaults(func=cmd_next)

    sub.add_parser("history", help="print every agent's scores and review").set_defaults(
        func=cmd_history)

    rec = sub.add_parser("record", help="add a scored run to an agent's averages")
    rec.add_argument("model")
    rec.add_argument("effort")
    rec.add_argument("scores", help=",".join(SCORES) + " (each 0-5)")
    rec.add_argument("review", help="the agent's full updated review")
    rec.set_defaults(func=cmd_record)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
