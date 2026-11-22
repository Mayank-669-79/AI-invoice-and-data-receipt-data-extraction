from datetime import datetime
from typing import Any


def _recognizable_date(value: str) -> bool:
    formats = (
        "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
        "%d.%m.%Y", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
        "%d/%m/%y", "%m/%d/%y", "%d-%b-%Y", "%d-%B-%Y",
    )
    return any(_matches_date(value, fmt) for fmt in formats)


def _matches_date(value: str, fmt: str) -> bool:
    try:
        datetime.strptime(value.strip(), fmt)
        return True
    except ValueError:
        return False


def validate_invoice(invoice: dict[str, Any], tolerance: float = 0.02) -> list[dict[str, str]]:
    """Return review warnings only; never alter source/model-extracted values."""
    warnings: list[dict[str, str]] = []
    for key, label in (
        ("vendor_name", "Vendor name"),
        ("invoice_number", "Invoice number"),
        ("invoice_date", "Invoice date"),
        ("total_amount", "Total amount"),
    ):
        if invoice.get(key) in (None, ""):
            warnings.append({"code": "missing_field", "field": key, "message": f"{label} was not identified; review the source document."})

    for field in ("invoice_date", "due_date"):
        value = invoice.get(field)
        if value not in (None, "") and not _recognizable_date(str(value)):
            warnings.append({"code": "date_unverified", "field": field, "message": f"{field.replace('_', ' ').capitalize()} format could not be recognized; compare the preserved value with the source."})

    subtotal, tax, total = invoice.get("subtotal"), invoice.get("tax_amount"), invoice.get("total_amount")
    if subtotal is not None and tax is not None and total is not None:
        expected = float(subtotal) + float(tax)
        if abs(expected - float(total)) > tolerance:
            warnings.append({
                "code": "total_mismatch", "field": "total_amount",
                "message": f"Printed subtotal plus tax ({expected:.2f}) differs from printed total ({float(total):.2f}); values were not changed.",
            })

    for index, item in enumerate(invoice.get("items") or []):
        quantity, unit_price, amount = item.get("quantity"), item.get("unit_price"), item.get("amount")
        if quantity is not None and unit_price is not None and amount is not None:
            expected = float(quantity) * float(unit_price)
            if abs(expected - float(amount)) > tolerance:
                warnings.append({
                    "code": "line_item_mismatch", "field": f"items[{index}].amount",
                    "message": f"Line item {index + 1}: quantity × unit price ({expected:.2f}) differs from printed amount ({float(amount):.2f}); values were not changed.",
                })
    return warnings
