#!/usr/bin/env bash
# Deploy ERP-Demo to Railway from this repo.
# Requires: RAILWAY_TOKEN = Project Token (Project → Settings → Tokens).
# Does not touch ATLAS. Do not use Account/Workspace tokens here.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TOKEN="$(printf '%s' "${RAILWAY_TOKEN:-}" | tr -d '\r\n[:space:]')"
if [[ -z "$TOKEN" ]]; then
  echo "RAILWAY_TOKEN is required (Project Token from Railway project Settings → Tokens)" >&2
  exit 1
fi
export RAILWAY_TOKEN="$TOKEN"

if ! command -v railway >/dev/null 2>&1; then
  npm install -g @railway/cli
fi

echo "Deploying ERP-Demo (synth sandbox) — not ATLAS"
# Project tokens cannot run whoami/link; only up/redeploy/logs.
railway up --ci ${RAILWAY_SERVICE:+--service "$RAILWAY_SERVICE"}
echo "Verify: curl -s https://erp-demo-production-9ab8.up.railway.app/health"
