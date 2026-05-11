# ACMI Install & Auth Guide

ACMI runs as an MCP server (`@madezmedia/acmi-mcp`) backed by Upstash Redis. There are two transports — local stdio (one process per host) and Smithery-hosted HTTP (one shared URL for any host) — and the right choice depends on the surface.

## TL;DR by surface

| Surface | Transport | Get-started |
|---|---|---|
| Claude Desktop, Cursor, Cline, Windsurf | stdio (local npm) | `npm install -g @madezmedia/acmi-mcp` + add to `mcpServers` config |
| Claude Code, Cowork | stdio (local npm) | Same as above; add via `claude mcp add` or Cowork's connector UI |
| Claude.ai (web), Perplexity | Smithery HTTP | Connect URL: `https://server.smithery.ai/@madezmediapartners/acmi-mcp` |
| Headless API / your own bot | SDK direct | `npm i @madezmedia/acmi @upstash/redis` and use `UpstashAdapter` |

## Prerequisites

You need an Upstash Redis instance — they have a generous free tier suitable for individual fleets. From [console.upstash.com](https://console.upstash.com), create a Redis database and grab two values from the REST API tab:

- `UPSTASH_REDIS_REST_URL` — looks like `https://<id>.upstash.io`
- `UPSTASH_REDIS_REST_TOKEN` — the read-write token

For multi-agent fleets, every agent uses the same two creds. For per-tenant isolation (SPEC §12), provision one Upstash DB per tenant.

## Path A: Local stdio (Claude Desktop, Cursor, Cline, Windsurf, Claude Code, Cowork)

### 1. Install the MCP server

```bash
npm install -g @madezmedia/acmi-mcp
```

Verify: `which acmi-mcp` should print a path. If you get "command not found", check your npm global bin is on PATH (`npm config get prefix` + `/bin`).

### 2. Add to your MCP host config

**Claude Desktop** — edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows). Add to `mcpServers`:
```json
{
  "mcpServers": {
    "acmi": {
      "command": "acmi-mcp",
      "env": {
        "UPSTASH_REDIS_REST_URL": "https://<your-id>.upstash.io",
        "UPSTASH_REDIS_REST_TOKEN": "<your-token>"
      }
    }
  }
}
```
Restart Claude Desktop.

**Cursor** — Settings → Cursor Settings → MCP → Add new global MCP server. Same JSON shape.

**Cline / Windsurf** — Settings → MCP servers → Add. Same JSON shape.

**Claude Code** — `claude mcp add acmi acmi-mcp -e UPSTASH_REDIS_REST_URL=... -e UPSTASH_REDIS_REST_TOKEN=...`

**Cowork** — Open the connectors panel and add a custom MCP with command `acmi-mcp` and the two env vars.

### 3. Verify

In any host with the server connected, ask Claude to call `acmi_list(namespace="agent")`. If you get an array (possibly empty), you're live.

## Path B: Smithery HTTP (Claude.ai web, Perplexity, anywhere else)

Smithery hosts the MCP server for you. No install, no local Node, no global package — just paste a URL into the host's MCP settings.

### 1. Visit the Smithery listing

[smithery.ai/server/madezmediapartners/acmi-mcp](https://smithery.ai/server/madezmediapartners/acmi-mcp)

### 2. Provide your Upstash credentials

Smithery's per-user config UI will ask for `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`. These are stored encrypted per-user in your Smithery account; the hosted server proxies your requests with your credentials.

### 3. Connect from your host

Smithery generates a per-user URL like:
```
https://server.smithery.ai/@madezmediapartners/acmi-mcp/mcp?config=<base64>
```
Paste this into Claude.ai's "Connect MCP server" UI, Perplexity's MCP settings, or any other HTTP-MCP-capable host.

### 4. Verify

Same as Path A: ask the host to call `acmi_list(namespace="agent")`.

## Path C: SDK direct (headless / non-MCP usage)

For your own scripts, bots, or backend services, skip MCP and use the SDK:

```bash
npm install @madezmedia/acmi
```

```ts
import { createAcmi } from "@madezmedia/acmi";
import { UpstashAdapter } from "@madezmedia/acmi/adapters/upstash";

const acmi = createAcmi(
  new UpstashAdapter({
    url: process.env.UPSTASH_REDIS_REST_URL!,
    token: process.env.UPSTASH_REDIS_REST_TOKEN!,
  })
);

await acmi.profile.set("agent:my-bot", { actor_type: "agent", name: "my-bot" });
await acmi.timeline.append("agent:my-bot", {
  source: "agent:my-bot",
  kind: "spawn",
  correlationId: `myBotSpawn-${Date.now()}`,
  summary: "[spawn] hello",
});
```

Other adapters: `InMemoryAdapter` (tests, examples), `RedisAdapter` (self-hosted Redis via ioredis).

## Troubleshooting

**`-32601 Method not found`** — The MCP host is calling a tool name that the server doesn't expose. Check you're on `@madezmedia/acmi-mcp` v1.3.0+; older versions had different tool names.

**`-32001 Authorization required`** — The Upstash token is missing or wrong. Re-check the env vars in your host config.

**`serverInfo null` (Smithery)** — Smithery's scan probe isn't getting a clean handshake. Usually fixed by re-running scan after a config update; if persistent, file an issue at [github.com/madezmedia/acmi/issues](https://github.com/madezmedia/acmi/issues).

**Tool calls return empty arrays / null profiles** — You're connected but the namespace is empty. Either you have a fresh DB (expected) or you're connected to the wrong tenant.

**Events appear out of order** — `ts` is wall-clock at the writer's machine. If multiple writers' clocks drift, ordering can wobble. Use `correlationId` chains, not timestamp ordering, for causality.

## Per-tenant / per-client setups

For deployments serving multiple clients, the recommended pattern is one Upstash DB per tenant (matching SPEC §12.4 isolation). Pass a different `UPSTASH_REDIS_REST_URL` / `_TOKEN` pair per tenant in the host config, or use Smithery's per-user config with each client logged into Smithery separately.

For single-DB multi-tenant (cheaper, less isolated), use the `tenant:` key prefix from SPEC §12.2 and discipline yourself to never SCAN across tenants.

## Going further

- Full SDK docs: [github.com/madezmedia/acmi#readme](https://github.com/madezmedia/acmi)
- Live demo (timeline browser): [huggingface.co/spaces/madezmedia/acmi-timeline-browser](https://huggingface.co/spaces/madezmedia/acmi-timeline-browser)
- npm: [@madezmedia/acmi](https://www.npmjs.com/package/@madezmedia/acmi), [@madezmedia/acmi-mcp](https://www.npmjs.com/package/@madezmedia/acmi-mcp)
- Smithery: [smithery.ai/server/madezmediapartners/acmi-mcp](https://smithery.ai/server/madezmediapartners/acmi-mcp)
