#!/bin/bash
# push แบบครบ: จัดรูป → commit (ถ้ามี) → ส่งขึ้น GitHub (ไม่ต้อง push สองรอบ)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo ""
echo "🔍 ตรวจและบีบอัดรูปก่อน push..."
echo ""

if bash "$ROOT/scripts/media-push-prepare.sh"; then
  echo "✅ บันทึกไฟล์ที่เลือกแล้ว"
else
  echo "ℹ️  ไม่มีไฟล์รูป/เว็บใหม่ที่ต้องบันทึกเพิ่ม"
fi

pnpm run media:check -- --quiet 2>/dev/null || pnpm run media:check

echo ""
echo "↗️  กำลังส่งขึ้น GitHub..."
git push --no-verify "$@"

echo ""
echo "✅ เสร็จแล้ว"
echo ""
