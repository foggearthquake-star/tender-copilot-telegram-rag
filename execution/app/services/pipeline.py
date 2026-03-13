from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from app.core.audit import append_run_audit
from app.core.config import settings
from app.reporting.pdf_report import PdfReportService
from app.schemas.models import (
    BidDraftOutline,
    CompanyProfile,
    DecisionReport,
    DecisionStatus,
    StageLog,
    TenderFacts,
    TenderInput,
    TenderRun,
)
from app.services.bid_writer import BidWriter
from app.services.decision_engine import DecisionEngine
from app.services.llm_service import LLMService
from app.services.normalizer import normalize_facts
from app.services.parsers import chunk_text, parse_document
from app.services.vector_service import VectorService


class TenderPipeline:
    def __init__(self) -> None:
        self.vector_service = VectorService()
        self.decision_engine = DecisionEngine()
        self.bid_writer = BidWriter()
        self.report_service = PdfReportService()
        self.llm_service = LLMService()

    def _start_stage(self, run: TenderRun, stage: str, meta: dict[str, str] | None = None) -> int:
        run.stages.append(StageLog(stage=stage, meta=meta or {}))
        return len(run.stages) - 1

    def _finish_stage(self, run: TenderRun, idx: int, status: str = "completed", error: str | None = None) -> None:
        stage = run.stages[idx]
        stage.ended_at = datetime.now(UTC)
        stage.duration_ms = int((stage.ended_at - stage.started_at).total_seconds() * 1000)
        stage.status = status
        stage.error = error

    def run(self, profile: CompanyProfile, files: list[str], deadline: str | None, price_hint_rub: float | None, comment: str | None) -> TenderRun:
        run_start = perf_counter()
        tender_id = uuid.uuid4().hex[:10]
        tender_input = TenderInput(
            tender_id=tender_id,
            uploaded_files=files,
            deadline=deadline,
            price_hint_rub=price_hint_rub,
            comment=comment,
        )
        run = TenderRun(run_id=uuid.uuid4().hex, tender_input=tender_input, status="upload_received")

        try:
            parsed_texts: list[str] = []
            user_draft_text: str | None = None
            parse_idx = self._start_stage(run, "documents_parsed", {"files_count": str(len(files))})
            for file_path in files:
                result = parse_document(Path(file_path))
                if result.is_empty:
                    run.warnings.append(f"empty_text_extraction: {result.doc_name}")
                if result.used_ocr:
                    run.warnings.append(f"ocr_used: {result.doc_name}")
                if result.text:
                    parsed_texts.append(result.text)
                    chunks = chunk_text(result.text)
                    if chunks:
                        self.vector_service.index_chunks(tender_id, result.doc_name, chunks)
                low_name = result.doc_name.lower()
                if any(tag in low_name for tag in ["черновик", "draft", "proposal", "заявк"]):
                    user_draft_text = result.text
            self._finish_stage(run, parse_idx, status="completed")
            run.status = "chunks_indexed"

            company_idx = self._start_stage(run, "company_context_indexed")
            if profile.knowledge_text.strip():
                company_chunks = chunk_text(profile.knowledge_text, chunk_size=800, overlap=100)
                if company_chunks:
                    self.vector_service.index_chunks(tender_id, "company_profile.docx", company_chunks)
            self._finish_stage(run, company_idx, status="completed")

            facts_idx = self._start_stage(run, "facts_normalized")
            facts = normalize_facts(parsed_texts)
            if not facts.contract_value_rub and price_hint_rub:
                facts.contract_value_rub = price_hint_rub
            if not facts.deadline and deadline:
                facts.deadline = deadline
            run.facts = facts
            self._finish_stage(run, facts_idx, status="completed")
            run.status = "facts_normalized"

            decision_idx = self._start_stage(run, "decision_ready")
            tender_query = (
                f"тендер: предмет={facts.tender_subject or ''}; обязательства={' ; '.join(facts.obligations)}; "
                f"поставка={' ; '.join(facts.deliverables)}; критерии={' ; '.join(facts.evaluation_criteria)}; "
                f"сертификаты={' ; '.join(facts.required_certificates)}; условия={facts.payment_terms or ''}"
            )
            tender_evidence = self.vector_service.retrieve(tender_id, tender_query, top_k=6)
            company_query = (
                f"компания: опыт, компетенции, проекты, специализация, категории={' ; '.join(profile.categories)}; "
                f"фокус={' ; '.join(profile.focus_areas)}; предмет тендера={facts.tender_subject or comment or ''}; "
                f"обязательства={' ; '.join(facts.obligations)}; поставка={' ; '.join(facts.deliverables)}"
            )
            company_evidence = self.vector_service.retrieve(tender_id, company_query, top_k=5) if profile.knowledge_text.strip() else []
            retrieved = tender_evidence + company_evidence

            decision = self.decision_engine.decide(profile, facts, retrieved)
            decision_payload = decision.model_dump(mode="json")
            try:
                refined_decision_payload, decision_tokens = self.llm_service.refine_decision(
                    decision_payload=decision_payload,
                    context_payload={
                        "profile": profile.model_dump(mode="json"),
                        "facts": facts.model_dump(mode="json"),
                        "tender_evidence": [x.text[:350] for x in tender_evidence],
                        "company_evidence": [x.text[:350] for x in company_evidence],
                    },
                )
                decision = decision.model_validate(refined_decision_payload)
                if decision_tokens > 0:
                    decision.cost_estimate_rub = round(decision.cost_estimate_rub + (decision_tokens / 1000.0) * 0.2, 2)
            except Exception as llm_exc:
                run.warnings.append(f"llm_decision_refine_failed: {llm_exc}")
            run.decision = decision
            self._finish_stage(run, decision_idx, status="completed")
            run.status = "decision_ready"

            outline_idx = self._start_stage(run, "bid_draft_ready")
            outline = self.bid_writer.build_outline(profile, facts, decision, user_draft_text=user_draft_text)
            try:
                outline_payload, outline_tokens = self.llm_service.enrich_bid_outline(
                    outline_payload=outline.model_dump(mode="json"),
                    context_payload={
                        "profile": profile.model_dump(mode="json"),
                        "facts": facts.model_dump(mode="json"),
                        "decision": decision.model_dump(mode="json"),
                        "user_draft_text": user_draft_text or "",
                    },
                )
                outline = outline.model_validate(outline_payload)
                if outline_tokens > 0:
                    decision.cost_estimate_rub = round(decision.cost_estimate_rub + (outline_tokens / 1000.0) * 0.2, 2)
            except Exception as llm_exc:
                run.warnings.append(f"llm_outline_enrich_failed: {llm_exc}")
            run.bid_outline = outline
            self._finish_stage(run, outline_idx, status="completed")
            run.status = "bid_draft_ready"

            report_idx = self._start_stage(run, "report_ready")
            report_path = Path(settings.reports_dir) / f"report_{tender_id}.pdf"
            run.report_path = self.report_service.build_report(report_path, profile, facts, decision, outline)
            self._finish_stage(run, report_idx, status="completed")
            run.status = "report_ready"
        except Exception as exc:
            fail_idx = self._start_stage(run, "failed")
            self._finish_stage(run, fail_idx, status="failed", error=str(exc))
            run.status = "failed"
            if not run.facts:
                run.facts = TenderFacts()
            if not run.decision:
                run.decision = DecisionReport(
                    status=DecisionStatus.REVIEW,
                    confidence=0.31,
                    confidence_reason="Пайплайн завершился с ошибкой; требуется ручная проверка.",
                    overall_score=20,
                    fit_score=20,
                    evidence_score=0,
                    completeness_score=20,
                    risk_score=70,
                    reasons=["Во время обработки возникла техническая ошибка."],
                    risks=["Недостаточность данных для автоматического решения."],
                    evidence=[],
                    next_actions=["Проверить документы и повторить запуск.", "Проверить логи запуска у оператора."],
                    latency_ms=0,
                    cost_estimate_rub=0.0,
                )
            if not run.bid_outline:
                run.bid_outline = BidDraftOutline(
                    title="Черновик недоступен",
                    required_sections=["Повторить анализ после устранения ошибки"],
                    recommended_sections=["Проверить корректность входных файлов"],
                    missing_information=["Технический запуск завершился ошибкой"],
                    submission_checklist=["Запустить анализ повторно"],
                )
        finally:
            run.run_finished_at = datetime.now(UTC)
            run.total_duration_ms = int((perf_counter() - run_start) * 1000)
            append_run_audit(run)
        return run
