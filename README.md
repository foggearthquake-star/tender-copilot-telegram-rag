# Tender Copilot

Telegram-first AI copilot for analyzing tender documentation. Uploads a tender PDF or DOCX, gets a structured **GO / REVIEW / NO_GO** decision with evidence citations and a draft bid in 15–20 minutes — down from several hours of manual reading.

Production. Paid B2B use case.

---

## What it does

- **Ingests tender documents** — PDF, DOCX, and scanned pages (OCR via Tesseract through PyMuPDF)
- **Builds a per-tender RAG index** — chunking, embeddings, vector search in pgvector
- **Scores the tender** — three-stage LLM pipeline produces GO / REVIEW / NO_GO with structured rationale: company fit, document completeness, risk factors
- **Cites the source** — every claim is grounded in a chunk of the original document; the bot returns evidence quotes alongside the decision
- **Generates a bid draft** — structured PDF skeleton based on the tender's stated requirements

---

## Architecture

```
Telegram
   │
   ▼
Aiogram 3 handlers ───► FastAPI internal API
                              │
                              │ enqueue
                              ▼
                       Celery + Redis
                              │
        ┌─────────────────────┼─────────────────────────┐
        ▼                     ▼                         ▼
   Document parser     Embedding + index         LLM scoring
   (PyMuPDF, OCR)      (pgvector)                (3-stage)
                                                       │
                                                       ▼
                                             Report generator
                                             (ReportLab PDF)
                                                       │
                                                       ▼
                                          Telegram reply with
                                          decision + citations
                                          + PDF attachment
```

---

## Engineering decisions

**Citations are mandatory.** No claim ships without a quote from the source document. If the retriever finds nothing relevant, the decision is forced to REVIEW — not a confident GO/NO_GO.

**Three-stage scoring, not one prompt.** Splitting the decision into company-fit / completeness / risk lets each stage have its own retrieval, its own prompt, and its own eval. A single 4K-token "judge everything" prompt is unreliable and untestable.

**Graceful degradation.** LLM timeout or 5xx does not crash the run — the decision is downgraded to REVIEW with a warning, and the user gets a partial report with whatever evidence was retrieved.

**Idempotent jobs.** Same document, same config → same result. Retries are safe; audit log records every step with timestamps.

**Async-first.** Tender PDFs are 50–300 pages. Synchronous parsing would block the Telegram event loop and time out webhooks. All heavy work runs in Celery.

---

## Observed metrics (internal test set)

| Metric | Value |
|---|---|
| Decision accuracy (vs. human ground truth) | 100% |
| Avg. confidence on correct decisions | 77% |
| Citation coverage (claims with evidence) | 100% |
| LLM API cost per tender | < $0.10 |
| End-to-end latency per tender | 15–20 min |

---

## Tech stack

- **Language / runtime:** Python 3.13
- **Bot:** Aiogram 3 (long polling)
- **API:** FastAPI
- **Storage:** PostgreSQL 16 + pgvector
- **Queue:** Celery + Redis
- **Document parsing:** PyMuPDF, pytesseract (for scanned pages)
- **Reporting:** ReportLab
- **LLM:** OpenAI-compatible API (provider-agnostic)
- **Validation:** Pydantic v2

---

## Quick start

```bash
git clone https://github.com/foggearthquake/tender-copilot-telegram-rag
cd tender-copilot-telegram-rag

cp .env.example .env   # BOT_TOKEN, OPENAI_API_KEY, DATABASE_URL, REDIS_URL
pip install -r requirements.txt

# Start dependencies
docker compose up -d postgres redis
alembic upgrade head

# Run bot + worker
python -m bot &
celery -A app.tasks worker --loglevel=info
```

---

## Repo layout

```
bot/             # Aiogram handlers, FSM
app/
  rag/           # parsing, chunking, embeddings, retrieval
  scoring/       # 3-stage LLM scoring pipeline
  reports/       # ReportLab PDF generator
  tasks/         # Celery jobs
  db/            # models, migrations
  core/          # config, logging, telemetry
tests/
```

---

**Author:** Ainur Gabdraupov — AI Architect / AI Engineer
[gabdra.pw](https://gabdra.pw) · [github.com/foggearthquake](https://github.com/foggearthquake)
