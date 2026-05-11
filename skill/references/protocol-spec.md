# ACMI Protocol Specification — v1.3 (condensed)

The full SPEC.md lives in [github.com/madezmedia/acmi](https://github.com/madezmedia/acmi). This is a condensed working reference for skill use. When in doubt about correctness or conformance, read the canonical SPEC.

## The three slots

Every entity has exactly three slots:

| Slot | Question | Storage | Mutation |
|---|---|---|---|
| `profile` | who | JSON document | overwrite + shallow merge |
| `signals` | now | KV map of JSON values | per-key set / delete |
| `timeline` | then | sorted set of events | append-only |

That's the entire data model. No other shapes, no other operations.

## Entity IDs

`<category>:<id>` — combined ≤ 256 chars.
- `<category>` matches `[a-z][a-z0-9_-]*`
- `<id>` matches `[a-zA-Z0-9_.-]+`

Adapter-side keys: `acmi:<category>:<id>:<slot>`. Reserved prefixes: don't use `acmi:` in your own IDs.

## Profile slot — operations

- `profileGet(id) → ProfileDoc | null`
- `profileSet(id, doc)` — overwrite
- `profileMerge(id, partial)` — shallow merge (top-level only)
- `profileDelete(id)`

Reads return copies; mutating the returned object MUST NOT affect storage.

## Signals slot — operations

- `signalsGet(id, key) → value | undefined`
- `signalsSet(id, key, value)`
- `signalsAll(id) → Record<string, value>`
- `signalsDelete(id, key)`

Storage may be STRING+JSON or native HASH; the choice is invisible to callers.

## Timeline slot — operations + Comms v1.1 event schema

- `timelineAppend(id, event)`
- `timelineRead(id, opts?) → events[]`
- `timelineSize(id) → number`

Event MUST have all five fields:

| Field | Type | Notes |
|---|---|---|
| `ts` | number | Wall-clock ms; monotonicity not required across writers |
| `source` | string | Entity-ID-formatted: `agent:foo`, `user:mikey` |
| `kind` | string | Event taxonomy |
| `correlationId` | string | Chain identifier |
| `summary` | string | Human-readable, ≤500 chars |

Optional: `parentCorrelationId`, `payload`, `tags`, `speaker_type` (v1.3).

`timelineRead` options: `limit`, `reverse`, `sinceMs`, `untilMs`.

**Append-only.** No mutation/deletion in the protocol; adapters MAY support it for compliance.

## Validation rules (SDK-side)

- Entity IDs match §2 pattern
- Profile docs are plain objects
- Signal keys are 1–128 chars
- Events have all five Comms v1.1 fields populated; `ts` finite number, others non-empty strings

## Conformance

Adapters pass the conformance suite at `@madezmedia/acmi/testing/conformance`. The suite asserts round-tripping, isolation, validation, and read-copy semantics.

## v1.3 additions

### §11 — Multi-actor

Profiles MUST declare `actor_type ∈ {agent, human, system, external}`.

| `actor_type` | Primary key prefix | Notes |
|---|---|---|
| `agent` | `acmi:agent:<id>:*` | Autonomous LLM/scripted |
| `human` | `acmi:user:<id>:*` | Note: `user:` prefix, not `human:` |
| `system` | (no profile required) | Cron, webhooks, telemetry |
| `external` | `acmi:external:<id>:*` (reserved for v1.3.1+) | Clients, vendors |

**Dual-projection forbidden.** Same `<id>` cannot exist in both `agent:` and `user:`. Resolve via §11.5 deprecation procedure.

SDK auto-fills `actor_type` from namespace prefix; MCP server does not auto-fill (include explicitly).

Optional event field `speaker_type` (v1.3, OPTIONAL → may be REQUIRED in v1.4) lets readers distinguish synthesizable agent reasoning from lived-experience human input.

Per-actor HITL queues:
```
acmi:hitl:user:<id>:open / :closed
acmi:hitl:agent:<id>:open / :closed
```
Shared queues from v1.2 remain valid.

### §12 — Multi-tenant

Optional `tenant_id` on profiles:
- `"madez"` (default — preserves v1.2 single-tenant behavior)
- `"client:<slug>"` per-client
- `"shared"` cross-tenant entities (registries, protocol data)

Key prefix for tenant-scoped entries:
```
acmi:tenant:<tenant_id>:<category>:<id>:<slot>
```

Workspace sub-scope (within a tenant) keeps the older `acmi:workspace:<workspace>:*` form.

**Isolation rules.** Different tenants MUST NOT share keys. Cross-tenant reference via `mention_alias` or `parent_correlation_id`, not direct key sharing.

## Versioning

ACMI follows semver at the SPEC level — major (breaking), minor (additive), patch (clarifications). The reference SDK has its own semver track.

v1.2 → v1.3 was MINOR (§11 + §12 are entirely additive; v1.2 deployments work unmodified).

## Extensions (informational, not part of core protocol)

These are layered conventions used in production:

- **Lock-Protocol** — optimistic locking via versioned signals
- **Anti-Dead Heartbeats** — periodic `kind: heartbeat` events for liveness
- **RL Cycle** — `payload.logAssessment` (0–100) on completion events
- **Fleet Coordination** — agent discovery via `acmi:registry:fleet:*`

See `patterns.md` for recipes.
