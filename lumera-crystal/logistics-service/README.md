# Logistics Service (Standalone)

独立物流服务（与主商城后端解耦），包含一版可操作的前后端骨架：

- 客户暂存单（接收商城需求）
- 计划订单（资源评估与预计送达）
- 运输订单（履约执行）
- 调度任务中心（统一四节点：已派单→已接单→已提货/提箱→已送达）

## Run

```bash
cd logistics-service
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

## Data Persistence

- 默认：SQLite 文件 `logistics-service/data/logistics.db`
- 推荐生产：独立 PostgreSQL 库（通过 `LOGISTICS_DATABASE_URL` 指定）
- 表名：
  - `logistics_traces`
  - `logistics_trace_events`

示例（独立库）：

```bash
export LOGISTICS_DATABASE_URL='postgresql+psycopg://postgres:your_password@10.103.71.232:6543/lumera_logistics'
```

启动后服务会自动建表（`create_all`）。

## APIs

轨迹（兼容商城支付后接入）：

- `GET /api/v1/logistics/health`
- `POST /api/v1/logistics/traces` 创建物流轨迹（按 `order_no` 幂等）
- `GET /api/v1/logistics/traces/{trace_no}` 查询物流轨迹
- `GET /api/v1/logistics/orders/{order_no}` 按订单号查询轨迹
- `POST /api/v1/logistics/traces/{trace_no}/advance` 推进轨迹步骤

履约主流程：

- `POST /api/v1/logistics/intake-orders` 创建客户暂存单
- `GET /api/v1/logistics/intake-orders` 暂存单列表
- `POST /api/v1/logistics/intake-orders/{intake_no}/plan` 暂存单转计划单
- `GET /api/v1/logistics/planned-orders` 计划单列表
- `POST /api/v1/logistics/planned-orders/{planned_no}/convert` 计划单转运输单
- `GET /api/v1/logistics/transport-orders` 运输单列表
- `POST /api/v1/logistics/transport-orders/{transport_no}/dispatch` 下发调度任务（供应商/内部司机）
- `GET /api/v1/logistics/tasks` 任务列表
- `GET /api/v1/logistics/tasks/{task_no}` 任务详情
- `POST /api/v1/logistics/tasks/{task_no}/advance` 推进任务四节点

## Dashboard (UI)

- `GET /dashboard` 物流控制台（左侧菜单分模块：总览、客户暂存单、计划订单、运输订单、调度中心）
- `GET /dashboard/traces/{trace_no}` 单个轨迹详情页
- 控制台可直接操作：
  - 创建暂存单
  - 暂存单转计划单
  - 计划单转运输单
  - 运输单下发调度任务
  - 任务推进四节点

## Typical Flow

1. 订单支付成功后，主商城调用 `POST /traces`。
2. 物流服务会自动补齐骨架链路（暂存单→计划单→运输单）。
3. 调度中心在 `/dashboard` 对运输单派单，生成任务。
4. 任务按四节点推进，完成后运输单自动变为 `completed`。
