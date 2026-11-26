# dicey-skills

Agent skills I use across coding harnesses, kept in one place. `install.sh`
links them into every harness installed on a machine, so an edit here shows up
everywhere right away.

## Quick start

Clone the repo somewhere permanent and run the installer:

```sh
git clone https://github.com/dicey-dev/dicey-skills.git ~/dicey-skills && ~/dicey-skills/install.sh
```

Already cloned? Run `./install.sh` from the repo. Then start a new session in
each harness to load the skills.

## Skills

16 skills live under `skills/`, one folder each with a `SKILL.md`.

| Skill | Use it for | Source |
| --- | --- | --- |
| `babysit-pr` | Watch a PR through review and CI | tstack |
| `council` | Say "council": get review from three models on three providers | tstack |
| `file-pr` | File a concise PR | tstack |
| `full-send` | Say "full send": finish the work through to a merged PR | tstack |
| `full-stop` | Say "full stop": like `full-send`, but leave the PR for you to merge | tstack |
| `leaving-pr-comments` | Leave comments on GitHub | tstack |
| `modernize` | Rebase an old PR and bring it up to date | tstack |
| `sol-loop` | Say "sol loop": review changes with GPT Sol in a loop | tstack |
| `takeover` | Take over a PR, branch or agent thread | tstack |
| `offload-task` | Say "big task": split work across subagents and track how each model does | This repo |
| `frontend-design` | Build distinctive, production-grade web interfaces | Vipul Gupta (MIT) |
| `docx` | Word documents | Anthropic (Apache 2.0) |
| `pdf` | PDF files | Anthropic (Apache 2.0) |
| `pptx` | PowerPoint decks | Anthropic (Apache 2.0) |
| `xlsx` | Spreadsheets | Anthropic (Apache 2.0) |
| `skill-creator` | Create, edit and evaluate skills | Anthropic (Apache 2.0) |

`offload-task` keeps its call counters and model history outside the skill, in
`~/.local/share/offload-task/` (`$XDG_DATA_HOME/offload-task`, or
`$OFFLOAD_DATA`), so updating the skill keeps the data.

## How install.sh works

`install.sh` symlinks every skill folder that has a `SKILL.md` into the skills
folder of each harness it finds. A harness counts as installed when its config
folder exists. Commands on `PATH` are not used, because tool managers such as
mise can add commands for tools that were never downloaded. The script skips
harnesses that are not installed and never replaces an existing entry, so
re-running it is safe. Because the skills are links, keep the clone where it is.

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

- Claude Code may already have `docx`, `pdf`, `pptx`, `xlsx` and
  `skill-creator` from claude.ai sync. If they show up twice, delete the links
  from `~/.claude/skills`.
- Kiro custom agents load skills only when their `resources` include
  `skill://~/.kiro/skills/*/SKILL.md`. The default agent loads them on its own.
- To add a harness, add a line to the `harnesses` list in `install.sh`.
- To remove a skill from a harness, delete its link from that harness's skills
  folder. Deleting a skill from this repo leaves broken links behind.

## Repository layout

- `skills/`: the skills.
- `install.sh`: the installer described above.
- `inventory.json`: where each copied skill came from and the SHA-256 of each
  file, recorded on 2026-11-15. `offload-task` is not listed because it was
  written here.
- `*-workspace/` folders hold local eval output from `skill-creator` and are
  git-ignored.

## History

The first commit was a snapshot of 21 skills installed on my machine, copied
from `~/.config/opencode/skills`, `~/.agents/skills`, `~/.claude/skills` and
the Apache-licensed skills synced from claude.ai into `~/.claude/skills/synced`.
Synced skills without a redistribution license were left out. Later changes
added `offload-task` and `install.sh`. They also removed the Omarchy skills
(`diagnose-crash`, `omarchy`, `omarchy-app`), because Omarchy ships its own
copies, and the personal `openai-quota-*` skills.

## Licenses

The tstack skills come from [tstack](https://github.com/t3dotgg/tstack) by
Theo Browne, under the MIT License, and match upstream commit
[`11e37a7`](https://github.com/t3dotgg/tstack/commit/11e37a7). `frontend-design`
is MIT-licensed by Vipul Gupta. The Anthropic skills are under the Apache
License 2.0. Each skill folder includes its upstream license file. Keep those
notices when sharing.
