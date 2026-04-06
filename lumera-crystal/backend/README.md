# Backend (FastAPI)

Layered architecture:

- `api`: route handlers
- `schemas`: request/response DTOs
- `models`: SQLAlchemy entities
- `repositories`: DB access layer
- `services`: business logic
- `core`: config and app settings
- `db`: base/session
- `alembic`: migrations

Run:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

Admin bootstrap:

```bash
python -m scripts.init_admin
```

Image storage (current implementation):
- PostgreSQL `BYTEA` table: `media_assets`
- product relations: `products.cover_media_id` + `product_images`
- upload API: `POST /api/v1/admin/uploads/images`
- read API: `GET /api/v1/media/{media_id}`
- gif/video duration limit: `MEDIA_MAX_DURATION_SECONDS` (auto trim to max duration)
- upload size envs: `MEDIA_MAX_UPLOAD_SIZE_MB` (images), `MEDIA_MAX_VIDEO_UPLOAD_SIZE_MB` (gif/video)
- storage abstraction:
  - active: `services/storage/db_storage.py` (`DatabaseStorageService`)
  - reserved: `LocalFileStorageService`, `S3StorageService`

Contact auto-reply:
- API: `POST /api/v1/contact`
- saves contact record first, then sends email reply via SMTP
- SMTP envs:
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
  - `SMTP_USE_TLS`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`

## Lightweight Shop Module

Added mall-oriented core with minimal retrofit:

- models:
  - `shop_users`
  - `coupons`
  - `shop_orders` / `shop_order_items`
  - `inventory_alerts`
  - `restock_requests`
  - `shipment_requests`
  - `user_behavior_events`
- migration: `alembic/versions/20260403_0005_shop_core.py`

Main APIs:

- `POST /api/v1/shop/users`
- `GET /api/v1/shop/products`
- `GET /api/v1/shop/products/{product_id}/inventory`
- `POST /api/v1/shop/orders`
- `PATCH /api/v1/shop/orders/{order_id}`
- `POST /api/v1/shop/orders/{order_id}/pay`
- `GET /api/v1/shop/users/{user_id}/orders`
- `POST /api/v1/shop/users/{user_id}/events/view/{product_id}`
- `GET /api/v1/shop/users/{user_id}/recommendations`
- `GET /api/v1/shop/reports/summary?range=daily|weekly|monthly`
- `POST /api/v1/shop/inventory/restock-requests/{request_id}/complete`

Business behavior:

- stock monitor threshold (default 5): `STOCK_LOW_THRESHOLD`
- low stock auto flow:
  - create inventory alert
  - send admin notification email (if SMTP configured)
  - create restock request via supplier service
  - auto set product status to `archived` (off-shelf)
- restock completion:
  - increase stock
  - resolve alert
  - auto set product back to `active`
- order payment:
  - lock stock rows and deduct inventory
  - mark order paid/fulfilled
  - create shipment request
  - apply coupon usage count and points changes
- recommendations:
  - based on behavior + purchase events
- reports:
  - paid orders/sales + inventory snapshot for daily/weekly/monthly windows

Extra envs:

- `STOCK_LOW_THRESHOLD`
- `AUTO_RESTOCK_QUANTITY`
- `POINTS_EARN_RATE`

Tests:

```bash
cd backend
source .venv/bin/activate
pytest -q
```
