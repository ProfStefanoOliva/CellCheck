"""Public data model exports for CellCheck."""

from .enums import (
    CcalDocumentType,
    ResultStatus,
    RuleType,
    ToleranceMode,
    WorkbookFormat,
)
from .color_scan import CellColorMatch, ColorScanResult, ColorScanSummary, ColorTarget
from .importer import ProfileImportOptions, ProfileImportResult, ProfileImportSummary
from .profile import CorrectionProfile, WorksheetProfile
from .report import CellCorrectionResult, CorrectionReport, ScoreSummary
from .rule import CorrectionRule
from .tolerance import ToleranceConfig
from .workbook import CellSnapshot, WorkbookInfo, WorksheetInfo

__all__ = [
    "CcalDocumentType",
    "CellColorMatch",
    "CellSnapshot",
    "CellCorrectionResult",
    "ColorScanResult",
    "ColorScanSummary",
    "ColorTarget",
    "CorrectionProfile",
    "CorrectionReport",
    "CorrectionRule",
    "ProfileImportOptions",
    "ProfileImportResult",
    "ProfileImportSummary",
    "ResultStatus",
    "RuleType",
    "ScoreSummary",
    "ToleranceConfig",
    "ToleranceMode",
    "WorkbookInfo",
    "WorkbookFormat",
    "WorksheetInfo",
    "WorksheetProfile",
]
