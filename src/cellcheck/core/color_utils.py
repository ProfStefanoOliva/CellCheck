"""Utilities for parsing, normalizing and resolving workbook colors."""

from __future__ import annotations

import colorsys
import string
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from openpyxl.styles.colors import COLOR_INDEX

from cellcheck.models import ColorTarget

from .errors import InvalidColorInputError

DRAWINGML_NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
DEFAULT_EMPTY_FILL_RAW_RGB = "00000000"


@dataclass(frozen=True)
class ResolvedWorkbookColor:
    """Stable internal representation of one workbook-derived color."""

    source_kind: str
    normalized_rgb: str
    normalized_argb: str


def parse_color_input(color_input: str) -> ColorTarget:
    """Parse and normalize a user-provided RGB or ARGB color string."""
    return normalize_color_input(color_input)


def normalize_color_input(color_input: str) -> ColorTarget:
    """Normalize a color string to uppercase RGB and canonical ARGB forms."""
    if color_input is None:
        raise InvalidColorInputError("Color input cannot be empty.")

    original_input = color_input
    normalized = color_input.strip()
    if not normalized:
        raise InvalidColorInputError("Color input cannot be empty.")

    normalized_argb = _normalize_hex_argb(normalized)
    if normalized_argb is None:
        raise InvalidColorInputError(
            "Color input must use 6 hex digits (RRGGBB) or 8 hex digits (AARRGGBB)."
        )
    normalized_rgb = normalized_argb[-6:]

    return ColorTarget(
        original_input=original_input,
        normalized_rgb=normalized_rgb,
        normalized_argb=normalized_argb,
    )


def normalize_color_token(raw_value: str | None) -> ResolvedWorkbookColor | None:
    """Normalize a raw workbook RGB/ARGB token to a stable resolved color."""
    normalized_argb = _normalize_hex_argb(raw_value)
    if normalized_argb is None:
        return None
    return ResolvedWorkbookColor(
        source_kind="rgb",
        normalized_rgb=normalized_argb[-6:],
        normalized_argb=normalized_argb,
    )


def resolve_openpyxl_color(color, workbook=None) -> ResolvedWorkbookColor | None:
    """Resolve an openpyxl color object to a stable RGB/ARGB value when reliable."""
    if color is None:
        return None

    color_type = getattr(color, "type", None)
    if color_type == "rgb":
        resolved = normalize_color_token(getattr(color, "rgb", None))
        if resolved is None:
            return None
        return ResolvedWorkbookColor(
            source_kind="rgb",
            normalized_rgb=resolved.normalized_rgb,
            normalized_argb=resolved.normalized_argb,
        )

    if color_type == "indexed":
        indexed_value = getattr(color, "indexed", None)
        if indexed_value is None:
            return None
        return _resolve_indexed_color(indexed_value, workbook)

    if color_type == "theme":
        theme_index = getattr(color, "theme", None)
        if theme_index is None:
            return None
        tint = getattr(color, "tint", 0.0) or 0.0
        return _resolve_theme_color(theme_index, tint, workbook)

    if color_type == "auto":
        return None

    return None


def color_matches_target(
    detected_color: ResolvedWorkbookColor | None,
    target_color: ColorTarget,
) -> bool:
    """Return True when the resolved workbook color matches the target color."""
    if detected_color is None:
        return False
    return detected_color.normalized_rgb == target_color.normalized_rgb


def has_meaningful_fill_color(cell, workbook=None) -> bool:
    """Return True when a cell exposes a resolvable non-empty background color."""
    fill = getattr(cell, "fill", None)
    if fill is None:
        return False

    for color in _iter_fill_colors(fill):
        if _is_default_empty_openpyxl_color(color):
            continue
        resolved = resolve_openpyxl_color(color, workbook)
        if resolved is None:
            continue
        return True
    return False


def resolve_cell_fill_color(cell, workbook=None) -> ResolvedWorkbookColor | None:
    """Resolve the visible background fill color for a cell when possible."""
    fill = getattr(cell, "fill", None)
    if fill is None:
        return None

    fill_pattern = getattr(fill, "patternType", None) or getattr(fill, "fill_type", None)
    if fill_pattern in (None, "", "none") and not has_meaningful_fill_color(cell, workbook):
        return None

    for color in _iter_fill_colors(fill):
        if fill_pattern in (None, "", "none") and _is_default_empty_openpyxl_color(color):
            continue
        resolved = resolve_openpyxl_color(color, workbook)
        if resolved is None:
            continue
        return resolved
    return None


