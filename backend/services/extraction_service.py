from dataclasses import dataclass

from backend.schemas.invoice_schema import InvoiceSchema
from backend.services.llm_service import ExtractionResult, extract_invoice_data
from backend.validators.invoice_validator import validate_invoice


@dataclass(frozen=True)
class InvoiceExtraction:
    invoice_data: dict
    warnings: list[dict[str, str]]
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


def extract_invoice(text: str, prompt_id: str = "p6") -> InvoiceExtraction:
    result: ExtractionResult = extract_invoice_data(text, prompt_id)
    invoice = InvoiceSchema.model_validate(result.invoice_data).model_dump()
    return InvoiceExtraction(
        invoice_data=invoice,
        warnings=validate_invoice(invoice),
        provider=result.provider,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
