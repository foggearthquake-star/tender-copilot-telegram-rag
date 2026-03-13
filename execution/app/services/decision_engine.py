from __future__ import annotations

from time import perf_counter

from app.schemas.models import CompanyProfile, DecisionReport, DecisionStatus, EvidenceItem, TenderFacts
from app.services.vector_service import VectorRecord


class DecisionEngine:
    def _keyword_overlap(self, profile: CompanyProfile, facts: TenderFacts) -> tuple[int, list[str], list[str]]:
        profile_terms = {
            *[x.lower() for x in profile.categories],
            *[x.lower() for x in profile.focus_areas],
        }
        knowledge_blob = " ".join(profile.project_examples + [profile.company_summary, profile.knowledge_text]).lower()
        tender_terms = [
            *(facts.obligations or []),
            *(facts.deliverables or []),
            *(facts.evaluation_criteria or []),
        ]
        matched: list[str] = []
        missing: list[str] = []
        for term in tender_terms:
            term_lower = term.lower()
            if term_lower in profile_terms or term_lower in knowledge_blob:
                matched.append(term)
            else:
                missing.append(term)
        return len(matched), matched[:5], missing[:5]

    def decide(self, profile: CompanyProfile, facts: TenderFacts, evidence_records: list[VectorRecord]) -> DecisionReport:
        start = perf_counter()
        reasons: list[str] = []
        risks: list[str] = []
        next_actions: list[str] = []
        status = DecisionStatus.GO
        confidence = 0.84
        confidence_reason = "Извлечены ключевые данные и найдены подтверждающие фрагменты из тендера и профиля компании."

        profile_capability_hits = [r for r in evidence_records if r.doc_name.startswith("company_profile")]
        tender_hits = [r for r in evidence_records if not r.doc_name.startswith("company_profile")]

        fit_score = 72
        completeness_score = 100
        evidence_score = 100 if tender_hits else 30
        risk_score = 15

        matched_count, matched_terms, missing_terms = self._keyword_overlap(profile, facts)
        if matched_terms:
            reasons.append("Профиль компании подтверждает релевантные компетенции под предмет тендера: " + ", ".join(matched_terms))
            fit_score += min(15, matched_count * 4)
        elif facts.obligations or facts.deliverables:
            reasons.append("Не найдено достаточно явных подтверждений, что профиль компании покрывает предмет тендера.")
            fit_score -= 10
            risk_score += 10

        if missing_terms:
            risks.append("Часть требований тендера не подтверждена профилем компании: " + ", ".join(missing_terms))
            next_actions.append("Проверить наличие опыта, кейсов или ресурсов по неподтвержденным требованиям.")

        if facts.contract_value_rub and profile.max_contract_value_rub > 0:
            ratio = facts.contract_value_rub / profile.max_contract_value_rub
            if ratio > 1:
                status = DecisionStatus.NO_GO
                reasons.append("Сумма контракта превышает лимит компании.")
                risks.append("Финансовая емкость компании ниже суммы тендера.")
                fit_score -= 35
                risk_score += 40
            elif ratio > 0.85:
                reasons.append("Сумма тендера близка к лимиту компании.")
                risks.append("Высокая нагрузка на бюджетный лимит компании.")
                fit_score -= 10
                risk_score += 15

        missing_certs = [c for c in facts.required_certificates if c not in {x.lower() for x in profile.required_certificates}]
        if missing_certs:
            status = DecisionStatus.NO_GO
            reasons.append("Не подтверждены обязательные лицензии или сертификаты.")
            risks.append(f"Отсутствуют обязательные документы: {', '.join(missing_certs)}")
            fit_score -= 25
            risk_score += 25

        if not facts.deadline:
            completeness_score -= 20
            reasons.append("Не извлечен дедлайн подачи заявки.")
            next_actions.append("Уточнить дедлайн подачи у заказчика или найти его в приложениях.")
        if not facts.contract_value_rub:
            completeness_score -= 20
            reasons.append("Не извлечена сумма контракта или НМЦК.")
            next_actions.append("Уточнить бюджет тендера и финансовую модель участия.")
        if not facts.tender_subject:
            completeness_score -= 10
            reasons.append("Предмет тендера определен не полностью.")
        if not tender_hits:
            completeness_score -= 20

        if facts.payment_terms and any(sf.lower() in facts.payment_terms.lower() for sf in profile.stop_factors):
            status = DecisionStatus.NO_GO
            reasons.append("Условия оплаты противоречат стоп-факторам компании.")
            risks.append("Коммерческие условия тендера неприемлемы для клиента.")
            fit_score -= 20
            risk_score += 25

        if facts.special_terms:
            reasons.append("Обнаружены специальные условия участия: " + ", ".join(facts.special_terms[:4]))
            risk_score += min(10, len(facts.special_terms) * 2)

        if facts.regions and profile.regions:
            normalized_profile_regions = {x.lower() for x in profile.regions}
            normalized_tender_regions = {x.lower() for x in facts.regions}
            if not (normalized_profile_regions & normalized_tender_regions or "россия" in normalized_profile_regions or "рф" in normalized_profile_regions):
                reasons.append("Регион исполнения тендера не совпадает с основными регионами компании.")
                risks.append("Потребуется дополнительная логистика или расширение географии работ.")
                fit_score -= 10
                risk_score += 10

        if profile_capability_hits:
            reasons.append("В документах компании найдены фрагменты, подтверждающие опыт, специализацию или проекты под тендер.")
            evidence_score = min(100, evidence_score + 10)
        else:
            reasons.append("В профиле компании мало подтверждающих фрагментов для предмета тендера.")
            evidence_score = max(20, evidence_score - 15)

        if not tender_hits:
            if status == DecisionStatus.GO:
                status = DecisionStatus.REVIEW
            confidence = min(confidence, 0.5)
            confidence_reason = "Не удалось извлечь достаточное количество текстовых доказательств из тендерных файлов."
            risks.append("Тендерные документы могли быть сканами или плохо распознаться.")
            next_actions.append("Загрузить текстовый PDF или проверить OCR для сканированного документа.")
            evidence_score = max(15, evidence_score - 30)

        if completeness_score < 80 and status != DecisionStatus.NO_GO:
            status = DecisionStatus.REVIEW
            confidence = min(confidence, 0.64)
            confidence_reason = "Для уверенного решения не хватает ключевых полей или доказательств."

        if status == DecisionStatus.GO:
            next_actions.extend([
                "Сформировать комплект заявки по обязательным требованиям.",
                "Проверить финальные реквизиты, сроки и состав приложений.",
            ])
        elif status == DecisionStatus.NO_GO:
            next_actions.extend([
                "Зафиксировать причину отказа от участия.",
                "Проверить, можно ли снять блокеры в следующих итерациях работы с клиентом.",
            ])

        fit_score = max(0, min(100, fit_score))
        completeness_score = max(0, min(100, completeness_score))
        evidence_score = max(0, min(100, evidence_score))
        risk_score = max(0, min(100, risk_score))
        overall_score = max(0, min(100, int(round(fit_score * 0.35 + completeness_score * 0.25 + evidence_score * 0.20 + (100 - risk_score) * 0.20))))

        evidence: list[EvidenceItem] = []
        for rec in evidence_records[:8]:
            relevance = 0.9 if rec.doc_name.startswith("company_profile") else 0.82
            evidence.append(
                EvidenceItem(
                    doc_name=rec.doc_name,
                    fragment_ref=rec.fragment_ref,
                    quote=rec.text[:280],
                    relevance=relevance,
                )
            )

        latency_ms = int((perf_counter() - start) * 1000)
        return DecisionReport(
            status=status,
            confidence=round(confidence, 2),
            confidence_reason=confidence_reason,
            overall_score=overall_score,
            fit_score=fit_score,
            evidence_score=evidence_score,
            completeness_score=completeness_score,
            risk_score=risk_score,
            reasons=list(dict.fromkeys(reasons))[:8],
            risks=list(dict.fromkeys(risks))[:8],
            evidence=evidence,
            next_actions=list(dict.fromkeys(next_actions))[:8],
            latency_ms=latency_ms,
            cost_estimate_rub=round(0.15 + 0.03 * len(evidence), 2),
        )
