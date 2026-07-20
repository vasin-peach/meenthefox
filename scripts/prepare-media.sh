#!/bin/bash
# จัดชื่อไฟล์ → บีบอัดรูป → ตรวจสอบขนาด (ใช้ก่อน push อัตโนมัติ)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SILENT=0
for arg in "$@"; do
  if [[ "$arg" == "--silent" ]]; then
    SILENT=1
  fi
done

if [[ "$SILENT" -eq 0 ]]; then
  echo "════════════════════════════════════════"
  echo "  ระบบจัดการรูปอัตโนมัติ (ไม่ต้องทำเอง)"
  echo "════════════════════════════════════════"
  echo ""
fi

python3 "$ROOT/scripts/organize-media-names.py"
if [[ "$SILENT" -eq 0 ]]; then
  echo ""
fi
python3 "$ROOT/scripts/compress-images.py" --replace media
if [[ "$SILENT" -eq 0 ]]; then
  echo ""
fi
python3 "$ROOT/scripts/verify-media.py"
if [[ "$SILENT" -eq 0 ]]; then
  echo ""
fi
bash "$ROOT/scripts/sync-public-media.sh"

if [[ "$SILENT" -eq 0 ]]; then
  echo ""
  echo "✨ เสร็จแล้ว — ใช้ git push ได้เลย"
fi
