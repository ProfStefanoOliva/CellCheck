"""Automatic CorrectionProfile importer from workbook templates."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from cellcheck.models import (
    CorrectionProfile,
    CorrectionRule,
    ProfileImportOptions,
    ProfileImportResult,
    ProfileImportSummary,
    RuleType,
    WorkbookFormat,
    WorksheetProfile,
)

from .color_scanner import ColorScanner
from .color_utils import parse_color_input
from .errors import ProfileImportError, WorkbookStructureMismatchError, WorksheetNotFoundError
from .workbook_reader import WorkbookReader


class ProfileImporter:
    """Generate correction profiles from an empty template and a solved template."""

    def import_profile(
        self,
        empty_workbook_path: str | Path,
        solution_workbook_path: str | Path,
        options: ProfileImportOptions,
    ) -> ProfileImportResult:
        """Build a CorrectionProfile from colored cells in the empty workbook."""
        empty_path = Path(empty_workbook_path)
        solution_path = Path(solution_workbook_path)
        color_target = parse_color_input(options.target_color)

        with ColorScanner(empty_path) as color_scanner, WorkbookReader(
            solution_path, data_only=False
        ) as solution_reader:
            color_scan_result = color_scanner.scan_fill_color(
                options.target_color,
                sheet_names=options.sheet_names,
            )
            solution_info = solution_reader.get_workbook_info()

            rules_by_sheet: dict[str, list[CorrectionRule]] = defaultdict(list)
            formula_rules_count = 0
            numeric_rules_count = 0
            text_rules_count = 0
            manual_review_rules_count = 0
            non_empty_rules_count = 0

            for match in color_scan_result.matches:
                if match.sheet_name not in solution_info.sheet_names:
                    raise WorkbookStructureMismatchError(
                        f"Worksheet '{match.sheet_name}' exists in the empty workbook but is missing in the solution workbook."
                    )

                try:
                    cell_snapshot = solution_reader.get_cell_snapshot(match.sheet_name, match.cell)
                except WorksheetNotFoundError as exc:
                    raise WorkbookStructureMismatchError(
                        f"Worksheet '{match.sheet_name}' exists in the empty workbook but is missing in the solution workbook."
                    ) from exc

                rule = self._build_rule_from_snapshot(
                    sheet_name=match.sheet_name,
                    cell_ref=match.cell,
                    value=cell_snapshot.value,
                    formula=cell_snapshot.formula,
                    has_formula=cell_snapshot.has_formula,
                    default_weight=options.default_weight,
                    include_empty_solution_cells=options.include_empty_solution_cells,
                )
                if rule is None:
                    continue

                rules_by_sheet[match.sheet_name].append(rule)

                if rule.rule_type == RuleType.FORMULA_EXACT:
                    formula_rules_count += 1
                elif rule.rule_type == RuleType.NUMERIC_VALUE:
                    numeric_rules_count += 1
                elif rule.rule_type == RuleType.TEXT_VALUE:
                    text_rules_count += 1
                elif rule.rule_type == RuleType.MANUAL_REVIEW:
                    manual_review_rules_count += 1
                elif rule.rule_type == RuleType.NON_EMPTY:
                    non_empty_rules_count += 1

            worksheets = [
                WorksheetProfile(sheet_name=sheet_name, rules=rules)
                for sheet_name, rules in rules_by_sheet.items()
                if rules
            ]

            profile = CorrectionProfile(
                minimum_cellcheck_version="0.6.0",
                exercise_name=options.exercise_name,
                max_grade=options.max_grade,
                source_empty_workbook=str(empty_path),
                source_solution_workbook=str(solution_path),
                source_workbook_format=color_scanner.workbook_format,
                macro_enabled=(
                    color_scanner.workbook_format == WorkbookFormat.XLSM
                    or solution_info.workbook_format == WorkbookFormat.XLSM
                ),
                worksheets=worksheets,
            )

            summary = ProfileImportSummary(
                exercise_name=options.exercise_name,
                empty_workbook_path=str(empty_path),
                solution_workbook_path=str(solution_path),
                target_rgb=color_target.normalized_rgb,
                target_argb=color_target.normalized_argb,
                scanned_sheets=color_scan_result.summary.scanned_sheets,
                generated_rules_count=sum(len(worksheet.rules) for worksheet in worksheets),
                manual_review_rules_count=manual_review_rules_count,
                formula_rules_count=formula_rules_count,
                numeric_rules_count=numeric_rules_count,
                text_rules_count=text_rules_count,
                non_empty_rules_count=non_empty_rules_count,
                workbook_format=color_scanner.workbook_format,
                macro_enabled=profile.macro_enabled,
            )

        return ProfileImportResult(profile=profile, summary=summary)

    def _build_rule_from_snapshot(
        self,
        *,
        sheet_name: str,
        cell_ref: str,
        value,
        formula: str | None,
        has_formula: bool,
        default_weight: float,
        include_empty_solution_cells: bool,
    ) -> CorrectionRule | None:
        """Convert a solution cell snapshot into a CorrectionRule."""
        rule_id = f"{sheet_name}!{cell_ref}"

        if has_formula and formula is not None:
            return CorrectionRule(
                id=rule_id,
                sheet_name=sheet_name,
                cell=cell_ref,
                range_ref=None,
                rule_type=RuleType.FORMULA_EXACT,
                expected_formula=formula,
                expected_value=None,
                weight=default_weight,
                enabled=True,
                tolerance=None,
                teacher_note="",
            )

        if value is None:
            if not include_empty_solution_cells:
                return None

            return CorrectionRule(
                id=rule_id,
                sheet_name=sheet_name,
                cell=cell_ref,
                range_ref=None,
                rule_type=RuleType.MANUAL_REVIEW,
                expected_formula=None,
                expected_value=None,
                weight=default_weight,
                enabled=True,
                tolerance=None,
                teacher_note="",
            )

        if isinstance(value, bool):
            # CellCheck has no dedicated boolean rule yet. Keep the expected
            # boolean value but classify it as text-like for now.
            rule_type = RuleType.TEXT_VALUE
        elif isinstance(value, (int, float)):
            rule_type = RuleType.NUMERIC_VALUE
        elif isinstance(value, str):
            rule_type = RuleType.TEXT_VALUE
        else:
            raise ProfileImportError(
                f"Unsupported solution cell value type at '{sheet_name}!{cell_ref}': {type(value).__name__}."
            )

        return CorrectionRule(
            id=rule_id,
            sheet_name=sheet_name,
            cell=cell_ref,
            range_ref=None,
            rule_type=rule_type,
            expected_formula=None,
            expected_value=value,
            weight=default_weight,
            enabled=True,
            tolerance=None,
            teacher_note="",
        )
