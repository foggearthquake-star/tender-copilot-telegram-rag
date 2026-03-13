from __future__ import annotations

import re
from typing import Iterable

from app.schemas.models import TenderFacts


MONEY_RE = re.compile(r"(\d[\d\s]{2,})\s?(?:руб|RUB|₽)", re.IGNORECASE)
DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})")
CERT_RE = re.compile(r"(лицензия|сертификат|сро|допуск|iso\s*\d+)", re.IGNORECASE)
PAYMENT_RE = re.compile(r"(аванс[^.\n]{0,120}|постоплата[^.\n]{0,120}|оплата[^.\n]{0,120})", re.IGNORECASE)
REGION_RE = re.compile(r"(Москва|Санкт-Петербург|Екатеринбург|Казань|Новосибирск|РФ|Россия)", re.IGNORECASE)
SUBJECT_RE = re.compile(r"(?:предмет закупки|предмет договора|объект закупки|наименование закупки)[:\s-]{0,10}(.{20,220})", re.IGNORECASE)


OBLIGATION_KEYWORDS = [
    "гарантия",
    "штраф",
    "срок поставки",
    "техническое задание",
    "интеграция",
    "разработка",
    "внедрение",
    "монтаж",
    "поставка",
    "обслуживание",
    "поддержка",
    "обучение",
]
EVALUATION_KEYWORDS = [
    "опыт",
    "квалификация",
    "цена",
    "срок",
    "качество",
    "наличие специалистов",
    "деловая репутация",
]
SPECIAL_TERMS_KEYWORDS = [
    "обеспечение заявки",
    "обеспечение исполнения",
    "банковская гарантия",
    "неустойка",
    "аванс",
    "постоплата",
    "этапность",
]


def _to_float(value: str) -> float:
    compact = value.replace(" ", "")
    return float(compact)


def _collect_keywords(text: str, keywords: list[str]) -> list[str]:
    lower = text.lower()
    return [keyword for keyword in keywords if keyword in lower]


def normalize_facts(texts: Iterable[str]) -> TenderFacts:
    merged = "\n".join(texts)
    merged_lower = merged.lower()

    money_match = MONEY_RE.search(merged)
    date_match = DATE_RE.search(merged)
    subject_match = SUBJECT_RE.search(merged)
    certs = sorted({m.group(1).lower() for m in CERT_RE.finditer(merged)})
    payments = PAYMENT_RE.findall(merged)
    regions = sorted({m.group(1) for m in REGION_RE.finditer(merged)})
    obligations = _collect_keywords(merged, OBLIGATION_KEYWORDS)
    evaluation_criteria = _collect_keywords(merged, EVALUATION_KEYWORDS)
    special_terms = _collect_keywords(merged, SPECIAL_TERMS_KEYWORDS)

    deliverables: list[str] = []
    for keyword in ["поставка", "монтаж", "внедрение", "разработка", "поддержка", "обслуживание", "обучение"]:
        if keyword in merged_lower:
            deliverables.append(keyword)

    tender_subject = None
    if subject_match:
        tender_subject = subject_match.group(1).strip(" .;:-")[:220]
    elif deliverables:
        tender_subject = ", ".join(deliverables[:4])

    return TenderFacts(
        contract_value_rub=_to_float(money_match.group(1)) if money_match else None,
        deadline=date_match.group(1) if date_match else None,
        tender_subject=tender_subject,
        required_certificates=certs,
        regions=regions,
        payment_terms="; ".join(payments) if payments else None,
        obligations=obligations,
        deliverables=sorted(set(deliverables)),
        evaluation_criteria=sorted(set(evaluation_criteria)),
        special_terms=sorted(set(special_terms)),
    )
