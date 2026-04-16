#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
VENV_BIN="$BACKEND_DIR/.venv/bin"

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "未找到后端目录：$BACKEND_DIR"
  exit 1
fi

if [[ ! -x "$VENV_BIN/uvicorn" ]]; then
  echo "未找到后端虚拟环境或 uvicorn：$VENV_BIN/uvicorn"
  echo "请先在 backend 目录下创建 .venv 并安装依赖"
  exit 1
fi

cd "$BACKEND_DIR"
exec "$VENV_BIN/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload
