#!/usr/bin/env python3
"""
dry-run-validator.py — Validate an ACMI event payload against Comms v1.1 before
calling acmi_event. Reads JSON from stdin, prints PASS/FAIL with reasons.

Usage:
  echo '{"ts": 1778423299460, "source": "agent:claude", "kind": "milestone-shipped",
         "correlationId": "claudeShip-1778423299460", "summary": "[milestone-shipped @mikey] ..."}' \\
    | dry-run-validator.py

Exit code: 0 PASS, 1 FAIL.
"""

import json
import sys

REQUIRED_FIELDS = {"ts", "source", "kind", "correlationId", "summary"}
SUMMARY_MAX = 500
SIGNAL_KEY_MAX = 128


def validate(event: dict) -> list[str]:
    errors: list[str] = []

    missing = REQUIRED_FIELDS - set(event.keys())
    if missing:
        errors.append(f"Missing required fields: {sorted(missing)}")

    # ts
    ts = event.get("ts")
    if ts is not None:
        if not isinstance(ts, (int, float)):
            errors.append(f"`ts` must be a number, got {type(ts).__name__}")
        elif ts <= 0:
            errors.append(f"`ts` must be positive, got {ts}")

    # source
    src = event.get("source")
    if isinstance(src, str):
        if not src:
            errors.append("`source` must be non-empty")
        elif ":" not in src:
            errors.append(
                f"`source` should be entity-ID-formatted (e.g. agent:foo, user:mikey); got '{src}'"
            )

    # kind
    kind = event.get("kind")
    if isinstance(kind, str) and not kind:
        errors.append("`kind` must be non-empty")

    # correlationId
    cid = event.get("correlationId")
    if isinstance(cid, str):
        if not cid:
            errors.append("`correlationId` must be non-empty")
        elif "-" not in cid:
            errors.append(
                f"`correlationId` should follow <descCamel>-<msEpoch> form; got '{cid}'"
            )
        elif len(cid) > 128:
            errors.append(f"`correlationId` exceeds 128 chars ({len(cid)})")

    # summary
    summary = event.get("summary")
    if isinstance(summary, str):
        if not summary:
            errors.append("`summary` must be non-empty")
        elif len(summary) > SUMMARY_MAX:
            errors.append(
                f"`summary` exceeds {SUMMARY_MAX} chars ({len(summary)})"
            )
        elif not summary.lstrip().startswith("["):
            errors.append(
                "`summary` should start with [<kind-tag> @recipient...] convention"
            )

    # Optional fields — sanity check shapes
    if "parentCorrelationId" in event and not isinstance(
        event["parentCorrelationId"], str
    ):
        errors.append("`parentCorrelationId` must be a string when present")

    if "payload" in event and event["payload"] is not None:
        try:
            json.dumps(event["payload"])
        except (TypeError, ValueError) as e:
            errors.append(f"`payload` must be JSON-serializable: {e}")

    if "tags" in event:
        tags = event["tags"]
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            errors.append("`tags` must be a list of strings when present")

    return errors


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("FAIL: no input on stdin", file=sys.stderr)
        return 1
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"FAIL: invalid JSON — {e}", file=sys.stderr)
        return 1

    if not isinstance(event, dict):
        print("FAIL: input must be a JSON object", file=sys.stderr)
        return 1

    errors = validate(event)
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    print(f"  source         : {event['source']}")
    print(f"  kind           : {event['kind']}")
    print(f"  correlationId  : {event['correlationId']}")
    print(f"  summary length : {len(event['summary'])} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
