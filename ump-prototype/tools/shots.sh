#!/bin/bash
# Screenshots every screen of the built prototype through headless Chrome, and
# fails loudly if any of them threw a console error. Used to check a change did
# not break a screen that is not the one being worked on.
set -u

# Any Chromium will do — whichever this machine happens to have.
CHROME="${CHROME:-}"
if [ -z "$CHROME" ]; then
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
  do
    [ -x "$c" ] && CHROME="$c" && break
  done
fi
if [ -z "$CHROME" ] || [ ! -x "$CHROME" ]; then
  echo "no Chromium found — install Chrome, Chromium, Brave or Edge, or set CHROME=/path/to/binary" >&2
  exit 2
fi
echo "using $(basename "$CHROME")"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-/tmp/ump-shots}"
W="${W:-1600}"; H="${H:-2400}"
mkdir -p "$OUT"; rm -f "$OUT"/*.png "$OUT"/*.log

ROUTES=(
  "desk::desk"
  "market::market"
  "blueprint/phases::bp-phases"
  "blueprint/personas::bp-personas"
  "blueprint/agents::bp-agents"
  "blueprint/lineage::bp-lineage"
  "blueprint/learn::bp-learn"
  "blueprint/flow::bp-flow"
  "plan/intake/worked::intake"
  "plan/discovery/worked::discovery"
  "plan/strategize/worked::strategize"
  "plan/analyze/worked::analyze"
  "plan/approval/worked::approval"
  "plan/approval/worked/inventory::approval-inventory"
)

fail=0
for r in "${ROUTES[@]}"; do
  hash="${r%%::*}"; name="${r##*::}"
  log="$OUT/$name.log"
  "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --window-size="$W,$H" --virtual-time-budget=4000 \
    --screenshot="$OUT/$name.png" --enable-logging=stderr --v=0 \
    "file://$HERE/UMP-Prototype.html#$hash" >"$log" 2>&1
  errs=$(grep -Ei 'SEVERE|Uncaught|ERROR:CONSOLE' "$log" | grep -v 'GPU\|gpu\|Fontconfig\|dbus\|Voice' || true)
  sz=$(stat -f%z "$OUT/$name.png" 2>/dev/null || echo 0)
  if [ -n "$errs" ]; then
    echo "FAIL  $name"; echo "$errs" | sed 's/^/        /'; fail=1
  elif [ "$sz" -lt 12000 ]; then
    echo "THIN  $name  (${sz}b — screen probably rendered empty)"; fail=1
  else
    echo "ok    $name  (${sz}b)"
  fi
done
echo
[ "$fail" -eq 0 ] && echo "all screens clean" || echo "some screens need attention"
exit $fail
