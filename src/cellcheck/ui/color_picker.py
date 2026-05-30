"""Reusable Qt color picker helpers for CellCheck."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QLineEdit, QWidget

from cellcheck.core import parse_color_input
from cellcheck.ui.i18n import tr

DEFAULT_PICKER_COLOR = "#D9D9D9"

ColorDialogGetter = Callable[[QColor, QWidget | None], QColor]


def normalize_color_for_display(raw_value: str) -> str | None:
    """Return a normalized #RRGGBB color string when the value is valid."""
    try:
        normalized = parse_color_input(raw_value)
    except Exception:
        return None
    return f"#{normalized.normalized_rgb}"


def resolve_initial_qcolor(
    current_text: str,
    fallback_hex: str = DEFAULT_PICKER_COLOR,
) -> QColor:
    """Return the initial QColor for the picker from current or fallback text."""
    normalized_text = normalize_color_for_display(current_text)
    if normalized_text is None:
        normalized_text = normalize_color_for_display(fallback_hex) or DEFAULT_PICKER_COLOR
    return QColor(normalized_text)


def apply_qcolor_to_line_edit(line_edit: QLineEdit, selected_color: QColor | None) -> bool:
    """Write a confirmed QColor into the line edit as uppercase #RRGGBB."""
    if selected_color is None or not selected_color.isValid():
        return False
    line_edit.setText(selected_color.name(QColor.HexRgb).upper())
    return True


def choose_color_for_line_edit(
    line_edit: QLineEdit,
    parent: QWidget | None = None,
    *,
    dialog_getter: ColorDialogGetter | None = None,
    fallback_hex: str = DEFAULT_PICKER_COLOR,
) -> bool:
    """Open a color dialog and update the line edit only when confirmed."""
    initial_color = resolve_initial_qcolor(line_edit.text(), fallback_hex)
    active_getter = dialog_getter or _default_dialog_getter
    selected_color = active_getter(initial_color, parent)
    return apply_qcolor_to_line_edit(line_edit, selected_color)


def _default_dialog_getter(initial_color: QColor, parent: QWidget | None) -> QColor:
    """Open the Qt color dialog using the translatable non-native picker."""
    options = QColorDialog.ColorDialogOption.DontUseNativeDialog
    return QColorDialog.getColor(
        initial_color,
        parent,
        tr("color_dialog.title"),
        options,
    )
