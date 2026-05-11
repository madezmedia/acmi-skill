# ACMI MCP Tool Reference

The `@madezmedia/acmi-mcp` server exposes 16 tools. This file is the authoritative reference for what each one takes, what it returns, and the gotchas that bite first-time users. Tools are grouped by purpose; within each group they're listed roughly in order of how often you'll reach for them.

## Table of contents

1. Entity read/write — `acmi_profile`, `acmi_signal`, `acmi_event`, `acmi_get`, `acmi_list`
2. Multi-stream — `acmi_cat`
3. Work items — `acmi_work_create`, `acmi_work_event`, `acmi_work_signal`, `acmi_work_get`, `acmi_work_list`
4. Agent lifecycle — `acmi_spawn`, `acmi_bootstrap`, `acmi_active`, `acmi_rollup_set`
5. Housekeeping — `acmi_delete`

A note on argument shapes: every tool that writes JSON (`profile`, `signals`, `rollup`) takes a **JSON-encoded string**, not a JSON object. The MCP server validates and parses internally. Always `json.dumps(...)` (or equivalent) before passing.

---

## 1. Entity read/write

### `acmi_get` — read everything

The single most-called tool. Returns profile + signals + last 10 timeline events for one entity.

| Param | Type | Required | Notes |
|---|---|---|---|
| `namespace` | string | yes | e.g., `"agent"`, `"thread"`, `"work"` |
| `id` | string | yes | Entity ID within the namespace |

Returns an object shaped `{ profile, signals, timeline_recent }`. Both `profile` and `signals` may be `null` if never set; `timeline_recent` is always an array (possibly empty).

**Worked example.** Read claude-engineer's current state:
```
acmi_get(namespace="agent", id="claude-engineer")
```

### `acmi_profile` — write profile

Writes a profile (overwrite, not merge — this is one footgun). The MCP tool does not implement `profileMerge` from the SDK; if you want to merge, read first, mutate, then write back.

| Param | Type | Required | Notes |
|---|---|---|---|
| `namespace` | string | yes | |
| `id` | string | yes | |
| `profile` | JSON string | yes | Must be a JSON object. Include `actor_type` for v1.3 conformance. |

**Worked example.**
```
acmi_profile(
  namespace="agent",
  id="my-new-agent",
  profile='{"actor_type":"agent","name":"my-new-agent","role":"researcher","fleet_role":"data-analysis"}'
)
```

### `acmi_signal` — write signals (batched per call)

This is named `acmi_signal` (singular) but takes a **map** of multiple signals to set in one call. Every key in the JSON string is set on the entity's signal map; existing keys not in the JSON are preserved.

| Param | Type | Required | Notes |
|---|---|---|---|
| `namespace` | string | yes | |
| `id` | string | yes | |
| `signals` | JSON string | yes | Object whose keys become signal keys. Values are arbitrary JSON. |

**Worked example.** Update three signals on a work item in one call:
```
acmi_signal(
  namespace="work",
  id="amd-hackathon-multi-framework-acmi",
  signals='{"submission_status":"SHIPPED","loom_recorded":true,"hf_space_url":"https://huggingface.co/spaces/madezmedia/acmi-timeline-browser"}'
)
```

### `acmi_event` — append a timeline event

The workhorse. Every cross-session, cross-agent breadcrumb goes through this.

| Param | Type | Required | Notes |
|---|---|---|---|
| `namespace` | string | yes | |
| `id` | string | yes | |
| `source` | string | yes | Who wrote it. Use entity-ID format: `agent:claude-engineer`, `user:mikey`. |
| `summary` | string | yes | One line, ≤500 chars. Use the `[kind-tag @recipient] ...` convention. |
| `kind` | string | no, but you almost always want it | Event taxonomy — `milestone-shipped`, `decision`, `handoff-ack`, etc. |
| `correlationId` | string | no, but you almost always want it | `<descriptiveCamelCase>-<msEpoch>` form. |

The tool auto-fills `ts` (current wall-clock ms). Optional fields — `parentCorrelationId`, `payload`, `tags` — are not exposed as named MCP parameters in v1.3.0 of the server; if you need them, write via the SDK directly or include them in `summary` until the next MCP release.

**Worked example.** Log a milestone with chain anchoring:
```
acmi_event(
  namespace="agent",
  id="claude-engineer",
  source="agent:claude-engineer",
  kind="milestone-shipped",
  correlationId="claudeEngineerSmitheryQualityWin-1778174324664",
  summary="[milestone-shipped @bentley @mikey] Smithery quality score reached 83 — 7-point gain after configSchema fix",
)
```

### `acmi_list` — list entity IDs in a namespace

Returns an array of entity IDs. Good for fleet discovery, sanity-checking your namespace usage, or finding work items whose IDs you've forgotten.

| Param | Type | Required | Notes |
|---|---|---|---|
| `namespace` | string | yes | |

**Worked example.**
```
acmi_list(namespace="work")  # returns array of all work item IDs
```

---

## 2. Multi-stream

### `acmi_cat` — merge timelines from multiple entities

Reads timeline events from multiple entities and returns them merged in chronological order. The "git log across the fleet" tool.

| Param | Type | Required | Notes |
|---|---|---|---|
| `keys` | array of strings | yes | Entries like `"thread:agent-coordination"`, `"agent:claude-engineer"`, or full keys `"acmi:thread:newsroom:timeline"` |
| `since` | string | no | Time window: `"30m"`, `"24h"`, `"7d"`. Default: all time. |
| `limit` | number | no | Default 50. Cap at a few hundred to keep responses reasonable. |

