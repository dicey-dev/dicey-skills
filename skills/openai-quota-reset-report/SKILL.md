---
name: OpenAI Quota Reset Report
description: Check how many banked OpenAI/Codex usage-limit resets are available and when each expires. Read-only; does not redeem a reset. Not ordinary quota reset times.
---

# Check available usage resets

Run once:

```bash
python3 ~/.config/opencode/skills/openai-quota-reset-report/scripts/resets.py status
```

Report `available_count`, available credit titles/scopes, and expiry times concisely. Preserve credit IDs and `account_ref` if the user subsequently asks to redeem one. A null expiry means unknown, not never expires. A null count means unknown, not zero.

This reads the active OpenCode OpenAI OAuth credential read-only and makes exactly one GET request. Never print or manually inspect credentials, refresh tokens, switch accounts, or retry on failure. Report errors as returned. API-key accounts do not support banked subscription resets.

Checking availability is not permission to consume a reset. Use `openai-quota-reset-once` only when the user explicitly asks to spend one. For remaining quota and scheduled window reset times, use `openai-quota-report` instead.

The backend endpoint is undocumented, but confirmed in OpenAI's Codex source:
https://github.com/openai/codex/blob/main/codex-rs/backend-client/src/client/rate_limit_resets.rs

`GET https://chatgpt.com/backend-api/wham/rate-limit-reset-credits`
