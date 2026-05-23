"""Correction engine for applying a profile to a student workbook."""

from __future__ import annotations

from pathlib import Path

from cellcheck.models import (
    CellCorrectionResult,
    CorrectionProfile,
    CorrectionReport,
    CorrectionRule,
    ResultStatus,
    RuleType,
    ToleranceConfig,
    ToleranceMode,
)

from .errors import CorrectionRuleError, UnsupportedRuleTypeError, WorksheetNotFoundError
from .scoring import calculate_score_summary
from .workbook_reader import WorkbookReader


class CorrectionEngine:
    """Apply correction rules to a student workbook and produce a report."""

    def correct_workbook(
        self, profile: CorrectionProfile, student_workbook_path: str | Path
    ) -> CorrectionReport:
        """Apply all profile rules to the student workbook."""
        student_path = Path(student_workbook_path)
        results: list[CellCorrectionResult] = []

        with WorkbookReader(student_path, data_only=False) as formula_reader, WorkbookReader(
            student_path, data_only=True
        ) as value_reader:
            workbook_info = formula_reader.get_workbook_info()

            for worksheet_profile in profile.worksheets:
                if worksheet_profile.sheet_name not in workbook_info.sheet_names:
                    for rule in worksheet_profile.rules:
                        results.append(self._build_missing_sheet_result(rule))
                    continue

                for rule in worksheet_profile.rules:
                    results.append(
                        self._evaluate_rule(
                            rule=rule,
                            formula_reader=formula_reader,
                            value_reader=value_reader,
                        )
                    )

            summary = calculate_score_summary(results, profile.max_grade)

            return CorrectionReport(
                minimum_cellcheck_version="0.7.0",
                profile_name=profile.exercise_name,
                student_file=str(student_path),
                student_workbook_format=workbook_info.workbook_format,
                macro_enabled=workbook_info.macro_enabled,
                max_grade=profile.max_grade,
                summary=summary,
                results=results,
            )

    def _evaluate_rule(
        self,
        *,
        rule: CorrectionRule,
        formula_reader: WorkbookReader,
        value_reader: WorkbookReader,
    ) -> CellCorrectionResult:
        """Evaluate a single correction rule."""
        if not rule.enabled:
            return self._build_result(
                rule=rule,
                status=ResultStatus.SKIPPED,
                message="Regola disabilitata.",
                score_awarded=0.0,
            )

        if rule.range_ref is not None:
            return self._build_result(
                rule=rule,
                status=ResultStatus.MANUAL_REVIEW,
                message="Range non ancora supportati in questa fase.",
                score_awarded=0.0,
            )

        if rule.cell is None:
            return self._build_result(
                rule=rule,
                status=ResultStatus.ERROR,
                message="Riferimento cella mancante.",
                score_awarded=0.0,
            )

        try:
            formula_snapshot = formula_reader.get_cell_snapshot(rule.sheet_name, rule.cell)
            value_snapshot = value_reader.get_cell_snapshot(rule.sheet_name, rule.cell)
        except WorksheetNotFoundError:
            return self._build_missing_sheet_result(rule)
        except Exception as exc:
            return self._build_result(
                rule=rule,
                status=ResultStatus.ERROR,
                message=f"Errore nella lettura della cella: {exc}",
                score_awarded=0.0,
            )

        try:
            return self._dispatch_rule(
                rule=rule,
                formula_snapshot=formula_snapshot,
                value_snapshot=value_snapshot,
            )
        except UnsupportedRuleTypeError as exc:
            return self._build_result(
                rule=rule,
                status=ResultStatus.WARNING,
                student_formula=formula_snapshot.formula,
                student_value=value_snapshot.value,
                message=str(exc),
                score_awarded=0.0,
            )
        except CorrectionRuleError as exc:
            return self._build_result(
                rule=rule,
                status=ResultStatus.ERROR,
                student_formula=formula_snapshot.formula,
                student_value=value_snapshot.value,
                message=str(exc),
                score_awarded=0.0,
            )

    def _dispatch_rule(self, *, rule, formula_snapshot, value_snapshot) -> CellCorrectionResult:
        """Route rule evaluation to the matching implementation."""
        if rule.rule_type == RuleType.FORMULA_EXACT:
            return self._evaluate_formula_exact(rule, formula_snapshot, value_snapshot)
        if rule.rule_type == RuleType.NUMERIC_VALUE:
            return self._evaluate_numeric_value(rule, formula_snapshot, value_snapshot)
        if rule.rule_type == RuleType.TEXT_VALUE:
            return self._evaluate_text_value(rule, formula_snapshot, value_snapshot)
        if rule.rule_type == RuleType.TEXT_NORMALIZED:
            return self._evaluate_text_normalized(rule, formula_snapshot, value_snapshot)
        if rule.rule_type == RuleType.NON_EMPTY:
            return self._evaluate_non_empty(rule, formula_snapshot, value_snapshot)
        if rule.rule_type == RuleType.EMPTY:
            return self._evaluate_empty(rule, formula_snapshot, value_snapshot)
        if rule.rule_type == RuleType.MANUAL_REVIEW:
            return self._build_result(
                rule=rule,
                status=ResultStatus.MANUAL_REVIEW,
                student_formula=formula_snapshot.formula,
                student_value=value_snapshot.value,
                message="Regola da revisionare manualmente.",
                score_awarded=0.0,
            )
        if rule.rule_type == RuleType.FORMULA_NORMALIZED:
            return self._build_result(
                rule=rule,
                status=ResultStatus.WARNING,
                student_formula=formula_snapshot.formula,
                student_value=value_snapshot.value,
                message="Normalized formula comparison not implemented yet.",
                score_awarded=0.0,
            )

        raise UnsupportedRuleTypeError(
            f"Tipo regola non ancora supportato: {rule.rule_type.value}."
        )

    def _evaluate_formula_exact(self, rule, formula_snapshot, value_snapshot) -> CellCorrectionResult:
        """Compare formulas by exact string match."""
        student_formula = formula_snapshot.formula
        if student_formula == rule.expected_formula:
            return self._build_result(
                rule=rule,
                status=ResultStatus.PASSED,
                student_formula=student_formula,
                student_value=value_snapshot.value,
                message="Formula corretta.",
                score_awarded=rule.weight,
            )

        return self._build_result(
            rule=rule,
            status=ResultStatus.FAILED,
            student_formula=student_formula,
            student_value=value_snapshot.value,
            message="Formula diversa da quella attesa.",
            score_awarded=0.0,
        )

    def _evaluate_numeric_value(self, rule, formula_snapshot, value_snapshot) -> CellCorrectionResult:
        """Compare numeric values with optional tolerance."""
        expected_value = rule.expected_value
        student_value = value_snapshot.value

        if not isinstance(expected_value, (int, float)) or isinstance(expected_value, bool):
            raise CorrectionRuleError(
                f"Regola numerica '{rule.id}' con expected_value non numerico."
            )

        if not isinstance(student_value, (int, float)) or isinstance(student_value, bool):
            if formula_snapshot.has_formula and student_value is None:
                message = "Valore numerico non verificabile: formula senza valore cache disponibile."
            else:
                message = "Valore numerico non valido."
            return self._build_result(
                rule=rule,
                status=ResultStatus.FAILED,
                student_formula=formula_snapshot.formula,
                student_value=student_value,
                message=message,
                score_awarded=0.0,
            )

        try:
            is_match = self._compare_numeric(
                expected=float(expected_value),
                student=float(student_value),
                tolerance=rule.tolerance,
            )
        except CorrectionRuleError:
            raise

        return self._build_result(
            rule=rule,
            status=ResultStatus.PASSED if is_match else ResultStatus.FAILED,
            student_formula=formula_snapshot.formula,
            student_value=student_value,
            message=(
                "Valore numerico corretto."
                if is_match
                else "Valore numerico fuori tolleranza."
            ),
            score_awarded=rule.weight if is_match else 0.0,
        )

    def _evaluate_text_value(self, rule, formula_snapshot, value_snapshot) -> CellCorrectionResult:
        """Compare text values by exact string equality."""
        expected_text = "" if rule.expected_value is None else str(rule.expected_value)
        student_text = "" if value_snapshot.value is None else str(value_snapshot.value)
        is_match = expected_text == student_text

        return self._build_result(
            rule=rule,
            status=ResultStatus.PASSED if is_match else ResultStatus.FAILED,
            student_formula=formula_snapshot.formula,
            student_value=value_snapshot.value,
            message="Testo corretto." if is_match else "Testo diverso da quello atteso.",
            score_awarded=rule.weight if is_match else 0.0,
        )

    def _evaluate_text_normalized(self, rule, formula_snapshot, value_snapshot) -> CellCorrectionResult:
        """Compare text values case-insensitively and trimming outer spaces."""
        expected_text = "" if rule.expected_value is None else str(rule.expected_value)
        student_text = "" if value_snapshot.value is None else str(value_snapshot.value)
        is_match = expected_text.strip().casefold() == student_text.strip().casefold()

        return self._build_result(
            rule=rule,
            status=ResultStatus.PASSED if is_match else ResultStatus.FAILED,
            student_formula=formula_snapshot.formula,
            student_value=value_snapshot.value,
            message="Testo corretto." if is_match else "Testo diverso da quello atteso.",
            score_awarded=rule.weight if is_match else 0.0,
        )

    def _evaluate_non_empty(self, rule, formula_snapshot, value_snapshot) -> CellCorrectionResult:
        """Pass when the student cell is not empty."""
        is_non_empty = not self._is_effectively_empty(
            formula_snapshot=formula_snapshot,
            value_snapshot=value_snapshot,
        )
        return self._build_result(
            rule=rule,
            status=ResultStatus.PASSED if is_non_empty else ResultStatus.FAILED,
            student_formula=formula_snapshot.formula,
            student_value=value_snapshot.value,
            message="Cella non vuota." if is_non_empty else "Cella vuota.",
            score_awarded=rule.weight if is_non_empty else 0.0,
        )

    def _evaluate_empty(self, rule, formula_snapshot, value_snapshot) -> CellCorrectionResult:
        """Pass when the student cell is empty."""
        is_empty = self._is_effectively_empty(
            formula_snapshot=formula_snapshot,
            value_snapshot=value_snapshot,
        )
        return self._build_result(
            rule=rule,
            status=ResultStatus.PASSED if is_empty else ResultStatus.FAILED,
            student_formula=formula_snapshot.formula,
            student_value=value_snapshot.value,
            message="Cella vuota." if is_empty else "Cella non vuota.",
            score_awarded=rule.weight if is_empty else 0.0,
        )

    def _compare_numeric(
        self, *, expected: float, student: float, tolerance: ToleranceConfig | None
    ) -> bool:
        """Evaluate numeric equality with optional tolerance."""
        if tolerance is None or tolerance.mode == ToleranceMode.NONE:
            return student == expected

        absolute_diff = abs(student - expected)
        absolute_ok = False
        relative_ok = False

        if tolerance.mode in (
            ToleranceMode.ABSOLUTE,
            ToleranceMode.ABSOLUTE_OR_RELATIVE,
        ):
            if tolerance.absolute is None:
                raise CorrectionRuleError("Configurazione tolleranza assoluta non valida.")
            absolute_ok = absolute_diff <= tolerance.absolute

        if tolerance.mode in (
            ToleranceMode.RELATIVE,
            ToleranceMode.ABSOLUTE_OR_RELATIVE,
        ):
            if tolerance.relative is None:
                raise CorrectionRuleError("Configurazione tolleranza relativa non valida.")
            if expected == 0:
                relative_ok = absolute_diff == 0
            else:
                relative_ok = (absolute_diff / abs(expected)) <= tolerance.relative

        if tolerance.mode == ToleranceMode.ABSOLUTE:
            return absolute_ok
        if tolerance.mode == ToleranceMode.RELATIVE:
            return relative_ok
        if tolerance.mode == ToleranceMode.ABSOLUTE_OR_RELATIVE:
            return absolute_ok or relative_ok

        raise CorrectionRuleError("Modalita di tolleranza non supportata.")

    def _is_effectively_empty(self, *, formula_snapshot, value_snapshot) -> bool:
        """Treat formulas as non-empty even when Excel cache is unavailable."""
        if formula_snapshot.has_formula:
            return False
        return value_snapshot.value in (None, "")

    def _build_missing_sheet_result(self, rule: CorrectionRule) -> CellCorrectionResult:
        """Create an error result when the worksheet is missing."""
        return self._build_result(
            rule=rule,
            status=ResultStatus.ERROR,
            message="Foglio previsto dal profilo non presente nel workbook studente.",
            score_awarded=0.0,
        )

    def _build_result(
        self,
        *,
        rule: CorrectionRule,
        status: ResultStatus,
        message: str,
        score_awarded: float,
        student_formula: str | None = None,
        student_value=None,
    ) -> CellCorrectionResult:
        """Create a CellCorrectionResult from a rule evaluation."""
        return CellCorrectionResult(
            rule_id=rule.id,
            sheet_name=rule.sheet_name,
            cell=rule.cell,
            range_ref=rule.range_ref,
            rule_type=rule.rule_type,
            expected_formula=rule.expected_formula,
            student_formula=student_formula,
            expected_value=rule.expected_value,
            student_value=student_value,
            weight=rule.weight,
            score_awarded=score_awarded,
            status=status,
            message=message,
            teacher_comment="",
        )
