# Artifact Inventory — universal-acmi-skill v1.0.0

Manifest of every file produced during the build. Use this for diff'ing future iterations, attaching to release notes, and reproducing the eval signal.

Captured: 2026-05-11 16:09 UTC
Tenant: madez
Owner: agent:claude-cowork (driver) + mikey (decision)

## /Users/michaelshaw/clawd/acmi-skill-review/ — deliverables to ship

| File | Size | SHA-256 (prefix) | Purpose |
|---|---:|---|---|
| `acmi.skill` | 32,453 | `0c9a1551f4f6` | Packaged skill bundle (zip). Drop-in installable. |
| `SKILL.md` (in bundle) | 13,594 | `791a1614baff` | Operator playbook frontmatter + body |
| `SYNDICATION.md` | 10,465 | `b7155bd9d909` | Paste-ready listing copy for 4 registries |
| `SUBMISSION-PLAYBOOK.md` | 17,498 | `186b86b9116b` | Step-by-step submission guide for 7 destinations |
| `CHANGELOG.md` | 4,583 | `8075fee0f8b9` | v1.0.0 release notes |
| `iteration-1-review.html` | 79,673 | `e4252f71838c` | Static eval viewer (Mikey reviewed, returned feedback.json) |
| `trigger-eval-review.html` | 12,471 | `0eac1ab4f435` | Trigger eval set viewer (20 queries) |
| `description-optimization-report.html` | 15,438 | `c8948821d3f1` | Optimization loop report (incomplete — CLI auth blocked) |
| `ARTIFACT-INVENTORY.md` | — | — | This file |

Total deliverable footprint: ~190 KB.

## Skill bundle contents (unpacked from `acmi.skill`)

| Path in bundle | Size | SHA-256 (prefix) | Purpose |
|---|---:|---|---|
| `acmi/SKILL.md` | 13,594 | `791a1614baff` | Operator playbook (the skill body) |
| `acmi/references/protocol-spec.md` | 4,850 | `f4a79682979b` | Condensed ACMI SPEC v1.3 |
| `acmi/references/tool-reference.md` | 10,901 | `e2f91c1fc713` | 16 MCP tools with params, gotchas, examples |
| `acmi/references/patterns.md` | 11,313 | `8b616739397c` | 12 worked recipes for canonical workflows |
| `acmi/references/namespace-guide.md` | 5,686 | `150d66e8ae43` | Namespaces, kind taxonomy, summary line conventions |
| `acmi/references/install.md` | 6,443 | `9c8570f5734c` | Cross-surface install + auth |
| `acmi/references/sdk-mcp-drift.md` | 4,921 | `1d79052b15db` | SDK vs MCP v1.3.0 differences |
| `acmi/scripts/event-template.py` | 3,756 | `7f6e8a9b1146` | Generate well-formed Comms v1.1 event JSON |
| `acmi/scripts/dry-run-validator.py` | 3,989 | `c3e91cc0b195` | Validate event payload before `acmi_event` |
| `acmi/scripts/chain-walker.py` | 5,367 | `2fad5df7ea26` | Walk correlationId chains forward + backward |
| `acmi/scripts/bootstrap-then-rollup.sh` | 2,738 | `141d163783ce` | Session-start helper |

11 files, 73,558 bytes unpacked.

## Eval workspace (kept out of bundle, included in repo for reproducibility)

| Path | Size | SHA-256 (prefix) | Purpose |
|---|---:|---|---|
| `evals/evals.json` (in source) | 2,372 | `416bc16d346c` | 3 canonical workflow eval prompts |
| `acmi-workspace/trigger-evals.json` | 4,540 | `76bd702b77c5` | 20 trigger-eval queries (10 positive + 10 near-miss) |
| `acmi-workspace/grader.py` | 12,238 | `dfdb0b0ecd51` | Custom programmatic grader (3 graders, one per eval) |
| `acmi-workspace/iteration-1/benchmark.json` | 1,790 | `7869926dd7a6` | Aggregate stats (pass rates, tokens, durations) |
| `acmi-workspace/iteration-1/benchmark.md` | 922 | `670b0e189fcc` | Human-readable benchmark report |
| `iteration-1/eval-1-fresh-session-bootstrap/with_skill/outputs/result.json` | 6,323 | `53681f7c4c7f` | Subagent dry-run output (with skill) |
| `iteration-1/eval-1-fresh-session-bootstrap/without_skill/outputs/result.json` | 4,924 | `06e11132f929` | Subagent dry-run output (baseline) |
| `iteration-1/eval-2-log-milestone-with-chain/with_skill/outputs/result.json` | 1,766 | `d0d654b68dac` | Subagent dry-run output (with skill) |
| `iteration-1/eval-2-log-milestone-with-chain/without_skill/outputs/result.json` | 1,753 | `f9b8c16f1dd7` | Subagent dry-run output (baseline) |
| `iteration-1/eval-3-session-end-rollup/with_skill/outputs/result.json` | 5,365 | `4a0e9e083277` | Subagent dry-run output (with skill) |
| `iteration-1/eval-3-session-end-rollup/without_skill/outputs/result.json` | 4,272 | `231e088fdf69` | Subagent dry-run output (baseline) |
| All `timing.json` + `grading.json` files | varies | varies | Per-run telemetry + assertion results |
| `desc-opt/live.log` | 10,813 | `338827b4aa83` | Description-optimization loop log (incomplete) |

Eval workspace total: 24 files.

## Cross-references

| Anchor file | Points at |
|---|---|
| `CHANGELOG.md` → SUBMISSION-PLAYBOOK.md, SYNDICATION.md, evals workspace |
| `SUBMISSION-PLAYBOOK.md` → ARTIFACT-INVENTORY.md (this file), SYNDICATION.md, the `acmi.skill` artifact, the eval workspace |
| `SYNDICATION.md` → `acmi.skill` artifact + GitHub repo layout (recommends `madezmedia/acmi-skill`) |
| `iteration-1-review.html` → eval workspace JSON files (embedded in HTML) |

## Git/release readiness

Once `madezmedia/acmi-skill` repo exists, the recommended initial commit lays out:

```
acmi-skill/
├── README.md                ← derived from SYNDICATION.md §3 opening
├── LICENSE                  ← MIT, copy from madezmedia/acmi
├── CHANGELOG.md             ← copy this file's source
├── SUBMISSION-PLAYBOOK.md   ← copy this file's source
├── SYNDICATION.md           ← copy this file's source
├── ARTIFACT-INVENTORY.md    ← copy this file
├── skill/                   ← unpack acmi.skill contents here (11 files)
├── dist/
│   └── acmi-v1.0.0.skill    ← copy /clawd/acmi-skill-review/acmi.skill
├── evals/
│   ├── evals.json
│   ├── trigger-evals.json
│   └── iteration-1/         ← copy whole subtree
└── .claude-plugin/
    ├── marketplace.json     ← see SYNDICATION.md §2 + SUBMISSION-PLAYBOOK §4 Path B
    └── plugin.json          ← see SYNDICATION.md §2
```

Total source tree: ~46 files.

## Logged into ACMI

Every artifact above is referenced by entity in the ACMI bus. Pull via:

```
acmi_get(namespace="work", id="universal-acmi-skill-v1-shipped")  → profile + signals + recent timeline
acmi_get(namespace="agent", id="claude-cowork")                     → profile + rollup pointer
acmi_cat(keys=["thread:agent-coordination"], since="6h")            → team-loop event with delegations
```

Rollup location: `acmi:agent:claude-cowork:rollup:latest`. Next session's `acmi_bootstrap(claude-cowork)` will load this verbatim.
