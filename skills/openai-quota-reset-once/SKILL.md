---
name: OpenAI Quota Reset Once
description: Redeem exactly one banked OpenAI/Codex usage-limit reset when the user explicitly asks to spend or use a reset. Irreversible; never use for status checks.
---

# Use one usage reset

Only proceed when the user explicitly asks to consume one reset now. Creating/testing this skill, checking availability, or discussing resets is not authorization. If intent is ambiguous, ask first. Explain that this spends one banked credit; it does not purchase quota or bypass limits.

1. Load `openai-quota-reset-report` and run its status command once, unless this turn already has a fresh result.
2. If no available credits exist, stop. If the user specified a credit, use only that credit. Otherwise choose the available credit with the earliest known expiry (unknown expiries last). If scopes differ and the requested scope is unclear, ask which to use.
3. Use the exact credit ID and `account_ref` returned by status:

```bash
python3 ~/.config/opencode/skills/openai-quota-reset-report/scripts/resets.py consume \
  --credit-id '<credit ID>' --account-ref '<account_ref>' --confirm
```

The script rechecks the same active account and credit, then sends at most one POST. It pins the credit and derives a stable idempotency key from account + credit ID. Never loop, automatically retry, choose another credit on failure, or omit the account guard. Do not inspect credentials, refresh tokens, or switch accounts.

Report the returned outcome faithfully: `reset`, `nothing_to_reset`, `no_credit`, or `already_redeemed`. Only `reset` confirms a new reset. Report `windows_reset` when present. HTTP success alone is not proof a window reset. For an unknown outcome or a lost/failed POST response, say the result is uncertain; do not repeat redemption. A subsequent read-only status check is safe if needed.

The shared script must remain installed with `openai-quota-reset-report`. Authentication uses the active OpenCode OAuth account, not a separate Codex login. API keys are unsupported.

Undocumented backend API, confirmed in OpenAI's Codex source:
https://github.com/openai/codex/blob/main/codex-rs/backend-client/src/client/rate_limit_resets.rs

`POST https://chatgpt.com/backend-api/wham/rate-limit-reset-credits/consume`

Body: `{"credit_id": "...", "redeem_request_id": "<stable UUID>"}`.
