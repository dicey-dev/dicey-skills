#!/usr/bin/env python3
"""Pick offload agents and record results for the offload-task skill.

  offload.py select --category code [--exclude opus-5.5]
  offload.py record --branch explore --category code \
      --run sonnet-5.5 high 8 "Clean fix, tests pass" \
      --run gpt-6.1-sol high 6 "Missed an edge case"
  offload.py status

State lives in state.json next to SKILL.md (override with OFFLOAD_STATE).
"""
import argparse
import fcntl
import json
import os
import random
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
STATE = Path(os.environ.get("OFFLOAD_STATE", SKILL_DIR / "state.json"))

# Model pool, grouped by provider. Names are labels: resolve exact IDs with
# orchestrator_capabilities. Edit this list to add or remove models.
MODELS = {
    "anthropic": ["opus-5.5", "sonnet-5.5", "haiku-5.5"],
    "openai": ["gpt-6.1-sol", "gpt-6.1-terra"],
}
EFFORTS = ["medium", "high"]
DEFAULTS = {"code": ("sonnet-5.5", "high"), "research": ("gpt-6.1-sol", "high")}
CYCLE = ["exploit", "explore", "exploit", "explore", "exploit"]  # 3:2
MIN_RUNS = 3  # scored runs a model + effort needs before it can become default


def load():
    if not STATE.exists():
        return {"calls": 0, "decisions": 0, "runs": []}
    return json.loads(STATE.read_text())


def save(state):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    tmp.replace(STATE)


@contextmanager
def locked():
    fd = os.open(STATE.parent, os.O_RDONLY)  # lock the folder; no lock file left behind
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def scores(state, category):
    """(model, effort) -> list of scores for this category."""
    out = {}
    for r in state["runs"]:
        if r["category"] == category and r["score"] is not None:
            out.setdefault((r["model"], r["effort"]), []).append(r["score"])
    return out


def default_agent(state, category, exclude=()):
    ranked = sorted(
        ((sum(s) / len(s), len(s), k) for k, s in scores(state, category).items()
         if len(s) >= MIN_RUNS and k[0] not in exclude),
        reverse=True,
    )
    if ranked:
        mean, n, (model, effort) = ranked[0]
        return {"model": model, "effort": effort, "why": f"best mean {mean:.1f} over {n} runs"}
    model, effort = DEFAULTS[category]
    return {"model": model, "effort": effort, "why": "starting default (not enough history)"}


def explore_agents(state, category, exclude):
    """One least-tried model + effort from each of two different providers."""
    counts = {k: len(v) for k, v in scores(state, category).items()}
    picks = []
    for models in MODELS.values():
        options = [(m, e) for m in models if m not in exclude for e in EFFORTS]
        if options:
            fewest = min(counts.get(o, 0) for o in options)
            picks.append(random.choice([o for o in options if counts.get(o, 0) == fewest]))
    if len(picks) < 2:
        sys.exit("error: exploration needs models from two providers")
    return [{"model": m, "effort": e, "runs": counts.get((m, e), 0)}
            for m, e in random.sample(picks, 2)]


def cmd_select(args):
    state = load()
    branch = CYCLE[state["decisions"] % len(CYCLE)]
    if branch == "exploit":
        agents = [default_agent(state, args.category, args.exclude)]
    else:
        agents = explore_agents(state, args.category, args.exclude)
    print(json.dumps({"decision": state["decisions"] + 1, "branch": branch,
                      "category": args.category, "agents": agents}, indent=2))


def parse_score(raw):
    if raw in ("-", "—"):
        return None
    score = int(raw)
    if not 0 <= score <= 10:
        raise ValueError
    return score


def cmd_record(args):
    try:
        runs = [(m, e, parse_score(s), review.strip()) for m, e, s, review in args.run]
    except ValueError:
        sys.exit("error: score must be an integer 0-10, or '-' if unscored")
    if args.branch == "explore" and len(runs) < 2:
        sys.exit("error: an explore decision needs two runs")

    with locked():
        state = load()
        state["calls"] += 1
        if args.branch != "user":
            state["decisions"] += 1
        best = max((r[2] for r in runs if r[2] is not None), default=None)
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        rows = []
        for model, effort, score, review in runs:
            won = "" if len(runs) == 1 else ("yes" if best is not None and score == best else "no")
            run = {"date": date, "call": state["calls"], "branch": args.branch,
                   "category": args.category, "model": model, "effort": effort,
                   "score": score, "won": won, "review": review}
            state["runs"].append(run)
            cells = [date, str(state["calls"]), args.branch, args.category, model,
                     effort, "—" if score is None else str(score), won,
                     review.replace("|", "\\|").replace("\n", " ")]
            rows.append("| " + " | ".join(cells) + " |")
        save(state)
        text = SKILL_MD.read_text().rstrip("\n")
        SKILL_MD.write_text(text + "\n" + "\n".join(rows) + "\n")
    print(f"recorded call {state['calls']}: {len(runs)} run(s)")


def cmd_status(_args):
    state = load()
    print(f"calls: {state['calls']}, parent-chosen decisions: {state['decisions']}, "
          f"next branch: {CYCLE[state['decisions'] % len(CYCLE)]}")
    for category in DEFAULTS:
        agent = default_agent(state, category)
        print(f"{category} default: {agent['model']} / {agent['effort']} ({agent['why']})")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sel = sub.add_parser("select", help="choose agents for the next decision")
    sel.add_argument("--category", choices=DEFAULTS, required=True)
    sel.add_argument("--exclude", nargs="*", default=[], help="models to skip, e.g. the parent model")
    sel.set_defaults(func=cmd_select)

    rec = sub.add_parser("record", help="save scored runs after the offload finishes")
    rec.add_argument("--branch", choices=["exploit", "explore", "user"], required=True)
    rec.add_argument("--category", choices=DEFAULTS, required=True)
    rec.add_argument("--run", nargs=4, action="append", required=True,
                     metavar=("MODEL", "EFFORT", "SCORE", "REVIEW"))
    rec.set_defaults(func=cmd_record)

    sub.add_parser("status", help="show counters and current defaults").set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
