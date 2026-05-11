---
name: acmi
description: Use this skill whenever the user works with ACMI (Agentic Context Memory Interface) — the open protocol giving AI agents persistent Profile/Signals/Timeline memory via @madezmedia/acmi-mcp. Triggers include any acmi_* tool name (acmi_profile, acmi_signal, acmi_event, acmi_get, acmi_list, acmi_cat, acmi_bootstrap, acmi_spawn, acmi_rollup_set, acmi_work_create, acmi_work_event, acmi_work_signal, acmi_work_get, acmi_work_list, acmi_delete); explicit references to ACMI, the @madezmedia/acmi npm package, the Smithery acmi-mcp listing, named ACMI threads (agent-coordination, newsroom) or agents (claude-engineer, bentley, claude-web, gemini-cli); the protocol vocabulary (Profile/Signals/Timeline, correlationId chains, parentCorrelationId, rollups, work items, bootstrap, spawn). Works across Claude Code, Claude.ai, Desktop, Cowork, Cursor, Cline, Perplexity. If acmi-mcp tools aren't connected, walks through install + auth first.
license: MIT
---

# ACMI — Agentic Context Memory Interface

ACMI is an open protocol (MIT, [github.com/madezmedia/acmi](https://github.com/madezmedia/acmi)) that gives AI agents three things every persistent agent needs:

```
Profile  →  who   (identity, configuration, role)         — stable, overwrite/merge
Signals  →  now   (current state, what's open, what's hot) — mutable KV map
Timeline →  then  (everything that happened, in order)     — append-only event log
```

Every entity in ACMI — an agent, a human, a project, a thread, a work item — has exactly these three slots. That's the whole protocol. No schemas, no migrations, no joins. The reference SDK is `@madezmedia/acmi` on npm; the MCP server is `@madezmedia/acmi-mcp`, also listed on Smithery as `madezmediapartners/acmi-mcp`.

## When this skill applies

Use this skill any time the user is doing one of:

- **Reading agent state** ("what is claude-engineer working on?", "show me the latest events on the agent-coordination thread")
- **Writing agent state** ("log this decision", "checkpoint this milestone", "set my current task to X")
- **Coordinating agents** ("hand this off to bentley", "ping the fleet", "who's awake right now")
- **Bootstrapping a session** ("get me caught up", "what was I doing yesterday", "resurrect the rollup")
- **Managing work items** ("create a work item for X", "what's the status of the smithery-specialist work item")
- **Walking correlation chains** ("show me everything related to incident-Y", "trace this decision back to its parent")
- **Setting up ACMI for the first time** (install, auth, transport, first event)

If the `acmi_*` tools are not present in the current session, **walk the user through install/auth before anything else** — see `references/install.md`.

## The mental model — read this once, internalize it

There is one universe of entities, addressed by `<namespace>:<id>`. Common namespaces are `agent`, `user`, `thread`, `work`, `project`, `session`. Each entity has the three slots above, stored in Redis under `acmi:<namespace>:<id>:profile`, `…:signals`, and `…:timeline`. Adapters hide the storage; you only ever think in terms of the three slots.

Three rules carry their weight in nearly every workflow:

1. **The timeline is the source of truth for "what happened."** When in doubt, append an event. Profiles capture identity, signals capture now, but only the timeline captures history. Events are cheap; missing history is expensive.
2. **`correlationId` makes events composable.** Every event takes a `correlationId`; events that continue a workflow take a `parentCorrelationId` pointing at the originating event. Together this forms a chain you can walk backward to trace a decision, or forward to find every spinoff. Prefer descriptive camelCase IDs (`incidentSecretsLeak-1778419629871`) over opaque UUIDs — humans read these.
3. **Bootstrap before you act.** When a fresh session starts and there's even a chance prior context exists, call `acmi_bootstrap` first. It returns profile + signals + recent timeline + rollup in one shot. Acting blind on a stateful agent is how you make duplicate work and contradictory decisions.

## The 16 MCP tools — quick map

The `@madezmedia/acmi-mcp` server exposes 16 tools, grouped by purpose. Detailed signatures and examples live in `references/tool-reference.md`; this is the at-a-glance:

```
ENTITY READ/WRITE              WORK ITEMS                AGENT LIFECYCLE
acmi_profile  (write profile)  acmi_work_create          acmi_spawn       (log session start)
acmi_signal   (write signals)  acmi_work_event           acmi_bootstrap   (full context bundle)
acmi_event    (append event)   acmi_work_signal          acmi_active      (track thread engagement)
acmi_get      (read all 3)     acmi_work_get             acmi_rollup_set  (cross-session summary)
acmi_list     (list IDs in ns) acmi_work_list

MULTI-STREAM           HOUSEKEEPING
acmi_cat               acmi_delete (dry-run by default)
```

A few footguns to internalize:

- **`acmi_signal` is plural-by-payload.** The MCP tool takes a JSON string and merges every key in it into the entity's signals map. The SDK exposes `signals.set(key, value)` per-key; the MCP tool batches because every call is a round trip. Compose the full update object, then pass it once.
- **`acmi_event` requires source + summary; everything else is optional but you usually want `kind` and `correlationId`.** Without `correlationId`, your event is an orphan; nobody can chain off it.
- **Namespaces are not enforced; conventions are.** The protocol doesn't care if you write to `acmi:foo:bar:profile`. The fleet does. Use the canonical namespaces (`agent`, `user`, `thread`, `work`) unless you have a deliberate reason not to. See `references/namespace-guide.md`.

## The four canonical workflows

These four patterns cover ~90% of real usage. Each has a worked recipe in `references/patterns.md` and a runnable script under `scripts/`.

### 1. Bootstrap-on-spawn (every fresh agent session)

```
acmi_spawn(agentId)                   # log that you started
ctx = acmi_bootstrap(agentId)         # one call, full context
# read ctx.profile, ctx.signals, ctx.recent_timeline, ctx.rollup
# → now act with full prior context
```

Always do this at the top of an agent session if there's any chance the agent has prior history. Skipping it is the #1 cause of agents repeating themselves or contradicting yesterday's decisions.

### 2. Log a milestone with a correlationId chain

```
correlationId = "<descriptiveCamelCase>-<msEpoch>"
acmi_event(
  namespace="agent", id="claude-engineer",
  source="agent:claude-engineer",
  kind="milestone-shipped",
  correlationId=correlationId,
  summary="[milestone-shipped @mikey] Smithery listing reached 90 quality score",
)
# Children of this event reference parentCorrelationId=correlationId
```

Notice the `[kind-tag @recipient]` prefix in the summary — this is a fleet convention that makes timelines scannable. See `references/patterns.md` for the full convention list.

### 3. Hand off work between agents

```
# Sender: log handoff event referencing the receiver
acmi_event(
  namespace="thread", id="agent-coordination",
  source="agent:bentley",
  kind="task-delegation",
  correlationId="bentleyHandoffToEngineer-<ts>",
  summary="[task-delegation @claude-engineer] Smithery scan failing — debug + fix",
)
# Receiver (next session): bootstrap, see the handoff event, ack with parentCorrelationId
acmi_event(
  namespace="thread", id="agent-coordination",
  source="agent:claude-engineer",
  kind="handoff-ack",
  correlationId="engineerAckBentleyHandoff-<ts>",
  parentCorrelationId="bentleyHandoffToEngineer-<ts>",
  summary="[handoff-ack] picking up Smithery scan debug",
)
```

### 4. Roll up a session before you sleep

```
acmi_rollup_set(
  agentId="claude-engineer",
  rollup=json.dumps({
    "session_summary": "...",
    "decisions_made": [...],
    "open_blockers": [...],
    "next_session_priorities": [...],
    "key_correlation_ids": [...]
  })
)
```

The next session's `acmi_bootstrap` will load this rollup. A good rollup is the difference between a fresh session that resumes mid-thought and one that re-derives everything from scratch.

## Cross-surface notes

ACMI is surface-agnostic — the same MCP tools work the same way everywhere. A few surface-specific tips:

- **Claude Code / Cowork** — You have shell + file tools. The bundled scripts in `scripts/` (e.g., `bootstrap-then-rollup.sh`, `chain-walker.py`) work directly; use them to avoid burning model time on repeated patterns.
- **Claude.ai / Claude Desktop** — No shell. Stick to the MCP tools directly; copy script logic into a Python REPL artifact if needed.
- **Perplexity / Cursor / Cline / other MCP hosts** — Same MCP tools, same semantics. These hosts often connect via the Smithery hosted URL rather than local stdio; the tool names and behavior are identical either way.
- **Headless API usage** — Use the `@madezmedia/acmi` SDK directly with the `UpstashAdapter`; see `examples/02-claude-integration.mjs` in the npm package.

## When the tools aren't available — install + auth

If you call any `acmi_*` tool and get "tool not found", or if the user is setting up ACMI for the first time, route them through `references/install.md`. The TL;DR is:

```
npm install -g @madezmedia/acmi-mcp
export UPSTASH_REDIS_REST_URL="https://your-instance.upstash.io"
export UPSTASH_REDIS_REST_TOKEN="..."
# Then add to MCP host config (Claude Desktop, Cursor, Cline, Cowork) — see install.md
```

For Smithery-hosted (no local install), give the user the connect URL: `https://server.smithery.ai/@madezmediapartners/acmi-mcp`. Auth is via per-user Upstash credentials passed through the host's MCP config.

## Reference files — when to read which

- `references/protocol-spec.md` — Full ACMI Specification v1.3. Read when the user asks about correctness, conformance, multi-actor (`actor_type`), or multi-tenant (`tenant_id`) behavior.
- `references/tool-reference.md` — Every MCP tool with full parameter list, return shape, gotchas, and a worked example. Read when you need exact tool semantics.
- `references/patterns.md` — Worked recipes for the four canonical workflows plus 8 more (heartbeats, RL signals, lock protocol, fleet discovery, HITL queues, etc.). Read when the user describes a coordination pattern.
- `references/namespace-guide.md` — Canonical namespaces, naming conventions, and the `[kind-tag @recipient]` summary convention. Read before writing any event.
- `references/install.md` — Install, auth, transport choice (stdio vs HTTP), per-host configuration, troubleshooting. Read when the tools aren't connected.
- `references/sdk-mcp-drift.md` — Known drift between the SDK API surface and the MCP tool surface. Read when something in the SDK docs doesn't match what the MCP tool does.

## Bundled scripts

- `scripts/bootstrap-then-rollup.sh` — Run at session start: spawns + bootstraps + prints a human summary of priorities. Usage: `bootstrap-then-rollup.sh <agentId>`
- `scripts/chain-walker.py` — Walks a `correlationId` chain forward and backward across multiple entity timelines. Usage: `chain-walker.py <correlationId> [--depth=5]`
- `scripts/event-template.py` — Generates a well-formed event JSON with a fresh camelCase correlationId. Usage: `event-template.py --kind=milestone-shipped --to="@mikey" --summary="..."`
- `scripts/dry-run-validator.py` — Validates an event payload against ACMI Comms v1.1 before you call `acmi_event`. Usage: `echo '<json>' | dry-run-validator.py`

## Conventions worth memorizing

- **Summary format:** `[kind-tag @recipient] <one-line description>` — kind-tag matches the event's `kind` field; `@recipient` is the agent or human the event addresses; the line should make sense in a timeline browser without expanding the payload.
- **Kind taxonomy:** Prefer existing kinds (`milestone-shipped`, `decision`, `handoff-ack`, `work-created`, `work-update`, `work-completed`, `incident-update`, `scope-decision`, `coord-note`, `heartbeat`, `artifact-published`, `team-loop`). Inventing a new kind is fine — be deliberate about it and document it in `references/patterns.md` if it's reusable.
- **CorrelationId format:** `<descriptiveCamelCase>-<msEpoch>`. Example: `mikeyDeadlineDayDecisions-1778390495224`. The epoch suffix gives uniqueness; the prefix gives human readability.
- **Actor type (v1.3):** Profiles MUST declare `actor_type` ∈ {`agent`, `human`, `system`, `external`}. The SDK auto-fills based on namespace prefix (`agent:` → `"agent"`, `user:` → `"human"`); the MCP server does not auto-fill, so include it explicitly when writing profiles via MCP.
- **Tenant (v1.3, optional):** Multi-customer deployments add `tenant_id` to profiles. Default is `"madez"`; use `"client:<slug>"` for per-client isolation, `"shared"` for cross-tenant.

## What this skill does NOT do

- It does not deploy the MCP server or stand up Upstash for the user — that's manual ops, see `install.md`.
- It does not validate Smithery listings or push npm releases — see the separate `smithery-expert` skill if it exists.
- It does not invent new kinds, namespaces, or schema fields without a clear reason — those decisions are fleet-level governance, not per-session.

## One last thing

ACMI is a protocol, not a framework. The whole point is that nothing about how you use it is mandated — only the three slots and the event shape. Use this skill as guardrails for the common case; depart from it deliberately when the situation calls for it.
