from evaluation.ocr_quality import character_error_rate, word_error_rate


def test_ocr_error_rates_normalize_case_and_whitespace():
    assert character_error_rate("Vendor\nTotal 12.00", "vendor total 12.00") == 0
    assert word_error_rate("Vendor Name", "Vendor Nmae") > 0


def test_empty_reference_is_handled_without_division_by_zero():
    assert character_error_rate("", "") == 0
    assert character_error_rate("", "extra") == 1
    assert word_error_rate("", "extra word") == 1
