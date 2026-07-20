#!/bin/bash
# คัดลอก media/ → public/media/ ให้เว็บโฮสต์แบบ static (Netlify ฯลฯ) เปิดรูปได้
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

rm -rf "$ROOT/public/media"
cp -R "$ROOT/media" "$ROOT/public/media"
find "$ROOT/public/media" -name '.DS_Store' -delete 2>/dev/null || true
