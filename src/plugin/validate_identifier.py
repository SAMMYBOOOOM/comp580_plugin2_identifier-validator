"""Deterministic IBAN (ISO 13616) and ISBN-13 (ISO 2108) validation.

This module is the tool side. It must not import from ``verifier`` — the
verifier re-implements the same rules independently so that a bug here
cannot hide a bug there.
"""

from __future__ import annotations

import re

from contract import KIND_IBAN, KIND_ISBN13, KINDS, ValidateInput, ValidateOutput

# IBAN registry: total identifier length per country code (ISO 13616 snapshot).
IBAN_LENGTHS: dict[str, int] = {
    "AD": 24,
    "AE": 23,
    "AL": 28,
    "AO": 25,
    "AT": 20,
    "AZ": 28,
    "BA": 20,
    "BE": 16,
    "BF": 28,
    "BG": 22,
    "BH": 22,
    "BI": 27,
    "BJ": 28,
    "BR": 29,
    "BY": 28,
    "CF": 27,
    "CG": 27,
    "CH": 21,
    "CI": 28,
    "CM": 27,
    "CR": 22,
    "CV": 25,
    "CY": 28,
    "CZ": 24,
    "DE": 22,
    "DJ": 27,
    "DK": 18,
    "DO": 28,
    "DZ": 26,
    "EE": 20,
    "EG": 29,
    "ES": 24,
    "FI": 18,
    "FO": 18,
    "FR": 27,
    "GA": 27,
    "GB": 22,
    "GE": 22,
    "GI": 23,
    "GL": 18,
    "GQ": 27,
    "GR": 27,
    "GT": 28,
    "GW": 25,
    "HN": 28,
    "HR": 21,
    "HU": 28,
    "IE": 22,
    "IL": 23,
    "IQ": 23,
    "IR": 26,
    "IS": 26,
    "IT": 27,
    "JO": 30,
    "KG": 20,
    "KM": 27,
    "KW": 30,
    "KZ": 20,
    "LB": 28,
    "LC": 32,
    "LI": 21,
    "LT": 20,
    "LU": 20,
    "LV": 21,
    "LY": 25,
    "MA": 28,
    "MC": 27,
    "MD": 24,
    "ME": 22,
    "MG": 27,
    "MK": 19,
    "ML": 28,
    "MN": 20,
    "MR": 27,
    "MT": 31,
    "MU": 30,
    "MZ": 25,
    "NE": 28,
    "NI": 28,
    "NL": 18,
    "NO": 15,
    "OM": 23,
    "PK": 24,
    "PL": 28,
    "PS": 29,
    "PT": 25,
    "QA": 29,
    "RO": 24,
    "RS": 22,
    "RU": 33,
    "SA": 24,
    "SC": 31,
    "SD": 18,
    "SE": 24,
    "SI": 19,
    "SK": 24,
    "SM": 27,
    "SN": 28,
    "SO": 23,
    "ST": 25,
    "SV": 28,
    "TD": 27,
    "TG": 28,
    "TL": 23,
    "TM": 24,
    "TN": 24,
    "TR": 26,
    "UA": 29,
    "VA": 22,
    "VG": 24,
    "XK": 20,
}

# 2 letters, 2 digits, then 11..30 alphanumerics -> total length 15..34.
_IBAN_PATTERN = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\Z")
_ALNUM_PATTERN = re.compile(r"[A-Z0-9]*\Z")
_DIGITS_PATTERN = re.compile(r"[0-9]+\Z")

_ISBN_PREFIXES = ("978", "979")


def _mod97(text: str) -> int:
    """ISO 7064 MOD 97-10 remainder over letters-as-numbers and digits."""
    remainder = 0
    for char in text:
        if "0" <= char <= "9":
            remainder = (remainder * 10 + (ord(char) - 48)) % 97
        else:
            remainder = (remainder * 100 + (ord(char) - 55)) % 97
    return remainder


def _iban_check_digits(country_code: str, bban: str) -> str:
    return f"{98 - _mod97(bban + country_code + '00'):02d}"


def _isbn13_check_digit(first_twelve: str) -> str:
    total = 0
    for index, char in enumerate(first_twelve):
        weight = 1 if index % 2 == 0 else 3
        total += (ord(char) - 48) * weight
    return str((10 - total % 10) % 10)


