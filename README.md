# dicey-skills

Versioned copies of the locally installed skills available to T3 Code.

## Installed-skill snapshot

The initial `main` commit contains 21 skills under `skills/`, including their
scripts, references, assets, and bundled license files. Identical copies from
multiple skill directories are deduplicated. `inventory.json` records source
paths and SHA-256 hashes for every copied file.

Sources: `~/.config/opencode/skills`, `~/.agents/skills`, `~/.claude/skills`,
and the Apache-licensed packages under `~/.claude/skills/synced`. Synced
skills without a redistribution license are excluded. Symlinked skill folders
are copied as real files. Temporary staging files and Python caches are excluded.
Harness-bundled skills that are not locally installed (such as OpenCode's
`browser`, `opencode`, and `report`) are not part of this snapshot.

This repository is a snapshot, not an installer or live sync. Changes here do
not change the installed skills. Preserve upstream license notices when sharing.

## Offload task (new skill)

`skills/offload-task/SKILL.md` describes bounded T3 Code delegation, defaulting
explicit requests to GPT-6.1 Sol/high and allowing parent-selected model/effort
for token-intensive execution. The parent verifies and scores outcomes and
updates the initially empty history; no automatic harness integration is implied.
Parent-selected, safe exploration uses about one trial per ten exploitation
decisions. This new skill is not included in the installed-snapshot inventory.

Validate the new skill and unchanged snapshot:

```sh
python -m unittest discover -s tests -v
python skills/skill-creator/scripts/quick_validate.py skills/offload-task
```

Two dry-run behavior cases and their graders live in `skills/offload-task/evals`.
They test planning, not live execution or guaranteed token savings. Local paired
runs passed 4/4 assertions with the skill and 2/4 without it (one run per case;
manually graded). Usage/timing were not exposed. No performance records were
seeded from these simulations. Results are in the ignored
`skills/offload-task-workspace/iteration-1/` directory.
