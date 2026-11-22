# Architecture and module responsibilities

The application is a single modular FastAPI backend and React/Vite frontend. It does not add a database by default; MongoDB/history is optional and is not needed for the current non-persistent workflow.

- `frontend/pages/WorkspacePage.jsx` owns workspace state and navigation. `frontend/components/` contains upload, result, and evaluation views; `frontend/src/` is the Vite entrypoint and styling.
- `backend/main.py` creates the FastAPI app. `backend/routes/invoice_routes.py` exposes health-independent invoice, prompt, and evaluation HTTP routes.
- `backend/services/document_processor.py` enforces type, size, signature, and UTF-8 rules. `ocr_service.py` extracts digital PDF text and applies RapidOCR to images, scanned PDF pages, and image-only pages in mixed PDFs.
- `llm_service.py` performs Gemini-first requests with local Ollama fallback in `auto` mode; `LLM_PROVIDER=ollama` disables cloud calls. `extraction_service.py` validates returned fields and attaches review warnings.
- `backend/prompts/prompt_v1.txt`–`prompt_v6.txt` hold the six independently selectable experiment instructions. `prompt_loader.py` reads their IDs, descriptions, and text.
- `backend/schemas/invoice_schema.py` defines the Pydantic data model; `backend/validators/invoice_validator.py` detects missing values, unreadable dates, and selected arithmetic conflicts without changing printed values.
- `dataset/invoices/` and `dataset/ground_truth/` are paired, hand-authored synthetic text examples and labels. `experiments/` executes controlled comparisons and writes actual CSV results. `evaluation/` calculates prompt metrics, plots results, and provides a separate OCR character/word error scorer when scanned samples and transcriptions are added under the documented paths.

## Research design and limitations

P1–P6 are compared on the same 50 examples and a single explicitly selected provider. The script defaults to Gemini to isolate prompt strategy; set `EXPERIMENT_PROVIDER=ollama` to run a distinct local-model experiment. It does not automatically mix providers inside one prompt comparison. A run uses 300 model calls. The data are synthetic text and do not measure OCR quality. Unsupported-field rate is a proxy, not a manually adjudicated hallucination rate. No measured scores are checked into the initial project.

## Suggested six-person division

1. Backend API and integration.
2. PDF/image processing and OCR quality tests.
3. Prompt design and provider/model integration.
4. Dataset curation, ground truth, experiments, and evaluation analysis.
5. React interface and usability.
6. Schema/validator design, test integration, documentation and responsible-use review.

All contributors should inspect prompts, ground truth, failure cases, and experiment limitations before claiming a winner. P6 is a combined candidate, not presumed best.
