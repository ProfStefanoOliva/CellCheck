"""Custom exceptions for CellCheck .ccal storage operations."""


class CellCheckStorageError(Exception):
    """Base exception for storage-related errors."""


class InvalidCcalExtensionError(CellCheckStorageError):
    """Raised when a path does not use the .ccal extension."""


class CcalFileExistsError(CellCheckStorageError):
    """Raised when attempting to overwrite an existing .ccal file."""


class CcalJsonError(CellCheckStorageError):
    """Raised when a .ccal file does not contain valid JSON data."""


class CcalDocumentTypeError(CellCheckStorageError):
    """Raised when a .ccal file contains an unexpected document type."""
