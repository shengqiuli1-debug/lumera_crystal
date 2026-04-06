# LUMERA CRYSTAL 安装与修复清单

更新时间：2026-03-29（Asia/Shanghai）

## 1) 发现的问题

- 运行 `backend/app/main.py` 报错：`ModuleNotFoundError: No module named 'fastapi'`
- 本机缺少工具：`uv`、`node`、`npm`
- Homebrew 安装失败（权限不足，`/opt/homebrew` 不可写）

## 2) 我执行过的命令（按顺序）

### 环境检查

```bash
python3 --version
uv --version
node --version
npm --version
brew --version
```

### 尝试（失败，已记录）

```bash
brew install uv
brew install node
```

失败原因：Homebrew 目录权限不足。

### 后端可用性修复（成功）

```bash
python3 -m venv /Users/qiuqiuqiu/ai_agent/lumera-crystal/backend/.venv
/Users/qiuqiuqiu/ai_agent/lumera-crystal/backend/.venv/bin/python -m pip install fastapi 'uvicorn[standard]' sqlalchemy alembic 'psycopg[binary]' pydantic-settings email-validator python-slugify
/Users/qiuqiuqiu/ai_agent/lumera-crystal/backend/.venv/bin/python -m pip install uv
/Users/qiuqiuqiu/ai_agent/lumera-crystal/backend/.venv/bin/python -m pip install -e /Users/qiuqiuqiu/ai_agent/lumera-crystal/backend
```

### 用户级 Node 安装（成功，绕过 Homebrew）

```bash
curl https://get.volta.sh | bash
$HOME/.volta/bin/volta install node
```

### 前端依赖安装（成功）

```bash
$HOME/.volta/bin/npm install
```

### 验证命令（成功）

```bash
/Users/qiuqiuqiu/ai_agent/lumera-crystal/backend/.venv/bin/python - <<'PY'
import fastapi,uvicorn,sqlalchemy,alembic,pydantic_settings
print('imports-ok')
PY

node --version
npm --version
```

## 3) 实际安装到的核心依赖

### 后端 Python（在 `backend/.venv`）

- fastapi
- uvicorn[standard]
- sqlalchemy
- alembic
- psycopg[binary]
- pydantic-settings
- email-validator
- python-slugify
- uv

### 前端 Node（通过 Volta）

- Node.js `v24.14.1`
- npm `11.11.0`
- `frontend/package.json` 中全部依赖（已生成 `node_modules` 与 `package-lock.json`）

## 4) 本次新增/变更的关键文件

- 新增目录：`backend/.venv/`（后端虚拟环境）
- 新增文件：`frontend/package-lock.json`
- 新增目录：`frontend/node_modules/`
- 变更文件：`backend/pyproject.toml`
  - 新增 `email-validator` 依赖
  - 新增 `[tool.hatch.build.targets.wheel] packages = ["app"]`
  - 作用：修复 `pip install -e .` 元数据构建失败

## 5) 你现在可以直接用的启动命令

### 后端

```bash
cd /Users/qiuqiuqiu/ai_agent/lumera-crystal/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd /Users/qiuqiuqiu/ai_agent/lumera-crystal/frontend
npm run dev
```

