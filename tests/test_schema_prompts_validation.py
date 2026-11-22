from backend.services.prompt_loader import PROMPTS, get_prompt
from backend.schemas.invoice_schema import InvoiceSchema
from backend.validators.invoice_validator import validate_invoice


def test_six_distinct_prompts_load_from_versioned_text_files():
    assert len(PROMPTS) == 6
    assert [prompt.id for prompt in PROMPTS] == [f"p{i}" for i in range(1, 7)]
    assert "example" in get_prompt("p3").description.lower()
    assert "not presumed best" in get_prompt("p6").technique.lower()


def test_schema_handles_unknown_optional_values_and_has_no_google_unsupported_key():
    invoice = InvoiceSchema.model_validate({"vendor_name": "Acme", "items": [{"description": "Pen", "amount": 6}]})
    assert invoice.total_amount is None
    assert invoice.items[0].quantity is None

    def contains_additional_properties(value):
        if isinstance(value, dict):
            return "additionalProperties" in value or any(contains_additional_properties(child) for child in value.values())
        if isinstance(value, list):
            return any(contains_additional_properties(child) for child in value)
        return False

    assert not contains_additional_properties(InvoiceSchema.model_json_schema())


def test_arithmetic_and_unrecognized_date_create_warnings_without_mutation():
    data = {"vendor_name": "Acme", "invoice_number": "A-1", "invoice_date": "not a date", "subtotal": 10, "tax_amount": 1, "total_amount": 12, "items": [{"quantity": 2, "unit_price": 3, "amount": 7}]}
    original_total = data["total_amount"]
    codes = {warning["code"] for warning in validate_invoice(data)}
    assert {"date_unverified", "total_mismatch", "line_item_mismatch"}.issubset(codes)
    assert data["total_amount"] == original_total
