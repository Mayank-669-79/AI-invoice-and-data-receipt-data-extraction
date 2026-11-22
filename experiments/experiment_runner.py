"""Run P1-P6 on the same paired synthetic set using one explicitly selected provider.

From repository root: python -m experiments.experiment_runner
Default cost/volume: 6 prompts x 50 examples = 300 model calls.
"""
import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from backend.schemas.invoice_schema import InvoiceSchema
from backend.services.llm_service import ProviderRequestError, _find_ollama_model, extract_with_provider
from backend.services.prompt_loader import PROMPTS
from evaluation.accuracy import score_accuracy
from evaluation.hallucination import score_missing_and_unsupported
from evaluation.visualizations import render_report

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "backend" / ".env")
INVOICE_DIR = ROOT / "dataset" / "invoices"
TRUTH_DIR = ROOT / "dataset" / "ground_truth"
RESULTS_DIR = ROOT / "documentation" / "experiment_results"
CSV_PATH = ROOT / "experiments" / "prompt_results.csv"


def load_cases() -> list[dict]:
    cases = []
    for invoice_path in sorted(INVOICE_DIR.glob("*.txt")):
        truth_path = TRUTH_DIR / f"{invoice_path.stem}.json"
        if not truth_path.exists():
            raise FileNotFoundError(f"Ground truth not found for {invoice_path.name}")
        cases.append({
            "id": invoice_path.stem,
            "text": invoice_path.read_text(encoding="utf-8"),
            "ground_truth": json.loads(truth_path.read_text(encoding="utf-8")),
        })
    return cases


