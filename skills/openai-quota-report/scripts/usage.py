#!/usr/bin/env python3
"""Read active OpenAI subscription quota with one provider request."""

import base64
import json
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    database = subprocess.check_output(
        ["opencode", "debug", "paths", "db"], text=True, stderr=subprocess.DEVNULL
    ).strip()
    uri = Path(database).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        row = connection.execute(
            "SELECT value FROM credential WHERE integration_id = 'openai' AND active = 1"
        ).fetchone()
    finally:
        connection.close()
    if not row:
        raise RuntimeError("No active OpenAI account. Select one through /connect.")
    credential = json.loads(row[0])
    if credential.get("type") != "oauth":
        raise RuntimeError("API-key quotas are unsupported. See https://platform.openai.com/usage.")

    access = credential["access"]
    metadata = credential.get("metadata") or {}
    account = metadata.get("accountId") or metadata.get("account_id")
    if not account:
        try:
            payload = access.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            account = claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id")
        except (ValueError, IndexError, KeyError):
            pass
    headers = {"Authorization": "Bearer " + access, "Accept": "application/json", "User-Agent": "opencode"}
    if account:
        headers["ChatGPT-Account-Id"] = account
    request = urllib.request.Request("https://chatgpt.com/backend-api/wham/usage", headers=headers)
    opener = urllib.request.build_opener(NoRedirect)
    with opener.open(request, timeout=30) as response:
        result = json.load(response)

    print("Plan:", result.get("plan_type", "unknown"))
    limits = result.get("rate_limit") or {}
    labels = {604800: "Weekly", 18000: "5-hour", 86400: "Daily"}
    found = False
    for name in ("primary_window", "secondary_window"):
        window = limits.get(name)
        if not window or window.get("used_percent") is None:
            continue
        found = True
        remaining = max(0, 100 - window["used_percent"])
        label = labels.get(window.get("limit_window_seconds"), name.replace("_", " ").title())
        reset = window.get("reset_at")
        reset_text = datetime.fromtimestamp(reset, timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if reset else "unknown"
        print(f"{label}: {remaining:g}% remaining; resets {reset_text}")
    if not found:
        print("The provider did not return a usage percentage.")
    if limits.get("limit_reached"):
        print("Usage limit reached.")
    elif limits.get("allowed") is False:
        print("Requests are currently not allowed.")
    elif limits.get("allowed") is True:
        print("Requests allowed; no limit reached.")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as error:
        print(
            f"Quota request failed (HTTP {error.code}). Reconnect through /connect if authentication expired.",
            file=sys.stderr,
        )
        sys.exit(1)
    except urllib.error.URLError:
        print("Quota endpoint could not be reached.", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except (OSError, subprocess.SubprocessError, sqlite3.Error, ValueError, KeyError):
        print(
            "Quota lookup failed. Check the active OpenAI OAuth connection and OpenCode database compatibility.",
            file=sys.stderr,
        )
        sys.exit(1)
