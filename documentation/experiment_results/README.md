# Experiment results

No measured model results are bundled. The initial `experiments/prompt_results.csv` contains only its column header. Run `python -m experiments.experiment_runner` from the project root to produce the real JSON report, CSV comparison, and visualizations. The default run makes 300 API requests (six prompts × 50 synthetic invoices); check provider quota/cost before running it. The data are text-only, so the experiment does not measure OCR quality.

For OCR metrics, add appropriately licensed scanned documents and same-stem UTF-8 text transcripts, then run `python -m evaluation.ocr_quality`. That writes separate `ocr_quality.json` and `ocr_quality.csv` files; the current bundle has no scan/transcript pairs and therefore no OCR measurements.
