#!/usr/bin/env bash
# Deploy ERP-Demo to Railway from this repo.
# Requires: RAILWAY_TOKEN in env. Does not touch ATLAS.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${RAILWAY_TOKEN:-}" ]]; then
  echo "RAILWAY_TOKEN is required" >&2
  exit 1
fi

if ! command -v railway >/dev/null 2>&1; then
  npm install -g @railway/cli
fi

echo "Deploying ERP-Demo (synth sandbox) — not ATLAS"
railway up --ci ${RAILWAY_SERVICE:+--service "$RAILWAY_SERVICE"}
echo "Verify: curl -s https://erp-demo-production-9ab8.up.railway.app/health"
