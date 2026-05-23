from pydantic import ValidationError

from cellcheck.models import (
    CellCorrectionResult,
    CorrectionProfile,
    CorrectionReport,
    CorrectionRule,
    ResultStatus,
    RuleType,
    ScoreSummary,
    WorkbookFormat,
    WorksheetProfile,
)


def build_rule() -> CorrectionRule:
    return CorrectionRule(
        id="rule-1",
        sheet_name="Sheet1",
        cell="A1",
        rule_type=RuleType.NUMERIC_VALUE,
        expected_value=42,
        weight=2.0,
    )


def build_profile() -> CorrectionProfile:
    return CorrectionProfile(
        exercise_name="Budget Exercise",
        max_grade=30.0,
        source_empty_workbook="exercise.xlsx",
        source_solution_workbook="solution.xlsx",
        source_workbook_format=WorkbookFormat.XLSX,
        worksheets=[
            WorksheetProfile(
                sheet_name="Sheet1",
                rules=[build_rule()],
            )
        ],
    )


def build_report() -> CorrectionReport:
    return CorrectionReport(
        profile_name="Budget Exercise",
        student_file="student.xlsm",
        student_workbook_format=WorkbookFormat.XLSM,
        macro_enabled=True,
        max_grade=30.0,
        summary=ScoreSummary(
            total_rules=1,
            passed=1,
            failed=0,
            warnings=0,
            manual_review=0,
            skipped=0,
            errors=0,
            total_weight=2.0,
            awarded_weight=2.0,
            final_grade=30.0,
        ),
        results=[
            CellCorrectionResult(
                rule_id="rule-1",
                sheet_name="Sheet1",
                cell="A1",
                rule_type=RuleType.NUMERIC_VALUE,
                expected_value=42,
                student_value=42,
                weight=2.0,
                score_awarded=2.0,
                status=ResultStatus.PASSED,
                message="Value matches.",
            )
        ],
    )


def test_models_are_importable() -> None:
    assert CorrectionProfile is not None
    assert CorrectionReport is not None
    assert WorkbookFormat.XLSX.value == "xlsx"


def test_create_valid_correction_profile() -> None:
    profile = build_profile()
    assert profile.document_type.value == "correction_profile"
    assert profile.worksheets[0].rules[0].id == "rule-1"


def test_create_valid_correction_report() -> None:
    report = build_report()
    assert report.document_type.value == "correction_report"
    assert report.results[0].status == ResultStatus.PASSED


def test_negative_weight_is_rejected() -> None:
    try:
        CorrectionRule(
            id="rule-2",
            sheet_name="Sheet1",
            cell="A2",
            rule_type=RuleType.TEXT_VALUE,
            expected_value="hello",
            weight=-1.0,
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("negative weight should not be accepted")


def test_non_positive_max_grade_is_rejected() -> None:
    try:
        CorrectionProfile(
            exercise_name="Invalid",
            max_grade=0,
            worksheets=[],
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("non-positive max_grade should not be accepted")


def test_score_awarded_greater_than_weight_is_rejected() -> None:
    try:
        CellCorrectionResult(
            rule_id="rule-3",
            sheet_name="Sheet1",
            cell="A3",
            rule_type=RuleType.NUMERIC_VALUE,
            expected_value=10,
            student_value=8,
            weight=1.0,
            score_awarded=1.5,
            status=ResultStatus.FAILED,
            message="Too high score.",
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("score_awarded greater than weight should not be accepted")


def test_supports_xlsx_workbook_format() -> None:
    profile = build_profile()
    assert profile.source_workbook_format == WorkbookFormat.XLSX


def test_supports_xlsm_workbook_format() -> None:
    report = build_report()
    assert report.student_workbook_format == WorkbookFormat.XLSM
    assert report.macro_enabled is True


def test_correction_profile_json_roundtrip() -> None:
    profile = build_profile()
    payload = profile.to_json_string()
    restored = CorrectionProfile.from_json_string(payload)
    assert restored == profile


def test_correction_report_json_roundtrip() -> None:
    report = build_report()
    payload = report.to_json_string()
    restored = CorrectionReport.from_json_string(payload)
    assert restored == report
