import pytest

from backend.services.llm_service import ExtractionResult, ProviderRequestError
from experiments import experiment_runner as runner


def test_small_diagnostic_runs_only_requested_prompt_and_case(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    monkeypatch.setattr(runner, "load_cases", lambda: [{"id": "synthetic-001", "text": "Acme invoice", "ground_truth": {"vendor_name": "Acme"}}])
    calls = []

    def fake_provider(text, prompt_id, provider):
        calls.append((text, prompt_id, provider))
        return ExtractionResult({"vendor_name": "Acme"}, "Gemini", "test-model")

    monkeypatch.setattr(runner, "extract_with_provider", fake_provider)
    report = runner.run_experiments("gemini", prompt_ids=["p1"], limit=1, write_results=False)
    assert calls == [("Acme invoice", "p1", "gemini")]
    assert report["sample_count"] == report["prompt_count"] == 1
    assert report["diagnostic_only"] is True
    assert report["prompts"][0]["valid_json_rate"] == 1


def test_provider_transport_failure_stops_before_other_cases(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    monkeypatch.setattr(runner, "load_cases", lambda: [
        {"id": f"synthetic-{i:03d}", "text": "invoice", "ground_truth": {"vendor_name": "Acme"}}
        for i in range(1, 4)
    ])
    calls = []

    def offline(*args):
        calls.append(args)
        raise ProviderRequestError("Gemini client setup failed (SSLError): test certificate error")

    monkeypatch.setattr(runner, "extract_with_provider", offline)
    with pytest.raises(RuntimeError, match="Stopped at p1/synthetic-001.*SSLError"):
        runner.run_experiments("gemini", prompt_ids=["p1"], write_results=False)
    assert len(calls) == 1
