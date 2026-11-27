from evaluation.accuracy import score_accuracy
from evaluation.hallucination import score_missing_and_unsupported
from experiments.experiment_runner import load_cases


def test_accuracy_uses_labeled_keys_and_item_exact_match():
    truth = {"vendor_name": "Acme", "items": [{"description": "Pen", "quantity": 2, "unit_price": 3, "amount": 6}]}
    predicted = {"vendor_name": "Acme", "items": [{"description": "Pen", "quantity": 2, "unit_price": 3.0, "amount": 6.0}], "invoice_date": None}
    score = score_accuracy(truth, predicted)
    assert score["field_accuracy"] == 1
    assert score["record_exact"] is True
    assert score["line_item_exact"] is True


def test_optional_null_keys_do_not_break_exact_line_item_match():
    truth = {"items": [{"description": "Screen replacement", "amount": 55.65}]}
    prediction = {"items": [{"description": "Screen replacement", "quantity": None, "unit_price": None, "amount": 55.65}]}
    assert score_accuracy(truth, prediction)["line_item_exact"] is True


def test_missing_handling_proxy_is_computed_and_dataset_pairs_50_cases():
    score = score_missing_and_unsupported({}, {"vendor_name": "invented"})
    assert score["unsupported_field_count"] == 1
    assert score["missing_field_handling_accuracy"] < 1
    cases = load_cases()
    assert len(cases) == 50
    assert cases[0]["id"] == "synthetic-001"


def test_few_shot_examples_are_not_leaked_into_the_fixed_benchmark():
    from backend.services.prompt_loader import get_prompt

    prompt = get_prompt("p3").instructions
    texts = [case["text"] for case in load_cases()]
    assert "Example 2" in prompt
    assert all("Maple Works" not in text and "Acme | Invoice A-1" not in text for text in texts)
