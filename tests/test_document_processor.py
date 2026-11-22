import pymupdf
import pytest

from backend.services import ocr_service
from backend.services.document_processor import DocumentProcessingError, MAX_FILE_SIZE, process_document


def test_utf8_bom_text_is_decoded():
    result = process_document("sample.txt", b"\xef\xbb\xbfVendor\nTotal: 12.30")
    assert result.text == "Vendor\nTotal: 12.30"
    assert result.method == "Text file"


def test_invalid_and_oversized_documents_are_rejected():
    with pytest.raises(DocumentProcessingError, match="signature"):
        process_document("wrong.pdf", b"not pdf")
    with pytest.raises(DocumentProcessingError, match="15 MB"):
        process_document("large.txt", b"x" * (MAX_FILE_SIZE + 1))
    with pytest.raises(DocumentProcessingError, match="Supported files"):
        process_document("invoice.docx", b"x")
    with pytest.raises(DocumentProcessingError, match="empty"):
        process_document("empty.txt", b"")


def test_mixed_pdf_runs_ocr_only_on_pages_without_text(monkeypatch):
    doc = pymupdf.open()
    first = doc.new_page()
    first.insert_text((72, 72), "Digital invoice page")
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    calls = []

    def fake_ocr(page):
        calls.append(page.number)
        return "Scanned continuation page"

    monkeypatch.setattr(ocr_service, "_ocr_pdf_page", fake_ocr)
    result = process_document("mixed.pdf", pdf_bytes)
    assert calls == [1]
    assert "Digital invoice page" in result.text
    assert "Scanned continuation page" in result.text
    assert result.method == "PyMuPDF + RapidOCR"
