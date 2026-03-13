# Non-Functional Directions

## Reliability
- Retry external operations with exponential backoff.
- Graceful fallback to heuristic mode when external AI/vector services unavailable.

## Observability
- Persist pipeline status transitions.
- Log latency and token/cost estimate fields for each run.
- Persist per-stage logs (`stage`, `duration_ms`, `status`, `error`) and expose recent runs in bot UX.

## Security
- Do not execute uploaded file content.
- Validate file extensions and parse defensively.
- Keep local storage JSON for MVP; no sensitive secrets in repository.
