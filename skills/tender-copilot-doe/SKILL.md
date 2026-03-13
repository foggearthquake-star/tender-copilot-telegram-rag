---
name: tender-copilot-doe
description: Use when building or evolving the Tender Copilot + Bid Writer project with DOE workflow (Directions -> Orchestration -> Execution), including Telegram flow, schema-first contracts, RAG retrieval, decision engine GO/REVIEW/NO_GO, explainability, and PDF reporting.
---

# Tender Copilot DOE Skill

Use this skill for tasks in this repository related to Tender Copilot implementation and planning.

## When to trigger
- User asks to implement or refine Tender Copilot / Bid Writer features.
- Work includes Telegram bot UX, document ingestion (PDF/DOCX), decisioning, evidence, bid draft, or reporting.
- User asks to follow project method from `COdex.md`.

## Mandatory workflow
1. Read `COdex.md`.
2. Ensure `directions/` documents are present and aligned with requested scope.
3. Ensure an `orchestration/` plan exists before coding.
4. Only then implement inside `execution/`.

Do not skip this sequence.

## Repository contract
- `directions/`: policies, SOP, constraints, acceptance criteria.
- `orchestration/`: pipeline/state plan, data contracts, decomposition.
- `execution/`: runnable code, scripts, tests, configs.

## Product defaults (v1)
- Language: Russian.
- Input: manual document upload only.
- Output statuses: `GO`, `REVIEW`, `NO_GO`.
- Explainability required: reasons + evidence (doc fragment references + quote).
- Delivery format: Telegram messages + PDF report.

## Required data contracts (schema-first)
Keep/extend these entities in code:
- `CompanyProfile`
- `TenderInput`
- `TenderFacts`
- `DecisionReport`
- `BidDraftOutline`
- `EvidenceItem`

If adding fields, update:
- schema models
- orchestration contracts document
- tests

## Implementation checklist
- Ingestion handles both PDF and DOCX with parse fallback.
- Retrieval supports local mode and optional vector backend.
- Decision engine applies hard blockers and review triggers.
- Bid writer returns required/recommended sections + missing info.
- Report generator creates PDF with summary, reasons, risks, evidence, next steps.
- Reliability includes retries/backoff for external operations.
- Metrics include latency and cost estimate placeholders.

## Definition of done
- Full Telegram flow works from profile setup to report export.
- Unit/integration tests pass.
- README explains architecture, KPI, limits, and run instructions.

## File hygiene rules
- Prefer small cohesive modules in `execution/app/*`.
- Keep business logic deterministic where possible.
- Never introduce non-ASCII unless file already uses it.
- Update docs whenever behavior contracts change.
