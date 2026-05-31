"""Localized presentation helpers for report widgets."""

from __future__ import annotations

import re

from cellcheck.models import ResultStatus, RuleType
from cellcheck.ui.i18n import tr

_PARTIAL_SCORE_RE = re.compile(
    r"^(Revisione manuale docente:|Rettifica manuale docente:)\s+assegnato punteggio parziale\s+(.+?)\.\s*(Esito originale:|Esito automatico originale:)\s*(.+)$"
)
_PARTIAL_SCORE_RE_NO_ORIGIN = re.compile(
    r"^(Revisione manuale docente:|Rettifica manuale docente:)\s+assegnato punteggio parziale\s+(.+?)\.$"
)
_MALUS_RE = re.compile(
    r"^(Revisione manuale docente:|Rettifica manuale docente:)\s+applicato malus, punteggio finale\s+(.+?)\.\s*(Esito originale:|Esito automatico originale:)\s*(.+)$"
)
_MALUS_RE_NO_ORIGIN = re.compile(
    r"^(Revisione manuale docente:|Rettifica manuale docente:)\s+applicato malus, punteggio finale\s+(.+?)\.$"
)


def localized_result_status(status: ResultStatus | str) -> str:
    """Return one localized user-facing label for a result status."""
    raw_value = status.value if isinstance(status, ResultStatus) else str(status)
    return {
        ResultStatus.PASSED.value: tr("report.summary.passed"),
        ResultStatus.FAILED.value: tr("report.summary.failed"),
        ResultStatus.WARNING.value: tr("report.summary.warnings"),
        ResultStatus.MANUAL_REVIEW.value: tr("report.summary.manual_review"),
        ResultStatus.SKIPPED.value: tr("report.summary.skipped"),
        ResultStatus.ERROR.value: tr("report.summary.errors"),
    }.get(raw_value, raw_value)


def localized_rule_type(rule_type: RuleType | str) -> str:
    """Return one localized user-facing label for a rule type."""
    raw_value = rule_type.value if isinstance(rule_type, RuleType) else str(rule_type)
    return {
        RuleType.FORMULA_EXACT.value: tr("text_report.rule_type.formula_exact"),
        RuleType.FORMULA_NORMALIZED.value: tr("text_report.rule_type.formula_normalized"),
        RuleType.NUMERIC_VALUE.value: tr("text_report.rule_type.numeric_value"),
        RuleType.TEXT_VALUE.value: tr("text_report.rule_type.text_value"),
        RuleType.TEXT_NORMALIZED.value: tr("text_report.rule_type.text_normalized"),
        RuleType.NON_EMPTY.value: tr("text_report.rule_type.non_empty"),
        RuleType.EMPTY.value: tr("text_report.rule_type.empty"),
        RuleType.MANUAL_REVIEW.value: tr("text_report.rule_type.manual_review"),
    }.get(raw_value, raw_value.replace("_", " ").strip() or tr("text_report.unavailable"))


def localized_result_message(message: str) -> str:
    """Translate known program-generated report messages while preserving free text."""
    text = message.strip()
    if not text:
        return text

    direct_map = {
        "Formula corretta.": tr("report.message.formula_ok"),
        "Formula diversa da quella attesa.": tr("report.message.formula_mismatch"),
        "Formula corretta dopo normalizzazione.": tr("report.message.formula_normalized_ok"),
        "Formula diversa da quella attesa dopo normalizzazione.": tr("report.message.formula_normalized_mismatch"),
        "Valore numerico non verificabile: formula senza valore cache disponibile.": tr("report.message.numeric_no_cache"),
        "Valore numerico non valido.": tr("report.message.numeric_invalid"),
        "Valore numerico corretto.": tr("report.message.numeric_ok"),
        "Valore numerico fuori tolleranza.": tr("report.message.numeric_out_of_tolerance"),
        "Testo corretto.": tr("report.message.text_ok"),
        "Testo diverso da quello atteso.": tr("report.message.text_mismatch"),
        "Cella non vuota.": tr("report.message.non_empty_ok"),
        "Cella vuota.": tr("report.message.empty_ok"),
        "Regola da revisionare manualmente.": tr("report.message.manual_rule_pending"),
        "Revisione manuale docente: voce accettata.": f"{tr('report.message.teacher_review_prefix')} {tr('report.message.teacher_accept')}",
        "Rettifica manuale docente: voce accettata.": f"{tr('report.message.teacher_override_prefix')} {tr('report.message.teacher_accept')}",
        "Revisione manuale docente: lasciato punteggio zero.": f"{tr('report.message.teacher_review_prefix')} {tr('report.message.teacher_zero')}",
        "Rettifica manuale docente: lasciato punteggio zero.": f"{tr('report.message.teacher_override_prefix')} {tr('report.message.teacher_zero')}",
        "Revisione manuale docente: annotata decisione senza modifica del punteggio.": f"{tr('report.message.teacher_review_prefix')} {tr('report.message.teacher_note_only')}",
        "Annotazione docente su esito automatico: nessuna modifica al punteggio.": tr("report.message.teacher_automatic_note"),
    }
    if text in direct_map:
        return direct_map[text]

    for pattern, is_malus in (
        (_PARTIAL_SCORE_RE, False),
        (_PARTIAL_SCORE_RE_NO_ORIGIN, False),
        (_MALUS_RE, True),
        (_MALUS_RE_NO_ORIGIN, True),
    ):
        match = pattern.match(text)
        if not match:
            continue
        prefix = match.group(1)
        score_value = match.group(2)
        localized_prefix = (
            tr("report.message.teacher_review_prefix")
            if prefix.startswith("Revisione")
            else tr("report.message.teacher_override_prefix")
        )
        action = (
            tr("report.message.teacher_malus").format(score=score_value)
            if is_malus
            else tr("report.message.teacher_partial").format(score=score_value)
        )
        if len(match.groups()) >= 4:
            original_label = match.group(3)
            original_message = match.group(4)
            localized_original_label = (
                tr("report.message.original_outcome")
                if original_label.startswith("Esito originale")
                else tr("report.message.original_automatic_outcome")
            )
            return f"{localized_prefix} {action} {localized_original_label} {localized_result_message(original_message)}"
        return f"{localized_prefix} {action}"

    if text.startswith("Revisione manuale docente: annotata decisione senza modifica del punteggio. Esito originale: "):
        original = text.removeprefix(
            "Revisione manuale docente: annotata decisione senza modifica del punteggio. Esito originale: "
        )
        return (
            f"{tr('report.message.teacher_review_prefix')} "
            f"{tr('report.message.teacher_note_only')} "
            f"{tr('report.message.original_outcome')} "
            f"{localized_result_message(original)}"
        )
    if text.startswith("Annotazione docente su esito automatico: nessuna modifica al punteggio. Esito automatico originale: "):
        original = text.removeprefix(
            "Annotazione docente su esito automatico: nessuna modifica al punteggio. Esito automatico originale: "
        )
        return (
            f"{tr('report.message.teacher_automatic_note')} "
            f"{tr('report.message.original_automatic_outcome')} "
            f"{localized_result_message(original)}"
        )
    return text
