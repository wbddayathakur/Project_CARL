#!/usr/bin/env bash
#
# The weekly run. Schedule this, not the Python module directly — it handles
# the parts a bare `python -m` call gets wrong under cron: no PATH, no shell
# profile, no working directory, and no record of what happened.
#
#   crontab -e
#   0 7 * * 1  /Users/dthakur/Documents/LocalRepo/iceberg-catalog-agent/run-weekly.sh
#
# Monday 07:00 is deliberate. The page has to be current before the week's
# intake requests start arriving, not after.
#
# Credentials are read from the environment. Under cron there is no shell
# profile, so put them in an .env file next to this script:
#
#   CONFLUENCE_USER=you@wbd.com
#   CONFLUENCE_TOKEN=...
#
# .env is gitignored. Do not put credentials in config.yaml.

set -euo pipefail

cd "$(dirname "$0")"

PYTHON=".venv/bin/python"
LOG_DIR="out/logs"
LOG="${LOG_DIR}/run-$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ ! -x "$PYTHON" ]]; then
  echo "No virtualenv at $PYTHON. Create one first:" >&2
  echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') ==="

  # --source auto: try live Glue, fall back to the last successful run's JSON
  # if no account can be reached. A stale page that says so is better than a
  # missing one, because the link to it is embedded in the intake form.
  "$PYTHON" -m iceberg_catalog \
    --source auto \
    --publish \
    "$@"

  echo "=== done ==="
} 2>&1 | tee -a "$LOG"

# Keep a quarter of history, drop the rest.
find "$LOG_DIR" -name 'run-*.log' -mtime +90 -delete 2>/dev/null || true
