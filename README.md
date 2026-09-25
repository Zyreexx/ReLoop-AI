# ReLoop AI — The Next-Life Engine for Electronics

> **ReLoop AI determines the highest-value next life for a product — repair, upgrade, refurbishment, reuse, component recovery, or, only when necessary, recycling.**

Built for the **PCCoE International Grand Challenge 2026**  
**Category:** Smart Cities, Energy & Circular Economy  
**Focus:** Circular Economy Solutions & Next-Life Lifecycle Decision Optimization

---

## ♻️ Overview & Circular Pathways Hierarchy

Consumer and enterprise IT hardware (e.g. laptops) is frequently discarded prematurely when only a single modular component degrades. ReLoop AI provides a deterministic, multi-objective decision optimization engine that balances economic cost, useful life extension, carbon abatement ($CO_2e$ avoided), and recovery turnaround time.

```text
       [ Physical Device + Diagnostics + Visual Inspection ]
                                ↓
                 [ Evidence Provenance Layer ]
        (VISUAL, DIAGNOSTIC, USER_REPORTED, DATABASE, ESTIMATE)
                                ↓
               [ Component Condition Synthesis ]
                                ↓
        [ Deterministic Circular Pathway Optimizer ]
  ┌──────────────┬──────────────┬──────────────┬──────────────┐
  ↓              ↓              ↓              ↓              ↓
REPAIR        UPGRADE       REFURBISH        REUSE     COMPONENT RECOVERY → RECYCLE
                                ↓
          [ Guarded Multimodal Explanation & Audit Report ]
```

---

## 📁 Repository Structure

```text
ReLoop-AI/
├── backend/
│   ├── app/
│   │   ├── ai/               # Gemini multimodal provider, versioned prompts, output schemas
│   │   ├── api/routes/       # FastAPI endpoints (products, vision, diagnostics, assessment, recommendations, reports)
│   │   ├── db/               # SQLAlchemy engine, session management, repositories, in-memory store
│   │   ├── knowledge/        # Structured hardware specs catalog, repair costs, lifecycle assumptions, sample data
│   │   ├── models/           # Database entity models
│   │   ├── optimizer/        # Deterministic scoring engine, eligibility rules, min-max normalizer, tie-breaking
│   │   ├── schemas/          # Pydantic v2 domain schemas and error models
│   │   ├── services/         # Business logic (assessment, diagnostics, vision, recommendations, reports)
│   │   └── utils/            # Upload validation, magic byte checking, sanitization
│   ├── tests/                # 175+ test suite (golden fixtures, guardrails, API contracts, hardening)
│   ├── Dockerfile            # Container build with dynamic PORT binding
│   └── requirements.txt      # Backend Python dependencies
├── data/
│   ├── demo/                 # 4 canonical demo scenarios (healthy, repairable, borderline, recovery)
│   └── products/             # Curated laptop model specification JSON catalogs
├── docs/                     # Architecture, rules, design, PRD, and phase specifications
├── scripts/
│   ├── seed_demo_data.py     # Idempotent DB seeder for demo cases
│   ├── smoke_test.py         # End-to-end deployment smoke test against /health and full API
│   └── validate_demo_case.py # Validation runner asserting expected pathways across all 4 demo cases
├── docker-compose.yml        # Multi-container orchestration (FastAPI backend + PostgreSQL)
└── README.md                 # System documentation and API reference
```

---

## ⚙️ Environment Variables

Configure environment variables in `.env` (or set directly in deployment platforms):

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | `int` | `8000` | Port for the FastAPI server to bind. |
| `HOST` | `str` | `0.0.0.0` | Host interface to listen on. |
| `DATABASE_URL` | `str` | `postgresql+psycopg://postgres:postgres@localhost:5432/reloop` | PostgreSQL connection URI. Automatically falls back to SQLite `reloop.db` if unavailable. |
| `DEMO_FALLBACK` | `bool` | `false` | When `true`, serves precomputed demo fixtures labeled with `source: "sample-data"`. |
| `GEMINI_API_KEY` | `str` | `""` | Google Gemini API key for multimodal identification, damage analysis, and explanations. |
| `GEMINI_MODEL` | `str` | `gemini-2.5-flash` | Gemini model variant to use. |
| `CORS_ORIGINS` | `str` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated list of allowed frontend origins. |
| `ENVIRONMENT` | `str` | `development` | Deployment environment (`development`, `staging`, `production`). |

