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

This repository has no installer. To use a skill from here, symlink its folder
into a harness's skills directory; edits here then take effect there right away.
Copying a folder instead gives a snapshot that does not update. Preserve
upstream license notices when sharing.

## Installing in Antigravity

The Antigravity CLI (`agy`) loads user skills from `~/.gemini/config/skills`.
Link every skill from this repository there:

```sh
cd /path/to/dicey-skills
mkdir -p ~/.gemini/config/skills
for d in skills/*/; do
  [ -f "$d/SKILL.md" ] || continue           # skips *-workspace folders
  s=$(basename "$d")
  [ -e ~/.gemini/config/skills/"$s" ] || ln -s "$PWD/skills/$s" ~/.gemini/config/skills/"$s"
done
```

The loop leaves existing entries alone. `diagnose-crash`, `omarchy` and
`omarchy-app` are usually already linked to
`/usr/share/omarchy/default/agents/skills`, which Omarchy updates. Keep those
links. Start a new `agy` session to load the skills, then check with
`agy -p "list your skills"`.

The same symlink setup works for other harnesses: Claude Code uses
`~/.claude/skills`, and harnesses that share skills use `~/.agents/skills`.

## Third-party skills

These skills come from [tstack](https://github.com/t3dotgg/tstack) by Theo
Browne, under the MIT License: `babysit-pr`, `council`, `file-pr`,
`full-send`, `full-stop`, `leaving-pr-comments`, `modernize`, `sol-loop`, and
`takeover`. They match upstream commit
[`11e37a7`](https://github.com/t3dotgg/tstack/commit/11e37a7). Each skill
folder includes the upstream `LICENSE` with its copyright notice.
