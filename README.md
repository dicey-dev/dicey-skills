# dicey-skills

Versioned copies of the locally installed skills available to T3 Code.

## Quick start

Clone the repo somewhere permanent and run the installer:

```sh
git clone https://github.com/dicey-dev/dicey-skills.git ~/dicey-skills && ~/dicey-skills/install.sh
```

Already cloned? Run `./install.sh` from the repo. Then start a new session in
each harness to load the skills.

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

## How install.sh works

`install.sh` symlinks every skill folder that has a `SKILL.md` into the skills
folder of each harness it finds. It skips harnesses that are not installed,
and it never replaces an existing entry. Re-running it is safe. Because the
skills are links, edits in this repo take effect right away, so keep the clone
where it is. Preserve upstream license notices when sharing.

| Harness | Detected by | Skills folder |
| --- | --- | --- |
| Claude Code | `~/.claude` | `~/.claude/skills` |
| OpenCode | `~/.config/opencode` | `~/.config/opencode/skills` |
| Codex | `~/.codex` (`$CODEX_HOME`) | `~/.codex/skills` |
| Pi | `~/.pi/agent` | `~/.pi/agent/skills` |
| Antigravity CLI | `~/.gemini/antigravity-cli` | `~/.gemini/config/skills` |
| Gemini CLI | `~/.gemini/settings.json` | `~/.gemini/skills` |
| Grok | `~/.grok` | `~/.grok/skills` |
| Cursor | `~/.cursor` | `~/.cursor/skills` |
| Kiro | `~/.kiro` (`$KIRO_HOME`) | `~/.kiro/skills` |
| Copilot CLI | `~/.copilot` | `~/.copilot/skills` |

Notes:

- `diagnose-crash`, `omarchy` and `omarchy-app` are usually already linked to
  `/usr/share/omarchy/default/agents/skills`, which Omarchy keeps updated. The
  installer keeps those links.
- Claude Code may already have `docx`, `pdf`, `pptx`, `xlsx` and
  `skill-creator` from claude.ai sync. If they show up twice, delete the links
  from `~/.claude/skills`.
- Kiro custom agents load skills only when their `resources` include
  `skill://~/.kiro/skills/*/SKILL.md`. The default agent loads them on its own.
- To add a harness, add a line to the `harnesses` list in `install.sh`.

## Third-party skills

These skills come from [tstack](https://github.com/t3dotgg/tstack) by Theo
Browne, under the MIT License: `babysit-pr`, `council`, `file-pr`,
`full-send`, `full-stop`, `leaving-pr-comments`, `modernize`, `sol-loop`, and
`takeover`. They match upstream commit
[`11e37a7`](https://github.com/t3dotgg/tstack/commit/11e37a7). Each skill
folder includes the upstream `LICENSE` with its copyright notice.
