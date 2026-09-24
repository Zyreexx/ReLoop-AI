# ReLoop AI — Architecture

## 1. Architecture Goals
- Separate AI interpretation from deterministic decision-making.
- Preserve evidence provenance.
- Make the laptop MVP easy to demo.
- Keep product-category knowledge modular.
- Avoid unnecessary infrastructure.
- Allow later expansion to other durable products.

## 2. High-Level Flow
```text
USER
  |
  +--> Product Photos --------> Vision / Product Identification
  |
  +--> Diagnostic Report -----> Diagnostic Normalization
  |
  +--> User Symptoms ---------> Symptom Parsing
                                  |
                                  v
                           CONDITION PROFILE
                                  |
                                  v
                       CIRCULAR PATH GENERATION
                                  |
                                  v
                       DETERMINISTIC OPTIMIZER
                                  |
                                  v
                     EXPLAINABLE RECOMMENDATION
                                  |
                +-----------------+----------------+
                |                 |                |
              Repair            Reuse          Recovery
                |                 |                |
          Upgrade/Refurbish   Second Life       Recycle*
```
`*Only when higher-value pathways are no longer technically/economically feasible.`

## 3. AI vs Decision Engine

### AI layer
Responsible for:
- Product identification from images
- Visible-damage extraction
- Symptom parsing
- Natural-language explanation

Not responsible for:
- Inventing measurements
- Declaring invisible component health from a photo
- Final pathway scoring
- Unsupported cost/impact values

### Deterministic layer
Python is responsible for:
- Input validation
- Pathway eligibility
- Metric normalization
- Weighted scoring
- Reproducible recommendation

## 4. Tech Stack
- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI, Pydantic
- **AI:** Gemini multimodal model/API
- **Database:** PostgreSQL
- **ORM/data layer:** SQLAlchemy or SQLModel
- **Decision engine:** Plain Python
- **Charts:** Recharts
- **Deployment:** Vercel + Render/Railway + PostgreSQL

## 5. Folder Structure
```text
reloop-ai/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docs/
│   ├── prd.md
│   ├── architecture.md
│   ├── rules.md
│   ├── phases.md
│   ├── design.md
│   └── memory.md
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── scan/
│   │   ├── product/
│   │   ├── diagnostics/
│   │   ├── assessment/
│   │   ├── recommendation/
│   │   └── report/
│   ├── components/
│   │   ├── ui/
│   │   ├── product/
│   │   ├── diagnostics/
│   │   ├── assessment/
│   │   └── recommendation/
│   ├── lib/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── utils.ts
│   └── public/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/routes/
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── services/
│   │   ├── ai/
│   │   │   ├── prompts/
│   │   │   └── gemini_client.py
│   │   ├── optimizer/
│   │   │   ├── scorer.py
│   │   │   ├── pathways.py
│   │   │   └── rules.py
│   │   ├── knowledge/
│   │   └── db/
│   └── requirements.txt
├── data/
│   ├── demo/
│   ├── products/
│   └── schemas/
└── scripts/
    ├── seed_demo_data.py
    └── validate_demo_case.py
```

## 6. Main Data Objects
### Product
`id, manufacturer, model, model_year, category, serial_or_identifier, age`

### Evidence
`id, product_id, type, source, value, confidence, timestamp`

### ComponentCondition
`component, status, observations, measurements, confidence, evidence_ids`

### Pathway
`type, eligibility, estimated_cost, expected_life_extension, value_retained, material_retained, environmental_estimate, logistics, assumptions`

### Recommendation
`selected_pathway, objective, score, alternative_pathways, reasoning, evidence_ids, assumptions`

## 7. Recommendation Pipeline
```text
Raw input
→ Normalize
→ Validate
→ Create evidence records
→ Build condition profile
→ Generate eligible pathways
→ Calculate pathway metrics
→ Apply user objective weights
→ Rank deterministically
→ Generate explanation
→ Return recommendation + evidence + assumptions
```

## 8. Scoring
```text
Circular Value =
    w1 × LifeExtension
  + w2 × ProductValueRetained
  + w3 × MaterialRetained
  + w4 × EnvironmentalBenefit
  - w5 × Cost
  - w6 × Logistics
```
Normalize metrics before weighting. The LLM must not directly choose the final score.

## 9. MVP API
```text
POST /api/products/identify
POST /api/vision/analyze
POST /api/diagnostics/validate
POST /api/symptoms/parse
POST /api/assessment/build
POST /api/recommendations/generate
GET  /api/products/{id}
GET  /api/reports/{id}
```

## 10. Deployment Boundary
One Next.js frontend + one FastAPI backend + one PostgreSQL database + one external multimodal AI API.

Do not split the MVP into microservices.
