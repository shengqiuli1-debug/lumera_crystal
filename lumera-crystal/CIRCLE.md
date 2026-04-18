# Circle Script Record

统一记录当前项目里的启动/运行脚本与用途。

## 根目录脚本

- `start_backend.sh`
  - 用途：准备后端运行环境并启动 `uvicorn`
  - 关键行为：
    - 自动创建 `backend/.venv`
    - 自动安装依赖（优先 `uv`，否则 `pip install -e .`）
    - 可选数据库连通检查
    - 可选执行 Alembic 迁移
  - 常用参数：
    - `RUN_DB_CHECK=0`：跳过数据库可达性检查
    - `RUN_MIGRATIONS=0`：跳过迁移
    - `FAIL_ON_DB_CHECK=1`：数据库不通时直接失败

- `start_frontend.sh`
  - 用途：准备前端依赖并启动 Next.js 开发服务
  - 关键行为：
    - 自动识别 `npm/pnpm/yarn`
    - 首次自动安装依赖
    - 自动将 `~/.local/node/bin` 加入 `PATH`（若存在）

- `start_logistics.sh`
  - 用途：启动独立物流服务（`logistics-service`，端口 `8010`）
  - 关键行为：
    - 自动创建 `logistics-service/.venv`
    - 自动安装物流服务依赖
    - 启动 `uvicorn app.main:app --port 8010`

- `run_logistics_dashboard.sh`
  - 用途：一键启动物流服务并访问物流前端看板（`/dashboard`）
  - 关键行为：
    - 自动读取 `logistics-service/.env`（若存在）中的 `LOGISTICS_DATABASE_URL`
    - 调用 `start_logistics.sh` 启动服务

- `run_shop_all.sh`
  - 用途：一键启动商场前后端（backend + frontend）
  - 关键行为：
    - 并行启动 `start_backend.sh` 与 `start_frontend.sh`
    - 日志写入 `.run-logs/backend.log`、`.run-logs/frontend.log`
    - 支持 `Ctrl+C` 一键停止两端进程

## 备注

- 后续新增脚本，请统一补充到本文件中。
- 当前记录日期：`2026-04-16`
