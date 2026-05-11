# SDK ↔ MCP Drift Report

This file documents known differences between the `@madezmedia/acmi` SDK API surface and the `@madezmedia/acmi-mcp` v1.3.0 MCP tool surface. The SDK is the canonical reference; the MCP server is a wrapper that occasionally simplifies or batches operations to reduce round-trip cost.

When in doubt, the SPEC.md operations are authoritative — both SDK and MCP MUST honor them, but the MCP tool names and call shapes may differ for ergonomics.

## Naming differences

| Operation | SDK (canonical) | MCP tool | Notes |
|---|---|---|---|
| Read profile + signals + recent timeline | `acmi.bootstrap(id)` (composite) | `acmi_get(namespace, id)` | MCP returns last 10 timeline events; SDK call returns full bootstrap context including rollup |
| Set profile | `acmi.profile.set(id, doc)` | `acmi_profile(namespace, id, profile=<JSON string>)` | MCP requires JSON-string serialization |
| Set one signal | `acmi.signals.set(id, key, value)` | `acmi_signal(namespace, id, signals=<JSON string of map>)` | MCP batches; pass a map of multiple keys per call |
| Append timeline event | `acmi.timeline.append(id, event)` | `acmi_event(namespace, id, source, summary, kind?, correlationId?)` | MCP exposes the five Comms v1.1 fields as named params; `parentCorrelationId`, `payload`, `tags` not exposed in v1.3.0 — use SDK if you need them |
| Read timeline (multi-entity) | `acmi.timeline.cat(ids[], opts)` (extension) | `acmi_cat(keys, since?, limit?)` | Same shape, different param names |
| Set rollup | `acmi.rollup.set(agentId, rollup)` | `acmi_rollup_set(agentId, rollup=<JSON string>)` | |
| Spawn session | `acmi.spawn(agentId, opts)` | `acmi_spawn(agentId, sessionId?, modelId?)` | |

## Behavioral differences

### `actor_type` auto-fill

- **SDK**: Auto-fills `actor_type` based on entity-ID namespace prefix (`agent:` → `"agent"`, `user:` → `"human"`).
- **MCP**: Does NOT auto-fill. You must include `actor_type` explicitly in the profile JSON when writing via `acmi_profile`.

If you write a profile via MCP without `actor_type`, the entity will not be v1.3-conformant. Reads still work; downstream v1.3-aware tools may reject or warn.

### Profile merge semantics

- **SDK**: `acmi.profile.merge(id, partial)` does a shallow merge — top-level key replacement.
- **MCP**: No `acmi_profile_merge` tool. `acmi_profile` is overwrite-only. To merge, do `acmi_get` + mutate + `acmi_profile`.

### Per-key signal write atomicity

- **SDK**: `signals.set(id, key, value)` is atomic at the per-key level (uses HSET on Redis HASH adapters).
- **MCP**: `acmi_signal` writes the full provided map; existing keys not in the payload are preserved, but the merge happens at the server side. Two concurrent `acmi_signal` calls with overlapping keys race.

For high-contention slots, use the lock-protocol (see `patterns.md`).

### Event optional fields

- **SDK**: `timeline.append` accepts `parentCorrelationId`, `payload` (any JSON), `tags` (string[]), `speaker_type` (v1.3), and arbitrary additional fields — adapters round-trip losslessly.
- **MCP**: `acmi_event` exposes only `source`, `summary`, `kind`, `correlationId` as named params in v1.3.0. Optional fields can't be set through MCP today.

**Workaround.** When you need `parentCorrelationId` or `payload` from an MCP-only context, embed the relationship in the `summary` (e.g., "[child-of cidXyz-...]") until the next MCP server release exposes the full schema. Or call the SDK directly from a script.

## Tool name historical drift

- The early MCP server prototype used `acmi_signals` (plural) and `acmi_timeline`. Current v1.3.0 uses `acmi_signal` (singular, batched) and `acmi_event`. If you see references to the old names in older docs or work items, treat them as the new names.
- Some early Smithery listings used "Agentic Context Management Infrastructure" as the expansion; the SPEC and current README use "Agentic Context Memory Interface". Both expand to ACMI; the SPEC name is canonical.

## What the MCP server does that the SDK doesn't

- **One-call bootstrap with rollup.** `acmi_bootstrap` is a higher-level composite — profile + signals + active threads + recent timeline + spawns + rollup. The SDK has equivalent operations but doesn't ship a single-call bootstrap helper out of the box.
- **Auto-filled timestamps.** `acmi_event` fills `ts` server-side. The SDK requires you to set `ts` (usually `Date.now()`); some convenience wrappers do it for you.
- **Dry-run delete.** `acmi_delete` is dry-run by default — returns what would be deleted, requires explicit confirmation. The SDK's `*.delete` operations are immediate.

## Reporting drift

If you find a tool that behaves differently from this document or from the SPEC, please file an issue at [github.com/madezmedia/acmi/issues](https://github.com/madezmedia/acmi/issues) with the version of `@madezmedia/acmi-mcp` you're using (`acmi-mcp --version`).
