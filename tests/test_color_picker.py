import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QLineEdit

from cellcheck.ui.color_picker import (
    apply_qcolor_to_line_edit,
    choose_color_for_line_edit,
    normalize_color_for_display,
    resolve_initial_qcolor,
)
from cellcheck.ui.localization import install_qt_italian_translations


def _qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_normalize_color_for_display_returns_hash_rrggbb() -> None:
    assert normalize_color_for_display("ffd9d9d9") == "#D9D9D9"
    assert normalize_color_for_display("D9D9D9") == "#D9D9D9"


def test_normalize_color_for_display_returns_none_for_invalid_text() -> None:
    assert normalize_color_for_display("not-a-color") is None


def test_install_qt_italian_translations_is_importable_and_safe() -> None:
    _qapp()
    installed = install_qt_italian_translations(QApplication.instance())
    assert installed is not None


def test_resolve_initial_qcolor_uses_fallback_for_invalid_value() -> None:
    color = resolve_initial_qcolor("invalid", "#FFFF00")
    assert color.name(QColor.HexRgb).upper() == "#FFFF00"


def test_apply_qcolor_to_line_edit_writes_uppercase_hash_rgb() -> None:
    _qapp()
    line_edit = QLineEdit()

    changed = apply_qcolor_to_line_edit(line_edit, QColor("#d9d9d9"))

    assert changed is True
    assert line_edit.text() == "#D9D9D9"


def test_choose_color_for_line_edit_does_not_modify_text_when_dialog_is_cancelled() -> None:
    _qapp()
    line_edit = QLineEdit("#D9D9D9")

    changed = choose_color_for_line_edit(
        line_edit,
        dialog_getter=lambda initial, parent: QColor(),
    )

    assert changed is False
    assert line_edit.text() == "#D9D9D9"


def test_choose_color_for_line_edit_uses_selected_color_when_confirmed() -> None:
    _qapp()
    line_edit = QLineEdit("FFFF00")

    changed = choose_color_for_line_edit(
        line_edit,
        dialog_getter=lambda initial, parent: QColor("#00FF00"),
    )

    assert changed is True
    assert line_edit.text() == "#00FF00"
