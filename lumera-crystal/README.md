# LUMERA CRYSTAL

Production-oriented fullstack skeleton for a gemstone / crystal brand website.

## Tech Stack

- Frontend: Next.js App Router + TypeScript + Tailwind CSS + shadcn-style UI components + Framer Motion
- Backend: FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL + Pydantic
- Python package manager: uv
- Deployment/dev: Docker Compose

## Project Structure

- `frontend`: brand site pages and reusable UI components
- `backend`: layered API service (`api/schemas/models/services/repositories/core/db/migrations`)
- `docker-compose.yml`: postgres + backend + frontend

## Quick Start (Local)

### 1) Start PostgreSQL

```bash
docker compose up -d postgres
```

### 2) Backend

```bash
cd backend
cp .env.example .env
uv venv
source .venv/bin/activate
uv pip install -e .
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open:
- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`
- Admin: `http://localhost:3000/admin/login`

## Quick Start (Docker)

```bash
docker compose up --build
```

Then execute migration and seed once:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed
```

## API Modules

- `GET /api/v1/health`
- `GET /api/v1/products`
- `GET /api/v1/products/{slug}`
- `GET /api/v1/categories`
- `GET /api/v1/categories/{slug}`
- `GET /api/v1/posts`
- `GET /api/v1/posts/{slug}`
- `POST /api/v1/contact`
- `POST /api/v1/newsletter`
- `GET /api/v1/ai/health` (placeholder)
- `POST /api/v1/ai/mail/command` (自然语言触发邮件发送)
- Shop APIs:
  - `POST /api/v1/shop/users`
  - `GET /api/v1/shop/products`
  - `GET /api/v1/shop/products/{product_id}/inventory`
  - `POST /api/v1/shop/orders`
  - `PATCH /api/v1/shop/orders/{order_id}`
  - `POST /api/v1/shop/orders/{order_id}/pay`
  - `GET /api/v1/shop/users/{user_id}/orders`
  - `GET /api/v1/shop/users/{user_id}/recommendations`
  - `GET /api/v1/shop/reports/summary?range=daily|weekly|monthly`

Admin APIs:
- `POST /api/v1/admin/auth/login`
- `GET /api/v1/admin/auth/me`
- `GET/POST/PATCH/DELETE /api/v1/admin/products`
- `GET/POST/PATCH/DELETE /api/v1/admin/categories`
- `GET/POST/PATCH/DELETE /api/v1/admin/posts`
- `GET /api/v1/admin/dashboard/overview`
- `GET /api/v1/admin/messages`
- `PATCH /api/v1/admin/messages/{id}/read`
- `GET /api/v1/admin/newsletter`
- `POST /api/v1/admin/uploads/image`
- `POST /api/v1/admin/uploads/images`
- `GET /api/v1/media/{media_id}`

Products support filtering/search/pagination:
- `category`, `min_price`, `max_price`, `color`, `intention`, `search`, `page`, `page_size`

Admin login defaults:
- email: `admin@lumeracrystal.com`
- password: `Lumera@123456`
- can be overridden via `.env` (`ADMIN_DEFAULT_EMAIL`, `ADMIN_DEFAULT_PASSWORD`)

Admin init helper:
```bash
cd backend
source .venv/bin/activate
python -m scripts.init_admin
```

## Image Storage (Current Phase)

Current strategy stores image binary directly in PostgreSQL `BYTEA`:

- table: `media_assets` (stores binary + metadata + hash)
- relation: `products.cover_media_id` + `product_images` (gallery with sort order)
- read endpoint: `GET /api/v1/media/{media_id}`
- upload endpoints:
  - `POST /api/v1/admin/uploads/images` (multi-file)
  - `POST /api/v1/admin/uploads/image` (single-file compatibility)

Default upload policy:
- allowed mime: `image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime`
- max size: `5MB` per file (gif/video can be adjusted)
- max duration: `8` seconds for gif/video (longer files are auto trimmed to 8s)
- configurable via `.env`:
  - `MEDIA_MAX_UPLOAD_SIZE_MB`
  - `MEDIA_MAX_VIDEO_UPLOAD_SIZE_MB`
  - `MEDIA_ALLOWED_MIME_TYPES`
  - `MEDIA_MAX_DURATION_SECONDS`

Contact form behavior:
- `POST /api/v1/contact` saves `name/email/subject/message` into `contact_messages`
- backend attempts auto-reply email and stores status:
  - `auto_reply_status` (`sent` / `failed` / `pending`)
  - `auto_reply_subject` / `auto_reply_body` / `auto_replied_at`
- SMTP config in `.env`:
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
  - `SMTP_USE_TLS`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`

