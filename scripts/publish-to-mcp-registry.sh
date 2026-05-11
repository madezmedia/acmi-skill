#!/usr/bin/env bash
# Publishes @madezmedia/acmi-mcp to the official MCP Registry.
# Run this in your own Terminal — the GitHub device-code flow needs an
# interactive browser tab you can authorize.

set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

PUBLISHER="$HOME/code/registry/bin/mcp-publisher"
SERVER_JSON="$(dirname "$0")/../server.json"

if [ ! -x "$PUBLISHER" ]; then
  echo "ERROR: $PUBLISHER not found. Build with: cd ~/code/registry && make publisher"
  exit 1
fi

if [ ! -f "$SERVER_JSON" ]; then
  echo "ERROR: $SERVER_JSON not found."
  exit 1
fi

echo "→ Validating server.json …"
"$PUBLISHER" validate "$SERVER_JSON"
echo ""

echo "→ GitHub login (opens a device-code flow in your browser) …"
"$PUBLISHER" login github
echo ""

echo "→ Publishing io.github.madezmedia/acmi-mcp@1.3.0 …"
"$PUBLISHER" publish "$SERVER_JSON"
echo ""

echo "✅ DONE."
echo "   Verify at: https://registry.modelcontextprotocol.io/v0/servers/io.github.madezmedia/acmi-mcp"
echo "   Glama auto-indexes within hours."
