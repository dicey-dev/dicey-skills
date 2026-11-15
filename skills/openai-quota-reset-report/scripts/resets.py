"""Inspect banked Codex resets or explicitly redeem one pinned credit."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://chatgpt.com/backend-api/wham/rate-limit-reset-credits"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def active_account():
    database = subprocess.check_output(
        ["opencode", "debug", "paths", "db"],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()
    connection = sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT value FROM credential WHERE integration_id = 'openai' AND active = 1"
        ).fetchall()
    finally:
        connection.close()
    if len(rows) != 1:
        raise RuntimeError("Select exactly one active OpenAI OAuth account through /connect.")
    credential = json.loads(rows[0][0])
    if credential.get("type") != "oauth":
        raise RuntimeError("API-key accounts do not support banked subscription resets.")
    access = credential["access"]
    metadata = credential.get("metadata") or {}
    account = metadata.get("accountId") or metadata.get("account_id")
    if not account:
        payload = access.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        account = claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id")
    if not isinstance(account, str) or not account:
        raise RuntimeError("Active OAuth account has no account ID. Reconnect through /connect.")
    headers = {
        "Authorization": "Bearer " + access,
        "ChatGPT-Account-Id": account,
        "Accept": "application/json",
        "User-Agent": "opencode",
    }
    account_ref = hashlib.sha256(account.encode()).hexdigest()[:16]
    return headers, account, account_ref


def request(opener, headers, body=None):
    data = None if body is None else json.dumps(body).encode()
    request_headers = dict(headers)
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        BASE if body is None else BASE + "/consume",
        data=data,
        headers=request_headers,
        method="GET" if body is None else "POST",
    )
    try:
        with opener.open(req, timeout=30) as response:
            result = json.load(response)
        if not isinstance(result, dict):
            raise TypeError("Expected an object.")
        return result
    except (urllib.error.URLError, OSError, ValueError, TypeError) as error:
        if body is not None:
            raise RuntimeError(
                "Redemption response failed; outcome uncertain. Do not retry or spend another "
                "credit. Check reset status read-only or use the official Codex usage screen."
            ) from error
        raise


def summary(payload, account_ref):
    credits = payload.get("credits")
    if not isinstance(credits, list) or any(not isinstance(c, dict) for c in credits):
        raise RuntimeError("Unexpected reset-credit response. No redemption attempted.")
    count = payload.get("available_count")
    if type(count) is not int or count < 0:
        count = None
    fields = ("id", "status", "reset_type", "title", "granted_at", "expires_at")
    return {
        "account_ref": account_ref,
        "available_count": count,
        "credits": [{key: c.get(key) for key in fields} for c in credits],
    }


def validate_credit(result, credit_id):
    matches = [c for c in result["credits"] if c["id"] == credit_id]
    if len(matches) != 1 or matches[0]["status"] != "available":
        raise RuntimeError("Specified credit is not available. No redemption attempted.")
    if result["available_count"] == 0:
        raise RuntimeError("No resets available. No redemption attempted.")
    expiry = matches[0]["expires_at"]
    if expiry is not None:
        try:
            expires_at = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            if expires_at.tzinfo is None:
                raise ValueError("Missing expiry timezone.")
        except (AttributeError, TypeError, ValueError) as error:
            raise RuntimeError("Cannot verify credit expiry. No redemption attempted.") from error
        if expires_at <= datetime.now(timezone.utc):
            raise RuntimeError("Specified credit has expired. No redemption attempted.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Read-only: list reset credits.")
    consume = commands.add_parser("consume", help="Irreversibly consume exactly one credit.")
    consume.add_argument("--credit-id", required=True)
    consume.add_argument("--account-ref", required=True)
    consume.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "consume" and not args.confirm:
        parser.error("Redemption requires --confirm and explicit user authorization.")
    headers, account, account_ref = active_account()
    if args.command == "consume" and args.account_ref != account_ref:
        raise RuntimeError("Active account changed. No redemption attempted. Check status again.")
    opener = urllib.request.build_opener(NoRedirect)
    result = summary(request(opener, headers), account_ref)
    if args.command == "status":
        print(json.dumps(result, indent=2))
        return
    validate_credit(result, args.credit_id)
    # Bind retries to this account and credit, never a newly selected credit.
    redeem_request_id = str(uuid.uuid5(uuid.NAMESPACE_URL, BASE + "/" + account + "/" + args.credit_id))
    redeemed = request(
        opener,
        headers,
        {"credit_id": args.credit_id, "redeem_request_id": redeem_request_id},
    )
    code = redeemed.get("code")
    if code not in ("reset", "nothing_to_reset", "no_credit", "already_redeemed"):
        raise RuntimeError("Unrecognized redemption outcome. Do not retry; check status read-only.")
    windows = redeemed.get("windows_reset")
    print(
        json.dumps(
            {
                "account_ref": account_ref,
                "credit_id": args.credit_id,
                "code": code,
                "windows_reset": windows if type(windows) is int and windows >= 0 else None,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as error:
        print(f"Reset status request failed (HTTP {error.code}). No redemption attempted.", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError:
        print("Reset status endpoint could not be reached. No redemption attempted.", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except (OSError, subprocess.SubprocessError, sqlite3.Error, ValueError, KeyError, IndexError, TypeError):
        print(
            "Reset lookup failed. Check the active OAuth connection and OpenCode database compatibility.",
            file=sys.stderr,
        )
        sys.exit(1)
