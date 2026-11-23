# Render Deployment Guide for UniAssist AI (Edunexus)

This repository is optimized for deployment on [Render](https://render.com) using the root **Dockerfile** as a Web Service.

---

## Why the Initial Deploy Failed on Render

SQLAlchemy 2.0 with asynchronous drivers (`asyncpg`) requires the `greenlet` C-extension. While present in local environments, it was missing from `requirements.txt`. We have now added:
- `sqlalchemy[asyncio]>=2.0.32`
- `greenlet>=3.0.0`
- `azure-ai-documentintelligence>=1.0.0b4`
- `pymupdf>=1.24.0`

---

## Render Service Configuration

### Service Settings
- **Service Type:** Web Service
- **Environment:** Docker
- **Branch:** `main`
- **Docker Command:** (Leave empty; defaults to the `CMD` in Dockerfile: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`)
- **Health Check Path:** `/api/v1/health`

### Environment Variables
Configure these under **Environment** tab on your Render dashboard:

| Variable | Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(Click "Generate" or enter a 32+ char key)* | Used for JWT signing |
| `ENVIRONMENT` | `production` | Run mode |
| `DEBUG` | `False` | Turn off debug traces |
| `SEED_DEMO_DATA` | `True` | Seed initial student & admin demo users |
| `USE_SQLITE_FALLBACK` | `True` *(or `False` if PostgreSQL is attached)* | Enables local SQLite if no PostgreSQL is provisioned |
| `ADMIN_DEFAULT_EMAIL` | `admin@example.com` | Default admin email |
| `ADMIN_DEFAULT_PASSWORD` | `AdminPassword123!` | Default admin password |
| `STUDENT_DEFAULT_EMAIL` | `student@example.com` | Default student email |
| `STUDENT_DEFAULT_PASSWORD` | `StudentPassword123!` | Default student password |
| `DATABASE_URL` | *(Auto-set if Render Postgres is linked)* | PostgreSQL connection string |

*(Optional Azure AI services: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, `AZURE_STORAGE_CONNECTION_STRING`)*

---

## Optional: Connecting Render PostgreSQL

1. In Render Dashboard, click **New + > PostgreSQL**.
2. Name it e.g. `edunexus-db` and select the Free or Starter tier.
3. Once created, copy the **Internal Database URL** (e.g., `postgresql://...`).
4. In your `edunexus` Web Service, add the environment variable `DATABASE_URL` with this value.
5. Set `USE_SQLITE_FALLBACK=False`.
6. Our backend adapter will automatically convert `postgres://` or `postgresql://` to `postgresql+asyncpg://`, strip conflicting `sslmode` parameters, and initialize all tables.
