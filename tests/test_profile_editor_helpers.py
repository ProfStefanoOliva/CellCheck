from cellcheck.ui.dialogs.profile_rule_dialog import ProfileRuleDialog
from cellcheck.ui.number_format import format_decimal_for_ui, parse_decimal_input
from cellcheck.ui.pages.profile_import_page import ProfilePage


def test_parse_decimal_input_accepts_comma_decimal() -> None:
    assert parse_decimal_input("0,7") == 0.7


def test_parse_decimal_input_accepts_dot_decimal() -> None:
    assert parse_decimal_input("0.7") == 0.7


def test_parse_decimal_input_accepts_two_decimal_places_with_comma() -> None:
    assert parse_decimal_input("1,25") == 1.25


def test_parse_decimal_input_rejects_ambiguous_mixed_separators() -> None:
    try:
        parse_decimal_input("1.000,5")
    except ValueError:
        return
    raise AssertionError("ambiguous decimal input should not be accepted")


def test_format_decimal_for_ui_uses_comma() -> None:
    assert format_decimal_for_ui(0.7) == "0,7"


def test_format_decimal_for_ui_hides_useless_decimal_zero() -> None:
    assert format_decimal_for_ui(1.0) == "1"


def test_format_decimal_for_ui_limits_noise() -> None:
    assert format_decimal_for_ui(0.333333, max_decimals=4) == "0,3333"


def test_parse_positive_weight_accepts_comma_decimal() -> None:
    assert ProfileRuleDialog._parse_positive_weight("1,25") == 1.25


def test_parse_positive_weight_rejects_zero() -> None:
    try:
        ProfileRuleDialog._parse_positive_weight("0")
    except ValueError:
        return
    raise AssertionError("zero weight should not be accepted")


def test_quota_vote_text_formats_integer_result() -> None:
    assert ProfilePage._quota_vote_text(1.0, 10.0, 100.0) == "10"


def test_quota_vote_text_formats_fractional_result() -> None:
    assert ProfilePage._quota_vote_text(0.5, 10.0, 100.0) == "5"


def test_quota_vote_text_uses_italian_decimal_format() -> None:
    assert ProfilePage._quota_vote_text(1.0, 8.0, 10.0) == "1,25"
