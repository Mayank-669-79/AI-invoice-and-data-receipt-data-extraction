from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "prompt_results.csv"


def compare_results(path: Path = RESULTS) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError("No measured prompt_results.csv exists yet. Run `python -m experiments.experiment_runner` first.")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError("The results CSV contains headers only; run the experiment before comparing prompts.")
    return frame.sort_values(["field_accuracy", "exact_record_accuracy"], ascending=False, na_position="last")


if __name__ == "__main__":
    ranked = compare_results()
    print(ranked[["prompt_id", "name", "field_accuracy", "exact_record_accuracy", "valid_json_rate", "mean_latency_seconds"]].to_string(index=False))
