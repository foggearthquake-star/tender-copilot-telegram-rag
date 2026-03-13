from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.schemas.models import BidDraftOutline, CompanyProfile, DecisionReport, TenderFacts


def _register_ru_font() -> str:
    candidates = [
        ("ArialUnicode", Path("C:/Windows/Fonts/arial.ttf")),
        ("DejaVuSans", Path("C:/Windows/Fonts/DejaVuSans.ttf")),
    ]
    for name, path in candidates:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
                return name
            except Exception:
                continue
    return "Helvetica"


class PdfReportService:
    def build_report(
        self,
        path: Path,
        profile: CompanyProfile,
        facts: TenderFacts,
        decision: DecisionReport,
        bid_outline: BidDraftOutline,
    ) -> str:
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        styles = getSampleStyleSheet()
        font_name = _register_ru_font()

        title_style = ParagraphStyle("RuTitle", parent=styles["Title"], fontName=font_name)
        h2_style = ParagraphStyle("RuH2", parent=styles["Heading2"], fontName=font_name)
        normal_style = ParagraphStyle("RuBody", parent=styles["Normal"], fontName=font_name, leading=14)

        parts = []
        status_map = {
            "GO": "ПОДАВАТЬСЯ",
            "REVIEW": "ПРОВЕРИТЬ ВРУЧНУЮ",
            "NO_GO": "НЕ ПОДАВАТЬСЯ",
        }
        status_ru = status_map.get(decision.status.value, decision.status.value)
        parts.append(Paragraph("Отчет Tender Copilot", title_style))
        parts.append(Paragraph(f"Компания: {profile.company_name}", normal_style))
        parts.append(Paragraph(f"Статус: {status_ru} ({decision.status.value})", normal_style))
        parts.append(Paragraph(f"Уверенность: {decision.confidence} ({decision.confidence_reason})", normal_style))
        parts.append(Spacer(1, 12))

        parts.append(Paragraph("Причины решения", h2_style))
        for item in decision.reasons:
            parts.append(Paragraph(f"- {item}", normal_style))

        parts.append(Spacer(1, 8))
        parts.append(Paragraph("Риски", h2_style))
        if decision.risks:
            for item in decision.risks:
                parts.append(Paragraph(f"- {item}", normal_style))
        else:
            parts.append(Paragraph("- Не выявлены", normal_style))

        parts.append(Spacer(1, 8))
        parts.append(Paragraph("Доказательства", h2_style))
        if decision.evidence:
            for ev in decision.evidence:
                parts.append(Paragraph(f"[{ev.doc_name}:{ev.fragment_ref}] {ev.quote}", normal_style))
        else:
            parts.append(Paragraph("Не удалось извлечь текстовые фрагменты из документов.", normal_style))

        parts.append(Spacer(1, 8))
        parts.append(Paragraph("Следующие действия", h2_style))
        for step in decision.next_actions:
            parts.append(Paragraph(f"- {step}", normal_style))

        parts.append(Spacer(1, 8))
        parts.append(Paragraph("Черновик структуры заявки", h2_style))
        for section in bid_outline.required_sections:
            parts.append(Paragraph(f"- {section}", normal_style))

        if facts.contract_value_rub:
            parts.append(Paragraph(f"Оценка цены контракта: {facts.contract_value_rub:,.0f} RUB".replace(",", " "), normal_style))

        doc.build(parts)
        return str(path)
