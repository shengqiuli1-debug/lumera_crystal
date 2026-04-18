#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$SCRIPT_DIR/logistics-service"
VENV_BIN="$SERVICE_DIR/.venv/bin"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ ! -d "$SERVICE_DIR" ]]; then
  echo "未找到物流服务目录：$SERVICE_DIR"
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "未找到 Python，请先安装 Python 3.11+"
  exit 1
fi

cd "$SERVICE_DIR"

if [[ ! -d ".venv" ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

# 每次启动前同步依赖，避免 pyproject 变更后环境不一致
"$VENV_BIN/python" -m pip install --upgrade pip || true
"$VENV_BIN/python" -m pip install -e .

echo "启动物流服务..."
exec "$VENV_BIN/uvicorn" app.main:app --host 0.0.0.0 --port 8010 --reload
