"""Independent verifier for the identifier-validator plugin.

Deliberately duplicates the standards' rules instead of importing
``plugin.validate_identifier``: the verifier re-parses and re-computes the
whole record from the raw input, so a bug in the tool cannot hide here.
"""

from __future__ import annotations

import re

from contract import KIND_IBAN, KIND_ISBN13, KINDS, ValidateInput
from verifier.checks import result

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

_IBAN_PATTERN = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\Z")
_ALNUM_PATTERN = re.compile(r"[A-Z0-9]*\Z")
_DIGITS_PATTERN = re.compile(r"[0-9]+\Z")

_ISBN_PREFIXES = ("978", "979")

FIELDS: tuple[str, ...] = (
    "kind",
    "normalized",
    "valid",
    "reason",
    "country_code",
    "check_digits",
    "bban",
    "computed_check",
    "isbn_prefix",
    "isbn_body",
    "isbn_check_digit",
)


def _mod97(text: str) -> int:
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


def _record(
    kind: str,
    normalized: str,
    reason: str | None,
    country_code: str | None = None,
    check_digits: str | None = None,
    bban: str | None = None,
    computed_check: str | None = None,
    isbn_prefix: str | None = None,
    isbn_body: str | None = None,
    isbn_check_digit: str | None = None,
) -> dict[str, object]:
    return {
        "kind": kind,
        "normalized": normalized,
        "valid": reason is None,
        "reason": reason,
        "country_code": country_code,
        "check_digits": check_digits,
        "bban": bban,
        "computed_check": computed_check,
        "isbn_prefix": isbn_prefix,
        "isbn_body": isbn_body,
        "isbn_check_digit": isbn_check_digit,
    }


def _expected_iban(value: str) -> dict[str, object]:
    normalized = value.replace(" ", "").upper()

    if not normalized:
        return _record(KIND_IBAN, normalized, "empty")

    if not _ALNUM_PATTERN.match(normalized):
        return _record(KIND_IBAN, normalized, "invalid-characters")

    if not _IBAN_PATTERN.match(normalized):
        return _record(KIND_IBAN, normalized, "bad-format")

    country_code = normalized[0:2]
    check_digits = normalized[2:4]
    bban = normalized[4:]

    if country_code not in IBAN_LENGTHS:
        return _record(
            KIND_IBAN,
            normalized,
            "bad-country",
            country_code=country_code,
            check_digits=check_digits,
            bban=bban,
        )

    computed_check = _iban_check_digits(country_code, bban)

    if len(normalized) != IBAN_LENGTHS[country_code]:
        return _record(
            KIND_IBAN,
            normalized,
            "bad-length",
            country_code=country_code,
            check_digits=check_digits,
            bban=bban,
            computed_check=computed_check,
        )

    if _mod97(bban + normalized[0:4]) != 1:
        return _record(
            KIND_IBAN,
            normalized,
            "check-digit-mismatch",
            country_code=country_code,
            check_digits=check_digits,
            bban=bban,
            computed_check=computed_check,
        )

    return _record(
        KIND_IBAN,
        normalized,
        None,
        country_code=country_code,
        check_digits=check_digits,
        bban=bban,
        computed_check=computed_check,
    )


def _expected_isbn13(value: str) -> dict[str, object]:
    normalized = value.replace(" ", "").replace("-", "").upper()

    if not normalized:
        return _record(KIND_ISBN13, normalized, "empty")

    if not _DIGITS_PATTERN.match(normalized):
        return _record(KIND_ISBN13, normalized, "invalid-characters")

    if len(normalized) != 13:
        return _record(KIND_ISBN13, normalized, "bad-length")

    isbn_prefix = normalized[0:3]
    isbn_body = normalized[3:12]
    isbn_check_digit = normalized[12]
    computed_check = _isbn13_check_digit(normalized[0:12])

    if isbn_prefix not in _ISBN_PREFIXES:
        return _record(
            KIND_ISBN13,
            normalized,
            "bad-format",
            computed_check=computed_check,
            isbn_prefix=isbn_prefix,
            isbn_body=isbn_body,
            isbn_check_digit=isbn_check_digit,
        )

    if isbn_check_digit != computed_check:
        return _record(
            KIND_ISBN13,
            normalized,
            "check-digit-mismatch",
            computed_check=computed_check,
            isbn_prefix=isbn_prefix,
            isbn_body=isbn_body,
            isbn_check_digit=isbn_check_digit,
        )

    return _record(
        KIND_ISBN13,
        normalized,
        None,
        computed_check=computed_check,
        isbn_prefix=isbn_prefix,
        isbn_body=isbn_body,
        isbn_check_digit=isbn_check_digit,
    )


def expected_output(input_payload: ValidateInput) -> dict[str, object]:
    """Re-derive the full expected record from the raw input alone."""
    if input_payload.kind == KIND_IBAN:
        return _expected_iban(input_payload.value)
    if input_payload.kind == KIND_ISBN13:
        return _expected_isbn13(input_payload.value)
    raise ValueError(f"kind must be one of {KINDS!r}, got {input_payload.kind!r}")


def verify_validate_identifier(
    input_payload: ValidateInput,
    output_payload: dict[str, object],
) -> str | None:
    """Return None if the output is correct, else a human-readable problem."""
    for field in FIELDS:
        if field not in output_payload:
            return f"missing field: {field}"

    if not isinstance(output_payload["valid"], bool):
        return f"valid: expected bool, got {type(output_payload['valid']).__name__}"

    try:
        expected = expected_output(input_payload)
    except ValueError as exc:
        return str(exc)

    checks = (
        ("kind", expected["kind"], output_payload["kind"]),
        ("normalized", expected["normalized"], output_payload["normalized"]),
        ("valid", expected["valid"], output_payload["valid"]),
        ("reason", expected["reason"], output_payload["reason"]),
        ("country_code", expected["country_code"], output_payload["country_code"]),
        ("check_digits", expected["check_digits"], output_payload["check_digits"]),
        ("bban", expected["bban"], output_payload["bban"]),
        ("computed_check", expected["computed_check"], output_payload["computed_check"]),
        ("isbn_prefix", expected["isbn_prefix"], output_payload["isbn_prefix"]),
        ("isbn_body", expected["isbn_body"], output_payload["isbn_body"]),
        ("isbn_check_digit", expected["isbn_check_digit"], output_payload["isbn_check_digit"]),
    )

    for field, exp, act in checks:
        if exp != act:
            return f"{field}: expected {exp!r}, got {act!r}"

    return result()