"""Helpers for workbook-preview cell highlighting based on correction profiles."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from openpyxl.utils.cell import range_boundaries

from cellcheck.ui.workbook_preview_navigation import excel_column_label

MAX_HIGHLIGHTED_RANGE_CELLS = 5000


def build_highlighted_cells_map(profile: object | None) -> dict[str, set[str]]:
    """Return workbook cells to highlight, grouped by worksheet name."""
    if profile is None:
        return {}

    highlighted: dict[str, set[str]] = defaultdict(set)
    for worksheet in getattr(profile, "worksheets", []) or []:
        sheet_name = _worksheet_name(worksheet)
        if not sheet_name:
            continue
        for rule in getattr(worksheet, "rules", []) or []:
            target_ref = _rule_target_reference(rule)
            if not target_ref:
                continue
            for cell_ref in expand_excel_reference(target_ref):
                highlighted[sheet_name].add(cell_ref)
    return {sheet_name: cells for sheet_name, cells in highlighted.items() if cells}


def expand_excel_reference(reference: str, *, max_cells: int = MAX_HIGHLIGHTED_RANGE_CELLS) -> set[str]:
    """Expand a single-cell or range reference like A1 or H7:K14."""
    normalized = (reference or "").strip().replace("$", "")
    if not normalized:
        return set()
    if ":" not in normalized:
        return {normalized.upper()}

    min_col, min_row, max_col, max_row = range_boundaries(normalized)
    total_cells = (max_col - min_col + 1) * (max_row - min_row + 1)
    if total_cells > max_cells:
        return set()

    expanded: set[str] = set()
    for column_index in range(min_col, max_col + 1):
        column_label = excel_column_label(column_index)
        for row_index in range(min_row, max_row + 1):
            expanded.add(f"{column_label}{row_index}")
    return expanded


def _worksheet_name(worksheet: object) -> str | None:
    """Extract one worksheet name without assuming a single profile model shape."""
    for attr_name in ("sheet_name", "name", "title"):
        value = getattr(worksheet, attr_name, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _rule_target_reference(rule: object) -> str | None:
    """Extract one rule cell or range reference without inventing new semantics."""
    for attr_name in ("cell", "cell_ref", "range_ref", "target", "target_ref", "cell_range"):
        value = getattr(rule, attr_name, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
