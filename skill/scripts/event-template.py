#!/usr/bin/env python3
"""
event-template.py — Generate a well-formed ACMI Comms v1.1 event with a fresh
camelCase correlationId. Prints JSON to stdout.

Usage:
  event-template.py --kind=milestone-shipped --to=mikey --summary="..."
  event-template.py --kind=decision --to=bentley --to=mikey --source=agent:claude-engineer \
                    --summary="repo boundary chosen" --parent=mikeyBatchRatify-1778253508631

The output is suitable for piping into acmi_event (after extracting fields) or
into the SDK's timeline.append. correlationId form: <descCamel>-<msEpoch>.
"""

import argparse
import json
import re
import sys
import time


def _camel(s: str) -> str:
    parts = re.split(r"[\s_\-]+", s.strip())
    parts = [p for p in parts if p]
    if not parts:
        return "event"
    return parts[0].lower() + "".join(p[:1].upper() + p[1:].lower() for p in parts[1:])


def _build_summary(kind: str, recipients: list[str], body: str) -> str:
    head = f"[{kind}"
    if recipients:
        head += " " + " ".join(f"@{r.lstrip('@')}" for r in recipients)
    head += "]"
    return f"{head} {body}"


def main() -> int:
    p = argparse.ArgumentParser(description="Generate a well-formed ACMI event JSON.")
    p.add_argument("--kind", required=True, help="Event kind (e.g. milestone-shipped)")
    p.add_argument(
        "--to",
        action="append",
        default=[],
        help="Recipient (no @ needed). Pass multiple --to flags for multiple recipients.",
    )
    p.add_argument("--source", default="agent:claude", help="source field; entity-ID format")
    p.add_argument("--summary", required=True, help="One-line description")
    p.add_argument("--parent", default=None, help="parentCorrelationId for chaining")
    p.add_argument(
        "--cid-prefix",
        default=None,
        help="Override the camelCase correlationId prefix (default derived from --kind + first --to)",
    )
    p.add_argument("--ts", type=int, default=None, help="Override ts (ms epoch). Default: now.")
    p.add_argument(
        "--namespace",
        default="thread",
        help="Target namespace for the event — informational only, included in output as a hint.",
    )
    p.add_argument(
        "--id",
        default="agent-coordination",
        help="Target entity id — informational only, included in output as a hint.",
    )
    args = p.parse_args()

    ts = args.ts if args.ts is not None else int(time.time() * 1000)

    if args.cid_prefix:
        cid_prefix = _camel(args.cid_prefix)
    else:
        seed = args.kind
        if args.to:
            seed = f"{args.kind} {args.to[0]}"
        cid_prefix = _camel(seed)
    correlation_id = f"{cid_prefix}-{ts}"

    summary = _build_summary(args.kind, args.to, args.summary)
    if len(summary) > 500:
        print(
            f"WARN: summary is {len(summary)} chars; ACMI Comms v1.1 caps at 500.",
            file=sys.stderr,
        )

    event = {
        "ts": ts,
        "source": args.source,
        "kind": args.kind,
        "correlationId": correlation_id,
        "summary": summary,
    }
    if args.parent:
        event["parentCorrelationId"] = args.parent

    out = {
        "_acmi_event_target": {"namespace": args.namespace, "id": args.id},
        "event": event,
        "_mcp_call_hint": {
            "tool": "acmi_event",
            "args": {
                "namespace": args.namespace,
                "id": args.id,
                "source": event["source"],
                "kind": event["kind"],
                "correlationId": event["correlationId"],
                "summary": event["summary"],
            },
        },
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