---

## 🚀 Run Instructions

### Option A: Local Development (Python)

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run FastAPI Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Interactive Swagger UI will be available at: `http://localhost:8000/docs`

3. **Seed Demo Cases (Optional):**
   ```bash
   python scripts/seed_demo_data.py
   ```

### Option B: Docker Compose (Backend + PostgreSQL)

```bash
# Build and launch both PostgreSQL and FastAPI backend
docker-compose up --build

# Run detached
docker-compose up -d
```

---

## 📡 API Reference & Example Requests

All error responses strictly adhere to the unified envelope:
`{"error": {"code": "...", "message": "...", "field": "..."}}`.

### 1. Health Check
- **`GET /health`**
  - **Response (200 OK):**
    ```json
    {
      "status": "ok",
      "version": "0.1.0",
      "environment": "development"
    }
    ```

---

### 2. Supported Hardware Catalog
- **`GET /api/products/catalog`**
  - Returns all supported laptop models and specifications from the curated knowledge base.

---

### 3. Product Identification
- **`POST /api/products/identify`**
  - **Payload (JSON or multipart with 1–3 photos):**
    ```json
    {
      "hint": "Dell Latitude 5420"
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "identified_model": {
        "manufacturer": "Dell",
        "model": "Latitude 5420",
        "model_year": 2021,
        "confidence": "HIGH",
        "specs": {
          "ram_modular": true,
          "ssd_modular": true,
          "battery_replaceable": true
        }
      },
      "is_supported": true,
      "confidence": 0.95,
      "needs_confirmation": true
    }
    ```

---

### 4. Product Registration / Confirmation
- **`POST /api/products`**
  - **Payload (JSON):**
    ```json
    {
      "manufacturer": "Dell",
      "model": "Latitude 5420",
      "model_year": 2021,
      "category": "LAPTOP",
      "age_years": 4.0
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "id": "prod_d8a903c86e",
      "manufacturer": "Dell",
      "model": "Latitude 5420",
      "model_year": 2021,
      "category": "LAPTOP",
      "age": 4.0,
      "specs": { ... }
    }
    ```

---

### 5. Visible Damage & Optical Analysis
- **`POST /api/vision/analyze`**
  - **Payload (JSON or Multipart with images):**
    ```json
    {
      "product_id": "prod_d8a903c86e",
      "inspection_notes": "2 missing keycaps: F4 and Alt; minor chassis scuffs."
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "product_id": "prod_d8a903c86e",
      "findings": [
        {
          "component": "KEYBOARD",
          "description": "2 missing keycaps observed",
          "severity": "MODERATE",
          "confidence": 0.9,
          "evidence_type": "VISUAL"
        }
      ],
      "overall_visual_condition": "SERVICE_REQUIRED"
    }
    ```

---

### 6. Diagnostic Telemetry Validation
- **`POST /api/diagnostics/validate`**
  - **Payload (JSON):**
    ```json
    {
      "product_id": "prod_d8a903c86e",
      "battery": {
        "design_capacity_mwh": 54000.0,
        "full_charge_capacity_mwh": 39400.0,
        "cycle_count": 680,
        "health_percentage": 73.0
      },
      "ssd": {
        "health_percentage": 91.0,
        "capacity_gb": 512,
        "smart_status": "PASS"
      },
      "ram": {
        "installed_gb": 16,
        "test_result": "PASS"
      },
      "thermals": {
        "cpu_max_temp_c": 96.0,
        "throttling_detected": true
      },
      "system": {
        "post_successful": true,
        "motherboard_power_stable": true
      }
    }
    ```

