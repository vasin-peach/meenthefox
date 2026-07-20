#!/bin/bash
# จัดรูป + commit ไฟล์ที่ push คู่กับเว็บ (รูป + สคริปต์ระบบรูป + package.json)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ไม่รวม .cursor/ — เป็นกฎสำหรับ AI ในเครื่องเท่านั้น
PUSH_AUTO_COMMIT_PATHS=(
  media
  public/index.html
  scripts
  package.json
  netlify.toml
  "วิธีใช้.md"
)

push_auto_status() {
  git status --porcelain -- "${PUSH_AUTO_COMMIT_PATHS[@]}"
}

push_auto_has_changes() {
  [ -n "$(push_auto_status)" ]
}

if ! command -v pnpm >/dev/null 2>&1; then
  echo "❌ ต้องมี pnpm — รัน: corepack enable && pnpm run setup"
  exit 1
fi

pnpm run media --silent

if ! push_auto_has_changes; then
  exit 1
fi

echo ""
echo "📦 เลือกไฟล์เหล่านี้ commit ก่อน push:"
while IFS= read -r line; do
  [ -z "$line" ] && continue
  echo "   • ${line:3}"
done < <(push_auto_status)
echo ""

git add -A -- "${PUSH_AUTO_COMMIT_PATHS[@]}"
git commit -m "$(cat <<'EOF'
chore: organize and compress media for web

EOF
)"
exit 0
