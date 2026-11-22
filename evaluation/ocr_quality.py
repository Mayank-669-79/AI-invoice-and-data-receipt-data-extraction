"""OCR quality is evaluated separately from prompt/LLM extraction.

Add scanned PDFs/images to dataset/invoices and matching UTF-8 transcripts with
identical stems under dataset/ocr_ground_truth, then run:
python -m evaluation.ocr_quality
"""
import json
import re
from pathlib import Path

import pandas as pd

from backend.services.document_processor import process_document

ROOT = Path(__file__).resolve().parents[1]
OCR_INPUTS = ROOT / "dataset" / "invoices"
OCR_TRUTH = ROOT / "dataset" / "ocr_ground_truth"
OUTPUT = ROOT / "documentation" / "experiment_results"
IMAGE_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png"}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def edit_distance(reference: list, hypothesis: list) -> int:
    """Levenshtein distance with O(min(n,m)) memory."""
    if len(reference) < len(hypothesis):
        reference, hypothesis = hypothesis, reference
    previous = list(range(len(hypothesis) + 1))
    for row, ref_item in enumerate(reference, start=1):
        current = [row]
        for column, hyp_item in enumerate(hypothesis, start=1):
            current.append(min(
                current[column - 1] + 1,
                previous[column] + 1,
                previous[column - 1] + (ref_item != hyp_item),
            ))
        previous = current
    return previous[-1]


def character_error_rate(reference: str, hypothesis: str) -> float:
    reference, hypothesis = normalize_text(reference), normalize_text(hypothesis)
    if not reference:
        return 0.0 if not hypothesis else 1.0
    return edit_distance(list(reference), list(hypothesis)) / len(reference)


def word_error_rate(reference: str, hypothesis: str) -> float:
    reference_words = normalize_text(reference).split()
    hypothesis_words = normalize_text(hypothesis).split()
    if not reference_words:
        return 0.0 if not hypothesis_words else 1.0
    return edit_distance(reference_words, hypothesis_words) / len(reference_words)


def run_ocr_evaluation() -> dict:
    sources = sorted(path for path in OCR_INPUTS.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
    if not sources:
        raise SystemExit(f"No scanned OCR samples found in {OCR_INPUTS}. Add a PDF/JPG/PNG and its matching transcript under {OCR_TRUTH}.")
    rows = []
    for source in sources:
        truth_path = OCR_TRUTH / f"{source.stem}.txt"
        if not truth_path.is_file():
            raise FileNotFoundError(f"Missing OCR transcript for {source.name}: expected {truth_path.name}")
        reference = truth_path.read_text(encoding="utf-8")
        extracted = process_document(source.name, source.read_bytes()).text
        rows.append({
            "document": source.name,
            "character_error_rate": character_error_rate(reference, extracted),
            "word_error_rate": word_error_rate(reference, extracted),
            "reference_characters": len(normalize_text(reference)),
            "reference_words": len(normalize_text(reference).split()),
        })
    report = {
        "dataset": "OCR transcription benchmark",
        "sample_count": len(rows),
        "mean_character_error_rate": sum(row["character_error_rate"] for row in rows) / len(rows),
        "mean_word_error_rate": sum(row["word_error_rate"] for row in rows) / len(rows),
        "note": "Character/word error rates compare OCR text only. This report is separate from LLM prompt accuracy.",
        "documents": rows,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "ocr_quality.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_csv(OUTPUT / "ocr_quality.csv", index=False)
    print(f"Evaluated {len(rows)} OCR samples; mean CER={report['mean_character_error_rate']:.4f}; mean WER={report['mean_word_error_rate']:.4f}")
    return report


if __name__ == "__main__":
    run_ocr_evaluation()