def _normalize_hex_argb(raw_value: str | None) -> str | None:
    """Normalize a 6/8-digit hex color token to canonical ARGB with FF alpha."""
    if raw_value is None:
        return None

    normalized = str(raw_value).strip()
    if not normalized:
        return None

    if normalized.startswith("#"):
        normalized = normalized[1:]

    normalized = normalized.upper()
    if len(normalized) not in (6, 8):
        return None

    if any(char not in string.hexdigits.upper() for char in normalized):
        return None

    if len(normalized) == 6:
        return f"FF{normalized}"

    return f"FF{normalized[-6:]}"


def _resolve_indexed_color(indexed_value: int, workbook=None) -> ResolvedWorkbookColor | None:
    """Resolve a workbook indexed color using workbook or openpyxl palette data."""
    palette = getattr(workbook, "_colors", None) or COLOR_INDEX
    if indexed_value < 0 or indexed_value >= len(palette):
        return None

    normalized_argb = _normalize_hex_argb(palette[indexed_value])
    if normalized_argb is None:
        return None

    return ResolvedWorkbookColor(
        source_kind="indexed",
        normalized_rgb=normalized_argb[-6:],
        normalized_argb=normalized_argb,
    )


def _resolve_theme_color(
    theme_index: int,
    tint: float,
    workbook=None,
) -> ResolvedWorkbookColor | None:
    """Resolve a workbook theme color and optional tint when the theme is available."""
    theme_colors = _extract_theme_colors(workbook)
    if theme_colors is None or theme_index < 0 or theme_index >= len(theme_colors):
        return None

    base_rgb = theme_colors[theme_index]
    if base_rgb is None:
        return None

    normalized_rgb = _apply_excel_tint(base_rgb, tint)
    return ResolvedWorkbookColor(
        source_kind="theme",
        normalized_rgb=normalized_rgb,
        normalized_argb=f"FF{normalized_rgb}",
    )


def _extract_theme_colors(workbook) -> list[str | None] | None:
    """Extract theme base colors from workbook.loaded_theme when available."""
    if workbook is None:
        return None

    loaded_theme = getattr(workbook, "loaded_theme", None)
    if not loaded_theme:
        return None

    try:
        if isinstance(loaded_theme, bytes):
            root = ET.fromstring(loaded_theme)
        else:
            root = ET.fromstring(str(loaded_theme).encode("utf-8"))
    except ET.ParseError:
        return None

    clr_scheme = root.find(".//a:clrScheme", DRAWINGML_NS)
    if clr_scheme is None:
        return None

    values: list[str | None] = []
    for child in list(clr_scheme):
        srgb_node = child.find("a:srgbClr", DRAWINGML_NS)
        if srgb_node is not None:
            values.append(_normalize_theme_rgb_value(srgb_node.get("val")))
            continue

        sysclr_node = child.find("a:sysClr", DRAWINGML_NS)
        if sysclr_node is not None:
            values.append(_normalize_theme_rgb_value(sysclr_node.get("lastClr")))
            continue

        values.append(None)

    return values


def _normalize_theme_rgb_value(value: str | None) -> str | None:
    """Normalize a theme base color to RGB without alpha."""
    normalized_argb = _normalize_hex_argb(value)
    if normalized_argb is None:
        return None
    return normalized_argb[-6:]


def _apply_excel_tint(rgb_value: str, tint: float) -> str:
    """Apply an Excel tint value to an RGB color."""
    red = int(rgb_value[0:2], 16) / 255.0
    green = int(rgb_value[2:4], 16) / 255.0
    blue = int(rgb_value[4:6], 16) / 255.0
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)

    if tint < 0:
        lightness = lightness * (1.0 + tint)
    else:
        lightness = lightness * (1.0 - tint) + tint

    lightness = max(0.0, min(1.0, lightness))
    tinted_red, tinted_green, tinted_blue = colorsys.hls_to_rgb(
        hue,
        lightness,
        saturation,
    )
    return "".join(
        f"{round(channel * 255):02X}"
        for channel in (tinted_red, tinted_green, tinted_blue)
    )


def _iter_fill_colors(fill) -> list[object]:
    """Return the most relevant openpyxl fill colors in resolution order."""
    return [
        getattr(fill, "fgColor", None),
        getattr(fill, "start_color", None),
        getattr(fill, "bgColor", None),
        getattr(fill, "end_color", None),
    ]


def _is_default_empty_openpyxl_color(color) -> bool:
    """Return True for the default empty RGB sentinel used by openpyxl fills."""
    if color is None or getattr(color, "type", None) != "rgb":
        return False
    return str(getattr(color, "rgb", "") or "").strip().upper() == DEFAULT_EMPTY_FILL_RAW_RGB
