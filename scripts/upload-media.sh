#!/bin/bash

# Upload all media files to R2 bucket
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BUCKET_NAME="meenthefox"
MEDIA_DIR="media"

echo "🚀 Starting upload to R2 bucket: $BUCKET_NAME"
echo "================================================"

pnpm run media:check

find "$MEDIA_DIR" -type f -not -name ".DS_Store" | while read -r file; do
    relative_path="${file#media/}"
    echo "📤 Uploading: $relative_path"
    bunx wrangler r2 object put "$BUCKET_NAME/$relative_path" --file="$file" --remote
    if [ $? -eq 0 ]; then
        echo "✅ Success: $relative_path"
    else
        echo "❌ Failed: $relative_path"
    fi
    echo ""
done

echo "================================================"
echo "✨ Upload complete!"
