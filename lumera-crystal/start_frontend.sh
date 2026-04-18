#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
LOCAL_NODE_BIN="$HOME/.local/node/bin"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "未找到前端目录：$FRONTEND_DIR"
  exit 1
fi

cd "$FRONTEND_DIR"

if [[ -d "$LOCAL_NODE_BIN" ]]; then
  export PATH="$LOCAL_NODE_BIN:$PATH"
fi

PKG_MGR=""
if command -v npm >/dev/null 2>&1; then
  PKG_MGR="npm"
elif command -v pnpm >/dev/null 2>&1; then
  PKG_MGR="pnpm"
elif command -v yarn >/dev/null 2>&1; then
  PKG_MGR="yarn"
fi

if [[ -z "$PKG_MGR" ]]; then
  echo "未找到 npm/pnpm/yarn，请先安装 Node.js（建议 LTS 18+）。"
  echo "安装后可重试：./start_frontend.sh"
  exit 1
fi

if [[ ! -d "node_modules" ]]; then
  echo "首次启动，正在安装依赖..."
  case "$PKG_MGR" in
    npm) npm install ;;
    pnpm) pnpm install ;;
    yarn) yarn install ;;
  esac
fi

echo "启动前端服务..."
case "$PKG_MGR" in
  npm) npm run dev ;;
  pnpm) pnpm dev ;;
  yarn) yarn dev ;;
esac
