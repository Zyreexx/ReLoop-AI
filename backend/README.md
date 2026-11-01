# ReLoop AI — Backend

The product-lifecycle intelligence and circular decision engine backend for ReLoop AI. Built with **FastAPI**, **Pydantic v2**, **SQLAlchemy**, and **Google Gemini 2.5/Flash multimodal AI**.

---

## 📁 Backend Structure

```text
backend/
├── app/
│   ├── ai/                   # Gemini multimodal provider, prompt loaders, vision & symptom extractors
│   ├── api/routes/           # API routes: /products, /vision, /diagnostics, /assessment, /recommendations, /reports, /health
│   ├── db/                   # SQLAlchemy engine, session management, base model, entity repositories
│   ├── knowledge/            # Hardware catalogs (data/products), baseline specs, component depreciation logic
│   ├── models/               # SQLAlchemy ORM entity models (Product, Assessment, Evidence, Recommendation, User)
│   ├── optimizer/            # Deterministic circular pathway scoring engine, eligibility filters, and tie-breakers
│   ├── schemas/              # Pydantic v2 models and error envelopes
│   ├── services/             # Core business logic (assessment synthesis, diagnostic validation, email reports)
│   ├── utils/                # File upload validation, MIME checking, image sanitization
│   ├── config.py             # App settings, environment loading, database path resolution
│   └── main.py               # FastAPI application entry point and middleware configuration
├── tests/                    # Pytest test suite (unit, integration, golden fixtures, and security contracts)
├── Dockerfile                # Production container specification
├── requirements.txt          # Python dependencies
├── reloop.db                 # Local development SQLite database (automatic fallback)
├── .env.example              # Sample environment variables
└── README.md                 # Backend documentation
```

---

## ⚙️ Prerequisites
- Python 3.11+
- Optional: PostgreSQL (or Docker for running PostgreSQL container)

---

## 🚀 Setup & Execution

### 1. Create and Activate Virtual Environment
```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp backend/.env.example backend/.env
```
Key variables:
- `DATABASE_URL`: Optional PostgreSQL connection URI. If omitted or set to SQLite, defaults automatically to `backend/reloop.db`.
- `GEMINI_API_KEY`: Google Gemini API key for visual defect inspection and symptom parsing.
- `DEMO_FALLBACK`: Set to `true` to use deterministic fallback fixtures without external AI dependencies.

### 4. Running the Server
From the project root:
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Or from the `backend/` directory:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- Redoc UI: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/api/health`

---

## 🧪 Running Tests

From the project root:
```bash
python -m pytest backend/tests -v
```
Or from the `backend/` directory:
```bash
pytest tests -v
```
