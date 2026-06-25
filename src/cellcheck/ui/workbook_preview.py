"""Read-only workbook preview window and helper models."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QCloseEvent, QColor, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cellcheck.core import WorkbookReader
from cellcheck.ui.i18n import tr
from cellcheck.ui.workbook_preview_highlights import expand_excel_reference
from cellcheck.ui.workbook_preview_navigation import (
    PreviewNavigationTarget,
    excel_column_label,
    parse_preview_reference,
    resolve_target_sheet_name,
)
from cellcheck.ui.workbook_preview_rule_creation import (
    PreviewRuleDraft,
    PreviewRuleMatch,
    PreviewSelectionBounds,
    build_rule_draft_from_preview_cell,
    excel_reference_from_selection,
)

DEFAULT_PREVIEW_ROW_LIMIT = 200
DEFAULT_PREVIEW_COLUMN_LIMIT = 50

HIGHLIGHT_FILL = QColor("#5a4a19")
HIGHLIGHT_TEXT = QColor("#fff4c7")
REPORT_TARGET_FILL = QColor("#8f1d1d")
REPORT_TARGET_TEXT = QColor("#fff7f7")
REPORT_TARGET_BORDER = QColor("#ff5a5a")
MANUAL_SELECTION_FILL = QColor("#9cffb0")
MANUAL_SELECTION_TEXT = QColor("#061f10")
MANUAL_SELECTION_BORDER = QColor("#00e676")
VISUAL_ROLE_DATA_ROLE = Qt.UserRole + 10


def workbook_basename(path: str | Path) -> str:
    """Return only the last path segment for display in the preview title."""
    raw_path = str(path).replace("\\", "/").rstrip("/")
    if not raw_path:
        return ""
    return raw_path.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class PreviewCellData:
    """Display-ready cell snapshot for the preview window."""

    sheet_name: str
    cell_ref: str
    display_value: str
    raw_value: object
    cached_value: str
    value_text: str
    formula_text: str
    has_formula: bool
    is_highlighted: bool
    is_report_target: bool
    visual_role: str


@dataclass(frozen=True)
class PreviewSheetData:
    """Visible table data for one worksheet preview."""

    sheet_name: str
    row_count: int
    column_count: int
    row_limit_reached: bool
    column_limit_reached: bool
    cells: list[list[PreviewCellData]]

    @property
    def is_truncated(self) -> bool:
        """Return True when the sheet exceeded the preview limits."""
        return self.row_limit_reached or self.column_limit_reached


def preview_visual_role(
    *,
    is_highlighted: bool,
    is_report_target: bool,
    is_selected: bool = False,
) -> str:
    """Return the visual priority role for one preview cell."""
    if is_report_target:
        return "report_target"
    if is_selected and is_highlighted:
        return "selected_profile_highlight"
    if is_highlighted:
        return "profile_highlight"
    if is_selected:
        return "selected"
    return "default"


def preview_selection_style_role(visual_role: str | None, *, is_selected: bool) -> str:
    """Return the effective selected-cell style role with report target priority."""
    if visual_role == "report_target":
        return "report_target_selection" if is_selected else "report_target"
    if not is_selected:
        return visual_role or "default"
    if visual_role in {"profile_highlight", "selected_profile_highlight"}:
        return "selected_profile_highlight"
    return "manual_selection"


class WorkbookPreviewItemDelegate(QStyledItemDelegate):
    """Keep selected profile cells readable and visibly distinct."""

    def initStyleOption(self, option: QStyleOptionViewItem, index) -> None:
        """Apply selection colors according to CellCheck visual priority."""
        super().initStyleOption(option, index)
        visual_role = index.data(VISUAL_ROLE_DATA_ROLE)
        if not (option.state & QStyle.State_Selected):
            return

        selection_role = preview_selection_style_role(visual_role, is_selected=True)
        if selection_role == "report_target_selection":
            option.palette.setBrush(QPalette.Highlight, QBrush(REPORT_TARGET_FILL))
            option.palette.setBrush(QPalette.HighlightedText, QBrush(REPORT_TARGET_TEXT))
        elif selection_role in {"manual_selection", "selected_profile_highlight"}:
            option.palette.setBrush(QPalette.Highlight, QBrush(MANUAL_SELECTION_FILL))
            option.palette.setBrush(QPalette.HighlightedText, QBrush(MANUAL_SELECTION_TEXT))

    def paint(self, painter, option: QStyleOptionViewItem, index) -> None:
        """Paint the cell and then add a strong selection border when needed."""
        super().paint(painter, option, index)
        if not (option.state & QStyle.State_Selected):
            return

        selection_role = preview_selection_style_role(
            index.data(VISUAL_ROLE_DATA_ROLE),
            is_selected=True,
        )
        if selection_role == "report_target_selection":
            border_color = REPORT_TARGET_BORDER
        elif selection_role in {"manual_selection", "selected_profile_highlight"}:
            border_color = MANUAL_SELECTION_BORDER
        else:
            return

        painter.save()
        painter.setPen(QPen(border_color, 3))
        painter.drawRect(option.rect.adjusted(1, 1, -2, -2))
        painter.restore()


class WorkbookPreviewDataSource:
    """Provide read-only workbook preview data without recalculation or saving."""

    def __init__(
        self,
        path: str | Path,
        *,
        row_limit: int = DEFAULT_PREVIEW_ROW_LIMIT,
        column_limit: int = DEFAULT_PREVIEW_COLUMN_LIMIT,
        highlighted_cells_by_sheet: dict[str, set[str]] | None = None,
    ) -> None:
        self.path = Path(path)
        self.row_limit = row_limit
        self.column_limit = column_limit
        self.highlighted_cells_by_sheet = highlighted_cells_by_sheet or {}
        self.report_target_sheet_name: str | None = None
        self.report_target_reference: str | None = None
        self.report_target_cells_by_sheet: dict[str, set[str]] = {}
        self._formula_reader = WorkbookReader(self.path, data_only=False)
        self._value_reader = WorkbookReader(self.path, data_only=True)
        self._workbook_info = self._formula_reader.get_workbook_info()
        self._sheet_cache: dict[str, PreviewSheetData] = {}
        self._cell_cache: dict[tuple[str, int, int], PreviewCellData] = {}

    @property
    def workbook_name(self) -> str:
        """Return the basename used for window title and header."""
        return workbook_basename(self.path)

    @property
    def sheet_names(self) -> list[str]:
        """Return workbook sheet names in file order."""
        return list(self._workbook_info.sheet_names)

    @property
    def active_sheet_name(self) -> str | None:
        """Return the workbook active sheet when available."""
        return self._workbook_info.active_sheet

    def load_sheet(self, sheet_name: str) -> PreviewSheetData:
        """Return cached preview data for one worksheet."""
        cached = self._sheet_cache.get(sheet_name)
        if cached is not None:
            return cached

        info = self._formula_reader.get_worksheet_info(sheet_name)
        row_count = max(1, min(info.max_row or 0, self.row_limit))
        column_count = max(1, min(info.max_column or 0, self.column_limit))

        cells: list[list[PreviewCellData]] = []
        for row_index in range(1, row_count + 1):
            row_cells: list[PreviewCellData] = []
            for column_index in range(1, column_count + 1):
                row_cells.append(self.get_cell_data(sheet_name, row_index, column_index))
            cells.append(row_cells)

        preview_sheet = PreviewSheetData(
            sheet_name=sheet_name,
            row_count=row_count,
            column_count=column_count,
            row_limit_reached=(info.max_row or 0) > row_count,
            column_limit_reached=(info.max_column or 0) > column_count,
            cells=cells,
        )
        self._sheet_cache[sheet_name] = preview_sheet
        return preview_sheet

    def get_cell_data(self, sheet_name: str, row_index: int, column_index: int) -> PreviewCellData:
        """Return display-ready cell details for one worksheet coordinate."""
        cache_key = (sheet_name, row_index, column_index)
        cached = self._cell_cache.get(cache_key)
        if cached is not None:
            return cached

        cell_ref = f"{excel_column_label(column_index)}{row_index}"
        formula_snapshot = self._formula_reader.get_cell_snapshot(sheet_name, cell_ref)
        value_snapshot = self._value_reader.get_cell_snapshot(sheet_name, cell_ref)

        has_formula = formula_snapshot.has_formula
        cached_value = self._stringify_cell_value(value_snapshot.value)
        if value_snapshot.value is None and has_formula:
            value_text = tr("workbook_preview.calculated_value_unavailable")
            display_value = formula_snapshot.formula or ""
        else:
            value_text = cached_value
            display_value = cached_value

        if not has_formula:
            formula_text = tr("workbook_preview.no_formula")
        else:
            formula_text = formula_snapshot.formula or tr("workbook_preview.no_formula")

        is_highlighted = cell_ref in self.highlighted_cells_by_sheet.get(sheet_name, set())
        is_report_target = cell_ref in self.report_target_cells_by_sheet.get(sheet_name, set())
        preview_cell = PreviewCellData(
            sheet_name=sheet_name,
            cell_ref=cell_ref,
            display_value=display_value,
            raw_value=value_snapshot.value,
            cached_value=cached_value,
            value_text=value_text,
            formula_text=formula_text,
            has_formula=has_formula,
            is_highlighted=is_highlighted,
            is_report_target=is_report_target,
            visual_role=preview_visual_role(
                is_highlighted=is_highlighted,
                is_report_target=is_report_target,
            ),
        )
        self._cell_cache[cache_key] = preview_cell
        return preview_cell

    def has_highlighted_cells(self) -> bool:
        """Return True when at least one profile-controlled cell should be highlighted."""
        return any(cells for cells in self.highlighted_cells_by_sheet.values())

    def has_report_target(self) -> bool:
        """Return True when at least one report-target cell is active."""
        return any(cells for cells in self.report_target_cells_by_sheet.values())

    def set_highlighted_cells(self, highlighted_cells_by_sheet: dict[str, set[str]]) -> bool:
        """Replace profile-controlled highlights and clear cached display cells when changed."""
        normalized_highlights = highlighted_cells_by_sheet or {}
        if self.highlighted_cells_by_sheet == normalized_highlights:
            return False
        self.highlighted_cells_by_sheet = normalized_highlights
        self._sheet_cache.clear()
        self._cell_cache.clear()
        return True

    def set_report_target(self, sheet_name: str, reference: str, first_cell: str) -> None:
        """Persist the report-target cells so they remain visible after navigation."""
        expanded_cells = expand_excel_reference(reference)
        if not expanded_cells:
            expanded_cells = {first_cell}
        self.report_target_sheet_name = sheet_name
        self.report_target_reference = reference
        self.report_target_cells_by_sheet = {sheet_name: expanded_cells}
        self._sheet_cache.clear()
        self._cell_cache.clear()

    def close(self) -> None:
        """Release workbook file handles held by the preview data source."""
        self._formula_reader.close()
        self._value_reader.close()

    @staticmethod
    def _stringify_cell_value(value: object) -> str:
        """Return a compact visible representation for a workbook cell value."""
        if value is None:
            return ""
        return str(value)


class WorkbookPreviewWindow(QMainWindow):
    """Non-modal top-level window that previews a workbook in read-only mode."""

    def __init__(
        self,
        workbook_path: str | Path,
        *,
        row_limit: int = DEFAULT_PREVIEW_ROW_LIMIT,
        column_limit: int = DEFAULT_PREVIEW_COLUMN_LIMIT,
        highlighted_cells_by_sheet: dict[str, set[str]] | None = None,
        on_rule_create_requested: Callable[[PreviewRuleDraft], bool] | None = None,
        on_rule_lookup_requested: Callable[[str, str], list[PreviewRuleMatch]] | None = None,
        on_rule_remove_requested: Callable[[str, str], bool] | None = None,
        can_create_rule: bool = False,
        rule_creation_source: str = "other",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowFlag(Qt.Window, True)
        self._data_source = WorkbookPreviewDataSource(
            workbook_path,
            row_limit=row_limit,
            column_limit=column_limit,
            highlighted_cells_by_sheet=highlighted_cells_by_sheet,
        )
        self._current_navigation_target: PreviewNavigationTarget | None = None
        self._on_rule_create_requested = on_rule_create_requested
        self._on_rule_lookup_requested = on_rule_lookup_requested
        self._on_rule_remove_requested = on_rule_remove_requested
        self._can_create_rule = can_create_rule
        self._rule_creation_source = rule_creation_source

        self.resize(980, 720)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self.file_label = QLabel()
        self.file_label.setObjectName("pageTitle")
        self.file_label.setWordWrap(True)
        top_row.addWidget(self.file_label, 1)

        self.sheet_label = QLabel()
        top_row.addWidget(self.sheet_label)

        self.sheet_combo = QComboBox()
        self.sheet_combo.currentTextChanged.connect(self._load_current_sheet)
        top_row.addWidget(self.sheet_combo)

        self.create_rule_button = QPushButton()
        self.create_rule_button.setMinimumHeight(34)
        self.create_rule_button.setMinimumWidth(190)
        self.create_rule_button.clicked.connect(self._create_rule_from_selection)
        top_row.addWidget(self.create_rule_button)

        self.remove_rule_button = QPushButton()
        self.remove_rule_button.setMinimumHeight(34)
        self.remove_rule_button.setMinimumWidth(160)
        self.remove_rule_button.clicked.connect(self._remove_rule_from_selection)
        top_row.addWidget(self.remove_rule_button)
        layout.addLayout(top_row)

        self.sheet_notice_label = QLabel()
        self.sheet_notice_label.setObjectName("warningText")
        self.sheet_notice_label.setWordWrap(True)
        self.sheet_notice_label.setVisible(False)
        layout.addWidget(self.sheet_notice_label)

        self.highlight_legend_label = QLabel()
        self.highlight_legend_label.setObjectName("warningText")
        self.highlight_legend_label.setWordWrap(True)
        layout.addWidget(self.highlight_legend_label)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setItemDelegate(WorkbookPreviewItemDelegate(self.table))
        self.table.itemSelectionChanged.connect(self._update_selected_cell_info)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table, 1)

        self.info_panel = QWidget()
        info_layout = QFormLayout(self.info_panel)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setHorizontalSpacing(12)
        info_layout.setVerticalSpacing(8)

        self.info_sheet_value = QLabel()
        self.info_sheet_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_cell_value = QLabel()
        self.info_cell_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_value_value = QLabel()
        self.info_value_value.setWordWrap(True)
        self.info_value_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_formula_value = QLabel()
        self.info_formula_value.setWordWrap(True)
        self.info_formula_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self._info_layout = info_layout
        layout.addWidget(self.info_panel)

        self.setCentralWidget(central_widget)
        self.retranslate_ui()
        self._populate_sheet_combo()

    @classmethod
    def open_or_warn(
        cls,
        workbook_path: str | Path | None,
        *,
        highlighted_cells_by_sheet: dict[str, set[str]] | None = None,
        on_rule_create_requested: Callable[[PreviewRuleDraft], bool] | None = None,
        on_rule_lookup_requested: Callable[[str, str], list[PreviewRuleMatch]] | None = None,
        on_rule_remove_requested: Callable[[str, str], bool] | None = None,
        can_create_rule: bool = False,
        rule_creation_source: str = "other",
        parent: QWidget | None = None,
    ) -> "WorkbookPreviewWindow | None":
        """Create a preview window or show a clear message when the file is unavailable."""
        if not workbook_path:
            QMessageBox.information(
                parent,
                tr("workbook_preview.file_unavailable_title"),
                tr("workbook_preview.file_unavailable_message"),
            )
            return None

        path = Path(workbook_path)
        if not path.exists():
            QMessageBox.information(
                parent,
                tr("workbook_preview.file_unavailable_title"),
                tr("workbook_preview.file_unavailable_message"),
            )
            return None

        try:
            return cls(
                path,
                highlighted_cells_by_sheet=highlighted_cells_by_sheet,
                on_rule_create_requested=on_rule_create_requested,
                on_rule_lookup_requested=on_rule_lookup_requested,
                on_rule_remove_requested=on_rule_remove_requested,
                can_create_rule=can_create_rule,
                rule_creation_source=rule_creation_source,
                parent=parent,
            )
        except Exception as exc:
            QMessageBox.critical(
                parent,
                tr("workbook_preview.file_unavailable_title"),
                str(exc),
            )
            return None

    def retranslate_ui(self) -> None:
        """Refresh all localized labels while preserving workbook contents."""
        workbook_name = self._data_source.workbook_name
        self.setWindowTitle(f"{tr('workbook_preview.title')} - {workbook_name}")
        self.file_label.setText(workbook_name)
        self.sheet_label.setText(tr("workbook_preview.sheet"))
        self.create_rule_button.setText(tr("workbook_preview.create_rule"))
        self.remove_rule_button.setText(tr("workbook_preview.remove_rule"))

        labels = [
            tr("workbook_preview.sheet"),
            tr("workbook_preview.cell"),
            tr("workbook_preview.value"),
            tr("workbook_preview.formula"),
        ]
        fields = [
            self.info_sheet_value,
            self.info_cell_value,
            self.info_value_value,
            self.info_formula_value,
        ]
        while self._info_layout.rowCount():
            self._info_layout.removeRow(0)
        for label_text, field in zip(labels, fields):
            self._info_layout.addRow(f"{label_text}:", field)

        self._refresh_legend_label()

        self._refresh_notice_label()
        self._update_selected_cell_info()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Release workbook readers when the window closes."""
        self._data_source.close()
        super().closeEvent(event)

    def set_rule_creation_available(self, available: bool) -> None:
        """Enable or disable preview-driven rule creation for the current profile state."""
        self._can_create_rule = available
        self._update_create_rule_button_state()

    def refresh_profile_highlights(self, highlighted_cells_by_sheet: dict[str, set[str]]) -> None:
        """Refresh profile-controlled highlights after a rule has been added elsewhere."""
        current_sheet = self.sheet_combo.currentText()
        if not self._data_source.set_highlighted_cells(highlighted_cells_by_sheet):
            return
        if current_sheet:
            self._load_current_sheet(current_sheet)
        self._refresh_legend_label()
        self._update_create_rule_button_state()

    def _populate_sheet_combo(self) -> None:
        """Fill the sheet selector using workbook order."""
        sheet_names = self._data_source.sheet_names
        self.sheet_combo.blockSignals(True)
        self.sheet_combo.clear()
        self.sheet_combo.addItems(sheet_names)
        preferred_sheet = self._data_source.active_sheet_name or (sheet_names[0] if sheet_names else "")
        current_index = max(0, self.sheet_combo.findText(preferred_sheet))
        self.sheet_combo.setCurrentIndex(current_index)
        self.sheet_combo.blockSignals(False)
        self._load_current_sheet(self.sheet_combo.currentText())

    def navigate_to_reference(self, sheet_name: str | None, reference: str | None) -> bool:
        """Switch to one sheet and select the requested cell or range anchor."""
        if not reference:
            QMessageBox.information(
                self,
                tr("workbook_preview.invalid_reference_title"),
                tr("workbook_preview.invalid_cell_reference"),
            )
            return False

        try:
            target = parse_preview_reference(reference)
        except Exception:
            title_key = (
                "workbook_preview.invalid_range_title"
                if ":" in str(reference)
                else "workbook_preview.invalid_reference_title"
            )
            body_key = (
                "workbook_preview.invalid_range_reference"
                if ":" in str(reference)
                else "workbook_preview.invalid_cell_reference"
            )
            QMessageBox.information(self, tr(title_key), tr(body_key))
            return False

        target_sheet = resolve_target_sheet_name(
            self._data_source.sheet_names,
            sheet_name,
            self.sheet_combo.currentText() or self._data_source.active_sheet_name,
        )
        if not target_sheet:
            QMessageBox.information(
                self,
                tr("workbook_preview.sheet_not_found_title"),
                tr("workbook_preview.sheet_not_found_message"),
            )
            return False
        sheet_index = self.sheet_combo.findText(target_sheet)
        self._current_navigation_target = target
        self._data_source.set_report_target(target_sheet, target.reference, target.first_cell)
        self.sheet_combo.setCurrentIndex(sheet_index)
        if self.sheet_combo.currentText() == target_sheet:
            self._load_current_sheet(target_sheet)
        target_item = self.table.item(target.first_row - 1, target.first_column - 1)
        if target_item is not None:
            self.table.setCurrentItem(target_item)
            self.table.scrollToItem(target_item, QTableWidget.PositionAtCenter)
        else:
            self.table.setCurrentCell(target.first_row - 1, target.first_column - 1)
        self.raise_()
        self.activateWindow()
        return True

    def _load_current_sheet(self, sheet_name: str) -> None:
        """Load one worksheet into the central table."""
        if not sheet_name:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.sheet_notice_label.clear()
            self.sheet_notice_label.setVisible(False)
            self._update_selected_cell_info()
            return

        preview_sheet = self._data_source.load_sheet(sheet_name)
        self.table.clear()
        self.table.setRowCount(preview_sheet.row_count)
        self.table.setColumnCount(preview_sheet.column_count)
        self.table.setHorizontalHeaderLabels(
            [excel_column_label(index) for index in range(1, preview_sheet.column_count + 1)]
        )
        self.table.setVerticalHeaderLabels(
            [str(index) for index in range(1, preview_sheet.row_count + 1)]
        )

        for row_index, row_cells in enumerate(preview_sheet.cells):
            for column_index, cell_data in enumerate(row_cells):
                item = QTableWidgetItem(cell_data.display_value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item.setData(VISUAL_ROLE_DATA_ROLE, cell_data.visual_role)
                if cell_data.visual_role == "report_target":
                    item.setBackground(QBrush(REPORT_TARGET_FILL))
                    item.setForeground(QBrush(REPORT_TARGET_TEXT))
                elif cell_data.visual_role == "profile_highlight":
                    item.setBackground(QBrush(HIGHLIGHT_FILL))
                    item.setForeground(QBrush(HIGHLIGHT_TEXT))
                self.table.setItem(row_index, column_index, item)

        self._refresh_notice_label()
        if preview_sheet.row_count > 0 and preview_sheet.column_count > 0:
            self.table.setCurrentCell(0, 0)
        else:
            self._update_selected_cell_info()

    def _refresh_notice_label(self) -> None:
        """Show a prudential message when the visible sheet was truncated."""
        sheet_name = self.sheet_combo.currentText()
        if not sheet_name:
            self.sheet_notice_label.clear()
            self.sheet_notice_label.setVisible(False)
            return

        preview_sheet = self._data_source.load_sheet(sheet_name)
        if not preview_sheet.is_truncated:
            self.sheet_notice_label.clear()
            self.sheet_notice_label.setVisible(False)
            return

        self.sheet_notice_label.setText(
            tr(
                "workbook_preview.sheet_too_large",
                rows=preview_sheet.row_count,
                columns=preview_sheet.column_count,
            )
        )
        self.sheet_notice_label.setVisible(True)

    def _update_selected_cell_info(self) -> None:
        """Refresh the detail panel for the currently selected table cell."""
        sheet_name = self.sheet_combo.currentText()
        row_index = self.table.currentRow()
        column_index = self.table.currentColumn()

        if not sheet_name or row_index < 0 or column_index < 0:
            self.info_sheet_value.setText(sheet_name)
            self.info_cell_value.setText("")
            self.info_value_value.setText("")
            self.info_formula_value.setText(tr("workbook_preview.no_formula"))
            self._update_create_rule_button_state()
            return

        cell_data = self._data_source.get_cell_data(sheet_name, row_index + 1, column_index + 1)
        self.info_sheet_value.setText(cell_data.sheet_name)
        self.info_cell_value.setText(cell_data.cell_ref)
        self.info_value_value.setText(cell_data.value_text)
        self.info_formula_value.setText(cell_data.formula_text)
        self._update_create_rule_button_state()

    def _refresh_legend_label(self) -> None:
        """Refresh the legend distinguishing profile highlights from report targets."""
        legend_lines: list[str] = []
        if self._data_source.has_highlighted_cells():
            legend_lines.append(tr("workbook_preview.highlighted_cells_legend"))
        if self._data_source.has_report_target():
            if self._current_navigation_target is not None and self._current_navigation_target.is_range:
                legend_lines.append(tr("workbook_preview.report_target_range_legend"))
            else:
                legend_lines.append(tr("workbook_preview.report_target_cell_legend"))

        if legend_lines:
            self.highlight_legend_label.setText("\n".join(legend_lines))
            self.highlight_legend_label.setVisible(True)
        else:
            self.highlight_legend_label.setText(tr("workbook_preview.no_profile_cells"))
            self.highlight_legend_label.setVisible(False)

    def _selected_reference(self) -> str | None:
        """Return a single-cell or rectangular range reference for the table selection."""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            row_index = self.table.currentRow()
            column_index = self.table.currentColumn()
            if row_index < 0 or column_index < 0:
                return None
            bounds = PreviewSelectionBounds(
                top_row=row_index + 1,
                left_column=column_index + 1,
                bottom_row=row_index + 1,
                right_column=column_index + 1,
            )
            return excel_reference_from_selection(bounds)

        if len(selected_ranges) != 1:
            return None

        selected_range = selected_ranges[0]
        bounds = PreviewSelectionBounds(
            top_row=selected_range.topRow() + 1,
            left_column=selected_range.leftColumn() + 1,
            bottom_row=selected_range.bottomRow() + 1,
            right_column=selected_range.rightColumn() + 1,
        )
        return excel_reference_from_selection(bounds)

    def _create_rule_from_selection(self) -> None:
        """Build a rule draft from the current preview selection and delegate saving."""
        if self._on_rule_create_requested is None:
            QMessageBox.information(
                self,
                tr("workbook_preview.profile_unavailable_title"),
                tr("workbook_preview.profile_unavailable_message"),
            )
            return

        selected_ranges = self.table.selectedRanges()
        if len(selected_ranges) > 1:
            QMessageBox.information(
                self,
                tr("workbook_preview.invalid_range_title"),
                tr("workbook_preview.non_contiguous_selection"),
            )
            return

        reference = self._selected_reference()
        sheet_name = self.sheet_combo.currentText()
        if not reference or not sheet_name:
            QMessageBox.information(
                self,
                tr("workbook_preview.no_selection_title"),
                tr("workbook_preview.no_selection_message"),
            )
            return

        anchor_row = self.table.currentRow() + 1
        anchor_column = self.table.currentColumn() + 1
        if selected_ranges:
            anchor_row = selected_ranges[0].topRow() + 1
            anchor_column = selected_ranges[0].leftColumn() + 1
        cell_data = self._data_source.get_cell_data(sheet_name, anchor_row, anchor_column)

        if self._rule_creation_source == "student":
            QMessageBox.warning(
                self,
                tr("workbook_preview.student_rule_warning_title"),
                tr("workbook_preview.student_rule_warning_message"),
            )

        draft = build_rule_draft_from_preview_cell(
            sheet_name=sheet_name,
            reference=reference,
            has_formula=cell_data.has_formula,
            formula_text=cell_data.formula_text,
            value=cell_data.raw_value,
            required_activity=tr("workbook_preview.required_activity_default"),
        )
        if self._on_rule_create_requested(draft):
            QMessageBox.information(
                self,
                tr("workbook_preview.rule_created_title"),
                tr("workbook_preview.rule_created_message"),
            )

    def _remove_rule_from_selection(self) -> None:
        """Delegate removal of one profile rule associated with the current selection."""
        if self._on_rule_remove_requested is None:
            return
        reference = self._selected_reference()
        sheet_name = self.sheet_combo.currentText()
        if not reference or not sheet_name:
            QMessageBox.information(
                self,
                tr("workbook_preview.no_associated_rule_title"),
                tr("workbook_preview.no_associated_rule_message"),
            )
            return
        self._on_rule_remove_requested(sheet_name, reference)

    def _update_create_rule_button_state(self) -> None:
        """Keep the preview rule command aligned with selection and profile availability."""
        selected_reference = self._selected_reference()
        has_selection = bool(selected_reference)
        if selected_reference and ":" in selected_reference:
            self.create_rule_button.setText(tr("workbook_preview.create_rule_from_range"))
        elif selected_reference:
            self.create_rule_button.setText(tr("workbook_preview.create_rule_from_cell"))
        else:
            self.create_rule_button.setText(tr("workbook_preview.create_rule"))
        self.create_rule_button.setEnabled(self._on_rule_create_requested is not None and has_selection)
        if self._on_rule_create_requested is None:
            self.create_rule_button.setToolTip(tr("workbook_preview.profile_unavailable_message"))
        elif not self._can_create_rule:
            self.create_rule_button.setToolTip(tr("workbook_preview.reference_models_required_message"))
        elif not has_selection:
            self.create_rule_button.setToolTip(tr("workbook_preview.no_selection_message"))
        elif self._rule_creation_source == "student":
            self.create_rule_button.setToolTip(tr("workbook_preview.student_rule_tooltip"))
        elif self._rule_creation_source == "solution":
            self.create_rule_button.setToolTip(tr("workbook_preview.solution_rule_tooltip"))
        else:
            self.create_rule_button.setToolTip(tr("workbook_preview.create_rule_tooltip"))

        rule_count = self._associated_rule_count(selected_reference)
        if selected_reference and ":" in selected_reference:
            self.remove_rule_button.setText(tr("workbook_preview.remove_rule_from_range"))
        elif selected_reference:
            self.remove_rule_button.setText(tr("workbook_preview.remove_rule_from_cell"))
        else:
            self.remove_rule_button.setText(tr("workbook_preview.remove_rule"))
        self.remove_rule_button.setEnabled(
            self._on_rule_remove_requested is not None and rule_count > 0
        )
        if rule_count > 1:
            self.remove_rule_button.setToolTip(tr("workbook_preview.multiple_rules_message"))
        elif rule_count == 1:
            self.remove_rule_button.setToolTip(tr("workbook_preview.remove_rule_tooltip"))
        else:
            self.remove_rule_button.setToolTip(tr("workbook_preview.no_associated_rule_message"))

    def _associated_rule_count(self, reference: str | None) -> int:
        """Return how many profile rules are associated with the selection."""
        sheet_name = self.sheet_combo.currentText()
        if not reference or not sheet_name or self._on_rule_lookup_requested is None:
            return 0
        return len(self._on_rule_lookup_requested(sheet_name, reference))
