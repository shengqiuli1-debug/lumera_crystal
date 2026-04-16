#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "未检测到 uv，请先安装："
  echo "  python3 -m pip install --user uv"
  exit 1
fi

cd "$BACKEND_DIR"
uv venv
uv pip install -e .
echo "完成依赖安装（uv）。"
