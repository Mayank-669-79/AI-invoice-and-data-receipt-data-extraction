from dataclasses import dataclass
from pathlib import Path

from backend.services.ocr_service import extract_image_text, extract_pdf_text

MAX_FILE_SIZE = 15 * 1024 * 1024
ALLOWED_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png", ".txt"}


class DocumentProcessingError(ValueError):
    pass


@dataclass(frozen=True)
class ProcessedDocument:
    text: str
    method: str
    filename: str


def process_document(filename: str, contents: bytes) -> ProcessedDocument:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise DocumentProcessingError("Supported files: PDF, JPG, JPEG, PNG, and TXT.")
    if not contents:
        raise DocumentProcessingError("Uploaded file is empty.")
    if len(contents) > MAX_FILE_SIZE:
        raise DocumentProcessingError("File size cannot exceed 15 MB.")
    if suffix == ".pdf":
        if not contents.startswith(b"%PDF-"):
            raise DocumentProcessingError("The uploaded file does not have a valid PDF signature.")
        text, method = extract_pdf_text(contents)
    elif suffix == ".txt":
        try:
            text = contents.decode("utf-8-sig").strip()
        except UnicodeDecodeError as exc:
            raise DocumentProcessingError("Text files must use UTF-8 encoding.") from exc
        method = "Text file"
    else:
        text = extract_image_text(contents)
        method = "RapidOCR"
    if not text.strip():
        raise DocumentProcessingError("No readable text found in the document.")
    return ProcessedDocument(text=text, method=method, filename=filename)
