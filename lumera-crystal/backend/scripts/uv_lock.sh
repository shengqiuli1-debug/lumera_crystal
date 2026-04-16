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
uv pip compile pyproject.toml -o requirements.lock
echo "已生成 requirements.lock"
