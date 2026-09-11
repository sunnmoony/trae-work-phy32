#!/usr/bin/env python3
"""Call the HT API execute endpoint without external dependencies."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://dyapi.huitun.com"
EXECUTE_PATH = "/v1/ai/api"
DEFAULT_TIMEOUT = 120


def parse_query(raw_query):
    try:
        query = json.loads(raw_query)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--query must be valid JSON: {exc.msg}") from exc
    if not isinstance(query, dict):
        raise SystemExit("--query must be a JSON object")
    return query


def write_payload(payload):
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        sys.stdout.write(payload)
        if payload and not payload.endswith("\n"):
            sys.stdout.write("\n")
        return
    json.dump(parsed, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Call the HT API execute endpoint.")
    parser.add_argument(
        "--base-url",
        default=os.getenv("HT_API_BASE_URL", DEFAULT_BASE_URL),
    )
    parser.add_argument("--auth", default=os.getenv("Data_Query_KEY"))
    parser.add_argument("--api", required=True, help="HT API name")
    parser.add_argument("--query", required=True, help="JSON object")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args()

    if not args.auth:
        raise SystemExit("Data_Query_KEY or --auth is required")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    body = {
        "api": args.api,
        "query": parse_query(args.query),
    }
    url = args.base_url.rstrip("/") + EXECUTE_PATH

    req = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "api-key": args.auth,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        if payload:
            write_payload(payload)
        sys.stderr.write(f"HTTP_STATUS:{exc.code}\n")
        return 1
    except (urllib.error.URLError, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        sys.stderr.write(f"Network error: {reason}\n")
        return 1

    write_payload(payload)
    sys.stderr.write(f"HTTP_STATUS:{status}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
