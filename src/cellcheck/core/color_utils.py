"""Utilities for parsing and normalizing color inputs."""

from __future__ import annotations

import string

from cellcheck.models import ColorTarget

from .errors import InvalidColorInputError


def parse_color_input(color_input: str) -> ColorTarget:
    """Parse and normalize a user-provided RGB or ARGB color string."""
    return normalize_color_input(color_input)


def normalize_color_input(color_input: str) -> ColorTarget:
    """Normalize a color string to uppercase RGB and ARGB forms."""
    if color_input is None:
        raise InvalidColorInputError("Color input cannot be empty.")

    original_input = color_input
    normalized = color_input.strip()
    if not normalized:
        raise InvalidColorInputError("Color input cannot be empty.")

    if normalized.startswith("#"):
        normalized = normalized[1:]

    normalized = normalized.upper()
    if len(normalized) not in (6, 8):
        raise InvalidColorInputError(
            "Color input must use 6 hex digits (RRGGBB) or 8 hex digits (AARRGGBB)."
        )

    if any(char not in string.hexdigits.upper() for char in normalized):
        raise InvalidColorInputError("Color input must contain only hexadecimal characters.")

    if len(normalized) == 6:
        normalized_rgb = normalized
        normalized_argb = f"FF{normalized}"
    else:
        normalized_argb = normalized
        normalized_rgb = normalized[-6:]

    return ColorTarget(
        original_input=original_input,
        normalized_rgb=normalized_rgb,
        normalized_argb=normalized_argb,
    )
