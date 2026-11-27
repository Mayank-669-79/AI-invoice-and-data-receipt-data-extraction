import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "documentation" / "experiment_results" / "latest_report.json"
OUTPUT = ROOT / "documentation" / "experiment_results"


def _save_bar(prompts: list[dict], metric: str, title: str, filename: str, output_dir: Path, bounded: bool = True) -> Path:
    labels = [item["prompt_id"].upper() for item in prompts]
    values = [item.get(metric) for item in prompts]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, [float("nan") if value is None else value for value in values], color="#176b69")
    ax.set_title(title)
    ax.set_ylabel("Rate" if bounded else "Seconds")
    if bounded:
        ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    path = output_dir / filename
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def render_report(report_path: Path = REPORT, output_dir: Path = OUTPUT) -> list[Path]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    prompts = report.get("prompts", [])
    if not prompts:
        raise ValueError("Report has no prompt results to visualize.")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [
        _save_bar(prompts, metric, title, filename, output_dir)
        for metric, title, filename in (
            ("field_accuracy", "Field-level accuracy", "field_accuracy.png"),
            ("exact_record_accuracy", "Exact-record accuracy", "record_accuracy.png"),
            ("line_item_exact_accuracy", "Exact line-item match", "item_accuracy.png"),
            ("valid_json_rate", "Schema-valid response rate", "json_validity.png"),
            ("missing_field_handling_accuracy", "Missing-field handling", "missing_field_handling.png"),
            ("unsupported_field_rate", "Unsupported-value proxy rate", "unsupported_field_rate.png"),
        )
    ]
    outputs.append(_save_bar(prompts, "mean_latency_seconds", "Mean model-call latency", "mean_latency.png", output_dir, bounded=False))

    labels = [item["prompt_id"].upper() for item in prompts]
    x = list(range(len(prompts)))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8, 4.5))
    inputs = [item.get("input_tokens") or 0 for item in prompts]
    outputs_tokens = [item.get("output_tokens") or 0 for item in prompts]
    ax.bar([value - width / 2 for value in x], inputs, width, label="Input", color="#176b69")
    ax.bar([value + width / 2 for value in x], outputs_tokens, width, label="Output", color="#c27b43")
    ax.set_xticks(x, labels)
    ax.set_title("Token usage (provider metadata when available)")
    ax.set_ylabel("Tokens")
    if not any(inputs) and not any(outputs_tokens):
        ax.text(0.5, 0.5, "Token counts were not returned by this provider", ha="center", va="center", transform=ax.transAxes)
    else:
        ax.legend()
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    path = output_dir / "token_usage.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    outputs.append(path)

    points = [(item.get("input_tokens", 0) + item.get("output_tokens", 0), item.get("field_accuracy")) for item in prompts if item.get("input_tokens") is not None and item.get("output_tokens") is not None and item.get("field_accuracy") is not None]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if points:
        ax.scatter([point[0] for point in points], [point[1] for point in points], color="#176b69")
        for prompt, point in zip([item for item in prompts if item.get("input_tokens") is not None and item.get("output_tokens") is not None and item.get("field_accuracy") is not None], points):
            ax.annotate(prompt["prompt_id"].upper(), point, xytext=(5, 5), textcoords="offset points")
    else:
        ax.text(0.5, 0.5, "Token counts were not returned by this provider", ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Field accuracy vs. total tokens")
    ax.set_xlabel("Input + output tokens")
    ax.set_ylabel("Field accuracy")
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    path = output_dir / "accuracy_vs_tokens.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    outputs.append(path)
    return outputs


if __name__ == "__main__":
    for path in render_report():
        print(path)
