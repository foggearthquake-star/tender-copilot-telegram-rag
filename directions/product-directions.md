# Product Directions: Tender Copilot + Bid Writer (Telegram-first)

## Product Goal
Provide a Russian-language Telegram assistant for manual tender document upload (PDF/DOCX) that returns:
- GO/REVIEW/NO_GO recommendation
- explainable evidence with citations
- structured bid draft outline
- downloadable PDF report

## Target User
Small/medium supplier teams in Russia preparing tender participation decisions.

## Core Scenario
1. User configures company profile via step-by-step wizard (`/company_setup`).
2. User uploads tender docs (`/new_tender`).
3. User confirms upload and enters optional metadata (deadline, price hint, comment).
4. System extracts key facts and runs decision engine.
5. User gets explainable decision and bid draft.
6. User exports PDF report (`/report`).

## Constraints
- Language: Russian only (v1).
- Source documents: manual upload only.
- Not a legal opinion; assistant is advisory.
- Solo-build MVP with practical portfolio focus.

## Acceptance KPIs
- Decision latency under 5 minutes per tender.
- Bid draft latency under 15 minutes.
- Evidence coverage: each key reason references at least one document fragment.
- Stable fallback for parse/retrieval errors with REVIEW status.

## Disclaimer
System outputs are analytical suggestions and must be validated by a qualified specialist before submission.
