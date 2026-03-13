# SOP: GO / REVIEW / NO_GO

## Status Definitions
- `GO`: critical checks passed, no blocking mismatch against company profile.
- `REVIEW`: insufficient or ambiguous data, or medium risks requiring manual validation.
- `NO_GO`: one or more hard blockers found.

## Hard Blockers (NO_GO)
- Required license/certificate missing in company profile.
- Budget exceeds company max contract limit.
- Payment terms conflict with company stop factors.
- Delivery region outside company service regions (if strict mode implied by profile).

## Review Triggers
- Missing deadline, budget, or requirement data in parsed facts.
- Low evidence quality (weak citations).
- Contradicting statements in different documents.

## Output Contract
Decision report includes:
- status
- confidence score (0..1) with explanation
- top reasons
- critical risks
- evidence list with document name + section/fragment + quote
- next actions
