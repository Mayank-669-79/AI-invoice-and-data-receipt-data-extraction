import json
import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.services.document_processor import DocumentProcessingError, MAX_FILE_SIZE, process_document
from backend.services.extraction_service import extract_invoice
from backend.services.prompt_loader import get_prompt, public_prompts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Invoice Intelligence"])
ROOT = Path(__file__).resolve().parents[2]


@router.get("/prompts")
def list_prompts():
    return {"prompts": public_prompts()}


@router.get("/evaluation/results")
def evaluation_results():
    report = ROOT / "documentation" / "experiment_results" / "latest_report.json"
    if not report.exists():
        return {"available": False, "message": "No measured results yet. Run `python -m experiments.experiment_runner` to execute the controlled prompt comparison."}
    return {"available": True, **json.loads(report.read_text(encoding="utf-8"))}


@router.get("/evaluation/plots/{filename}")
def evaluation_plot(filename: str):
    allowed = {
        "field_accuracy.png", "record_accuracy.png", "item_accuracy.png", "json_validity.png",
        "missing_field_handling.png", "unsupported_field_rate.png", "mean_latency.png",
        "token_usage.png", "accuracy_vs_tokens.png",
    }
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="Plot not found.")
    path = ROOT / "documentation" / "experiment_results" / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="No measured plot is available yet. Run the experiment first.")
    return FileResponse(path, media_type="image/png")


@router.post("/invoices/upload")
async def upload_invoice(file: UploadFile = File(...), prompt_version: str = Form("p6")):
    try:
        get_prompt(prompt_version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    filename = Path(file.filename or "upload").name
    contents = await file.read(MAX_FILE_SIZE + 1)
    try:
        processed = process_document(filename, contents)
    except DocumentProcessingError as exc:
        status_code = 413 if "15 MB" in str(exc) else 400 if any(word in str(exc) for word in ("Supported files", "signature")) else 422
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Document processing failed")
        raise HTTPException(status_code=422, detail="Document text extraction failed. Check the file and backend logs.") from exc

    try:
        result = extract_invoice(processed.text, prompt_version)
    except Exception as exc:
        logger.exception("AI extraction failed")
        raise HTTPException(status_code=502, detail=f"AI extraction failed. Check provider availability/configuration and backend logs. {exc}") from exc

    return {
        "filename": filename,
        "message": "Extraction complete. Review values before using them for accounting.",
        "prompt_version": prompt_version,
        "provider": result.provider,
        "model": result.model,
        "usage": {"input_tokens": result.input_tokens, "output_tokens": result.output_tokens},
        "extraction_method": processed.method,
        "extracted_text": processed.text,
        "character_count": len(processed.text),
        "invoice_data": result.invoice_data,
        "warnings": result.warnings,
    }
