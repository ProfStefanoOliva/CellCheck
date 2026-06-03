"""Helpers for navigating the workbook preview to one cell or range."""

from __future__ import annotations

from dataclasses import dataclass

from openpyxl.utils.cell import coordinate_to_tuple, range_boundaries


@dataclass(frozen=True)
class PreviewNavigationTarget:
    """Normalized navigation target for the workbook preview."""

    reference: str
    first_cell: str
    first_row: int
    first_column: int
    is_range: bool


def resolve_target_sheet_name(
    available_sheet_names: list[str],
    requested_sheet_name: str | None,
    fallback_sheet_name: str | None,
) -> str | None:
    """Return the target sheet when available, otherwise None."""
    preferred = requested_sheet_name or fallback_sheet_name
    if not preferred:
        return None
    return preferred if preferred in available_sheet_names else None


def parse_preview_reference(reference: str) -> PreviewNavigationTarget:
    """Parse a single cell or range reference into a normalized navigation target."""
    normalized = (reference or "").strip().replace("$", "").upper()
    if not normalized:
        raise ValueError("Empty workbook reference.")

    if ":" not in normalized:
        row_index, column_index = coordinate_to_tuple(normalized)
        return PreviewNavigationTarget(
            reference=normalized,
            first_cell=normalized,
            first_row=row_index,
            first_column=column_index,
            is_range=False,
        )

    min_col, min_row, _max_col, _max_row = range_boundaries(normalized)
    first_cell = f"{excel_column_label(min_col)}{min_row}"
    return PreviewNavigationTarget(
        reference=normalized,
        first_cell=first_cell,
        first_row=min_row,
        first_column=min_col,
        is_range=True,
    )


def first_cell_from_reference(reference: str) -> str:
    """Return the first cell for a single-cell or range reference."""
    return parse_preview_reference(reference).first_cell


def excel_column_label(index: int) -> str:
    """Convert a 1-based column index to Excel-style letters."""
    if index <= 0:
        raise ValueError("Excel columns are 1-based.")

    label = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        label = chr(ord("A") + remainder) + label
    return label
