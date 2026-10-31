"""Tests for the identifier-validator tool."""

from __future__ import annotations

import pytest

from contract import ValidateInput
from plugin.validate_identifier import validate_identifier


def _run(kind: str, value: str):
    return validate_identifier(ValidateInput(kind=kind, value=value))


# --- IBAN: correct output -------------------------------------------------


def test_valid_gb_iban() -> None:
    out = _run("iban", "GB82WEST12345698765432")
    assert out.valid is True
    assert out.reason is None
    assert out.kind == "iban"
    assert out.normalized == "GB82WEST12345698765432"
    assert out.country_code == "GB"
    assert out.check_digits == "82"
    assert out.bban == "WEST12345698765432"
    assert out.computed_check == "82"
    assert out.isbn_prefix is None
    assert out.isbn_body is None
    assert out.isbn_check_digit is None


def test_valid_de_iban() -> None:
    out = _run("iban", "DE89370400440532013000")
    assert out.valid is True
    assert out.reason is None
    assert out.country_code == "DE"
    assert out.computed_check == "89"


def test_iban_lowercase_and_spaces_are_normalised() -> None:
    out = _run("iban", "gb82 west 1234 5698 7654 32")
    assert out.valid is True
    assert out.normalized == "GB82WEST12345698765432"


def test_shortest_registered_iban_length_is_accepted() -> None:
    out = _run("iban", "NO9386011117947")
    assert out.valid is True
    assert out.country_code == "NO"
    assert len(out.normalized) == 15
    assert out.computed_check == "93"


# --- IBAN: incorrect output / rejections ----------------------------------


def test_iban_checksum_mismatch_reports_expected_check_digits() -> None:
    out = _run("iban", "GB83WEST12345698765432")
    assert out.valid is False
    assert out.reason == "check-digit-mismatch"
    assert out.check_digits == "83"
    assert out.computed_check == "82"


def test_iban_unknown_country_is_rejected() -> None:
    out = _run("iban", "ZZ82WEST12345698765432")
    assert out.valid is False
    assert out.reason == "bad-country"
    assert out.country_code == "ZZ"
    assert out.computed_check is None


def test_iban_wrong_country_length_is_rejected() -> None:
    out = _run("iban", "GB82WEST1234569876543")
    assert out.valid is False
    assert out.reason == "bad-length"
    assert out.computed_check is not None


def test_iban_too_short_is_bad_format() -> None:
    out = _run("iban", "NO938601111794")
    assert out.reason == "bad-format"
    assert out.country_code is None
    assert out.computed_check is None


def test_iban_too_long_is_bad_format() -> None:
    out = _run("iban", "GB82" + "A" * 31)
    assert out.reason == "bad-format"
    assert out.country_code is None


def test_iban_leading_characters_must_match_structure() -> None:
    out = _run("iban", "G823WEST12345698765432")
    assert out.reason == "bad-format"
    assert out.check_digits is None


def test_iban_invalid_characters_are_rejected() -> None:
    out = _run("iban", "GB82-WEST-1234-5698-7654-32")
    assert out.reason == "invalid-characters"
    assert out.valid is False
    assert out.normalized == "GB82-WEST-1234-5698-7654-32"


def test_iban_empty_input() -> None:
    out = _run("iban", "")
    assert out.valid is False
    assert out.reason == "empty"
    assert out.normalized == ""
    assert out.country_code is None


def test_iban_whitespace_only_input() -> None:
    out = _run("iban", "   ")
    assert out.reason == "empty"
    assert out.normalized == ""


# --- ISBN-13: correct output ----------------------------------------------


def test_valid_isbn13_with_978_prefix() -> None:
    out = _run("isbn13", "9780306406157")
    assert out.valid is True
    assert out.reason is None
    assert out.kind == "isbn13"
    assert out.normalized == "9780306406157"
    assert out.isbn_prefix == "978"
    assert out.isbn_body == "030640615"
    assert out.isbn_check_digit == "7"
    assert out.computed_check == "7"
    assert out.country_code is None
    assert out.check_digits is None
    assert out.bban is None


def test_valid_isbn13_with_979_prefix() -> None:
    out = _run("isbn13", "9791090636071")
    assert out.valid is True
    assert out.isbn_prefix == "979"
    assert out.computed_check == "1"


def test_isbn13_hyphens_and_spaces_are_normalised() -> None:
    out = _run("isbn13", "978-0-306-40615-7")
    assert out.valid is True
    assert out.normalized == "9780306406157"


# --- ISBN-13: rejections ---------------------------------------------------


def test_isbn13_checksum_mismatch() -> None:
    out = _run("isbn13", "9780306406158")
    assert out.valid is False
    assert out.reason == "check-digit-mismatch"
    assert out.isbn_check_digit == "8"
    assert out.computed_check == "7"


def test_isbn13_bad_prefix() -> None:
    out = _run("isbn13", "9770306406157")
    assert out.reason == "bad-format"
    assert out.isbn_prefix == "977"
    assert out.computed_check is not None


def test_isbn13_wrong_length() -> None:
    out = _run("isbn13", "978030640615")
    assert out.reason == "bad-length"
    assert out.isbn_prefix is None
    assert out.computed_check is None


def test_isbn13_invalid_characters() -> None:
    out = _run("isbn13", "978030640615X")
    assert out.reason == "invalid-characters"
    assert out.normalized == "978030640615X"


def test_isbn13_empty_input() -> None:
    out = _run("isbn13", " ")
    assert out.reason == "empty"
    assert out.normalized == ""


# --- Malformed input -------------------------------------------------------


def test_unknown_kind_raises_value_error() -> None:
    with pytest.raises(ValueError):
        _run("isin", "US0378331005")