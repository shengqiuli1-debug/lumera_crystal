#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/qiuqiuqiu/ai_agent/lumera-crystal"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_PY="$BACKEND_DIR/.venv/bin/python"
UVICORN="$BACKEND_DIR/.venv/bin/uvicorn"

if [[ ! -x "$VENV_PY" ]]; then
  echo "未找到后端虚拟环境：$VENV_PY"
  echo "请先执行：python3 -m venv $BACKEND_DIR/.venv"
  exit 1
fi

cd "$BACKEND_DIR"
"$UVICORN" app.main:app --reload --host 0.0.0.0 --port 8000
