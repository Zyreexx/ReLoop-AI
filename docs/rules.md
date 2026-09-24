# ReLoop AI — Engineering Rules

## 1. Core Boundaries
### Always
- Treat ReLoop as product-life extension and circular decision support.
- Keep visual, diagnostic, user-report, database, and estimate evidence separate.
- Prefer repair/upgrade/refurbishment/reuse/component recovery before recycling when feasible.
- Make the optimizer the core product.

### Never
- Add waste collection, smart bins, garbage routing, segregation, or disposal management as core features.
- Claim a photograph proves internal battery, SSD, motherboard, RAM, or other invisible health.
- Present model estimates as measured outcomes.
- Let the LLM invent diagnostics.

## 2. AI Boundaries
### AI may
- Identify likely product/model.
- Detect visible damage.
- Read visible labels when legible.
- Parse symptoms.
- Structure evidence.
- Explain a recommendation using supplied evidence.
- Suggest candidate pathways for evaluation.

### AI may not
- Invent battery health, SSD health, RAM results, temperatures, cycles, etc.
- Claim invisible components are healthy from an exterior photo.
- Override hard eligibility/safety rules.
- Produce final pathway scores.
- Invent prices, repair times, environmental savings, or life extension without labelled assumptions/sources.

### Preferred language
Use: “Visible damage detected”, “Based on available diagnostics”, “User-reported”, “Estimated”, “Modelled estimate”, “Insufficient evidence”.

Avoid absolute claims such as “The motherboard is healthy” when only indirect evidence exists.

## 3. Evidence
Important condition claims should carry:
- source_type
- source_reference
- value
- confidence
- timestamp where relevant

## 4. Decision Engine
Evaluate:
1. Repair
2. Upgrade
3. Refurbish
4. Reuse/redeploy
5. Component recovery
6. Recycling

The scoring engine must be deterministic, normalized, reproducible, and explainable.

## 5. Error Handling
Frontend:
- Actionable validation
- No raw stack traces
- Preserve form data on failure
- Loading/retry states
- Prevent duplicate submissions

Backend:
- Typed errors for invalid inputs, unsupported models, invalid diagnostics, AI failures, missing evidence, and invalid pathway calculations.

Example:
```json
{
  "error": {
    "code": "INVALID_DIAGNOSTIC",
    "message": "Full-charge capacity cannot exceed design capacity.",
    "field": "battery.full_charge_capacity"
  }
}
```

If AI fails, never fabricate an answer. Allow manual confirmation/input where possible.

## 6. Validation
- Full-charge capacity cannot exceed design capacity.
- Percentages must be in valid ranges.
- Cycle count must be non-negative.
- Required evidence must exist before a pathway depending on it is scored.
- Unsupported models must be clearly identified.
- Validate uploaded file type/size server-side.

## 7. Security
- Never commit API keys.
- Use `.env` locally and deployment secrets remotely.
- Do not log uploaded images/reports unnecessarily.
- Never expose database credentials to the frontend.
- Validate uploads.
- Sanitize filenames/user text.
- Separate demo data from real user data.

## 8. Library Rules
### Prefer
Next.js, React, TypeScript, Tailwind CSS, FastAPI, Pydantic, PostgreSQL, SQLAlchemy/SQLModel, Recharts, official Gemini SDK/API, standard Python libraries.

### Avoid for MVP
LangChain without a concrete requirement, complex agent frameworks, vector databases, custom ML training, TensorFlow/PyTorch training pipelines, microservices, Kubernetes, event buses, multiple databases, and heavy state-management libraries when simpler React state/context is sufficient.

Use the simplest reliable tool that solves the requirement.

## 9. Frontend
- TypeScript strict mode
- Reusable components
- Dedicated API client
- Business calculations outside UI components
- Accessible forms
- Semantic HTML
- Loading/empty/success/error states
- Backend remains source of truth

## 10. Backend
- Thin route handlers
- Business logic in services
- Optimization in optimizer module
- Pydantic validation
- Typed returns
- Versioned AI prompts
- AI provider code separate from scoring logic

## 11. Data Discipline
Every estimate must carry assumptions. Avoid fake precision.

Example:
`Expected life extension: 2–3 years`
`Basis: model estimate`
`Assumptions: compatible battery available; thermal issue is serviceable; no latent critical fault`

## 12. Demo
Use a controlled set of known laptop models and realistic cases. Maintain:
- one healthy-ish device
- one repairable device
- one borderline device
- one component-recovery case

The demo must be reproducible without unpredictable live data.

## 13. Scope
> A smaller working circular decision engine is better than a larger collection of unfinished AI features.
