# ReLoop AI — Backend

The product-lifecycle intelligence and circular decision engine backend for ReLoop AI.

## Prerequisites
- Python 3.11+
- PostgreSQL (or Docker to run PostgreSQL)

## Setup

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure environment variables**:
   Copy `.env.example` to `.env` and fill in necessary values:
   ```bash
   cp .env.example .env
   ```

4. **Start PostgreSQL database** (optional with Docker):
   ```bash
   docker compose up -d postgres
   ```

## Running the Development Server

From the `backend/` directory:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation will be available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

## Running Tests

From the `backend/` directory:
```bash
python -m pytest tests -v
```
