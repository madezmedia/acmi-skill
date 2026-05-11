#!/usr/bin/env bash
# bootstrap-then-rollup.sh — Run at agent session start. Spawns + bootstraps via
# the @madezmedia/acmi-mcp server and prints a human-readable session-start
# brief.
#
# Requirements:
#   - `acmi-mcp` on PATH (npm install -g @madezmedia/acmi-mcp)
#   - UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN in env
#   - jq for pretty-printing
#
# Usage:
#   bootstrap-then-rollup.sh <agentId> [<modelId>]
#
# This script does NOT call the MCP server over stdio (that requires a host).
# Instead it uses the SDK's bootstrap helper via a one-off Node invocation. If
# you'd rather call MCP directly, route through your host (Claude Desktop,
# Cowork, Claude Code) which gives you the equivalent acmi_bootstrap tool.

set -euo pipefail

AGENT_ID="${1:-}"
MODEL_ID="${2:-claude-opus-4-7}"

if [[ -z "$AGENT_ID" ]]; then
  echo "usage: bootstrap-then-rollup.sh <agentId> [<modelId>]" >&2
  exit 2
fi

if [[ -z "${UPSTASH_REDIS_REST_URL:-}" || -z "${UPSTASH_REDIS_REST_TOKEN:-}" ]]; then
  echo "ERROR: UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be set." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node not found on PATH." >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "WARNING: jq not on PATH; output will be raw JSON." >&2
fi

# Inline ESM script. Uses @madezmedia/acmi if present locally; otherwise falls
# back to a temp install. Reads bootstrap context, prints a digest.
SCRIPT="$(cat <<'EOF'
import { createAcmi } from "@madezmedia/acmi";
import { UpstashAdapter } from "@madezmedia/acmi/adapters/upstash";

const agentId = process.env.ACMI_AGENT_ID;
const modelId = process.env.ACMI_MODEL_ID;
const acmi = createAcmi(
  new UpstashAdapter({
    url: process.env.UPSTASH_REDIS_REST_URL,
    token: process.env.UPSTASH_REDIS_REST_TOKEN,
  })
);

const sessionId = `${agentId}-${Date.now()}`;
await acmi.timeline.append(`agent:${agentId}`, {
  source: `agent:${agentId}`,
  kind: "spawn",
  correlationId: `spawn-${sessionId}`,
  summary: `[spawn] session=${sessionId} model=${modelId}`,
  payload: { sessionId, modelId },
});

const profile = await acmi.profile.get(`agent:${agentId}`);
const signals = await acmi.signals.all(`agent:${agentId}`);
const recent = await acmi.timeline.read(`agent:${agentId}`, { limit: 10, reverse: true });
let rollup = null;
try { rollup = await acmi.rollup?.get?.(agentId); } catch { /* SDK may not expose */ }

const digest = { sessionId, agentId, profile, signals, recent_timeline: recent, rollup };
console.log(JSON.stringify(digest, null, 2));
await acmi.close?.();
EOF
)"

ACMI_AGENT_ID="$AGENT_ID" ACMI_MODEL_ID="$MODEL_ID" \
  node --input-type=module -e "$SCRIPT" \
  | { command -v jq >/dev/null && jq . || cat; }
