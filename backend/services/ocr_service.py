from functools import lru_cache
from io import BytesIO

import numpy as np
import pymupdf
from PIL import Image
from rapidocr import RapidOCR


@lru_cache(maxsize=1)
def _ocr_engine():
    return RapidOCR()


def _read_image(image: np.ndarray) -> list[str]:
    result = _ocr_engine()(image)
    texts = getattr(result, "txts", None)
    if texts:
        return [str(text) for text in texts if text]
    if isinstance(result, (tuple, list)) and len(result) > 1 and result[1]:
        return [str(text) for text in result[1] if text]
    return []


def _ocr_pdf_page(page) -> str:
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    return "\n".join(_read_image(image)).strip()


def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, str]:
    """Extract selectable text and OCR pages without selectable text in mixed PDFs."""
    blocks: list[str] = []
    used_text = False
    used_ocr = False
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
        for number, page in enumerate(pdf, start=1):
            text = page.get_text().strip()
            if text:
                used_text = True
            else:
                text = _ocr_pdf_page(page)
                used_ocr = True
            if text:
                blocks.append(f"--- Page {number} ---\n{text}")
    method = "PyMuPDF + RapidOCR" if used_text and used_ocr else "RapidOCR" if used_ocr else "PyMuPDF"
    return "\n".join(blocks).strip(), method


def extract_image_text(image_bytes: bytes) -> str:
    with Image.open(BytesIO(image_bytes)) as image:
        rgb = np.asarray(image.convert("RGB"))
    return "\n".join(_read_image(rgb)).strip()
