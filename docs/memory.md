# ReLoop AI — Project Memory

## Identity
**Name:** ReLoop AI  
**Tagline:** The Next-Life Engine for Products  
**Category:** Circular Economy Solutions  
**Initial category:** Laptops

> ReLoop does not manage waste. It manages the life of products.

## Problem
Products are often replaced when one or a few components fail, causing premature replacement and loss of usable product/component value.

Core question:
> What is the highest-value next action for this product, in this condition, for this user?

## Product Concept
ReLoop combines:
1. Product photos
2. Device diagnostics
3. User-reported symptoms

It creates a component-level condition profile and evaluates:
1. Repair
2. Upgrade
3. Refurbish
4. Reuse/Redeploy
5. Component Recovery
6. Recycling when higher-value pathways are no longer viable

The central innovation is the **Circular Path Optimizer** / next-life decision engine.

## Critical Technical Decision
A single photograph cannot reliably determine internal battery, SSD, motherboard, RAM, or other invisible electronic health.

Therefore:
- Vision = visible condition/product identification
- Diagnostics = functional evidence
- User symptoms = reported behavior
- Product database = known specifications/compatibility
- Deterministic engine = final pathway decision

Never claim otherwise.

## AI Role
AI can:
- Identify products from photos
- Extract visible damage
- Parse symptoms
- Structure evidence
- Explain recommendations

AI cannot:
- Invent diagnostics
- Diagnose invisible internal health from a photo
- Override decision rules
- Produce unsupported measurements
- Directly choose the final pathway without deterministic scoring

## Decision Engine
```text
Circular Value =
    w1 × LifeExtension
  + w2 × ProductValueRetained
  + w3 × MaterialRetained
  + w4 × EnvironmentalBenefit
  - w5 × Cost
  - w6 × Logistics
```

Objectives:
- Lowest cost
- Maximum life extension
- Environmental benefit
- Fastest recovery

## MVP
Laptop-first vertical slice supporting 3–5 known/demo models:
- Photo upload
- Model confirmation
- Visible damage
- Diagnostic input/report
- Symptom capture
- Condition profile
- Pathway generation
- Deterministic optimization
- Explainable recommendation
- Impact/assumption view

## Demo Scenario
A 4–5-year-old laptop has:
- Weak battery
- Minor keyboard damage
- Healthy SSD
- Passing RAM test
- Thermal throttling

Expected direction:
Battery replacement + keyboard repair/replacement + thermal service, while retaining healthy components and enabling a second life where appropriate.

## Positioning
ReLoop is not:
- Waste management
- Smart bins
- Garbage routing
- A generic repair chatbot
- A Digital Product Passport by itself
- A marketplace by itself

ReLoop is:
> A condition-aware product-lifecycle decision and optimization layer.

## Technology
- Next.js
- React
- TypeScript
- Tailwind CSS
- FastAPI
- Python
- Pydantic
- Gemini multimodal API
- PostgreSQL
- SQLAlchemy/SQLModel
- Recharts
- Vercel + Render/Railway

## Design
Fixed Apple Store India-inspired implementation palette:
- `#F5F5F7` background
- `#FFFFFF` surface
- `#1D1D1F` primary text
- `#6E6E73` secondary text
- `#0071E3` action blue
- `#D2D2D7` border
- `#34C759` success
- `#FF9F0A` warning
- `#FF3B30` danger

The interface should be clean, spacious, product-first, restrained, and human-made rather than futuristic or “AI-looking”.

## Non-Negotiables
1. Circular economy is not waste management.
2. A photo is not an internal hardware diagnosis.
3. LLM is not the final decision-maker.
4. Evidence must remain traceable.
5. Estimates must expose assumptions.
6. Optimizer is the core product.
7. Laptop-first MVP.
8. Complete vertical slice before breadth.

## Future
- More laptop models
- Batch institutional inventory
- Smartphones/tablets
- Appliances
- Industrial equipment
- Repair/refurbisher integrations
- Digital Product Passport interoperability
- Predictive maintenance
- Component reuse networks
