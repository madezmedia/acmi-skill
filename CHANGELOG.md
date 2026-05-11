# acmi-skill — Changelog

## v1.0.0 — 2026-05-11

Initial release of the universal ACMI operator playbook skill.

### Artifacts
- `acmi.skill` — packaged bundle (zip), installable via Cowork or unzipped into `~/.claude/skills/acmi/`
- 11 files: SKILL.md, 6 reference docs, 4 helper scripts
- ~74 KB unpacked
- License: MIT

### Skill bundle contents
- `SKILL.md` — operator playbook (the mental model, four canonical workflows, cross-surface notes, file index)
- `references/protocol-spec.md` — condensed ACMI SPEC v1.3
- `references/tool-reference.md` — every MCP tool with parameters, gotchas, worked examples
- `references/patterns.md` — 12 worked recipes (bootstrap-on-spawn, milestone chains, handoffs, rollups, heartbeats, RL signals, lock protocol, fleet discovery, HITL queues, incident chaining, work-item lifecycle, multi-stream `acmi_cat`)
- `references/namespace-guide.md` — canonical namespaces, summary line convention, kind taxonomy, correlationId format, tenant prefixing
- `references/install.md` — install/auth across Claude Desktop, Cursor, Cline, Windsurf, Claude Code, Cowork, Smithery HTTP, SDK direct
- `references/sdk-mcp-drift.md` — documented differences between `@madezmedia/acmi` SDK and `@madezmedia/acmi-mcp` v1.3.0
- `scripts/event-template.py` — generates well-formed Comms v1.1 event JSON with fresh camelCase correlationId
- `scripts/dry-run-validator.py` — validates event payload against Comms v1.1 before calling `acmi_event`
- `scripts/chain-walker.py` — walks correlationId chains forward + backward across multiple timelines
- `scripts/bootstrap-then-rollup.sh` — session-start helper (spawn + bootstrap + print brief)

### Iteration 1 evals
- 3 canonical workflows tested: fresh-session-bootstrap, log-milestone-with-chain, session-end-rollup
- **With-skill: 100% pass rate (17/17 assertions)**
- **Baseline (no skill): 60% pass rate (10/17 assertions)**
- **Delta: +40% absolute**
- Skill prevents three observed failure modes: inventing fake MCP parameter names (`workId`, `eventType`, `addressedTo`), reusing parent correlationIds as event correlationIds (chain corruption), and writing unstructured prose rollups instead of structured next-session briefs.

### Description optimization (iteration 1 → final)
Manual first-principles optimization (CLI loop blocked by sandbox auth). Changes:
- Leads with "Use this skill whenever" (pushy phrasing per skill-creator guidance — combats under-triggering)
- Drops generic over-triggers: `"remember"`, `"log"`, `"checkpoint"`, `"hand off"`, `"what's the state of X"`, `"agent memory"`, `"agent coordination"`, `"multi-agent fleets"`. These false-positive on near-miss queries (mem0, crewai, datadog correlationIds, generic remember requests).
- Adds named ACMI threads as triggers: `agent-coordination`, `newsroom`.
- Adds named ACMI agents as triggers: `claude-engineer`, `bentley`, `claude-web`, `gemini-cli`.
- Adds ACMI-specific protocol vocabulary: `parentCorrelationId`, `spawn`, `bootstrap` (as ACMI concepts, not generic).
- Removes Redis/Upstash mention (not load-bearing for triggering; lives in `install.md`).
- Final length: 929 / 1024 chars.

### Syndication targets
Copy + metadata for four registries documented in `SYNDICATION.md`:
1. **Smithery** — skill listing slug `madezmediapartners/acmi`, long description, 14 tags, quality-score checklist
2. **Cowork plugin marketplace** — `plugin.json` manifest with recommended_mcps and commands
3. **GitHub** — recommended repo layout (`madezmedia/acmi-skill`), README opening, 4 badges
4. **Anthropic skills index / general MCP registries** — directory entry copy

### Known gaps
- Description optimization didn't run the automated trigger-accuracy loop (CLI auth blocked in sandbox). Recommend running `python -m scripts.run_loop --eval-set trigger-evals.json --skill-path acmi/ --model claude-opus-4-7 --max-iterations 5` on host machine when convenient — the trigger-evals.json is already shipped.
- Companion `@madezmedia/acmi-mcp` v1.3.0 doesn't expose `parentCorrelationId`, `payload`, or `tags` as named MCP parameters. Workaround documented in `sdk-mcp-drift.md`; future MCP release should add these.
- The `acmi_delete` tool's confirm-flag semantics aren't fully specified in v1.3.0; documented as "dry-run by default, requires explicit confirmation".

### Companion work item
Related to the deferred `smithery-specialist-agent` work item (acmi://work/smithery-specialist-agent). This skill is a smaller, broader-scope sibling — covers all of ACMI, not just Smithery integration.
