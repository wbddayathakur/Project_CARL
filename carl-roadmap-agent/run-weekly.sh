#!/usr/bin/env bash
#
# The weekly refresh. Schedule this, not `python -m` directly — it handles the
# parts a bare module call gets wrong under cron: no PATH, no shell profile, no
# working directory, and no record of what happened.
#
#   crontab -e
#   0 7 * * 1  /Users/dthakur/Documents/LocalRepo/carl-roadmap-agent/run-weekly.sh
#
# Monday 07:00 is deliberate: the page has to be right before the week's
# reviews, not after them.
#
# Credentials come from the environment. Under cron there is no shell profile,
# so put them in a .env file next to this script:
#
#   JIRA_USER=you@wbd.com
#   JIRA_TOKEN=...            # id.atlassian.com -> Security -> API tokens
#
# .env is gitignored. Do not put credentials in config.yaml.
#
# A laptop that is shut on Monday morning silently stops publishing and nobody
# notices for a month. If that is a risk, run the GitHub workflow instead —
# .github/workflows/weekly-roadmap.yml does the same thing on a runner.

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

status=0
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
  "$PYTHON" -m carl_roadmap run "$@" || status=$?
  echo "=== exit ${status} ==="
} 2>&1 | tee -a "$LOG"

# Exit 1 means the run succeeded but found something that needs a person —
# normally a new epic with no programme assigned. Worth a notification, not an
# alarm. Exit 2 means Jira could not be reached and the page was not touched.
if [[ $status -eq 1 ]]; then
  echo "Refresh completed with findings that need attention — see $LOG" >&2
elif [[ $status -ne 0 ]]; then
  echo "Refresh FAILED — the page was left at last week's numbers. See $LOG" >&2
fi

find "$LOG_DIR" -name 'run-*.log' -mtime +90 -delete 2>/dev/null || true

exit $status
