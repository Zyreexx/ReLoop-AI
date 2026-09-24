# ReLoop AI — Development Phases

Phases are required because ReLoop is being built as a hackathon MVP first and a scalable platform later. Finish a complete vertical slice before adding breadth.

## Phase 0 — Scope Freeze
Lock:
- Laptop category
- 3–5 supported demo models
- Photos + diagnostics + symptoms
- Circular pathway recommendation
- Deterministic Python scoring
- PostgreSQL
- Gemini multimodal API

**Done:** complete user journey can be explained in one diagram.

## Phase 1 — Foundation
Build:
- Repository
- Next.js
- FastAPI
- PostgreSQL
- Environment configuration
- Shared types/schemas
- Basic routing

**Done:** frontend can call backend and backend can persist a product record.

## Phase 2 — Product & Evidence Intake
Build:
- Photo upload
- Model confirmation
- Visible-damage analysis
- Diagnostic form/report
- Symptom input

**Done:** a product is represented as structured evidence.

## Phase 3 — Condition Profile
Build:
- Evidence normalization
- Component records
- Confidence labels
- Condition dashboard
- Evidence provenance

**Done:** Battery / SSD / RAM / Thermals / Display / Keyboard / Chassis / System are represented with evidence sources.

## Phase 4 — Circular Path Optimizer
Build:
- Eligibility rules
- Pathway metrics
- User objective
- Weighted scoring
- Alternatives
- Explanation data

**Done:** identical inputs produce reproducible recommendations.

## Phase 5 — Recommendation & Report
Build:
- Recommendation screen
- Evidence summary
- Objective
- Alternative pathways
- Estimated cost/life/value/impact
- Assumption panel
- Condition report

**Done:** a judge understands the recommendation without developer intervention.

## Phase 6 — Demo Polish
Build:
- Loading states
- Error handling
- Empty states
- Visual consistency
- Seed data
- Sample reports
- Backup demo path

**Done:** complete demo runs repeatedly without manual database edits.

## Phase 7 — Post-MVP
Only after the laptop workflow is stable:
- Batch inventory
- Second-life matching
- More laptop models
- Smartphones
- Appliances
- Repair/refurbisher integrations
- DPP interoperability
- Predictive maintenance

## Hackathon Priority
1. End-to-end happy path
2. Condition profile
3. Deterministic optimizer
4. Recommendation explanation
5. Vision integration
6. Diagnostics upload
7. Impact estimates
8. Polish
9. Future features

Never sacrifice the working recommendation engine to add another AI feature.
