# ACMI — Multi-Registry Submission Playbook

This is the step-by-step playbook for publishing the ACMI ecosystem across every relevant registry as of May 2026. The ACMI work splits into two products that get submitted to overlapping-but-different places:

- **`@madezmedia/acmi-mcp`** — the MCP **server** (16 tools). Already on npm + Smithery, needs MCP-registry submission + Glama indexing + GitHub README presence.
- **`acmi-skill`** — the universal Claude **skill** we just built. New artifact; goes to Smithery Skills, Anthropic plugins directory, and your own marketplace if you host one.

Both share the GitHub repo `madezmedia/acmi`. Below are the seven destinations, what to submit at each, and the exact commands.

## Where to submit what

| Destination | What goes there | Difficulty | Time | Auto-discovery? |
|---|---|---|---|---|
| 1. Official MCP Registry (`registry.modelcontextprotocol.io`) | The MCP **server** | Medium | 30 min | No — explicit publish |
| 2. Smithery (`smithery.ai`) — server | The MCP **server** (already live) | — | done | n/a |
| 3. Smithery (`smithery.ai`) — skill | The **skill** | Easy | 15 min | Partial — needs CLI publish |
| 4. Anthropic plugins / skills marketplace | The **skill** (as a plugin bundle) | Easy | 10 min PR + review | No — PR-based |
| 5. Glama (`glama.ai`) | The MCP **server** | Easy | 0 min | YES — auto-indexed from registry/GitHub |
| 6. GitHub repo (`madezmedia/acmi-skill`) | The skill source + `.skill` artifact | Easy | 20 min | n/a — primary source |
| 7. npm (`@madezmedia/acmi-skill`, optional) | The skill as an npm package | Optional | 10 min | n/a |

Total realistic timeline if you do it in one focused session: ~2 hours.

---

## 1. Official MCP Registry — `registry.modelcontextprotocol.io`

The vendor-neutral, community-driven index maintained by the MCP steering group. Glama, Claude Desktop's connector picker, and most other clients pull from here. **Highest-leverage single submission** — once you're in, downstream registries discover you automatically.

### Prerequisites

- The server is on npm (it is — `@madezmedia/acmi-mcp@1.3.0`)
- The GitHub repo (`madezmedia/acmi`) is public (it is)
- You can prove namespace ownership via GitHub OAuth (you can — same account)

### Steps

1. **Build the publisher CLI:**
   ```bash
   git clone https://github.com/modelcontextprotocol/registry
   cd registry && make publisher
   # produces ./bin/publisher
   ```

2. **Create a `server.json` in `madezmedia/acmi` root.** Server name must be reverse-DNS form tied to your GitHub account:
   ```json
   {
     "$schema": "https://static.modelcontextprotocol.io/schemas/2025-09-29/server.schema.json",
     "name": "io.github.madezmedia/acmi-mcp",
     "description": "Persistent agent memory via the ACMI protocol — Profile, Signals, Timeline. 16 tools on Upstash Redis. Multi-agent fleet coordination.",
     "version": "1.3.0",
     "repository": {
       "url": "https://github.com/madezmedia/acmi",
       "source": "github"
     },
     "packages": [
       {
         "registryName": "npm",
         "name": "@madezmedia/acmi-mcp",
         "version": "1.3.0",
         "transport": { "type": "stdio" },
         "environmentVariables": [
           { "name": "UPSTASH_REDIS_REST_URL", "required": true, "secret": false },
           { "name": "UPSTASH_REDIS_REST_TOKEN", "required": true, "secret": true }
         ]
       }
     ],
     "remotes": [
       {
         "transport": { "type": "streamable-http" },
         "url": "https://server.smithery.ai/@madezmediapartners/acmi-mcp/mcp"
       }
     ],
     "_meta": {
       "io.modelcontextprotocol.registry/publisher-provided": {
         "homepage": "https://github.com/madezmedia/acmi",
         "tags": ["agent-memory", "multi-agent", "redis", "upstash", "protocol", "context-management"],
         "license": "MIT",
         "documentation": "https://github.com/madezmedia/acmi#readme"
       }
     }
   }
   ```

3. **Authenticate + publish:**
   ```bash
   ./bin/publisher auth login --provider github
   # opens browser, OAuths your madezmedia GitHub
   ./bin/publisher publish --file server.json
   ```

