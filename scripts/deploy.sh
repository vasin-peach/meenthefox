#!/bin/bash

# Cloudflare Pages Deployment Script
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "🚀 Starting Cloudflare Pages Deployment..."
echo ""

echo "📦 Switching to Node.js 20..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20 2>/dev/null || true

echo ""
echo "✅ Node version: $(node -v)"
echo "✅ pnpm version: $(pnpm -v)"
echo ""

if ! command -v wrangler &> /dev/null; then
    echo "📦 Installing Wrangler CLI globally..."
    pnpm add -g wrangler
fi

echo ""
echo "🚀 Deploying to Cloudflare Pages..."
wrangler pages deploy public --project-name=meen-the-fox

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your site should be live at: https://meen-the-fox.pages.dev"
echo ""