def run_experiments(
    provider: str | None = None,
    prompt_ids: list[str] | None = None,
    limit: int | None = None,
    write_results: bool = True,
) -> dict:
    provider = (provider or os.getenv("EXPERIMENT_PROVIDER", "gemini")).strip().lower()
    if provider not in {"gemini", "ollama"}:
        raise ValueError("EXPERIMENT_PROVIDER must be gemini or ollama. Experiments do not auto-fallback.")
    if provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("EXPERIMENT_PROVIDER=gemini requires GEMINI_API_KEY. No experiment requests were started.")
    if provider == "ollama":
        _find_ollama_model()  # fail before creating a report if local Ollama is not ready
    cases = load_cases()
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit must be at least 1.")
        cases = cases[:limit]
    if not cases:
        raise ValueError(f"No .txt invoices found under {INVOICE_DIR}")
    requested_ids = set(prompt_ids) if prompt_ids else {prompt.id for prompt in PROMPTS}
    unknown_ids = requested_ids - {prompt.id for prompt in PROMPTS}
    if unknown_ids:
        raise ValueError(f"Unknown prompt IDs: {', '.join(sorted(unknown_ids))}")
    selected_prompts = [prompt for prompt in PROMPTS if prompt.id in requested_ids]

    report = {
        "provider": provider,
        "model": None,
        "dataset": "paired synthetic invoice set v1",
        "sample_count": len(cases),
        "prompt_count": len(selected_prompts),
        "diagnostic_only": not write_results,
        "notice": "Synthetic, text-only pilot; labels are hand-authored. It does not measure OCR quality or establish general performance.",
        "metric_notes": {
            "field_accuracy": "Correct values divided by explicitly present ground-truth keys; omitted labels are not included.",
            "unsupported_field_rate": "Proxy counting non-empty predicted scalar fields whose ground truth is absent/null; not manually adjudicated hallucination.",
            "mean_latency_seconds": "Model-call time only; excludes OCR and upload processing.",
        },
        "prompts": [],
    }
    summary_rows = []
    for prompt in selected_prompts:
        field_correct = field_total = exact = item_correct = item_total = valid = 0
        missing_correct = missing_total = unsupported_count = unsupported_candidates = 0
        input_tokens = output_tokens = 0
        latencies = []
        case_results = []
        for case in cases:
            started = time.perf_counter()
            try:
                result = extract_with_provider(case["text"], prompt.id, provider)
                latency = time.perf_counter() - started
                prediction = InvoiceSchema.model_validate(result.invoice_data).model_dump()
                is_valid = True
                scores = score_accuracy(case["ground_truth"], prediction)
                missing = score_missing_and_unsupported(case["ground_truth"], prediction)
                field_correct += scores["field_correct"]
                field_total += scores["field_total"]
                exact += int(scores["record_exact"] is True)
                if scores["line_item_exact"] is not None:
                    item_total += 1
                    item_correct += int(scores["line_item_exact"])
                missing_correct += missing["missing_field_correct"]
                missing_total += missing["missing_field_total"]
                unsupported_count += missing["unsupported_field_count"]
                unsupported_candidates += missing["unsupported_field_candidates"]
                input_tokens += result.input_tokens or 0
                output_tokens += result.output_tokens or 0
                report["model"] = report["model"] or result.model
                latencies.append(latency)
                case_results.append({
                    "case_id": case["id"], "valid_json": True,
                    "field_accuracy": scores["field_accuracy"],
                    "record_exact": scores["record_exact"],
                    "prediction": prediction,
                })
                valid += 1
            except ProviderRequestError as exc:
                raise RuntimeError(
                    f"Stopped at {prompt.id}/{case['id']}: provider setup/request failed; "
                    f"no experiment report was saved. Check the API key, model ID, network, "
                    f"and Windows certificate configuration. Details: {exc}"
                ) from exc
            except Exception as exc:
                latency = time.perf_counter() - started
                latencies.append(latency)
                # An invalid/unavailable response counts as a failed extraction for labeled fields.
                truth = case["ground_truth"]
                field_total += len(truth)
                if "items" in truth:
                    item_total += 1
                missing = score_missing_and_unsupported(truth, {})
                missing_total += missing["missing_field_total"]
                unsupported_candidates += missing["unsupported_field_candidates"]
                case_results.append({"case_id": case["id"], "valid_json": False, "field_accuracy": 0.0, "record_exact": False, "error": str(exc)})
            case_result = case_results[-1]
            if case_result["valid_json"]:
                print(f"{prompt.id} {case['id']}: valid")
            else:
                print(f"{prompt.id} {case['id']}: invalid model output: {case_result.get('error', 'no details')}")

        count = len(cases)
        prompt_result = {
            "prompt_id": prompt.id,
            "name": prompt.name,
            "technique": prompt.technique,
            "field_accuracy": field_correct / field_total if field_total else None,
            "exact_record_accuracy": exact / count if count else None,
            "line_item_exact_accuracy": item_correct / item_total if item_total else None,
            "valid_json_rate": valid / count if count else None,
            "missing_field_handling_accuracy": missing_correct / missing_total if missing_total else None,
            "unsupported_field_rate": unsupported_count / unsupported_candidates if unsupported_candidates else None,
            "mean_latency_seconds": sum(latencies) / len(latencies) if latencies else None,
            "input_tokens": input_tokens or None,
            "output_tokens": output_tokens or None,
            "cases": case_results,
        }
        report["prompts"].append(prompt_result)
        summary_rows.append({key: value for key, value in prompt_result.items() if key != "cases"})
        print(f"{prompt.id}: field accuracy={prompt_result['field_accuracy']}; exact records={exact}/{count}; schema-valid={valid}/{count}")

    if write_results:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = RESULTS_DIR / "latest_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        pd.DataFrame(summary_rows).to_csv(CSV_PATH, index=False)
        render_report(report_path, RESULTS_DIR)
        print(f"Saved report: {report_path}\nSaved CSV: {CSV_PATH}\nSaved comparison charts under {RESULTS_DIR}")
    else:
        print("Diagnostic/subset run only; no full-comparison report or CSV was saved.")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare invoice prompts using one selected provider.")
    parser.add_argument("--provider", choices=("gemini", "ollama"), help="Override EXPERIMENT_PROVIDER for this run.")
    parser.add_argument("--prompt", dest="prompt_ids", action="append", choices=[prompt.id for prompt in PROMPTS], help="Run only this prompt; repeat the option to select more than one.")
    parser.add_argument("--limit", type=int, help="Use only the first N benchmark invoices (for a small diagnostic).")
    args = parser.parse_args()
    diagnostic = args.prompt_ids is not None or args.limit is not None
    try:
        run_experiments(args.provider, args.prompt_ids, args.limit, write_results=not diagnostic)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
