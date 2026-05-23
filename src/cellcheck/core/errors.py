"""Custom exceptions for core workbook reading operations."""


class CellCheckCoreError(Exception):
    """Base exception for core-related errors."""


class UnsupportedWorkbookFormatError(CellCheckCoreError):
    """Raised when a workbook extension is not supported."""


class WorkbookReadError(CellCheckCoreError):
    """Raised when a workbook cannot be opened or inspected."""


class WorksheetNotFoundError(CellCheckCoreError):
    """Raised when a worksheet is not present in the workbook."""


class CellReadError(CellCheckCoreError):
    """Raised when a cell reference cannot be read safely."""


class InvalidColorInputError(CellCheckCoreError):
    """Raised when a user-provided color string is invalid."""


class ColorScanError(CellCheckCoreError):
    """Raised when a workbook color scan cannot be completed."""


class ProfileImportError(CellCheckCoreError):
    """Raised when automatic profile import cannot be completed."""


class WorkbookStructureMismatchError(ProfileImportError):
    """Raised when workbook structures are incompatible for profile import."""
