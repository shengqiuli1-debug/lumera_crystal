#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
LOGISTICS_ENV_FILE="$PROJECT_DIR/logistics-service/.env"

cd "$PROJECT_DIR"

# 支持在 logistics-service/.env 里配置 LOGISTICS_DATABASE_URL
if [[ -f "$LOGISTICS_ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$LOGISTICS_ENV_FILE"
  set +a
fi

echo "即将启动独立物流服务..."
echo "启动后请访问: http://localhost:8010/dashboard"
echo

exec "$PROJECT_DIR/start_logistics.sh"
