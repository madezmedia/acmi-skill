# ACMI Skill — Syndication Guide

This is the packaging copy and metadata for distributing the `acmi` skill across four registries. Each section is self-contained — copy-paste what you need.

## Deliverables in this folder

| File | Purpose |
|---|---|
| `acmi.skill` | The packaged skill bundle (zip). Install via Cowork's "Add skill" UI, or unzip into `~/.claude/skills/acmi/`. |
| `iteration-1-review.html` | Static eval viewer — click through each test case, see with-skill vs baseline outputs side-by-side. Submit feedback at the bottom and the file downloads as `feedback.json`. |
| `SYNDICATION.md` | This document. |

## 1. Smithery — skill listing

Smithery currently lists `@madezmediapartners/acmi-mcp` as a server. The skill is a separate artifact — it's instructions, not a server — but Smithery has been adding skill cards alongside server cards. If/when the skill-listing flow is live, use this:

**Listing slug:** `madezmediapartners/acmi`

**Short description (1 sentence, ≤160 chars):**
> Operator playbook for ACMI — the open protocol that gives AI agents persistent Profile/Signals/Timeline memory. Works on every Claude surface.

**Long description body:**
```markdown
ACMI (Agentic Context Memory Interface) gives AI agents three things every persistent agent needs:

- **Profile** — who an entity is (stable identity)
- **Signals** — what's current (mutable state)
- **Timeline** — what happened (append-only event log)

That's the entire protocol. No schemas, no migrations, no joins.

This skill is the **operator playbook** for using ACMI from any Claude surface — Claude Code, Claude.ai, Desktop, Cowork, Cursor, Cline, Perplexity. It teaches Claude:

- When and how to bootstrap a session with prior context
- How to write events with correlationId chains so timelines stay readable
- The fleet conventions for `[kind-tag @recipient]` summaries
- How to do session-end rollups so the next session resumes mid-thought
- Multi-agent handoff patterns
- The MCP↔SDK drift (parameter names, optional fields, atomicity)

**Bundled with the skill:**
- 6 reference files (tool reference, patterns, namespace guide, protocol spec v1.3, install guide, SDK/MCP drift)
- 4 helper scripts (event-template generator, dry-run validator, correlationId chain walker, bootstrap-then-rollup runner)

**Pairs with:** the `@madezmedia/acmi-mcp` server on Smithery, which provides the 16 ACMI tools this skill teaches Claude to use.

**Evals:** 100% pass rate on the 3 canonical workflows (bootstrap, milestone-with-chain, session-end rollup) vs 60% baseline. The skill prevents three real failure modes Claude exhibits without it: inventing fake parameter names (workId/eventType/addressedTo), reusing parent correlationIds as event correlationIds (chain corruption), and writing unstructured prose rollups instead of structured next-session briefs.
```

**Tags / topics:**
`agent-memory`, `multi-agent`, `mcp`, `claude`, `cursor`, `cline`, `windsurf`, `perplexity`, `redis`, `upstash`, `protocol`, `context-management`, `fleet-coordination`, `correlation-id`

**Icon recommendation:** Use the same hero/icon as the `@madezmediapartners/acmi-mcp` listing for visual continuity — the three-key (Profile/Signals/Timeline) graphic.

**Quality-score-friendly metadata:**
- ✅ Description ≥ 800 chars
- ✅ Long description with code/structure
- ✅ Homepage URL: https://github.com/madezmedia/acmi
- ✅ License: MIT
- ✅ Repository link
- ✅ Tags ≥ 8
- ✅ Companion server listed
- ✅ Eval evidence cited

## 2. Cowork plugin marketplace

Cowork plugins bundle skills with optional MCPs and commands. The skill alone is shippable as a single-skill plugin.

**Plugin manifest (`plugin.json`):**
```json
{
  "name": "acmi",
  "displayName": "ACMI — Agentic Context Memory Interface",
  "version": "1.0.0",
  "description": "Operator playbook for ACMI. Gives Claude persistent Profile/Signals/Timeline memory via the acmi-mcp server. Works across every Claude surface.",
  "author": "Mad EZ Media Partners <michael@madezmedia.com>",
  "license": "MIT",
  "homepage": "https://github.com/madezmedia/acmi",
  "repository": "https://github.com/madezmedia/acmi",
  "category": "productivity",
  "tags": ["agent-memory", "multi-agent", "mcp", "context-management", "redis", "upstash"],
  "skills": ["./skills/acmi"],
  "commands": [
    {
      "name": "acmi-bootstrap",
      "description": "Run at session start — spawn + bootstrap + print session-start brief",
      "skill": "acmi"
    },
    {
      "name": "acmi-rollup",
      "description": "Write a session-end rollup so the next session resumes mid-thought",
      "skill": "acmi"
    }
  ],
  "recommended_mcps": [
    {
      "name": "acmi-mcp",
      "package": "@madezmedia/acmi-mcp",
      "transport": "stdio",
      "config_schema": {
        "UPSTASH_REDIS_REST_URL": {"type": "string", "required": true},
        "UPSTASH_REDIS_REST_TOKEN": {"type": "string", "required": true, "secret": true}
      }
    }
  ]
}
```

**Suggested marketplace category:** Productivity → Memory & Context

