#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/qiuqiuqiu/ai_agent/lumera-crystal"
FRONTEND_DIR="$PROJECT_DIR/frontend"

if [[ -x "$HOME/.volta/bin/npm" ]]; then
  NPM_BIN="$HOME/.volta/bin/npm"
else
  if ! command -v npm >/dev/null 2>&1; then
    echo "未找到 npm。请先安装 Node.js（建议 Volta）。"
    exit 1
  fi
  NPM_BIN="$(command -v npm)"
fi

cd "$FRONTEND_DIR"
"$NPM_BIN" run dev
