"""Models for workbook color scan results."""

from pydantic import BaseModel, Field

CellPreviewValue = str | int | float | bool | None


class ColorTarget(BaseModel):
    """Normalized representation of a user-provided color."""

    original_input: str
    normalized_rgb: str = Field(pattern=r"^[0-9A-F]{6}$")
    normalized_argb: str = Field(pattern=r"^[0-9A-F]{8}$")


class CellColorMatch(BaseModel):
    """Information about a cell whose fill color matched the target."""

    sheet_name: str
    cell: str
    detected_rgb: str | None = None
    detected_argb: str | None = None
    value_preview: CellPreviewValue = None
    has_formula: bool
    formula: str | None = None


class ColorScanSummary(BaseModel):
    """Aggregated information about a color scan operation."""

    workbook_path: str
    target_rgb: str = Field(pattern=r"^[0-9A-F]{6}$")
    target_argb: str = Field(pattern=r"^[0-9A-F]{8}$")
    scanned_sheets: list[str] = Field(default_factory=list)
    matched_cells_count: int = Field(ge=0)
    unsupported_color_cells_count: int = Field(ge=0)
    ignored_cells_count: int = Field(ge=0)


class ColorScanResult(BaseModel):
    """Full result of a workbook color scan."""

    summary: ColorScanSummary
    matches: list[CellColorMatch] = Field(default_factory=list)
