# ReLoop AI — Production Cloud Deployment & Operations Guide

> **Target Architecture:**  
> - **Frontend:** Next.js 16 (App Router) on **Vercel**  
> - **Backend API:** FastAPI on **Render** / **Railway** / **Google Cloud Run**  
> - **Database:** Managed PostgreSQL 16 on **Supabase** / **Neon** / **Render Postgres**  
> - **CI/CD:** Automated testing & verification via **GitHub Actions**

---

## 1. Production Architecture Overview

```text
[ Global Users & Enterprise IT Clients ]
                 │
      HTTPS / TLS 1.3 / Edge CDN
                 │
                 ▼
       ┌──────────────────┐
       │ Vercel (Edge)    │  ── Next.js 16 (App Router)
       │ Client Web App   │  ── Dual Theme / Framer Motion / Recharts
       └─────────┬────────┘
                 │
        REST API │ /backend-api (Reverse Proxy / HTTPS)
                 ▼
       ┌──────────────────┐
       │ Render / Railway │  ── FastAPI Backend (Uvicorn)
       │ Application API  │  ── Multimodal Gemini 2.5 Vision
       │ Container        │  ── Deterministic Circular Optimizer
       └─────────┬────────┘
                 │
        SSL/TLS  │ psycopg3 connection pool
                 ▼
       ┌──────────────────┐
       │ Supabase / Neon  │  ── Managed PostgreSQL 16
       │ PostgreSQL Store │  ── Automated daily backups & WAL replication
       └──────────────────┘
```

---

## 2. Production Environment Variables Reference

### Backend (`backend/.env` / Cloud Provider Environment Settings)

| Variable Name | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | **Yes** | `production` | Deployment mode (`production`, `staging`, `development`). |
| `PORT` | **Yes** | `8000` | Dynamic TCP port provided by cloud host. |
| `DATABASE_URL` | **Yes** | — | PostgreSQL connection string (`postgresql+psycopg://user:pass@host:5432/reloop?sslmode=require`). |
| `CORS_ORIGINS` | **Yes** | — | Comma-separated list of allowed frontend domains (e.g. `https://reloop.ai,https://reloop-frontend.vercel.app`). |
| `GEMINI_API_KEY` | **Yes** | — | Google Gemini API Key for multimodal photo inspection. |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model variant. |
| `EBAY_CLIENT_ID` | Optional | — | eBay Developer Application Client ID for live parts pricing. |
| `EBAY_CLIENT_SECRET` | Optional | — | eBay Developer Application Secret for OAuth token generation. |
| `NEXAR_CLIENT_ID` | Optional | — | Nexar / Octopart Client ID for electronic component inventory. |
| `NEXAR_CLIENT_SECRET` | Optional | — | Nexar / Octopart Client Secret. |
| `IFIXIT_API_KEY` | Optional | — | iFixit Store API Key (public endpoints operate without key). |
| `USD_TO_INR_RATE` | No | `85.0` | Live or baseline exchange rate for currency normalization. |

### Frontend (`frontend/.env.production` / Vercel Settings)

| Variable Name | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `NEXT_PUBLIC_BACKEND_URL` | **Yes** | — | Public URL of the deployed FastAPI backend (e.g. `https://reloop-api.onrender.com`). |

---

## 3. Step-by-Step Deployment Instructions

### Step 3.1: Provisioning the Managed Database (Supabase / Neon)
1. Create a new PostgreSQL 16 project on **Supabase** or **Neon**.
2. Copy the Connection Pooling URI (`Transaction` mode or direct URI).
3. Ensure `sslmode=require` is present in the URI.
4. Tables and indexes are auto-migrated on startup via `create_all_tables()` in `app.db.session`.

### Step 3.2: Deploying the Backend on Render
1. Connect your GitHub repository to **Render**.
2. Render will automatically detect the root `render.yaml` blueprint.
3. In the Render Dashboard, navigate to the `reloop-backend` service.
4. Set the environment secrets:
   - `DATABASE_URL`: Your Supabase/Neon PostgreSQL connection URI.
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `CORS_ORIGINS`: Your Vercel frontend URL (e.g., `https://reloop.ai`).
5. Render will execute `pip install -r backend/requirements.txt` and launch Uvicorn with auto-health checking on `/health`.

### Step 3.3: Deploying the Frontend on Vercel
1. In the **Vercel** dashboard, click **Add New Project** and import the `ReLoop-AI` repository.
2. Set the **Root Directory** to `frontend`.
3. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_BACKEND_URL`: `https://<your-render-backend-url>`
4. Click **Deploy**. Vercel will run `npm run build` and provision global CDN edge routing.

---

## 4. Database Backup Strategy

1. **Continuous Point-in-Time Recovery (PITR):**  
   Both Supabase and Neon include automated WAL (Write-Ahead Logging) archiving allowing rollback to any second in the past 7 days.
2. **Scheduled Logical Dump (`pg_dump`):**  
   A daily cron job can export encrypted snapshots to AWS S3 or Cloud Storage:
   ```bash
   pg_dump "$DATABASE_URL" --format=custom --file="reloop_backup_$(date +%Y%m%d).dump"
   ```
3. **Local Development Fallback:**  
   If `DATABASE_URL` is omitted, the backend automatically initializes and maintains local SQLite storage at `backend/reloop.db`.

---

## 5. Security & Operations Verification

- **Automated CI/CD:** Every push and pull request executes `.github/workflows/ci.yml`, running all backend tests, frontend TypeScript compilation, and build verification.
- **Health Checks:** Monitor endpoint `GET /health` which returns `{"status":"ok"}` with HTTP 200.
- **Zero Committed Secrets:** Repository is protected by pre-commit hooks and CI security scan filters.

