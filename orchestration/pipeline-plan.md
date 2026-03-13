# Orchestration Plan

## Pipeline Stages
1. `upload_received`
2. `documents_parsed`
3. `facts_normalized`
4. `chunks_indexed`
5. `decision_ready`
6. `bid_draft_ready`
7. `report_ready`
8. `failed`

## State Machine
- Input: `CompanyProfile`, `TenderInput`
- Transition path: upload -> parse -> normalize -> retrieve -> decide -> explain -> draft -> export
- On parse/retrieval exception: fallback to REVIEW with reduced confidence and explicit warning.

## Components
- IngestionService: parse PDF/DOCX and chunk text.
- VectorService: local cosine search + optional qdrant/pinecone adapters.
- DecisionEngine: profile + facts + evidence => GO/REVIEW/NO_GO.
- BidWriter: deterministic outline generator with required/recommended sections.
- ReportService: PDF output with reasons, risks, evidence, next steps.

## Telegram Commands
- `/start`
- `/company_setup`
- `/new_tender`
- `/status`
- `/runs`
- `/decision`
- `/bid_draft`
- `/report`
- `/cancel`

## UX Notes
- `company_setup` is a step-by-step wizard, not raw JSON.
- `new_tender` flow: upload docs -> send `ГОТОВО` -> provide deadline, price hint, comment.
- `/help`
