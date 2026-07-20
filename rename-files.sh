#!/bin/bash
# Deprecated: use pnpm run media:organize
exec python3 "$(dirname "$0")/scripts/organize-media-names.py" "$@"
