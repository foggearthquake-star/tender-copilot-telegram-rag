import json
from pathlib import Path

from app.schemas.models import CompanyProfile, TenderFacts
from app.services.decision_engine import DecisionEngine
from app.services.vector_service import VectorRecord


def run_eval(dataset_path: Path) -> dict:
    rows = json.loads(dataset_path.read_text(encoding="utf-8-sig"))
    engine = DecisionEngine()

    total = len(rows)
    matched = 0
    confidence_sum = 0.0
    latency_sum = 0
    cost_sum = 0.0
    evidence_cov_sum = 0.0

    evidence_stub = [VectorRecord("id", "eval.txt", "chunk_1", "требования и сроки", [0.1] * 96)]

    for row in rows:
        profile = CompanyProfile(**row["profile"])
        facts = TenderFacts(**row["facts"])
        report = engine.decide(profile, facts, evidence_stub)
        if report.status.value == row["expected_status"]:
            matched += 1
        confidence_sum += report.confidence
        latency_sum += report.latency_ms
        cost_sum += report.cost_estimate_rub
        evidence_cov_sum += 1.0 if report.evidence else 0.0

    return {
        "cases": total,
        "status_accuracy": round(matched / total, 3) if total else 0,
        "avg_confidence": round(confidence_sum / total, 3) if total else 0,
        "evidence_coverage": round(evidence_cov_sum / total, 3) if total else 0,
        "avg_latency_ms": round(latency_sum / total, 2) if total else 0,
        "avg_cost_estimate_rub": round(cost_sum / total, 2) if total else 0,
    }


if __name__ == "__main__":
    dataset = Path("execution/data/eval_dataset.json")
    metrics = run_eval(dataset)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

