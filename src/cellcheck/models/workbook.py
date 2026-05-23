"""Workbook metadata and snapshot models."""

from pydantic import BaseModel, Field

from .enums import WorkbookFormat

CellValue = str | int | float | bool | None


class WorkbookInfo(BaseModel):
    """Basic metadata collected from an opened workbook."""

    path: str
    filename: str
    workbook_format: WorkbookFormat
    macro_enabled: bool
    sheet_names: list[str] = Field(default_factory=list)
    active_sheet: str | None = None
    read_only: bool
    data_only: bool


class WorksheetInfo(BaseModel):
    """Basic metadata collected from a worksheet."""

    sheet_name: str
    max_row: int = Field(ge=0)
    max_column: int = Field(ge=0)
    calculated_dimension: str | None = None


class CellSnapshot(BaseModel):
    """Single-cell snapshot without any recalculation."""

    sheet_name: str
    cell: str
    value: CellValue = None
    data_type: str | None = None
    number_format: str | None = None
    has_formula: bool
    formula: str | None = None
