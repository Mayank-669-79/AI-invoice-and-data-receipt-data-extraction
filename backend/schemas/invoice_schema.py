from typing import Optional

from pydantic import BaseModel, Field


class InvoiceItem(BaseModel):
    """A single line item as printed on an invoice."""

    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class InvoiceSchema(BaseModel):
    """Normalized invoice fields. Unknown or absent values remain null."""

    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_gstin: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_gstin: Optional[str] = None
    items: list[InvoiceItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    payment_terms: Optional[str] = None
    description: Optional[str] = None
