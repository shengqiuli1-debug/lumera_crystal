#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "未找到前端目录：$FRONTEND_DIR"
  exit 1
fi

cd "$FRONTEND_DIR"

if [[ ! -d "node_modules" ]]; then
  echo "首次启动，正在安装依赖..."
  if command -v npm >/dev/null 2>&1; then
    npm install
  else
    echo "未找到 npm，请先安装 Node.js"
    exit 1
  fi
fi

echo "启动前端服务..."
npm run dev
