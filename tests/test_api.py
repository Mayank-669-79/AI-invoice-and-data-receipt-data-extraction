from fastapi.testclient import TestClient

from backend.main import app
from backend.routes import invoice_routes
from backend.services.extraction_service import InvoiceExtraction

client = TestClient(app)


def test_health_and_prompt_catalog():
    assert client.get("/health").json() == {"status": "healthy"}
    response = client.get("/api/prompts")
    assert response.status_code == 200
    assert [prompt["id"] for prompt in response.json()["prompts"]] == [f"p{i}" for i in range(1, 7)]


def test_txt_upload_returns_data_and_provider_without_ai_call(monkeypatch):
    invoice = {"vendor_name": "Acme", "invoice_number": "A-42", "invoice_date": "2026-01-02", "items": [{"description": "Pen", "quantity": 2, "unit_price": 3, "amount": 6}], "subtotal": 6, "tax_amount": 0, "total_amount": 6, "currency": "USD"}
    result = InvoiceExtraction(invoice, [], "Ollama (local)", "qwen3:4b")
    monkeypatch.setattr(invoice_routes, "extract_invoice", lambda text, prompt_id: result)
    response = client.post("/api/invoices/upload", data={"prompt_version": "p2"}, files={"file": ("invoice.txt", b"\xef\xbb\xbfAcme invoice A-42", "text/plain")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["prompt_version"] == "p2"
    assert data["provider"] == "Ollama (local)"
    assert data["model"] == "qwen3:4b"
    assert data["extracted_text"] == "Acme invoice A-42"
    assert data["invoice_data"]["items"][0]["amount"] == 6
    assert data["warnings"] == []


def test_bad_prompt_and_unsupported_file_are_rejected():
    unsupported = client.post("/api/invoices/upload", files={"file": ("invoice.docx", b"x")})
    assert unsupported.status_code == 400
    bad_prompt = client.post("/api/invoices/upload", data={"prompt_version": "p99"}, files={"file": ("invoice.txt", b"hello", "text/plain")})
    assert bad_prompt.status_code == 400


def test_evaluation_not_run_and_unknown_plot_is_404():
    results = client.get("/api/evaluation/results")
    assert results.status_code == 200
    assert results.json()["available"] is False
    assert client.get("/api/evaluation/plots/not-an-image.png").status_code == 404
