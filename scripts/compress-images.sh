#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! python3 -c "import PIL" 2>/dev/null; then
  echo "❌ ต้องติดตั้ง Pillow ก่อน — รัน: pnpm run setup"
  exit 1
fi

exec python3 "$ROOT/scripts/compress-images.py" "$@"
