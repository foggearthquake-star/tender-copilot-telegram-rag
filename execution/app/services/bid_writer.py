from __future__ import annotations

import re

from app.schemas.models import BidDraftOutline, CompanyProfile, DecisionReport, TenderFacts


class BidWriter:
    def _sections_from_user_draft(self, draft_text: str) -> list[str]:
        lines = [ln.strip(" -\t") for ln in draft_text.splitlines() if ln.strip()]
        section_lines: list[str] = []
        for ln in lines:
            if re.match(r"^(\d+[\).]|[A-Za-zА-Яа-я].{4,80}:)", ln) or len(ln) <= 90:
                section_lines.append(ln)
        return [ln for ln in section_lines if len(ln) >= 4][:12]

    def build_outline(
        self,
        profile: CompanyProfile,
        facts: TenderFacts,
        decision: DecisionReport,
        user_draft_text: str | None = None,
    ) -> BidDraftOutline:
        required_sections = [
            "1. Сведения об участнике",
            "2. Подтверждение соответствия обязательным требованиям",
            "3. Коммерческое предложение",
            "4. Сроки и этапы исполнения",
            "5. Подтверждающие документы",
        ]
        if user_draft_text:
            user_sections = self._sections_from_user_draft(user_draft_text)
            if len(user_sections) >= 3:
                required_sections = user_sections

        recommended_sections = [
            "6. Управление рисками исполнения",
            "7. Контроль качества и SLA",
            "8. План коммуникации с заказчиком",
        ]

        missing_information: list[str] = []
        if not facts.deadline:
            missing_information.append("Точная дата дедлайна подачи заявки")
        if not facts.contract_value_rub:
            missing_information.append("Подтвержденная максимальная цена контракта")
        if facts.required_certificates and not profile.required_certificates:
            missing_information.append("Перечень сертификатов компании для соответствия требованиям")
        if user_draft_text is None:
            missing_information.append("Если есть ваш черновик заявки, приложите его в следующем запуске")

        checklist = [
            "Проверить соответствие обязательным требованиям из ТЗ",
            "Проверить комплект документов и подписи",
            "Сверить цену и сроки с коммерческой моделью",
            "Провести финальный контроль перед подачей",
        ]
        if decision.status.name == "REVIEW":
            checklist.insert(0, "Снять вопросы и неопределенности у заказчика до подачи")

        return BidDraftOutline(
            title=f"Черновик структуры заявки: {profile.company_name}",
            required_sections=required_sections,
            recommended_sections=recommended_sections,
            missing_information=missing_information,
            submission_checklist=checklist,
        )
