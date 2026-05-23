"""Public core exports for CellCheck."""

from .errors import (
    CellCheckCoreError,
    CellReadError,
    ColorScanError,
    CorrectionEngineError,
    CorrectionRuleError,
    InvalidColorInputError,
    ProfileImportError,
    UnsupportedWorkbookFormatError,
    UnsupportedRuleTypeError,
    WorkbookStructureMismatchError,
    WorkbookReadError,
    WorksheetNotFoundError,
)
from .color_scanner import ColorScanner
from .color_utils import normalize_color_input, parse_color_input
from .correction_engine import CorrectionEngine
from .profile_importer import ProfileImporter
from .scoring import calculate_score_summary
from .workbook_reader import WorkbookReader

__all__ = [
    "CellCheckCoreError",
    "CellReadError",
    "ColorScanError",
    "ColorScanner",
    "CorrectionEngine",
    "CorrectionEngineError",
    "CorrectionRuleError",
    "InvalidColorInputError",
    "ProfileImportError",
    "ProfileImporter",
    "UnsupportedWorkbookFormatError",
    "UnsupportedRuleTypeError",
    "WorkbookStructureMismatchError",
    "WorkbookReadError",
    "WorkbookReader",
    "WorksheetNotFoundError",
    "calculate_score_summary",
    "normalize_color_input",
    "parse_color_input",
]