def _make(
    kind: str,
    normalized: str,
    reason: str | None,
    *,
    country_code: str | None = None,
    check_digits: str | None = None,
    bban: str | None = None,
    computed_check: str | None = None,
    isbn_prefix: str | None = None,
    isbn_body: str | None = None,
    isbn_check_digit: str | None = None,
) -> ValidateOutput:
    return ValidateOutput(
        kind=kind,
        normalized=normalized,
        valid=reason is None,
        reason=reason,
        country_code=country_code,
        check_digits=check_digits,
        bban=bban,
        computed_check=computed_check,
        isbn_prefix=isbn_prefix,
        isbn_body=isbn_body,
        isbn_check_digit=isbn_check_digit,
    )


def _validate_iban(value: str) -> ValidateOutput:
    normalized = value.replace(" ", "").upper()

    if not normalized:
        return _make(KIND_IBAN, normalized, "empty")

    if not _ALNUM_PATTERN.match(normalized):
        return _make(KIND_IBAN, normalized, "invalid-characters")

    if not _IBAN_PATTERN.match(normalized):
        return _make(KIND_IBAN, normalized, "bad-format")

    country_code = normalized[0:2]
    check_digits = normalized[2:4]
    bban = normalized[4:]

    if country_code not in IBAN_LENGTHS:
        return _make(
            KIND_IBAN,
            normalized,
            "bad-country",
            country_code=country_code,
            check_digits=check_digits,
            bban=bban,
        )

    computed_check = _iban_check_digits(country_code, bban)

    if len(normalized) != IBAN_LENGTHS[country_code]:
        return _make(
            KIND_IBAN,
            normalized,
            "bad-length",
            country_code=country_code,
            check_digits=check_digits,
            bban=bban,
            computed_check=computed_check,
        )

    if _mod97(bban + normalized[0:4]) != 1:
        return _make(
            KIND_IBAN,
            normalized,
            "check-digit-mismatch",
            country_code=country_code,
            check_digits=check_digits,
            bban=bban,
            computed_check=computed_check,
        )

    return _make(
        KIND_IBAN,
        normalized,
        None,
        country_code=country_code,
        check_digits=check_digits,
        bban=bban,
        computed_check=computed_check,
    )


def _validate_isbn13(value: str) -> ValidateOutput:
    normalized = value.replace(" ", "").replace("-", "").upper()

    if not normalized:
        return _make(KIND_ISBN13, normalized, "empty")

    if not _DIGITS_PATTERN.match(normalized):
        return _make(KIND_ISBN13, normalized, "invalid-characters")

    if len(normalized) != 13:
        return _make(KIND_ISBN13, normalized, "bad-length")

    isbn_prefix = normalized[0:3]
    isbn_body = normalized[3:12]
    isbn_check_digit = normalized[12]
    computed_check = _isbn13_check_digit(normalized[0:12])

    if isbn_prefix not in _ISBN_PREFIXES:
        return _make(
            KIND_ISBN13,
            normalized,
            "bad-format",
            computed_check=computed_check,
            isbn_prefix=isbn_prefix,
            isbn_body=isbn_body,
            isbn_check_digit=isbn_check_digit,
        )

    if isbn_check_digit != computed_check:
        return _make(
            KIND_ISBN13,
            normalized,
            "check-digit-mismatch",
            computed_check=computed_check,
            isbn_prefix=isbn_prefix,
            isbn_body=isbn_body,
            isbn_check_digit=isbn_check_digit,
        )

    return _make(
        KIND_ISBN13,
        normalized,
        None,
        computed_check=computed_check,
        isbn_prefix=isbn_prefix,
        isbn_body=isbn_body,
        isbn_check_digit=isbn_check_digit,
    )


def validate_identifier(payload: ValidateInput) -> ValidateOutput:
    """Validate one IBAN or one ISBN-13 identifier.

    Raises:
        ValueError: if ``payload.kind`` is not exactly ``"iban"`` or
            ``"isbn13"``.
    """
    if payload.kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS!r}, got {payload.kind!r}")

    if payload.kind == KIND_IBAN:
        return _validate_iban(payload.value)

    return _validate_isbn13(payload.value)