4. **Verify:**
   - Listing should appear at `https://registry.modelcontextprotocol.io/v0/servers/io.github.madezmedia/acmi-mcp` within ~60s
   - Glama auto-pulls within hours
   - Downstream clients (Claude Desktop's "Add MCP" picker, Cursor's MCP search) will index it on next scan

### Gotchas

- The `name` field **must** match `io.github.<your-gh-username>/*` for GitHub auth. `madezmedia` is your username/org — `io.github.madezmedia/acmi-mcp` is the right slug.
- The `_meta` block is your custom metadata zone — anything you'd want a fancy registry UI to show goes here under the `io.modelcontextprotocol.registry/publisher-provided` key.
- Updates: bump `version`, re-run `publisher publish --file server.json`. Old versions stay queryable.

---

## 2. Smithery — MCP server (already live)

Listing is already at `smithery.ai/server/madezmediapartners/acmi-mcp`. **Verification status: `verified: false`, `useCount: 0`** per the earlier audit. Two follow-ups:

1. **Apply for Smithery verification** — boosts the listing's quality score, gives the verified badge. Submit at the listing page → "Request Verification". Anthropic-style review.

2. **Add stdio variant as 2nd connection** — currently only HTTP-hosted. Stdio listing makes Claude Desktop and local installs work without going through Smithery's proxy. Needs:
   - `SMITHERY_API_KEY` in `.env` (currently missing)
   - `npm i -g @smithery/cli` (currently not installed)
   - Then: `smithery mcp publish https://server.smithery.ai/@madezmediapartners/acmi-mcp -n madezmediapartners/acmi-mcp` (the CLI updates the existing listing, doesn't create a duplicate)

Both are P2 — not urgent, but do them post-MCP-registry submission to compound the quality signal.

---

## 3. Smithery — skill listing

Smithery has a separate **Skills** registry alongside the server registry (`smithery.ai/skills/...`). The flow is:

1. **Push the skill to a public GitHub repo** — recommended: `madezmedia/acmi-skill` (see §6). The skill's `SKILL.md` lives at the repo root or in `skill/SKILL.md`.

2. **Submit via Smithery CLI:**
   ```bash
   npm i -g @smithery/cli
   smithery skill add madezmedia/acmi-skill --repo https://github.com/madezmedia/acmi-skill
   ```
   Or via the web UI: `smithery.ai/new?type=skill` → paste the GitHub URL → Smithery scans for `SKILL.md`.

3. **Verify the scan results** — Smithery extracts the `description` and references, runs basic validation. Check the listing renders correctly at `smithery.ai/skills/madezmediapartners/acmi`.

4. **Tags + categories.** From the `SYNDICATION.md` already in the workspace:
   - Categories: Memory & Context, Multi-Agent Coordination
   - Tags: `agent-memory`, `multi-agent`, `mcp`, `claude`, `cursor`, `cline`, `windsurf`, `perplexity`, `redis`, `upstash`, `protocol`, `context-management`, `fleet-coordination`, `correlation-id`

### Why this is a separate listing from the server

The skill teaches Claude **how to use** ACMI; the server **exposes** ACMI's tools. Smithery treats these as related-but-distinct artifacts: a user might install the skill standalone (for documentation/reference) without the server, or install the server without the skill (using their own ACMI knowledge). Cross-link them in both descriptions.

---

## 4. Anthropic plugins / skills marketplace

Anthropic maintains an official, Anthropic-managed directory: `github.com/anthropics/claude-plugins-official` (curated, "Anthropic Verified" badge) plus `github.com/anthropics/skills` (the public skills repo) and `github.com/anthropics/knowledge-work-plugins` (Cowork-targeted).

The marketplace is consumed by **both Claude Code and Claude Cowork** via `.claude-plugin/marketplace.json`. Two paths to get listed:

### Path A — submit to Anthropic's official directory (curated)

1. **Fork `anthropics/claude-plugins-official`** (or `knowledge-work-plugins` if the skill is more Cowork-focused — ACMI is cross-surface, so either works; `claude-plugins-official` is the broader catalog).

2. **Add an entry to `.claude-plugin/marketplace.json`:**
   ```json
   {
     "name": "acmi",
     "displayName": "ACMI — Agentic Context Memory Interface",
     "description": "Universal operator playbook for ACMI — persistent agent memory via Profile/Signals/Timeline.",
     "source": {
       "type": "github",
       "repository": "madezmedia/acmi-skill",
       "ref": "v1.0.0"
     },
     "category": "memory-and-context",
     "tags": ["agent-memory", "multi-agent", "mcp", "redis", "upstash"],
     "strict": false,
     "author": {
       "name": "Mad EZ Media Partners",
       "url": "https://github.com/madezmedia"
     },
     "homepage": "https://github.com/madezmedia/acmi-skill"
   }
   ```

3. **Open a PR.** Anthropic does an automated quality/security review. Curated plugins get the "Anthropic Verified" badge if they pass the deeper review. PRs typically merge in 1–2 weeks based on the merge history (e.g., [PR #148](https://github.com/anthropics/claude-plugins-official/pull/148) for the superpowers plugin).

4. **Once merged**, users find you via `/plugin marketplace` inside Claude Code or via the Cowork plugin picker UI.

### Path B — host your own marketplace (uncurated, no review needed)

If you'd rather not wait for Anthropic's review:

1. **Create `madezmedia/claude-marketplace`** (or reuse `madezmedia/acmi-skill`).

2. **Add `.claude-plugin/marketplace.json` at the repo root**, with your plugins listed (the structure above).

3. **Share the marketplace URL with users.** They run:
   ```
   /plugin marketplace add https://github.com/madezmedia/claude-marketplace
   ```
   inside Claude Code, and then `/plugin install acmi` to grab the skill.

Both paths can coexist. Recommendation: **do Path B first** (instant install for your audience), submit PR for Path A in parallel (broader distribution but slower).

---

## 5. Glama — `glama.ai`

Glama is a superset of the official MCP Registry — auto-indexes everything in `registry.modelcontextprotocol.io`, then adds quality scoring, tool schemas, security audits, and usage telemetry on top.

**You probably don't have to do anything.** Once step §1 lands, Glama picks up the server within hours and auto-builds the listing at `glama.ai/mcp/servers/madezmedia/acmi-mcp`.

If you want to **accelerate or enrich**:

1. **Submit directly via PR to** `meetmatt/glama-mcp-registry-mcp-server` (or the canonical Glama submissions repo if they've moved it — check their docs at `glama.ai/mcp/about`).

2. **Or, claim the auto-generated listing**: log in to Glama with your GitHub, claim the listing, and you can edit the rich metadata (icon, longer description, screenshots, maintainer notes).

Glama doesn't have a skills registry yet (as of May 2026) — they focus on servers. Skip for the skill.

---

## 6. GitHub — `madezmedia/acmi-skill` (new repo)

The skill needs its own home for the marketplace submissions above to point at. Don't co-mingle with `madezmedia/acmi` (that's the protocol/SDK repo) per the repo-architecture-decision work item ratification.

### Recommended layout

```
madezmedia/acmi-skill/
├── README.md                       (use the opening from SYNDICATION.md)
├── LICENSE                         (MIT — copy from madezmedia/acmi)
├── CHANGELOG.md                    (already drafted in /clawd/acmi-skill-review/)
├── .claude-plugin/
│   ├── marketplace.json            (if hosting your own marketplace)
│   └── plugin.json                 (the plugin manifest from SYNDICATION.md §2)
├── skill/                          (the unpacked skill — bit-perfect mirror of acmi.skill contents)
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
├── dist/
│   └── acmi-v1.0.0.skill           (the packaged bundle, regenerated per release)
├── evals/
│   ├── evals.json
│   ├── trigger-evals.json
│   └── iteration-1/                (the eval workspace — keep for reproducibility)
└── .github/
    └── workflows/
        ├── package.yml             (auto-builds acmi-v*.skill on release)
        └── eval.yml                (re-runs evals on PR via subagents)
```

### Steps

1. **Create the repo** (public, MIT):
   ```bash
   gh repo create madezmedia/acmi-skill --public --license MIT \
     --description "Universal Claude skill for the ACMI protocol — persistent agent memory"
   ```

2. **Initial commit:**
   ```bash
   git clone https://github.com/madezmedia/acmi-skill
   cd acmi-skill
   # Copy from /Users/michaelshaw/clawd/acmi-skill-review/:
   #   - acmi.skill            → dist/acmi-v1.0.0.skill
   #   - SYNDICATION.md, CHANGELOG.md → repo root
   # Unzip the .skill into skill/:
   unzip dist/acmi-v1.0.0.skill -d skill/
   mv skill/acmi/* skill/ && rmdir skill/acmi
   git add . && git commit -m "v1.0.0 — initial skill release"
   git tag v1.0.0 && git push --tags
   ```

3. **Tag the release on GitHub:**
   ```bash
   gh release create v1.0.0 dist/acmi-v1.0.0.skill \
     --title "v1.0.0 — Universal ACMI Skill" \
     --notes-file CHANGELOG.md
   ```

4. **Add badges to README.md** (from `SYNDICATION.md` §3):
   - Smithery skill badge
   - MIT license
   - Eval pass rate 100%
   - Companion `@madezmedia/acmi-mcp`

---

## 7. npm — `@madezmedia/acmi-skill` (optional)

Some skill-marketplace tooling lets users `npm install` a skill bundle. Optional, but cheap to do:

1. Create `package.json` in the repo root:
   ```json
   {
     "name": "@madezmedia/acmi-skill",
     "version": "1.0.0",
     "description": "Universal Claude skill for the ACMI protocol",
     "files": ["skill/", "dist/", "README.md", "LICENSE", "CHANGELOG.md"],
     "homepage": "https://github.com/madezmedia/acmi-skill",
     "repository": "github:madezmedia/acmi-skill",
     "license": "MIT",
     "keywords": ["claude", "skill", "acmi", "agent-memory", "mcp"]
   }
   ```

2. `npm publish --access public`. Done.

---

## Recommended submission order

If you have ~2 hours in one block, do them in this order — each step compounds discovery for the later steps:

1. **GitHub repo `madezmedia/acmi-skill`** (§6) — 20 min. Everything else points here.
2. **Official MCP Registry** (§1) — 30 min. Single highest-leverage submission for the server; downstream registries auto-pick-up.
3. **Anthropic plugins (Path B — your own marketplace.json)** (§4) — 10 min. Users can install immediately, no Anthropic review wait.
4. **Smithery skill** (§3) — 15 min. Big surface for Claude Desktop / Cursor users.
5. **Anthropic plugins (Path A — official PR)** (§4) — 10 min PR open, then 1–2 weeks waiting. Submit and forget.
6. **Smithery server follow-ups** (§2) — 15 min. Verification request + stdio variant.
7. **Glama** (§5) — 0 min (auto-indexes from step 2). Check it landed.
8. **npm** (§7) — 10 min, optional.

---

## Cross-link audit checklist

Once everything's submitted, make sure each surface points at every other surface so a user landing on any one of them can find the rest:

- [ ] `madezmedia/acmi` README → links to acmi-skill repo + Smithery skill listing
- [ ] `madezmedia/acmi-skill` README → links to acmi protocol repo + npm acmi-mcp + Smithery server listing + Glama + MCP registry entry
- [ ] Smithery server listing → mentions companion skill in description, links to GitHub
- [ ] Smithery skill listing → mentions companion `@madezmedia/acmi-mcp` server, links to GitHub
- [ ] MCP registry server.json `_meta.documentation` → links to acmi repo README
- [ ] Anthropic marketplace.json entry → `homepage` field set to acmi-skill repo
- [ ] All npm package.json files have matching `repository`, `homepage`, `bugs` fields
- [ ] CHANGELOG.md exists on every release surface (GitHub + npm)

---

## Sources

The exact submission flows referenced above:

- [Official MCP Registry](https://registry.modelcontextprotocol.io/) ([docs](https://registry.modelcontextprotocol.io/docs)) ([repo](https://github.com/modelcontextprotocol/registry))
- [Publish Your MCP Server](https://modelcontextprotocol.info/tools/registry/publishing/)
- [server.json Format Specification](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/generic-server-json.md)
- [Glama MCP Registry](https://glama.ai/) ([servers](https://glama.ai/mcp/servers))
- [Smithery CLI](https://github.com/smithery-ai/cli)
- [Smithery Skills](https://smithery.ai/skills) ([CLI docs](https://smithery.ai/docs/concepts/cli))
- [Anthropic Marketplace](https://claude.com/platform/marketplace) ([plugin docs](https://claude.com/plugins))
- [anthropics/claude-plugins-official (curated directory)](https://github.com/anthropics/claude-plugins-official)
- [anthropics/skills (public skills repo)](https://github.com/anthropics/skills/) ([marketplace.json](https://github.com/anthropics/skills/blob/main/.claude-plugin/marketplace.json))
- [anthropics/knowledge-work-plugins (Cowork-targeted)](https://github.com/anthropics/knowledge-work-plugins)
- [Discover and install prebuilt plugins (Claude Code docs)](https://code.claude.com/docs/en/discover-plugins)
- [Create and distribute a plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
