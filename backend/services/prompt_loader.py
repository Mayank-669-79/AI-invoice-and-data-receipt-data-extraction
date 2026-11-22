import json
from dataclasses import dataclass
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"
COMMON_CONTRACT = """Return an object with: invoice_number, invoice_date, due_date, vendor_name, vendor_address, vendor_gstin, customer_name, customer_address, customer_gstin, items (array of description, quantity, unit_price, amount), subtotal, tax_amount, total_amount, currency, payment_terms, and description. Use numeric values for readable quantities and amounts; use null for unknown scalar fields and [] when no line items are present. Return no prose."""


@dataclass(frozen=True)
class PromptVersion:
    id: str
    name: str
    technique: str
    description: str
    instructions: str


def _load_prompt(path: Path) -> PromptVersion:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Prompt metadata missing: {path.name}")
    metadata_text, instructions = text[4:].split("\n---\n", 1)
    metadata = json.loads(metadata_text)
    return PromptVersion(**metadata, instructions=instructions.strip())


PROMPTS = tuple(_load_prompt(PROMPT_DIR / f"prompt_v{i}.txt") for i in range(1, 7))


def get_prompt(prompt_id: str) -> PromptVersion:
    for prompt in PROMPTS:
        if prompt.id == prompt_id:
            return prompt
    raise ValueError(f"Unknown prompt version: {prompt_id}")


def public_prompts() -> list[dict[str, str]]:
    return [{key: getattr(p, key) for key in ("id", "name", "technique", "description")} for p in PROMPTS]
