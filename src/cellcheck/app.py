"""Application entry point for CellCheck."""

from . import __version__


def main() -> None:
    """Run the minimal CLI entry point."""
    print(f"CellCheck {__version__} - data models initialized")
