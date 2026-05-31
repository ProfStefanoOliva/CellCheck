"""Small helpers for numeric input and display in the GUI."""

from __future__ import annotations


def parse_decimal_input(text: str) -> float:
    """Parse one decimal GUI input accepting both comma and dot."""
    raw_value = text.strip()
    if not raw_value:
        raise ValueError(
            "Inserisci un numero valido. Puoi usare sia la virgola sia il punto come separatore decimale, ad esempio 0,5 oppure 0.5."
        )

    if "," in raw_value and "." in raw_value:
        raise ValueError(
            "Inserisci un numero valido. Puoi usare sia la virgola sia il punto come separatore decimale, ad esempio 0,5 oppure 0.5."
        )

    normalized = raw_value.replace(",", ".")
    try:
        return float(normalized)
    except ValueError as exc:
        raise ValueError(
            "Inserisci un numero valido. Puoi usare sia la virgola sia il punto come separatore decimale, ad esempio 0,5 oppure 0.5."
        ) from exc


def format_decimal_for_ui(value: float, *, max_decimals: int = 4) -> str:
    """Format one numeric value with Italian decimal comma for GUI display."""
    if float(value).is_integer():
        return str(int(value))

    formatted = f"{value:.{max_decimals}f}".rstrip("0").rstrip(".")
    return formatted.replace(".", ",")


def format_decimal_for_text(
    value: float,
    *,
    language_code: str,
    max_decimals: int = 4,
) -> str:
    """Format one numeric value for localized plain-text exports."""
    if float(value).is_integer():
        return str(int(value))

    formatted = f"{value:.{max_decimals}f}".rstrip("0").rstrip(".")
    if language_code == "it":
        return formatted.replace(".", ",")
    return formatted
