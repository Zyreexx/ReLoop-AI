# ReLoop AI — Product Requirements Document

## 1. Product
**Name:** ReLoop AI  
**Positioning:** The Next-Life Engine for Products  
**Category:** Circular Economy Solutions  
**MVP:** Laptops

ReLoop AI is a product-lifecycle intelligence platform that combines product photos, device diagnostics, and user-reported symptoms to determine the highest-value next-life pathway for a product: repair, upgrade, refurbishment, reuse/redeployment, component recovery, or recycling when higher-value pathways are no longer viable.

> ReLoop does not manage waste. It manages the life of products.

The MVP must remain focused on product-life extension and value retention. It must not become a waste collection, smart-bin, waste-routing, segregation, or disposal-management product.

## 2. Problem
Products such as laptops are often replaced when one or a few components fail. A weak battery, damaged keyboard, thermal issue, or performance problem can lead to replacement even when many components remain usable.

The missing decision layer is:

> **What is the highest-value next action for this product, in this condition, for this user?**

## 3. Target Users
### Primary
Consumers with aging laptops deciding whether to repair, upgrade, refurbish, reuse, or replace.

### Secondary
- Colleges/universities managing device inventories
- Businesses managing IT assets
- Repair businesses
- Refurbishers
- Institutional asset managers
- Manufacturers/circular-economy programs in future versions

### MVP focus
Build one excellent consumer laptop workflow first. Keep the data model extensible for institutional inventory later.

## 4. MVP User Journey
1. Upload 2–3 laptop photos or enter/confirm model.
2. Vision AI identifies likely make/model and visible damage.
3. Upload a diagnostic report or enter available values.
4. Select symptoms and usage requirements.
5. ReLoop builds a component-level condition profile.
6. Generate feasible circular pathways.
7. Select an objective: lowest cost, maximum life, environmental benefit, or fastest recovery.
8. Deterministic engine scores pathways.
9. Present recommendation with evidence and explanation.
10. Optionally generate a second-life/redeployment scenario.
11. Optionally show component recovery when whole-product reuse is not viable.

## 5. Core Features

### P0 — Must Have
- Product/model identification with user confirmation and confidence
- Photo-based visible-damage assessment
- Diagnostic input/report for battery, SSD, RAM, thermals and system signals
- User symptom capture
- Component-level condition profile
- Circular Path Optimizer
- Explainable recommendation
- Impact/estimate view with explicit assumptions

### Circular pathways
1. Repair
2. Upgrade
3. Refurbish
4. Reuse/redeploy
5. Component recovery
6. Recycling when higher-value pathways are no longer technically/economically feasible

### Evidence types
Every condition claim must remain distinguishable as:
- Visual observation
- Diagnostic measurement
- User report
- Product/database fact
- Model estimate

## 6. Example Condition Profile
| Component | Evidence | Example |
|---|---|---|
| Battery | Design/full-charge capacity, cycles | 73% estimated health |
| SSD | SMART/health data | 91% health |
| RAM | Memory diagnostic | PASS |
| Thermals | Temperature/throttling | Service required |
| Display | Photo/visual inspection | No visible crack |
| Keyboard | Photo/user report | 2 missing keys |
| Hinge/chassis | Photo | Moderate damage |
| System/motherboard | Available diagnostics | No critical faults detected from available diagnostics |

Do not claim a photograph proves internal component health.

## 7. Secondary Features
### P1
- What-if controls
- Pathway comparison
- Second-life use-case suggestion
- Download/share condition report
- Small-batch inventory mode

### P2 / Future
- Smartphones/tablets
- Appliances/electronics
- Industrial equipment
- Manufacturer integrations
- Digital Product Passport interoperability
- Repair/refurbisher network integration
- Predictive maintenance
- Institutional portfolio optimization

## 8. Success Criteria
A judge should be able to:
1. Upload a laptop photo.
2. Confirm the model.
3. See visible issues.
4. Enter/upload diagnostics.
5. See a component condition profile.
6. Select an objective.
7. Compare circular pathways.
8. See a deterministic recommendation.
9. Understand the evidence behind it.
10. Understand why recycling is a later loop.

## 9. Out of Scope
- Universal laptop support
- Automatic physical repair
- Certified safety testing
- Medical/safety-critical diagnosis
- Waste collection/routing/segregation
- Smart bins
- Recycling operations
- Marketplace payments
- Guaranteed environmental savings
- Guaranteed life-extension predictions
