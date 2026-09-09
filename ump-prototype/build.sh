#!/usr/bin/env bash
# Build the standalone prototype.
#   - transpiles JSX with the vendored Babel, run under macOS' built-in JavaScriptCore shell
#   - inlines React, ReactDOM and every source file into one HTML file
# No node, no npm, no build pipeline, nothing that needs someone else's environment.
set -euo pipefail
cd "$(dirname "$0")"

JSC="/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc"
OUT="UMP-Prototype.html"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SRC=(src/1*.js src/2*.js src/3*.js src/4*.js src/5*.js src/6*.js src/7*.js src/8*.js)

echo "transpiling…"
for f in "${SRC[@]}"; do
  "$JSC" tools/transpile.js -- "$f" "$TMP/$(basename "$f")" > /dev/null
done

echo "assembling…"
{
  cat src/00-head.html
  echo '<script>'; cat vendor/react.js;     echo '</script>'
  echo '<script>'; cat vendor/react-dom.js; echo '</script>'
  for f in "${SRC[@]}"; do
    b="$(basename "$f")"
    printf '\n<!-- ================= %s ================= -->\n<script>\n' "$b"
    cat "$TMP/$b"
    printf '\n</script>\n'
  done
  cat src/99-foot.html
} > "$OUT"

printf 'built %s  (%s lines, %s)\n' "$OUT" \
  "$(wc -l < "$OUT" | tr -d ' ')" \
  "$(du -h "$OUT" | cut -f1 | tr -d ' ')"