---

### 7. Assessment Profile Synthesis
- **`POST /api/assessment/build`**
  - **Payload (JSON):**
    ```json
    {
      "product_id": "prod_d8a903c86e"
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "product_id": "prod_d8a903c86e",
      "overall_hardware_health": "FAIR",
      "components": {
        "battery": { "status": "SERVICE_REQUIRED", "label": "73% — Service Recommended", "repairable": true },
        "ssd": { "status": "GOOD", "label": "91% — Healthy", "upgradeable": true },
        "ram": { "status": "GOOD", "label": "PASS", "upgradeable": true },
        "thermals": { "status": "SERVICE_REQUIRED", "label": "Service Required", "repairable": true },
        "display": { "status": "GOOD", "label": "Clean / No Cracks" },
        "keyboard": { "status": "SERVICE_REQUIRED", "label": "Key Damage / Missing", "repairable": true },
        "chassis": { "status": "FAIR", "label": "Solid / Minor Wear" },
        "system": { "status": "GOOD", "label": "POST & Power OK" }
      }
    }
    ```

---

### 8. Circular Pathway Recommendation
- **`POST /api/recommendations/generate`**
  - **Payload (JSON):**
    ```json
    {
      "product_id": "prod_d8a903c86e",
      "objective": "MAX_LIFE"
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "product_id": "prod_d8a903c86e",
      "objective": "MAX_LIFE",
      "selected_pathway": "REPAIR",
      "score": 77.4,
      "primary_recommendation": {
        "pathway_type": "REPAIR",
        "score": 77.4,
        "pathway": {
          "estimated_cost": { "min_val": 5400, "max_val": 9800, "unit": "INR" },
          "expected_life_extension_years": { "min_val": 2.5, "max_val": 3.5 },
          "environmental_estimate": { "co2_avoided_kg_min": 250.0, "co2_avoided_kg_max": 295.0, "ewaste_diverted_kg": 1.4 }
        }
      },
      "alternative_pathways": [ ... ],
      "explanation": {
        "summary": "Based on verified diagnostic and optical condition data, REPAIR was selected for Dell Latitude 5420 under the Max Life objective.",
        "details": [ ... ],
        "source": "template"
      }
    }
    ```

---

### 9. Unified Condition Report & Download
- **`GET /api/reports/{product_id}`**
  - Combines product, condition profile, recommendations, impact estimates, assumptions, and data gaps.
- **`GET /api/reports/{product_id}/download`**
  - Returns the complete report as a downloadable attachment (`reloop_report_{id}.json`).

---

## 🧪 Testing

The backend includes a comprehensive test suite of 175 tests covering golden optimizer fixtures, AI explanation guardrails, API contracts, and security hardening.

```bash
cd backend
python -m pytest
```

---

## 🔬 Demo Validation & Smoke Tests

### 1. Demo Case Validation Suite
Runs all 4 canonical demo cases through the real API end-to-end, asserts expected pathways, and outputs a structured pass/fail table:

```bash
# Run against in-process FastAPI engine:
python scripts/validate_demo_case.py

# Or run against live server:
python scripts/validate_demo_case.py --base-url http://localhost:8000
```

### 2. Deployment Smoke Test
Verifies `/health` endpoint and executes an end-to-end lifecycle on a sample device:

```bash
python scripts/smoke_test.py --base-url http://localhost:8000
```

---

## 🛡️ Fallback & Offline Mode

ReLoop AI supports reliable demo execution and offline resilience:
- **`DEMO_FALLBACK=true`**: Serves precomputed demo fixtures labeled with `source: "sample-data"`.
- **Automatic Fallback on AI Failure**: If a Gemini API call encounters a transient failure or unconfigured API key for a recognized demo model, ReLoop AI falls back to structured demo data with explicit provenance (`source: "sample-data"`), preventing runtime crashes while maintaining strict evidence boundaries.
- **Guardrail Protection**: Fallback mode is never used silently outside explicit configuration or verified demo model paths.
