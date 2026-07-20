#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SRC="$ROOT/scripts/hooks/pre-push"
HOOKS_DIR="$ROOT/.git/hooks"
HOOK_DST="$HOOKS_DIR/pre-push"

if [[ -n "${CI:-}" ]]; then
  echo "⚠️  โหมด CI — ข้ามการติด git hook"
  exit 0
fi

if [[ ! -d "$ROOT/.git" ]]; then
  echo "⚠️  ไม่พบ .git — ข้ามการติด git hook"
  exit 0
fi

if [[ ! -d "$HOOKS_DIR" ]]; then
  if ! mkdir -p "$HOOKS_DIR" 2>/dev/null; then
    echo "⚠️  สร้างโฟลเดอร์ hooks ไม่ได้ — ข้ามการติด git hook"
    exit 0
  fi
fi

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"
echo "✅ ติดตั้ง pre-push hook แล้ว (บีบอัดรูปอัตโนมัติก่อน push)"
