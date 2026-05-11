#!/usr/bin/env python3
"""
chain-walker.py — Walk an ACMI correlationId chain forward (children) and
backward (parents) across one or more entity timelines. Reads timeline events
from JSON on stdin (or from a file via --events) and prints the chain in order.

This is a pure post-processor: it does not call MCP or Redis directly. Get the
raw events first via acmi_cat (or the timeline browser export), then pipe them
in.

Usage:
  acmi_cat keys=[...]  --since=24h --limit=500  > /tmp/events.json
  chain-walker.py --events=/tmp/events.json --root=incident-secrets-leak-acmi-protocol-repo-1778419629871

Or via stdin:
  cat events.json | chain-walker.py --root=<correlationId>

Options:
  --root <cid>           The root correlationId to walk from (required)
  --events <file>        Read events from this JSON file (else stdin)
  --depth <n>            Max depth in either direction (default 10)
  --format json|tree     Output format (default tree)
"""

import argparse
import json
import sys
from collections import defaultdict


def _load_events(path: str | None) -> list[dict]:
    raw = open(path).read() if path else sys.stdin.read()
    data = json.loads(raw)
    # Accept either a flat list or a wrapper object {"events": [...]}.
    if isinstance(data, dict) and "events" in data:
        events = data["events"]
    elif isinstance(data, list):
        events = data
    else:
        raise SystemExit("FAIL: input must be a list of events or {events: [...]}")
    out: list[dict] = []
    for e in events:
        if not isinstance(e, dict):
            continue
        if "correlationId" not in e:
            continue
        out.append(e)
    return out


def _index(events: list[dict]) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    by_cid: dict[str, dict] = {}
    children: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        cid = e["correlationId"]
        # If multiple events share a cid (rare), keep the earliest as canonical
        if cid not in by_cid or e.get("ts", 0) < by_cid[cid].get("ts", 0):
            by_cid[cid] = e
        parent = e.get("parentCorrelationId")
        if parent:
            children[parent].append(e)
    for k in children:
        children[k].sort(key=lambda x: x.get("ts", 0))
    return by_cid, children


def _walk_back(cid: str, by_cid: dict[str, dict], depth: int) -> list[dict]:
    chain: list[dict] = []
    seen: set[str] = set()
    cur: str | None = cid
    while cur and depth > 0 and cur not in seen:
        seen.add(cur)
        ev = by_cid.get(cur)
        if not ev:
            break
        chain.append(ev)
        cur = ev.get("parentCorrelationId")
        depth -= 1
    return list(reversed(chain))


def _walk_forward(cid: str, children: dict[str, list[dict]], depth: int) -> list[dict]:
    out: list[dict] = []
    stack: list[tuple[str, int]] = [(cid, depth)]
    seen: set[str] = set()
    while stack:
        c, d = stack.pop(0)
        if d <= 0 or c in seen:
            continue
        seen.add(c)
        for kid in children.get(c, []):
            out.append(kid)
            stack.append((kid["correlationId"], d - 1))
    out.sort(key=lambda x: x.get("ts", 0))
    return out


def _render_tree(
    root_cid: str,
    by_cid: dict[str, dict],
    children: dict[str, list[dict]],
    depth: int,
) -> str:
    lines: list[str] = []

    def fmt(e: dict, indent: int) -> str:
        pad = "  " * indent
        ts = e.get("ts", "?")
        src = e.get("source", "?")
        kind = e.get("kind", "?")
        summary = (e.get("summary") or "").replace("\n", " ")
        if len(summary) > 120:
            summary = summary[:117] + "..."
        return f"{pad}{ts}  {src:30}  {kind:25}  {summary}"

    # Backward chain (root + ancestors), printed top-down
    back = _walk_back(root_cid, by_cid, depth)
    if back and back[0]["correlationId"] != root_cid:
        lines.append("ANCESTORS (oldest first):")
        for e in back[:-1]:
            lines.append(fmt(e, 0))
        lines.append("ROOT:")
        lines.append(fmt(back[-1], 0))
    elif back:
        lines.append("ROOT:")
        lines.append(fmt(back[-1], 0))
    else:
        lines.append(f"ROOT (cid={root_cid}) not found in events")

    # Forward chain (children, breadth-first)
    fwd = _walk_forward(root_cid, children, depth)
    if fwd:
        lines.append("")
        lines.append("DESCENDANTS (chronological):")
        for e in fwd:
            lines.append(fmt(e, 1))
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, help="Root correlationId to walk")
    p.add_argument("--events", default=None, help="JSON file with events (else stdin)")
    p.add_argument("--depth", type=int, default=10)
    p.add_argument("--format", choices=["json", "tree"], default="tree")
    args = p.parse_args()

    events = _load_events(args.events)
    by_cid, children = _index(events)

    if args.format == "tree":
        print(_render_tree(args.root, by_cid, children, args.depth))
    else:
        out = {
            "root": args.root,
            "ancestors": _walk_back(args.root, by_cid, args.depth),
            "descendants": _walk_forward(args.root, children, args.depth),
        }
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
