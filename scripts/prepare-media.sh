#!/bin/bash
# จัดชื่อไฟล์ → บีบอัดรูป → ตรวจสอบขนาด (ใช้ก่อน push อัตโนมัติ)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "════════════════════════════════════════"
echo "  ระบบจัดการรูปอัตโนมัติ (ไม่ต้องทำเอง)"
echo "════════════════════════════════════════"
echo ""

python3 "$ROOT/scripts/organize-media-names.py"
echo ""
python3 "$ROOT/scripts/compress-images.py" --replace media
echo ""
python3 "$ROOT/scripts/verify-media.py"

echo ""
echo "✨ เสร็จแล้ว — ใช้ git push ได้เลย"
