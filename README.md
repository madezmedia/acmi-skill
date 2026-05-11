# acmi-skill — universal ACMI operator playbook for Claude

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Eval Pass Rate](https://img.shields.io/badge/Eval%20Pass%20Rate-100%25-2d4a3e)](./evals/iteration-1/benchmark.md)
[![Companion: @madezmedia/acmi](https://img.shields.io/badge/Companion-%40madezmedia%2Facmi-blue)](https://github.com/madezmedia/acmi)
[![Companion: @madezmedia/acmi-mcp](https://img.shields.io/badge/MCP-%40madezmedia%2Facmi--mcp-orange)](https://smithery.ai/server/madezmediapartners/acmi-mcp)

A Claude skill that teaches Claude to use the [ACMI protocol](https://github.com/madezmedia/acmi) — three keys (Profile / Signals / Timeline) for persistent agent memory, exposed via the `@madezmedia/acmi-mcp` MCP server.

Works on every Claude surface: Claude Code, Claude.ai, Claude Desktop, Cowork, Cursor, Cline, Perplexity — anywhere `acmi-mcp` is connected.

## What it does

Without this skill, Claude knows the ACMI tool names exist but invents fake parameter names (`workId`, `eventType`, `addressedTo`), reuses parent correlationIds as event correlationIds (chain corruption), and writes unstructured prose rollups that don't help the next session.

With this skill, Claude:

- Bootstraps every session with the right context-loading order
- Writes events that follow the fleet's `[kind-tag @recipient]` summary convention
- Generates well-formed `<descCamel>-<msEpoch>` correlationIds and chains them via `parentCorrelationId`
- Knows the SDK ↔ MCP drift and works around v1.3.0 limitations
- Closes sessions with structured rollups the next bootstrap can read

## Install

**Via Cowork self-hosted marketplace (instant):**
```
/plugin marketplace add github:madezmedia/acmi-skill
/plugin install acmi
```

**Via Claude Code:**
```
/plugin marketplace add github:madezmedia/acmi-skill
/plugin install acmi
```

**Manually (any other surface):**
Download [`dist/acmi-v1.0.0.skill`](./dist/acmi-v1.0.0.skill) and unzip into your skills directory (e.g., `~/.claude/skills/acmi/`).

## Pairs with

The skill teaches Claude to use ACMI; the MCP server provides the 16 tools the skill calls.

- **MCP server (npm):** `npm install -g @madezmedia/acmi-mcp`
- **MCP server (Smithery):** [smithery.ai/server/madezmediapartners/acmi-mcp](https://smithery.ai/server/madezmediapartners/acmi-mcp)
- **SDK (headless / non-MCP):** `npm install @madezmedia/acmi`
- **Protocol spec:** [github.com/madezmedia/acmi](https://github.com/madezmedia/acmi) (SPEC v1.3)

See [`skill/references/install.md`](./skill/references/install.md) for full per-surface setup.

## What's in the bundle

| Path | Purpose |
|---|---|
| `skill/SKILL.md` | Operator playbook — mental model, four canonical workflows, cross-surface notes |
| `skill/references/protocol-spec.md` | Condensed ACMI SPEC v1.3 |
| `skill/references/tool-reference.md` | All 16 MCP tools with parameters, gotchas, examples |
| `skill/references/patterns.md` | 12 worked recipes (bootstrap, handoff, rollup, RL signals, lock protocol, …) |
| `skill/references/namespace-guide.md` | Canonical namespaces + `[kind-tag @recipient]` summary convention |
| `skill/references/install.md` | Cross-surface install + auth |
| `skill/references/sdk-mcp-drift.md` | Known differences between SDK and MCP v1.3.0 |
| `skill/scripts/event-template.py` | Generate well-formed Comms v1.1 event JSON |
| `skill/scripts/dry-run-validator.py` | Validate event payload before `acmi_event` |
| `skill/scripts/chain-walker.py` | Walk correlationId chains forward + backward |
| `skill/scripts/bootstrap-then-rollup.sh` | Session-start helper |

11 files, ~74 KB unpacked.

## Eval evidence

- **3 canonical workflow evals:** fresh-session-bootstrap, log-milestone-with-chain, session-end-rollup
- **With-skill:** 100% pass rate (17/17 assertions)
- **Baseline (no skill):** 60% pass rate (10/17 assertions)
- **Absolute delta:** +40%

Full eval workspace under [`evals/iteration-1/`](./evals/iteration-1/). Static reviewer HTML at [`evals/iteration-1-review.html`](./evals/iteration-1-review.html).

## Project structure

```
.
├── README.md
├── LICENSE                          # MIT
├── CHANGELOG.md                     # v1.0.0 release notes
├── SUBMISSION-PLAYBOOK.md           # How this skill gets distributed across 7 registries
├── SYNDICATION.md                   # Paste-ready listing copy
├── ARTIFACT-INVENTORY.md            # File-by-file inventory with hashes
├── .claude-plugin/
│   ├── marketplace.json             # Cowork / Claude Code marketplace manifest
│   └── plugin.json                  # Plugin manifest
├── skill/                           # The skill source (mirrors acmi-v1.0.0.skill)
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
├── dist/
│   └── acmi-v1.0.0.skill            # Packaged bundle
└── evals/                           # Eval workspace (kept for reproducibility)
    ├── evals.json
    ├── trigger-evals.json
    └── iteration-1/
```

## Roadmap

- v1.1 — Run the trigger-accuracy quantitative loop (currently manual; CLI sandbox blocked the automated path)
- v1.2 — Add `@madezmedia/acmi-mcp` v1.4 support once the upstream MCP server exposes `parentCorrelationId`, `payload`, `tags` as named parameters
- v2.0 — Multi-tenant guidance expanded (SPEC §12), more worked patterns for `actor_type: "external"` (per SPEC §11.1 v1.3.1+)

## License

[MIT](./LICENSE) © [Michael Shaw](https://github.com/madezmedia) / [Mad EZ Media](https://www.madezmedia.com)
