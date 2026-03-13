from __future__ import annotations

import re

from app.schemas.models import CompanyProfile


def _extract_sentences(text: str, max_items: int = 5) -> list[str]:
    chunks = [x.strip() for x in re.split(r"[\n\.\!\?]+", text) if x.strip()]
    filtered = [x for x in chunks if len(x) > 20][:max_items]
    return filtered


def build_profile_from_company_text(text: str) -> CompanyProfile:
    src = text or ""
    lower = src.lower()

    company_name = "Компания пользователя"
    name_patterns = [
        r"(ооо\s+[«\"„']?[^\n\"»']+[»\"']?)",
        r"(ип\s+[A-ЯЁA-Za-z][^\n,;]{2,})",
        r"(ао\s+[«\"„']?[^\n\"»']+[»\"']?)",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, src, flags=re.IGNORECASE)
        if match:
            company_name = match.group(1).strip()
            break

    categories: list[str] = []
    focus_areas: list[str] = []
    category_map = {
        "it": ["it", "айти", "разработка", "software", "saas", "devops", "интеграц"],
        "строительство": ["строительство", "подряд", "монтаж", "смет", "строй"],
        "маркетинг": ["маркетинг", "реклама", "smm", "контекст"],
        "логистика": ["логистика", "перевоз", "доставка", "склад"],
        "поставка": ["поставка", "закуп", "снабж", "оборудован"],
        "безопасность": ["безопасност", "слаботоч", "видеонаблюден", "скуд"],
    }
    for category, keys in category_map.items():
        if any(key in lower for key in keys):
            categories.append(category)
            focus_areas.append(category)

    regions = sorted(set(re.findall(r"Москва|Санкт-Петербург|Екатеринбург|Казань|Новосибирск|Россия|РФ", src, flags=re.IGNORECASE)))
    if not regions:
        regions = ["Россия"]

    max_contract = 10_000_000.0
    match_max = re.search(r"(?:лимит|макс(?:имум)?|до)\s*([\d\s]{3,})\s*(?:руб|₽|RUB)", src, flags=re.IGNORECASE)
    if match_max:
        try:
            max_contract = float(match_max.group(1).replace(" ", ""))
        except ValueError:
            pass

    min_margin = 10.0
    match_margin = re.search(r"(?:маржа|margin)[^\d]{0,10}(\d{1,2}(?:[\.,]\d+)?)\s*%", src, flags=re.IGNORECASE)
    if match_margin:
        try:
            min_margin = float(match_margin.group(1).replace(",", "."))
        except ValueError:
            pass

    required_certificates: list[str] = []
    cert_patterns = [r"лицензия", r"сро", r"iso\s*\d+", r"сертификат"]
    for pattern in cert_patterns:
        if re.search(pattern, lower, flags=re.IGNORECASE):
            required_certificates.append(pattern.replace("\\s*\\d+", ""))
    required_certificates = sorted(set(required_certificates))

    stop_factors: list[str] = []
    if "постоплата" in lower and re.search(r"постоплата[^\d]{0,10}(9\d|1\d\d)", lower):
        stop_factors.append("длинная постоплата")
    if "без аванса" in lower:
        stop_factors.append("без аванса")
    if "штраф" in lower and "высок" in lower:
        stop_factors.append("высокие штрафы")

    project_examples = _extract_sentences(src, max_items=6)
    summary_parts = _extract_sentences(src, max_items=3)
    company_summary = " ".join(summary_parts)[:500]

    return CompanyProfile(
        company_name=company_name,
        categories=sorted(set(categories)),
        regions=regions,
        max_contract_value_rub=max_contract,
        min_margin_percent=min_margin,
        required_certificates=required_certificates,
        stop_factors=sorted(set(stop_factors)),
        company_summary=company_summary,
        focus_areas=sorted(set(focus_areas)),
        project_examples=project_examples,
        knowledge_text=src[:12000],
    )