**One-line tagline for the card:** "Persistent memory for your AI agents — works everywhere."

## 3. GitHub public repo (madezmedia/acmi-skill)

Recommended repo layout:
```
acmi-skill/
├── README.md                       (the body below)
├── LICENSE                         (MIT — copy from madezmedia/acmi)
├── CHANGELOG.md
├── skill/                          (the skill source — unpacked)
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/
│   └── evals/                      (kept out of .skill bundle but tracked here)
├── dist/
│   └── acmi.skill                  (packaged artifact, refreshed per release)
├── docs/
│   ├── install.md
│   └── examples/
└── .github/
    └── workflows/
        ├── package.yml             (runs package_skill.py, attaches to release)
        └── eval.yml                (re-runs evals on PR)
```

**README badges:**
```markdown
[![Smithery](https://smithery.ai/badge/madezmediapartners/acmi)](https://smithery.ai/server/madezmediapartners/acmi)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Eval Pass Rate](https://img.shields.io/badge/Eval%20Pass%20Rate-100%25-2d4a3e)](./evals/)
[![Companion: @madezmedia/acmi](https://img.shields.io/badge/Companion-%40madezmedia%2Facmi-blue)](https://github.com/madezmedia/acmi)
```

**README opening:**
```markdown
# acmi-skill — the universal ACMI operator playbook

A Claude skill that teaches Claude to use the [ACMI protocol](https://github.com/madezmedia/acmi) — three keys (Profile / Signals / Timeline) for persistent agent memory, exposed via the `@madezmedia/acmi-mcp` MCP server.

Works on every Claude surface: Claude Code, Claude.ai, Claude Desktop, Cowork, Cursor, Cline, Perplexity — anywhere `acmi-mcp` is connected.

## What it does

Without this skill, Claude knows the ACMI tool names exist but invents fake parameter names (`workId`, `eventType`, `addressedTo`), reuses parent correlationIds as event correlationIds (chain corruption), and writes unstructured prose rollups that don't help the next session.

With this skill, Claude:
- Bootstraps every session with the right context-loading order
- Writes events that follow the fleet's `[kind-tag @recipient]` summary convention
- Generates well-formed `<descCamel>-<msEpoch>` correlationIds and chains them via parentCorrelationId
- Knows the SDK ↔ MCP drift and works around the v1.3.0 limitations
- Closes sessions with structured rollups the next bootstrap can read

## Install

**Via Smithery (recommended):**
[smithery.ai/skill/madezmediapartners/acmi](https://smithery.ai/skill/madezmediapartners/acmi) → Add to your host.

**Via Cowork plugin:**
Search "ACMI" in Cowork's plugin marketplace.

**Manually (Claude Code, Claude Desktop):**
Download `dist/acmi.skill` from the latest release and unzip into `~/.claude/skills/acmi/`.

## Pairs with

You also want the actual ACMI MCP server connected:

- **npm:** `npm install -g @madezmedia/acmi-mcp`
- **Smithery:** [smithery.ai/server/madezmediapartners/acmi-mcp](https://smithery.ai/server/madezmediapartners/acmi-mcp)
- **SDK:** `npm install @madezmedia/acmi` for headless / non-MCP usage

See [`skill/references/install.md`](./skill/references/install.md) for full setup.
```

## 4. Anthropic skills index / general MCP registries

These are simpler — they typically index the SKILL.md and let the description do the work. The skill's frontmatter description already names every trigger phrase, every tool, every surface. For directory entries, use:

**Title:** `acmi` (lowercase, matches skill folder name)

**One-line summary:** "Persistent agent memory via Profile/Signals/Timeline — works on every Claude surface."

**Category:** Memory & Context / Multi-Agent Coordination

**Required MCP:** `@madezmedia/acmi-mcp` (or Smithery-hosted equivalent)

**Eval evidence (link if registry supports):**
- 3 canonical workflow evals
- 17/17 assertions pass with-skill (vs 10/17 baseline)
- +40% absolute pass rate delta

**Pitch for registry editors:** This skill demonstrates the "operator playbook" pattern — instead of teaching Claude the tool surface (which it can read from the MCP schemas), it teaches the fleet conventions that the schemas don't capture. The SDK↔MCP drift file and the four bundled helper scripts are also rarer artifact patterns worth highlighting.

## Release checklist

- [ ] `dist/acmi.skill` is fresh — re-run `python -m scripts.package_skill skill/ dist/`
- [ ] Evals re-run on the latest skill; `iteration-1-review.html` regenerated
- [ ] Description optimization done (`scripts/run_loop.py` — optional, run when triggering accuracy matters more than completeness)
- [ ] Smithery listing's metadata fields filled (icon, homepage, repository, tags ≥ 8)
- [ ] Cowork plugin manifest validated
- [ ] GitHub release tagged with the skill version
- [ ] Companion `@madezmedia/acmi-mcp` server is on the same version axis (skill 1.0.0 ↔ mcp 1.3.0)

## Versioning

The skill follows its own semver track, separate from `@madezmedia/acmi` (SPEC) and `@madezmedia/acmi-mcp` (server). Major-version bumps coincide with breaking changes to skill behavior or the cross-surface contract; minor bumps add reference files or scripts; patches are content tweaks.
