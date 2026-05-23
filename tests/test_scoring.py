from cellcheck.core import calculate_score_summary
from cellcheck.models import CellCorrectionResult, ResultStatus, RuleType


def build_result(
    *,
    status: ResultStatus,
    weight: float = 2.0,
    score_awarded: float = 0.0,
) -> CellCorrectionResult:
    return CellCorrectionResult(
        rule_id=f"rule-{status.value}",
        sheet_name="Sheet1",
        cell="A1",
        range_ref=None,
        rule_type=RuleType.TEXT_VALUE,
        expected_formula=None,
        student_formula=None,
        expected_value="x",
        student_value="x",
        weight=weight,
        score_awarded=score_awarded,
        status=status,
        message="test",
        teacher_comment="",
    )


def test_score_summary_all_passed() -> None:
    results = [
        build_result(status=ResultStatus.PASSED, score_awarded=2.0),
        build_result(status=ResultStatus.PASSED, score_awarded=2.0),
    ]
    summary = calculate_score_summary(results, max_grade=30.0)
    assert summary.passed == 2
    assert summary.failed == 0
    assert summary.final_grade == 30.0


def test_score_summary_some_failed() -> None:
    results = [
        build_result(status=ResultStatus.PASSED, score_awarded=2.0),
        build_result(status=ResultStatus.FAILED, score_awarded=0.0),
    ]
    summary = calculate_score_summary(results, max_grade=30.0)
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.awarded_weight == 2.0


def test_final_grade_on_max_grade_100() -> None:
    results = [
        build_result(status=ResultStatus.PASSED, weight=2.0, score_awarded=2.0),
        build_result(status=ResultStatus.PASSED, weight=3.0, score_awarded=1.5),
    ]
    summary = calculate_score_summary(results, max_grade=100.0)
    assert summary.final_grade == 70.0


def test_final_grade_on_max_grade_10() -> None:
    results = [
        build_result(status=ResultStatus.PASSED, weight=4.0, score_awarded=2.0),
        build_result(status=ResultStatus.FAILED, weight=1.0, score_awarded=0.0),
    ]
    summary = calculate_score_summary(results, max_grade=10.0)
    assert summary.final_grade == 4.0


def test_total_weight_zero_returns_final_grade_zero() -> None:
    results = []
    summary = calculate_score_summary(results, max_grade=30.0)
    assert summary.total_weight == 0
    assert summary.final_grade == 0.0


def test_status_counts_include_manual_review_skipped_and_error() -> None:
    results = [
        build_result(status=ResultStatus.PASSED, score_awarded=1.0, weight=1.0),
        build_result(status=ResultStatus.FAILED, score_awarded=0.0, weight=1.0),
        build_result(status=ResultStatus.MANUAL_REVIEW, score_awarded=0.0, weight=1.0),
        build_result(status=ResultStatus.SKIPPED, score_awarded=0.0, weight=1.0),
        build_result(status=ResultStatus.ERROR, score_awarded=0.0, weight=1.0),
    ]
    summary = calculate_score_summary(results, max_grade=10.0)
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.manual_review == 1
    assert summary.skipped == 1
    assert summary.errors == 1
