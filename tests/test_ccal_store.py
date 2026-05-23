from pathlib import Path

import pytest

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
from cellcheck.storage import (
    CcalDocumentTypeError,
    CcalFileExistsError,
    CcalJsonError,
    InvalidCcalExtensionError,
    load_profile,
    load_report,
    read_document_type,
    save_profile,
    save_report,
    validate_ccal_path,
)


def build_profile() -> CorrectionProfile:
    return CorrectionProfile(
        exercise_name="Budget Exercise",
        max_grade=30.0,
        source_empty_workbook="exercise.xlsx",
        source_solution_workbook="solution.xlsm",
        source_workbook_format=WorkbookFormat.XLSM,
        macro_enabled=True,
        worksheets=[
            WorksheetProfile(
                sheet_name="Sheet1",
                rules=[
                    CorrectionRule(
                        id="rule-1",
                        sheet_name="Sheet1",
                        cell="A1",
                        rule_type=RuleType.NUMERIC_VALUE,
                        expected_value=42,
                        weight=2.0,
                    )
                ],
            )
        ],
    )


def build_report() -> CorrectionReport:
    return CorrectionReport(
        profile_name="Budget Exercise",
        student_file="student.xlsx",
        student_workbook_format=WorkbookFormat.XLSX,
        macro_enabled=False,
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


def test_validate_ccal_path_accepts_ccal() -> None:
    path = validate_ccal_path("profile.ccal")
    assert path == Path("profile.ccal")


def test_validate_ccal_path_accepts_mixed_case_extension() -> None:
    path = validate_ccal_path("PROFILE.CCAL")
    assert path == Path("PROFILE.CCAL")


def test_validate_ccal_path_rejects_json() -> None:
    with pytest.raises(InvalidCcalExtensionError):
        validate_ccal_path("profile.json")


def test_save_profile_creates_ccal_file(tmp_path: Path) -> None:
    path = tmp_path / "profile.ccal"
    written_path = save_profile(build_profile(), path)
    assert written_path == path
    assert path.exists()


def test_load_profile_reconstructs_valid_profile(tmp_path: Path) -> None:
    path = tmp_path / "profile.ccal"
    profile = build_profile()
    save_profile(profile, path)
    loaded = load_profile(path)
    assert loaded == profile


def test_save_report_creates_ccal_file(tmp_path: Path) -> None:
    path = tmp_path / "report.ccal"
    written_path = save_report(build_report(), path)
    assert written_path == path
    assert path.exists()


def test_load_report_reconstructs_valid_report(tmp_path: Path) -> None:
    path = tmp_path / "report.ccal"
    report = build_report()
    save_report(report, path)
    loaded = load_report(path)
    assert loaded == report


def test_read_document_type_recognizes_correction_profile(tmp_path: Path) -> None:
    path = tmp_path / "profile.ccal"
    save_profile(build_profile(), path)
    assert read_document_type(path).value == "correction_profile"


def test_read_document_type_recognizes_correction_report(tmp_path: Path) -> None:
    path = tmp_path / "report.ccal"
    save_report(build_report(), path)
    assert read_document_type(path).value == "correction_report"


def test_load_profile_rejects_correction_report(tmp_path: Path) -> None:
    path = tmp_path / "report.ccal"
    save_report(build_report(), path)
    with pytest.raises(CcalDocumentTypeError):
        load_profile(path)


def test_load_report_rejects_correction_profile(tmp_path: Path) -> None:
    path = tmp_path / "profile.ccal"
    save_profile(build_profile(), path)
    with pytest.raises(CcalDocumentTypeError):
        load_report(path)


def test_save_profile_does_not_overwrite_by_default(tmp_path: Path) -> None:
    path = tmp_path / "profile.ccal"
    save_profile(build_profile(), path)
    with pytest.raises(CcalFileExistsError):
        save_profile(build_profile(), path)


def test_save_profile_overwrites_when_enabled(tmp_path: Path) -> None:
    path = tmp_path / "profile.ccal"
    first_profile = build_profile()
    second_profile = build_profile().model_copy(update={"exercise_name": "Updated Exercise"})
    save_profile(first_profile, path)
    save_profile(second_profile, path, overwrite=True)
    loaded = load_profile(path)
    assert loaded.exercise_name == "Updated Exercise"


def test_malformed_json_raises_custom_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.ccal"
    path.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(CcalJsonError):
        load_profile(path)


def test_wrong_extension_raises_custom_error(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    with pytest.raises(InvalidCcalExtensionError):
        save_profile(build_profile(), path)
