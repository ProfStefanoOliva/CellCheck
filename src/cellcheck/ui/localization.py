"""Qt translation helpers for the Italian CellCheck UI."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

QT_TRANSLATION_CANDIDATES = ("qtbase_it", "qt_it")


def install_qt_italian_translations(app: QApplication) -> list[QTranslator]:
    """Install available Italian Qt translations and keep them alive on the app."""
    installed: list[QTranslator] = []
    search_paths = _translation_search_paths()

    for base_name in QT_TRANSLATION_CANDIDATES:
        translator = QTranslator(app)
        if _load_translator(translator, base_name, search_paths):
            app.installTranslator(translator)
            installed.append(translator)

    if installed:
        app.setProperty("_cellcheck_qt_translators", installed)
        QLocale.setDefault(QLocale(QLocale.Italian, QLocale.Italy))

    return installed


def _translation_search_paths() -> list[str]:
    """Return candidate folders that may contain Qt translation files."""
    paths: list[str] = []

    try:
        translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    except Exception:
        translations_path = ""

    if translations_path:
        paths.append(translations_path)

    module_root = Path(__file__).resolve().parents[3]
    paths.append(str(module_root / "PySide6" / "translations"))

    unique_paths: list[str] = []
    seen: set[str] = set()
    for path in paths:
        normalized = str(Path(path))
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_paths.append(normalized)
    return unique_paths


def _load_translator(
    translator: QTranslator,
    base_name: str,
    search_paths: list[str],
) -> bool:
    """Try to load one translation base name from the available search paths."""
    for search_path in search_paths:
        if translator.load(base_name, search_path):
            return True
    return False
