from pathlib import Path

from app.services.normalizer import normalize_facts
from app.services.parsers import chunk_text, parse_document


def test_chunk_text_basic() -> None:
    text = "a" * 2100
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 3
    assert all(chunks)


def test_normalize_facts_extracts_money_deadline() -> None:
    text = "Цена контракта 12 000 000 руб. Срок подачи до 2026-06-01. Требуется лицензия."
    facts = normalize_facts([text])
    assert facts.contract_value_rub == 12000000
    assert facts.deadline == "2026-06-01"
    assert "лицензия" in facts.required_certificates


def test_parse_document_unsupported(tmp_path: Path) -> None:
    file_path = tmp_path / "bad.txt"
    file_path.write_text("x", encoding="utf-8")
    try:
        parse_document(file_path)
        assert False, "expected error"
    except ValueError:
        assert True
