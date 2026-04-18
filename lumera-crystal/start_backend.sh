#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
VENV_BIN="$BACKEND_DIR/.venv/bin"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RUN_DB_CHECK="${RUN_DB_CHECK:-1}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"
FAIL_ON_DB_CHECK="${FAIL_ON_DB_CHECK:-0}"

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "未找到后端目录：$BACKEND_DIR"
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "未找到 Python，可用如下命令指定解释器："
  echo "  PYTHON_BIN=python3 ./start_backend.sh"
  exit 1
fi

cd "$BACKEND_DIR"

if [[ ! -d ".venv" ]]; then
  echo "未检测到 backend/.venv，正在创建虚拟环境..."
  "$PYTHON_BIN" -m venv .venv
fi

if [[ ! -x "$VENV_BIN/python" ]]; then
  echo "虚拟环境异常：$VENV_BIN/python 不存在"
  exit 1
fi

if [[ ! -x "$VENV_BIN/uvicorn" ]]; then
  echo "首次安装后端依赖..."
  if command -v uv >/dev/null 2>&1; then
    if ! uv sync; then
      echo "依赖安装失败。若是网络受限，请先恢复网络后重试。"
      exit 1
    fi
  else
    "$VENV_BIN/python" -m pip install --upgrade pip || true
    if ! "$VENV_BIN/python" -m pip install -e .; then
      echo "依赖安装失败。请检查网络或私有源配置后重试。"
      exit 1
    fi
  fi
fi

if [[ ! -x "$VENV_BIN/alembic" ]]; then
  echo "缺少 alembic，请检查依赖安装是否成功。"
  exit 1
fi

DB_URL="${DATABASE_URL:-}"
if [[ -z "$DB_URL" && -f ".env" ]]; then
  DB_URL="$(grep -E '^DATABASE_URL=' .env | tail -n 1 | cut -d'=' -f2- || true)"
fi

DB_AVAILABLE=1
if [[ "$RUN_DB_CHECK" == "1" && -n "$DB_URL" ]]; then
  if ! DB_CHECK_OUTPUT="$("$VENV_BIN/python" - "$DB_URL" <<'PY' 2>&1
import socket
import sys
from urllib.parse import urlparse

url = sys.argv[1]
parsed = urlparse(url.replace("+psycopg", ""))
host = parsed.hostname or "localhost"
port = parsed.port or 5432
try:
    with socket.create_connection((host, port), timeout=2):
        print(f"ok:{host}:{port}")
except OSError as exc:
    print(f"fail:{host}:{port}:{exc}")
    raise SystemExit(1)
PY
  )"; then
    DB_AVAILABLE=0
    echo "警告：数据库连接不可达：$DB_CHECK_OUTPUT"
    echo "请确认 PostgreSQL 已启动，或修正 backend/.env 的 DATABASE_URL。"
    echo "可执行：docker compose up -d postgres"
    echo "提示：当前 docker-compose 默认数据库端口是 5432。"
    if [[ "$FAIL_ON_DB_CHECK" == "1" ]]; then
      exit 1
    fi
  fi
fi

if [[ "$RUN_MIGRATIONS" == "1" ]]; then
  if [[ "$DB_AVAILABLE" == "1" ]]; then
    echo "执行数据库迁移..."
    "$VENV_BIN/alembic" upgrade head
  else
    echo "跳过数据库迁移（数据库不可达）。"
  fi
fi

echo "启动后端服务..."
exec "$VENV_BIN/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload
