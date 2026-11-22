# C11 — AI-Powered Invoice & Receipt Information Extraction

A prompt-engineering research prototype that turns invoices and receipts into structured, reviewable JSON. It compares six prompt strategies against a fixed hand-authored synthetic dataset. The application tries Gemini first and falls back to a local Ollama model when Gemini is unavailable. A local-only mode is available for sensitive documents.

## Current scope and honest limitations

The app accepts PDF, JPG/JPEG, PNG, and UTF-8 TXT files up to 15 MB. PyMuPDF reads digital PDF text; RapidOCR processes images, scanned PDF pages, and image-only pages in mixed PDFs. The backend validates model output with Pydantic and adds review warnings for missing key fields, unrecognized date strings, line-item arithmetic, and subtotal-plus-tax mismatches. It never silently changes extracted amounts.

The repository contains 50 synthetic **text** invoices and corresponding hand-authored ground-truth JSON. This supports a controlled prompt comparison, not a bundled scanned-document/OCR accuracy result. A separate OCR scorer is included: add scanned PDFs/images and matching UTF-8 transcriptions, then run `python -m evaluation.ocr_quality` to calculate character and word error rates independently. No scan set or OCR score is fabricated. The `unsupported_field_rate` is a proxy based on labels absent from the ground truth, not a manually adjudicated hallucination rate. No measured LLM scores are included in the starter package, and P6 is a candidate rather than a presumed winner. Review all model outputs before accounting use.

Invoice uploads are processed for the request and are not stored in an extraction history. In `LLM_PROVIDER=auto`, extracted document text is sent to Gemini first; if that call fails, it is sent to your local Ollama server. Use `LLM_PROVIDER=ollama` to guarantee the app does not call Gemini. Do not use confidential invoices in the synthetic benchmark or commit API keys.

## Run on Windows

Use Python 3.12 and Node.js 20.19+ or 22.12+. Open PowerShell in the project root (the folder containing `requirements.txt` and `frontend/`).

1. Create and activate the backend environment, then install dependencies. If you already have a working `.venv`, keep it and skip the first two lines.

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r .\requirements.txt
   ```

2. Create the environment file and set provider options. Keep this file private.

   ```powershell
   Copy-Item .\.env.example .\.env
   notepad .\.env
   ```

   For the default automatic mode set `LLM_PROVIDER=auto`, `GEMINI_API_KEY` to your Gemini key, `GEMINI_MODEL=gemini-3.8-flash`, and `OLLAMA_MODEL=qwen3:4b` (or the exact tag displayed by `ollama list`). If only one Ollama model is installed, `OLLAMA_MODEL` can be left blank for auto-discovery. Keep the Ollama Desktop app running. `OLLAMA_TIMEOUT_SECONDS=600` allows slower local CPU generation more time; structured extraction defaults to Qwen3 thinking disabled. A blank Gemini key is acceptable only if local Ollama fallback is available, or if you set `LLM_PROVIDER=ollama`.

   ```powershell
   ollama list
   ```

3. Start the API from the project root and leave that terminal open.

   ```powershell
   python -m uvicorn backend.main:app --reload --port 8000
   ```

   Check [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) for `{"status":"healthy"}`. Interactive API docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

4. Open another PowerShell window, enter the frontend folder, install its locked dependencies, and start Vite.

   ```powershell
   cd .\frontend
   npm ci
   npm run dev
   ```

   Open the localhost URL printed by Vite, usually `http://localhost:5173`. Keep both terminals running.

The result card identifies the provider and model used. If Gemini returns an error such as 503, the app attempts Ollama. A 4B model can be slow on a CPU; the first request may also take longer while Ollama loads the weights.

## Provider settings

`LLM_PROVIDER=auto` is Gemini-first, then Ollama. `LLM_PROVIDER=gemini` uses only Gemini. `LLM_PROVIDER=ollama` uses only the local Ollama server and never sends invoice text to Gemini. The Ollama API normally runs at `http://127.0.0.1:11434`; set `OLLAMA_BASE_URL` or `OLLAMA_MODEL` only if your configuration differs.

Prompt experiments do not auto-fallback between providers. Set `EXPERIMENT_PROVIDER=gemini` or `EXPERIMENT_PROVIDER=ollama` so all prompts in one comparison use the same model/provider. Gemini is the default; 300 requests (6 prompts × 50 documents) may use quota or incur charges.

## Prompt strategies and experiments

The instructions are stored independently in `backend/prompts/prompt_v1.txt` through `prompt_v6.txt`:

- P1: zero-shot baseline.
- P2: role-based.
- P3: few-shot, two synthetic formatting examples.
- P4: task decomposition.
- P5: explicit constraints and anti-hallucination rules.
- P6: combined candidate, whose superiority must be measured rather than assumed.

Run experiment commands from the **project root**, not from inside `experiments/` or `backend/`. If you see `No module named experiments`, return to the folder containing `requirements.txt`. If you see `No module named dotenv`, activate the project's `.venv` and install dependencies from that same root with `python -m pip install -r .\requirements.txt`.

First verify the provider with one prompt and one invoice. This makes exactly one model request, prints the setup/network error if it fails, and does not overwrite the full-comparison CSV/report:

```powershell
python -m experiments.experiment_runner --provider gemini --prompt p1 --limit 1
```

If that succeeds, run the controlled comparison from the repository root after setting the experiment provider/key:

```powershell
python -m experiments.experiment_runner
```

This compares every prompt over the same paired 50-case dataset. It writes `experiments/prompt_results.csv`, `documentation/experiment_results/latest_report.json`, and accuracy/latency PNG plots. Rank the actual measured results with:

```powershell
python -m experiments.comparison
```

The evaluation reports field-level accuracy over explicitly labeled keys, exact-record accuracy, exact line-item match, schema-valid response rate, missing-field handling, unsupported-value proxy, model-call latency, and token counts when returned by the provider. It creates comparison charts for these measures and accuracy-versus-token trade-offs. Latency does not include OCR. For a separate OCR evaluation, add image/PDF scans and same-stem transcripts under `dataset/ocr_ground_truth/`, then run `python -m evaluation.ocr_quality`; its character/word error rates do not conflate OCR mistakes with LLM extraction mistakes. The default synthetic text set does not measure OCR or general real-world performance. Review ground truth before making research claims.

## Tests and production build

From the project root:

```powershell
python -m pytest -q
```

Frontend checks:

```powershell
cd .\frontend
npm ci
npm run build
npm run lint
```

The test suite uses mocked provider calls; it does not consume Gemini quota or require a running Ollama server.

## Project structure

```text
invoice-extraction/
├── frontend/
│   ├── src/                 # Vite entrypoint and shared styles
│   ├── components/          # Upload, results, evaluation views
│   ├── pages/               # Workspace page and application state
│   └── package.json
├── backend/
│   ├── main.py
│   ├── routes/invoice_routes.py
│   ├── services/            # document_processor, ocr_service, llm_service, extraction_service
│   ├── prompts/             # prompt_v1.txt through prompt_v6.txt
│   ├── schemas/invoice_schema.py
│   └── validators/invoice_validator.py
├── dataset/
│   ├── invoices/            # 50 paired synthetic .txt inputs
│   ├── ground_truth/         # matching JSON labels
│   └── ocr_ground_truth/     # optional scan transcripts for CER/WER
├── experiments/             # runner, CSV results, comparison utility
├── evaluation/              # accuracy, unsupported-field proxy, visualizations
├── tests/
├── documentation/           # architecture/workflow diagrams, notes, measured outputs
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## University proposal alignment

The proposal named MongoDB history, GPT benchmarking, Vercel/Render deployment, and a separate OCR-quality study as optional or future directions. They are not represented as completed features. The current app intentionally does not persist uploaded invoices or extraction history. Six-person responsibilities and architecture notes are documented in `documentation/architecture.md`. Use only synthetic, licensed, or explicitly authorized documents; protect API keys and manually verify financial values.
