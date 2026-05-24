"""Helpers for resolving CellCheck branding assets."""

from __future__ import annotations

from pathlib import Path


def get_branding_dir() -> Path:
    """Return the repository branding directory."""
    return Path(__file__).resolve().parents[3] / "assets" / "branding"


def get_app_icon_path() -> Path | None:
    """Return the application icon path when available."""
    return _get_existing_asset("cellcheck_icon.ico")


def get_square_logo_path() -> Path | None:
    """Return the square logo path when available."""
    return _get_existing_asset("cellcheck_logo_square.png")


def get_horizontal_logo_path() -> Path | None:
    """Return the horizontal logo path when available."""
    return _get_existing_asset("cellcheck_logo_horizontal.png")


def _get_existing_asset(filename: str) -> Path | None:
    """Return a branding asset path only if the file exists."""
    path = get_branding_dir() / filename
    if path.is_file():
        return path
    return None
