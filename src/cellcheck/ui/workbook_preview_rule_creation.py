"""Helpers for creating correction-rule drafts from workbook preview data."""

from __future__ import annotations

from dataclasses import dataclass

from openpyxl.utils.cell import coordinate_to_tuple, range_boundaries

from cellcheck.models import RuleType
from cellcheck.ui.workbook_preview_navigation import excel_column_label


@dataclass(frozen=True)
class PreviewSelectionBounds:
    """1-based rectangular selection bounds from the workbook preview."""

    top_row: int
    left_column: int
    bottom_row: int
    right_column: int

    @property
    def is_single_cell(self) -> bool:
        """Return True when the selection contains exactly one cell."""
        return self.top_row == self.bottom_row and self.left_column == self.right_column


@dataclass(frozen=True)
class PreviewRuleDraft:
    """Safe initial values for the existing profile rule dialog."""

    sheet_name: str
    cell: str | None
    range_ref: str | None
    suggested_rule_type: RuleType | None
    expected_formula: str | None
    expected_value: str | int | float | bool | None
    required_activity: str = ""


@dataclass(frozen=True)
class PreviewRuleMatch:
    """One profile rule associated with a workbook-preview selection."""

    worksheet_index: int
    rule_index: int
    rule_id: str
    sheet_name: str
    target_ref: str
    match_kind: str


def excel_reference_from_selection(bounds: PreviewSelectionBounds) -> str:
    """Return the Excel A1 reference represented by rectangular preview bounds."""
    top_row = min(bounds.top_row, bounds.bottom_row)
    bottom_row = max(bounds.top_row, bounds.bottom_row)
    left_column = min(bounds.left_column, bounds.right_column)
    right_column = max(bounds.left_column, bounds.right_column)

    first_cell = f"{excel_column_label(left_column)}{top_row}"
    if top_row == bottom_row and left_column == right_column:
        return first_cell
    last_cell = f"{excel_column_label(right_column)}{bottom_row}"
    return f"{first_cell}:{last_cell}"


def find_rules_for_preview_reference(profile: object | None, sheet_name: str, reference: str) -> list[PreviewRuleMatch]:
    """Return profile rules associated with one preview cell or exact range."""
    if profile is None:
        return []

    normalized_sheet = (sheet_name or "").strip()
    normalized_reference = _normalize_reference(reference)
    if not normalized_sheet or not normalized_reference:
        return []

    matches: list[PreviewRuleMatch] = []
    selection_is_range = ":" in normalized_reference
    for worksheet_index, worksheet in enumerate(getattr(profile, "worksheets", []) or []):
        worksheet_name = getattr(worksheet, "sheet_name", "")
        if worksheet_name != normalized_sheet:
            continue
        for rule_index, rule in enumerate(getattr(worksheet, "rules", []) or []):
            target_ref = _rule_target_reference(rule)
            if not target_ref:
                continue
            normalized_target = _normalize_reference(target_ref)
            match_kind = _match_kind(
                selection_reference=normalized_reference,
                target_reference=normalized_target,
                selection_is_range=selection_is_range,
            )
            if match_kind is None:
                continue
            matches.append(
                PreviewRuleMatch(
                    worksheet_index=worksheet_index,
                    rule_index=rule_index,
                    rule_id=str(getattr(rule, "id", "")),
                    sheet_name=normalized_sheet,
                    target_ref=normalized_target,
                    match_kind=match_kind,
                )
            )
    return matches


def suggest_rule_type_from_cell(
    *,
    has_formula: bool,
    formula_text: str | None,
    value: object,
) -> RuleType | None:
    """Suggest a rule type only when the workbook cell makes it obvious."""
    if has_formula and isinstance(formula_text, str) and formula_text.strip().startswith("="):
        return RuleType.FORMULA_EXACT
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return RuleType.NUMERIC_VALUE
    if isinstance(value, str) and value != "":
        return RuleType.TEXT_VALUE
    return None


def _match_kind(
    *,
    selection_reference: str,
    target_reference: str,
    selection_is_range: bool,
) -> str | None:
    """Return how one selection relates to one rule target, if at all."""
    if selection_reference == target_reference:
        return "exact_range" if selection_is_range else "exact_cell"
    if selection_is_range:
        return None
    if ":" not in target_reference:
        return None
    if _cell_inside_range(selection_reference, target_reference):
        return "cell_inside_range"
    return None


def _cell_inside_range(cell_reference: str, range_reference: str) -> bool:
    """Return True when one A1 cell is within an A1 range."""
    row_index, column_index = coordinate_to_tuple(cell_reference)
    min_col, min_row, max_col, max_row = range_boundaries(range_reference)
    return min_row <= row_index <= max_row and min_col <= column_index <= max_col


def _normalize_reference(reference: str | None) -> str:
    """Normalize an Excel cell or range reference for comparison."""
    return (reference or "").strip().replace("$", "").upper()


def _rule_target_reference(rule: object) -> str | None:
    """Return one rule target reference without assuming one model shape."""
    cell = getattr(rule, "cell", None)
    if isinstance(cell, str) and cell.strip():
        return cell
    range_ref = getattr(rule, "range_ref", None)
    if isinstance(range_ref, str) and range_ref.strip():
        return range_ref
    return None


def build_rule_draft_from_preview_cell(
    *,
    sheet_name: str,
    reference: str,
    has_formula: bool,
    formula_text: str | None,
    value: object,
    required_activity: str = "",
) -> PreviewRuleDraft:
    """Build a rule draft from one selected preview cell or a rectangular range."""
    normalized_reference = (reference or "").strip().replace("$", "").upper()
    if not normalized_reference:
        raise ValueError("Empty workbook reference.")

    is_range = ":" in normalized_reference
    suggested_rule_type = (
        RuleType.MANUAL_REVIEW
        if is_range
        else suggest_rule_type_from_cell(
            has_formula=has_formula,
            formula_text=formula_text,
            value=value,
        )
    )
    expected_formula = None
    expected_value: str | int | float | bool | None = None
    if not is_range:
        if suggested_rule_type == RuleType.FORMULA_EXACT:
            expected_formula = formula_text.strip() if isinstance(formula_text, str) else None
        elif suggested_rule_type in {RuleType.NUMERIC_VALUE, RuleType.TEXT_VALUE}:
            expected_value = value

    return PreviewRuleDraft(
        sheet_name=sheet_name,
        cell=None if is_range else normalized_reference,
        range_ref=normalized_reference if is_range else None,
        suggested_rule_type=suggested_rule_type,
        expected_formula=expected_formula,
        expected_value=expected_value,
        required_activity=required_activity,
    )
