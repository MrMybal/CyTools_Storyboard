#!/usr/bin/env sh
# Linux launcher: opens the ImGui window (add --cli for the command line). Not executed on Linux yet.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$ROOT/runtime/python/bin/python" "$ROOT/runtime/bootstrap.py" "$@"
