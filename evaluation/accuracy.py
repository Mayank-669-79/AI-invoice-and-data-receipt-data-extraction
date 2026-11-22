from typing import Any


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize(child) for key, child in sorted(value.items()) if child is not None}
    if isinstance(value, list):
        return [normalize(child) for child in value]
    if isinstance(value, float):
        return round(value, 2)
    return value


def score_accuracy(truth: dict, prediction: dict) -> dict[str, Any]:
    """Score only explicitly labeled ground-truth keys; do not score omitted labels as false."""
    fields = list(truth)
    correct = sum(normalize(prediction.get(field)) == normalize(truth[field]) for field in fields)
    field_total = len(fields)
    has_items = "items" in truth
    item_exact = normalize(prediction.get("items", [])) == normalize(truth.get("items", [])) if has_items else None
    return {
        "field_correct": correct,
        "field_total": field_total,
        "field_accuracy": correct / field_total if field_total else None,
        "record_exact": correct == field_total if field_total else None,
        "line_item_exact": item_exact,
    }
