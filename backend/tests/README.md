# ReLoop AI — Backend Test Suite & Golden Fixtures

This directory contains the automated test suite for the ReLoop AI backend services, API routes, database persistence layer, AI guardrails, and deterministic optimizer engine.

---

## 1. Directory Structure

- `golden/`: JSON fixtures locking down the expected behavior and full pathway rankings for all 4 demo cases across all 4 optimization objectives (16 matrix points).
  - `demo_01_healthy.json`: Golden expectations for healthy corporate workhorse.
  - `demo_02_repairable.json`: Golden expectations for repairable enterprise laptop (battery, thermal & keyboard wear).
  - `demo_03_borderline.json`: Golden expectations for borderline 5-year fleet unit.
  - `demo_04_component_recovery.json`: Golden expectations for catastrophic motherboard failure with salvageable subcomponents.
  - `regenerate_fixtures.py`: Script to regenerate all golden fixtures when the scoring model is intentionally modified.
- `test_optimizer_golden.py`: Golden regression tests and mathematical property tests (determinism, permutation invariance, ineligibility ordering).
- `test_optimizer.py`: Unit tests for circular rules, scoring formulas, and zero-AI boundaries.
- `test_demo_cases.py`: High-level scenario tests for the 4 canonical demo profiles.
- `test_explanation_guardrail.py`: AI explanation post-generation numeric guardrail and deterministic fallback tests.
- `test_ai_provider.py`: Gemini client JSON validation, retries, and error handling.
- `test_persistence.py`: SQLite / PostgreSQL repository layer CRUD tests.
- `test_reports.py`: Unified condition report and download endpoint tests.
- `test_vision_routes.py`: Multimodal vision inspection endpoints.
- `test_api_routes.py`: Product and recommendation API endpoints.
- `test_diagnostics_validation.py`: Telemetry and diagnostic input validation tests.
- `test_knowledge_loader.py`: Knowledge catalog and model specification tests.
- `test_health.py`: Root `/health` and `/api/health` probes.

---

## 2. Running Tests

Run the full test suite using `pytest`:

```bash
cd backend
pytest
```

Run only the golden optimizer regression and property tests:

```bash
cd backend
pytest tests/test_optimizer_golden.py
```

---

## 3. Optimizer Golden Fixtures & Behavioral Lockdown

### Core Principle
The Circular Path Optimizer (`app/optimizer/`) is a 100% deterministic Python calculation. It evaluates 6 circular pathways (`REPAIR`, `UPGRADE`, `REFURBISH`, `REUSE`, `COMPONENT_RECOVERY`, `RECYCLE`) across 4 objectives (`LOWEST_COST`, `MAX_LIFE`, `ENVIRONMENTAL`, `FASTEST_RECOVERY`).

Golden tests lock down:
1. **Selected Pathway**: The top-ranked circular action chosen for each scenario.
2. **Ranked Pathway Ordering**: The exact 1st through 6th rank order of all pathways.
3. **Deterministic Scores**: Normalized scores computed from life extension, retained value, retained material, avoided CO2e, cost, and logistics turnaround.

### Property Invariants Tested
- **Pure Determinism**: Identical inputs run repeatedly produce identical scores, ranks, and selections.
- **Permutation Invariance**: Reordering component records in the condition profile has zero effect on the optimizer output.
- **Ineligible Pathway Demotion**: Pathways marked ineligible (e.g. `REPAIR` for healthy units, `UPGRADE` for soldered units, `RECYCLE` when higher loops are viable) receive penalties and always rank below all eligible pathways.

---

## 4. How to Intentionally Regenerate Golden Fixtures

When optimizer weights, eligibility rules, or normalization formulas are intentionally changed and approved as part of an architecture update:

1. Verify and test the logic changes inside `app/optimizer/`.
2. Run the regeneration script from the `backend/` directory:
   ```bash
   cd backend
   python tests/golden/regenerate_fixtures.py
   ```
3. Inspect the `git diff` on `tests/golden/*.json` to confirm that ranking and score changes match the intentional design updates.
4. Run `pytest` to confirm all tests pass against the newly generated fixtures.
5. Commit both the optimizer changes and the updated golden fixtures together.
