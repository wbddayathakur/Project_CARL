#!/usr/bin/env bash
# Launches the workbench dev server. Node was installed to ~/.local/node,
# which is not on the default PATH, so it is added here.
set -e
export PATH="$HOME/.local/node/bin:$PATH"
cd "$(dirname "$0")"
[ -d node_modules ] || npm install
exec npm run dev -- --host "$@"
