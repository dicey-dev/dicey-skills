---
name: OpenAI Quota Report
description: Report remaining OpenAI/Codex provider quota when the user asks about usage left, remaining quota, token allowance, weekly limits, or quota reset times. Not conversation context usage.
---

Run the bundled script once:

```bash
python3 ~/.config/opencode/skills/openai-quota-report/scripts/usage.py
```

The script reads the active OpenAI OAuth account from OpenCode's local database,
read-only, and makes exactly one provider request. It never prints credentials,
refreshes tokens, switches accounts, or changes configuration.

Report the script's remaining percentages and reset times concisely. These are
quota percentages, not remaining token counts. On failure, report the error;
do not retry, inspect credentials manually, or regenerate the script.

This uses an undocumented ChatGPT quota endpoint. An API-key connection is not
supported; direct those users to the OpenAI usage dashboard instead.
