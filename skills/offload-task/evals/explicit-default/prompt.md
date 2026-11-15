---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Dry-run only: do not launch agents, execute tests, or change any real history.
I want to offload running `python -m unittest discover -s tests -v` in my repo.
Show the compact delegation contract and exact target/options you would use.
Assume the discovered T3 catalog lists providerInstanceId `opencode`, model
`openai/gpt-6.1-sol` with option `variant` accepting `low`, `medium`, `high`;
the current parent's inherited options include `fastMode: true`.
Assume a child later returns "all tests passed" with no exit code, no log,
and no actual execution metadata. Explain what you would report and record,
including whether this outcome is a verified success and its parent score.
