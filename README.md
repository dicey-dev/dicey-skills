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
