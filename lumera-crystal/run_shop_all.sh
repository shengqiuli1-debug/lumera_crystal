#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
LOG_DIR="$PROJECT_DIR/.run-logs"

mkdir -p "$LOG_DIR"

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo
  echo "正在关闭商场前后端服务..."
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

echo "启动商场后端..."
(
  cd "$PROJECT_DIR"
  ./start_backend.sh
) >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
sleep 1
if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
  echo "后端启动失败，请查看日志：$BACKEND_LOG"
  exit 1
fi

echo "启动商场前端..."
(
  cd "$PROJECT_DIR"
  ./start_frontend.sh
) >"$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
sleep 1
if ! kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
  echo "前端启动失败，请查看日志：$FRONTEND_LOG"
  exit 1
fi

echo
echo "商场前后端已启动。"
echo "- 前端: http://localhost:3000"
echo "- 后端: http://localhost:8000/docs"
echo
echo "日志文件："
echo "- $BACKEND_LOG"
echo "- $FRONTEND_LOG"
echo
echo "按 Ctrl+C 可一键停止前后端。"
echo

wait -n "$BACKEND_PID" "$FRONTEND_PID"
echo "检测到服务退出，请检查日志定位问题。"
