# Finalization Checklist (v1)

## Product Readiness
- [x] Telegram-first UX with profile wizard and tender flow
- [x] Decision statuses: GO / REVIEW / NO_GO
- [x] Explainability with evidence fragments and quotes
- [x] Bid draft outline with required/recommended/missing/checklist
- [x] PDF report export and JSON export

## Engineering Readiness
- [x] Schema-first contracts and synchronized docs
- [x] Ingestion for PDF/DOCX with fallback handling
- [x] Vector retrieval with local + qdrant + pinecone adapters
- [x] LLM integration with retry/backoff and safe fallback
- [x] Stage-level observability (run_id, timings, statuses, errors)
- [x] Audit trail JSONL logging

## Quality Readiness
- [x] Unit + resilience tests passing
- [x] Eval script with baseline metrics
- [x] README with runbook, commands, and limits

## Manual Release Steps
- [ ] Rotate production secrets after sharing in chats
- [ ] Record demo video 3-5 min using real scenario
- [ ] Add screenshots/GIF to README for portfolio impact