## Shop Module (Lightweight Retrofit)

This project now includes a lightweight mall flow without heavy refactor:

- inventory monitor with threshold check (`STOCK_LOW_THRESHOLD`, default `5`)
- low-stock auto off-shelf (`products.status = archived`)
- auto restock request creation (`AUTO_RESTOCK_QUANTITY`) via supplier service stub
- restock complete callback API to restore stock and auto on-shelf (`active`)
- order + payment + shipping request chain
- points earning/redeeming (`POINTS_EARN_RATE`, default `10`)
- coupon application
- behavior-based recommendations
- daily/weekly/monthly report summary APIs

Added tables:

- `shop_users`, `coupons`
- `shop_orders`, `shop_order_items`
- `inventory_alerts`, `restock_requests`, `shipment_requests`
- `user_behavior_events`

Migration:

- `20260403_0005_shop_core.py`

Admin product edit flow:
1. Upload image via `/api/v1/admin/uploads/images`.
2. Receive `id` and `url` for each image.
3. Save `cover_media_id` and `gallery_media_ids` in product payload.
4. Render with returned `cover_image` / `gallery_images` URLs or rich media objects.

Future migration to object storage:
- keep business-side references (`cover_media_id`, `product_images`) unchanged.
- only replace storage implementation (currently `DatabaseStorageService`) with local/S3/OSS service.
- retain `media_assets` as metadata and pointer table, with `storage_type` switched from `db` to `local/s3/oss`.

## AI Extension Plan

Reserved architecture is included:
- `app/api/v1/ai`
- `app/services/ai_service.py`
- `app/services/prompt_manager.py`
- Database placeholders: `conversations`, `inquiries`

Future extension directions:
1. Smart gemstone recommendation based on user profile
2. Crystal Q&A assistant with domain prompt templates
3. RAG retrieval over brand knowledge/docs
4. AI-assisted blog and product copy generation

## 自然语言邮件指令

当输入文本以“发送邮件给”开头时，会触发邮件发送流程。

示例：
- 发送邮件给 li@example.com，告诉他明天下午3点开会，语气正式一点
- 发送邮件给 王总，主题是项目延期说明，内容是由于接口联调问题，预计延期到周五
- 发送邮件给 test@example.com，内容：报价单已更新，请查收

请求：
```
POST /api/v1/ai/mail/command
{
  "text": "发送邮件给 王总，主题是项目延期说明，内容是由于接口联调问题，预计延期到周五"
}
```

配置（.env）：
- `MAIL_CONTACTS_PATH` 联系人映射 JSON 文件路径（默认 `config/mail_contacts.json`）
- `LLM_PROVIDER` 本地模型提供方：`openai` 或 `ollama`
- `LLM_BASE_URL` 本地模型服务地址，例如 `http://localhost:11434` 或 `http://localhost:8001`
- `LLM_API_KEY` （OpenAI-compatible 可选）
- `LLM_MODEL` 模型名称
- `LLM_TIMEOUT_SECONDS` 请求超时

联系人映射示例：
```
{
  "王总": "boss@example.com"
}
```

说明：
- 规则优先解析“主题/内容”，缺失时调用本地模型补全。
- 若联系人名未映射邮箱，返回明确错误。

## Notes

- Current media URLs are placeholders (Unsplash); replace with your CDN/static assets later.
- This scaffold prioritizes extension-ready architecture over single-file demos.

## Testing

```bash
cd backend
source .venv/bin/activate
pytest -q
```
