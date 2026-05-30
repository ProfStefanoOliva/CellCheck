from cellcheck.models import CorrectionProfile, CorrectionRule, RuleType, WorksheetProfile
from cellcheck.ui.evaluation_table import (
    build_evaluation_table_text,
    safe_student_description,
    sanitize_windows_filename,
    suggested_evaluation_filename,
)
from cellcheck.ui.i18n import set_current_language


def _build_profile(rules: list[CorrectionRule], *, exercise_name: str = "Progetto Demo") -> CorrectionProfile:
    return CorrectionProfile(
        exercise_name=exercise_name,
        max_grade=10.0,
        worksheets=[WorksheetProfile(sheet_name="Foglio1", rules=rules)],
    )


def test_evaluation_table_uses_safe_teacher_note_when_available() -> None:
    set_current_language("it", persist=False)
    rule = CorrectionRule(
        id="rule-1",
        sheet_name="Foglio1",
        cell="A1",
        rule_type=RuleType.NON_EMPTY,
        weight=2.0,
        teacher_note="Inserire il titolo della tabella.",
        required_activity="Inserire il titolo della tabella.",
    )

    text = build_evaluation_table_text(_build_profile([rule]))

    assert "Inserire il titolo della tabella." in text


def test_evaluation_table_uses_neutral_fallback_when_note_is_missing() -> None:
    set_current_language("it", persist=False)
    rule = CorrectionRule(
        id="rule-1",
        sheet_name="Foglio1",
        cell="A1",
        rule_type=RuleType.NON_EMPTY,
        weight=2.0,
        teacher_note="",
        required_activity="",
    )

    assert (
        safe_student_description(rule)
        == "Completare la cella indicata secondo la consegna dell'esercizio."
    )


def test_evaluation_table_does_not_expose_formulas_or_expected_values() -> None:
    set_current_language("it", persist=False)
    rule = CorrectionRule(
        id="rule-1",
        sheet_name="Foglio1",
        cell="B2",
        rule_type=RuleType.FORMULA_EXACT,
        expected_formula="=SUM(A1:A3)",
        expected_value=42,
        weight=5.0,
        teacher_note="Formula attesa =SUM(A1:A3)",
        required_activity="Calcolare il totale richiesto dalla consegna.",
    )

    text = build_evaluation_table_text(_build_profile([rule]))

    assert "=SUM(A1:A3)" not in text
    assert "42" not in text
    assert "Formula attesa" not in text


def test_evaluation_table_uses_required_activity_when_present() -> None:
    set_current_language("it", persist=False)
    rule = CorrectionRule(
        id="rule-1",
        sheet_name="Foglio1",
        cell="C3",
        rule_type=RuleType.NON_EMPTY,
        weight=4.0,
        teacher_note="Nota tecnica da non esporre.",
        required_activity="Inserire il totale delle vendite annuali.",
    )

    text = build_evaluation_table_text(_build_profile([rule]))

    assert "Inserire il totale delle vendite annuali." in text
    assert "Nota tecnica da non esporre." not in text


def test_evaluation_table_includes_total_points_and_rule_points() -> None:
    set_current_language("it", persist=False)
    rules = [
        CorrectionRule(
            id="rule-1",
            sheet_name="Foglio1",
            cell="A1",
            rule_type=RuleType.NON_EMPTY,
            weight=1.0,
            teacher_note="Inserire un'intestazione descrittiva.",
            required_activity="Inserire un'intestazione descrittiva.",
        ),
        CorrectionRule(
            id="rule-2",
            sheet_name="Foglio1",
            cell="B2",
            rule_type=RuleType.NON_EMPTY,
            weight=3.0,
            teacher_note="Compilare la cella con il contenuto richiesto.",
            required_activity="Compilare la cella con il contenuto richiesto.",
        ),
    ]

    text = build_evaluation_table_text(_build_profile(rules))

    assert "Totale punti del compito: 10" in text
    assert "Punti: 2,5" in text
    assert "Punti: 7,5" in text


def test_suggested_filename_prefers_profile_name_and_sanitizes_it() -> None:
    profile = _build_profile([], exercise_name='Progetto: Excel/2026?')

    suggested = suggested_evaluation_filename(profile, None)

    assert suggested == "Progetto_ Excel_2026_TabValutazione.txt"


def test_suggested_filename_falls_back_to_profile_path_stem() -> None:
    suggested = suggested_evaluation_filename(None, r"C:\profili\Compito Finale.ccal")
    assert suggested == "Compito Finale_TabValutazione.txt"


def test_sanitize_windows_filename_strips_invalid_characters() -> None:
    assert sanitize_windows_filename('A<B>C:"D"/E\\F|G?* ') == "A_B_C_D_E_F_G_"
