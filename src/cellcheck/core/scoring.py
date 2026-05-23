"""Scoring helpers for correction results."""

from __future__ import annotations

from cellcheck.models import CellCorrectionResult, ResultStatus, ScoreSummary


def calculate_score_summary(
    results: list[CellCorrectionResult], max_grade: float
) -> ScoreSummary:
    """Aggregate correction results into a score summary."""
    total_rules = len(results)
    passed = sum(1 for result in results if result.status == ResultStatus.PASSED)
    failed = sum(1 for result in results if result.status == ResultStatus.FAILED)
    warnings = sum(1 for result in results if result.status == ResultStatus.WARNING)
    manual_review = sum(
        1 for result in results if result.status == ResultStatus.MANUAL_REVIEW
    )
    skipped = sum(1 for result in results if result.status == ResultStatus.SKIPPED)
    errors = sum(1 for result in results if result.status == ResultStatus.ERROR)

    total_weight = sum(max(result.weight, 0) for result in results)
    awarded_weight = sum(max(result.score_awarded, 0) for result in results)

    if total_weight == 0 or max_grade <= 0:
        final_grade = 0.0
    else:
        final_grade = round((awarded_weight / total_weight) * max_grade, 2)

    return ScoreSummary(
        total_rules=total_rules,
        passed=passed,
        failed=failed,
        warnings=warnings,
        manual_review=manual_review,
        skipped=skipped,
        errors=errors,
        total_weight=total_weight,
        awarded_weight=awarded_weight,
        final_grade=max(final_grade, 0.0),
    )
