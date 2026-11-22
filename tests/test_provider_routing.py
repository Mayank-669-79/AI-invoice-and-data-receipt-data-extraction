from types import SimpleNamespace

from backend.services import llm_service
from backend.services.llm_service import ExtractionResult


def test_auto_prefers_gemini(monkeypatch):
    result = ExtractionResult({"vendor_name": "cloud"}, "Gemini", "gemini-test")
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.setattr(llm_service, "_extract_with_gemini", lambda *args: result)
    monkeypatch.setattr(llm_service, "_extract_with_ollama", lambda *args: (_ for _ in ()).throw(AssertionError("Ollama should not run")))
    assert llm_service.extract_invoice_data("text").provider == "Gemini"


def test_auto_falls_back_to_ollama_if_gemini_fails(monkeypatch):
    local = ExtractionResult({"vendor_name": "local"}, "Ollama (local)", "qwen3:4b")
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.setattr(llm_service, "_extract_with_gemini", lambda *args: (_ for _ in ()).throw(ConnectionError("Gemini unavailable")))
    monkeypatch.setattr(llm_service, "_extract_with_ollama", lambda *args: local)
    assert llm_service.extract_invoice_data("text").provider == "Ollama (local)"


def test_local_only_never_calls_gemini(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setattr(llm_service, "_extract_with_ollama", lambda *args: (_ for _ in ()).throw(ConnectionError("offline")))
    monkeypatch.setattr(llm_service, "_extract_with_gemini", lambda *args: (_ for _ in ()).throw(AssertionError("must not send invoice to Gemini")))
    try:
        llm_service.extract_invoice_data("sensitive invoice")
    except ConnectionError as exc:
        assert "offline" in str(exc)
    else:
        raise AssertionError("Expected local provider failure")


def test_model_is_discovered_when_one_local_model_is_installed(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.setattr(llm_service.httpx, "get", lambda *args, **kwargs: SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"models": [{"name": "qwen3:4b"}]}))
    assert llm_service._find_ollama_model() == "qwen3:4b"


def test_gemini_client_is_cached_per_api_key(monkeypatch):
    calls = []

    def fake_client(api_key):
        client = object()
        calls.append((api_key, client))
        return client

    monkeypatch.setattr(llm_service.genai, "Client", fake_client)
    llm_service._gemini_client.cache_clear()
    first = llm_service._gemini_client("test-key")
    second = llm_service._gemini_client("test-key")
    llm_service._gemini_client.cache_clear()
    assert first is second
    assert len(calls) == 1