**Worked example.** Show me what happened on the agent-coordination thread + the three most relevant agents in the last 6 hours:
```
acmi_cat(
  keys=["thread:agent-coordination", "agent:claude-engineer", "agent:bentley", "agent:claude-web"],
  since="6h",
  limit=100
)
```

---

## 3. Work items

Work items are first-class entities under the `work:` namespace, intended for cross-session projects, tasks, or ideas. They have all three slots (profile/signals/timeline) like any other entity, plus four convenience tools that pre-set `namespace="work"`.

### `acmi_work_create` — create a work item

| Param | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Work item ID (use kebab-case: `acmi-mcp-browser-onboard`) |
| `profile` | JSON string | yes | Title, owner, status, priority, etc. |

**Worked example.**
```
acmi_work_create(
  id="acmi-skill-syndication",
  profile=json.dumps({
    "title": "Universal ACMI skill — syndicate to Smithery + Cowork + GitHub + Anthropic registry",
    "owner": "mikey + claude-engineer",
    "status": "DRAFT",
    "priority": "P2",
    "deliverables": ["SKILL.md", ".plugin bundle", "Smithery skill listing", "GitHub repo"]
  })
)
```

### `acmi_work_event` — append a progress event on a work item

Convenience wrapper around `acmi_event` with `namespace="work"`.

| Param | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Work item ID |
| `source` | string | yes | |
| `summary` | string | yes | |
| `sessionId` | string | no | Associate with a specific session for later grouping |

### `acmi_work_signal` — update work item signals

Same shape as `acmi_signal`, with `namespace="work"` implied.

### `acmi_work_get` — read a work item

Returns `{ profile, signals, timeline_recent }`, same shape as `acmi_get(namespace="work", id=...)`.

### `acmi_work_list` — list all work item IDs

Equivalent to `acmi_list(namespace="work")`.

---

## 4. Agent lifecycle

### `acmi_spawn` — log a session start

Records that an agent started a new session. Pairs with `acmi_bootstrap` (which reads). Cheap; call it at the top of every session.

| Param | Type | Required | Notes |
|---|---|---|---|
| `agentId` | string | yes | The agent that spawned |
| `sessionId` | string | no | Auto-generated if absent |
| `modelId` | string | no | Model powering the session, e.g., `claude-opus-4-7` |

### `acmi_bootstrap` — full context bundle

The most valuable tool for fresh agents. One call returns everything an agent needs to act with full prior context.

| Param | Type | Required | Notes |
|---|---|---|---|
| `agentId` | string | yes | |

Returns:
- `profile` — the agent's profile
- `signals` — current signals (mood, priorities, scores)
- `active_threads` — threads the agent is engaged in
- `recent_timeline` — last N events from the agent's timeline
- `spawns_recent` — recent session spawns
- `rollup` — the latest rollup snapshot from `acmi_rollup_set`

**Always call this at the top of an agent session if there's any chance of prior history.**

### `acmi_active` — track thread engagement

Tracks which threads an agent is currently engaged in. Useful for fleet dashboards and for `acmi_bootstrap` to know which threads to surface.

| Param | Type | Required | Notes |
|---|---|---|---|
| `agentId` | string | yes | |
| `action` | enum | yes | `"add"`, `"remove"`, or `"list"` |
| `threadKey` | string | yes for add/remove | e.g., `"agent-coordination"` |
| `role` | string | no | `"participant"` (default) or `"lead"` |

### `acmi_rollup_set` — set the agent's latest rollup

Stores a cross-session summary at `acmi:agent:<id>:rollup:latest`. `acmi_bootstrap` reads this. A good rollup makes the next session resume mid-thought.

| Param | Type | Required | Notes |
|---|---|---|---|
| `agentId` | string | yes | |
| `rollup` | JSON string | yes | Whatever shape you want; common keys are `session_summary`, `decisions_made`, `open_blockers`, `next_session_priorities`, `key_correlation_ids`. |

---

## 5. Housekeeping

### `acmi_delete` — remove an entity (dry-run by default)

Deletes profile + signals + timeline for an entity. **Dry-run by default** — you must explicitly confirm. The tool returns what would be deleted on first call; pass an explicit confirm flag (per current MCP server build) to actually delete.

This tool is mostly for cleanup of test entities, namespace migrations (per SPEC §11.5), and GDPR-style erasure. **Do not use it as part of normal workflow** — the timeline is supposed to be append-only.

---

## Cross-cutting gotchas

- **`acmi_signal` is not `acmi_signals`.** The plural-vs-singular naming is from the protocol's history; the MCP wrapper normalized to singular. The SDK exposes `signals.set(key, value)` per-key; the MCP tool batches via JSON. Don't expect a one-key call to be atomic — it's a write of the merged map.
- **Timestamps are server-side.** The MCP server fills `ts` with wall-clock ms at write-time. If you need an explicit `ts` (replaying historical events), write via the SDK directly.
- **No native deep merge.** Profile writes overwrite. If you want merge semantics, do read-mutate-write yourself.
- **No native atomicity across slots.** Writing profile + signals + an event is three calls and not transactional. For workflows that need atomicity, use the lock-protocol extension (see `patterns.md`).
- **Event ordering is by `ts`, not by write order.** If two writers are racing within the same millisecond, the order is undefined. Your `correlationId` chain is the recovery path.
