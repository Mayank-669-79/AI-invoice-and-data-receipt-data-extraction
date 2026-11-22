SCALAR_FIELDS = (
    "invoice_number", "invoice_date", "due_date", "vendor_name", "vendor_address",
    "vendor_gstin", "customer_name", "customer_address", "customer_gstin", "subtotal",
    "tax_amount", "total_amount", "currency", "payment_terms", "description",
)


def score_missing_and_unsupported(truth: dict, prediction: dict) -> dict[str, int | float | None]:
    """The unsupported rate is a proxy: predicted values for scalar labels absent/null in truth."""
    missing = [field for field in SCALAR_FIELDS if truth.get(field) in (None, "")]
    handled = sum(prediction.get(field) in (None, "") for field in missing)
    unsupported = len(missing) - handled
    return {
        "missing_field_correct": handled,
        "missing_field_total": len(missing),
        "missing_field_handling_accuracy": handled / len(missing) if missing else None,
        "unsupported_field_count": unsupported,
        "unsupported_field_candidates": len(missing),
        "unsupported_field_rate": unsupported / len(missing) if missing else None,
    }
