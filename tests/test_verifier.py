"""Tests for the identifier-validator verifier."""

from verifier import verify_input, verify_output, verify_task

TOOL = "validate_identifier"
TASK = "validate-identifier"


def _input(kind: str, value: str) -> dict:
    return {"kind": kind, "value": value}


def _iban_output(**overrides: object) -> dict:
    base: dict = {
        "kind": "iban",
        "normalized": "GB82WEST12345698765432",
        "valid": True,
        "reason": None,
        "country_code": "GB",
        "check_digits": "82",
        "bban": "WEST12345698765432",
        "computed_check": "82",
        "isbn_prefix": None,
        "isbn_body": None,
        "isbn_check_digit": None,
    }
    base.update(overrides)
    return base


def _isbn_output(**overrides: object) -> dict:
    base: dict = {
        "kind": "isbn13",
        "normalized": "9780306406157",
        "valid": True,
        "reason": None,
        "country_code": None,
        "check_digits": None,
        "bban": None,
        "computed_check": "7",
        "isbn_prefix": "978",
        "isbn_body": "030640615",
        "isbn_check_digit": "7",
    }
    base.update(overrides)
    return base


def test_verifier_accepts_correct_iban_output() -> None:
    inputs = _input("iban", "GB82WEST12345698765432")
    output = _iban_output()
    assert verify_input(TOOL, inputs) is None
    assert verify_output(TOOL, inputs, output, None) is None
    assert verify_task(TASK, [TOOL], inputs, output, None) is None


def test_verifier_accepts_correct_isbn_output() -> None:
    problem = verify_output(
        TOOL,
        _input("isbn13", "978-0-306-40615-7"),
        _isbn_output(),
        None,
    )
    assert problem is None


def test_verifier_rejects_wrong_valid_flag() -> None:
    problem = verify_output(
        TOOL,
        _input("iban", "GB82WEST12345698765432"),
        _iban_output(valid=False),
        None,
    )
    assert problem == "valid: expected True, got False"


def test_verifier_rejects_wrong_reason() -> None:
    # Input has a bad checksum; every fixture field matches what the verifier
    # expects except `reason`, so `reason` is the field that must surface.
    problem = verify_output(
        TOOL,
        _input("iban", "GB83WEST12345698765432"),
        _iban_output(
            normalized="GB83WEST12345698765432",
            valid=False,
            check_digits="83",
            reason="bad-length",
        ),
        None,
    )
    assert problem is not None
    assert problem.startswith("reason: expected 'check-digit-mismatch'")
    assert problem.endswith("got 'bad-length'")


def test_verifier_rejects_wrong_computed_check() -> None:
    problem = verify_output(
        TOOL,
        _input("iban", "GB82WEST12345698765432"),
        _iban_output(computed_check="83"),
        None,
    )
    assert problem == "computed_check: expected '82', got '83'"


def test_verifier_rejects_missing_field() -> None:
    output = _iban_output()
    del output["bban"]
    problem = verify_output(
        TOOL,
        _input("iban", "GB82WEST12345698765432"),
        output,
        None,
    )
    assert problem == "missing field: bban"


def test_verifier_rejects_non_boolean_valid() -> None:
    problem = verify_output(
        TOOL,
        _input("iban", "GB82WEST12345698765432"),
        _iban_output(valid=1),
        None,
    )
    assert problem == "valid: expected bool"


def test_verifier_accepts_empty_identifier_record() -> None:
    problem = verify_output(
        TOOL,
        _input("iban", "   "),
        {
            "kind": "iban",
            "normalized": "",
            "valid": False,
            "reason": "empty",
            "country_code": None,
            "check_digits": None,
            "bban": None,
            "computed_check": None,
            "isbn_prefix": None,
            "isbn_body": None,
            "isbn_check_digit": None,
        },
        None,
    )
    assert problem is None


def test_verifier_rejects_unknown_kind() -> None:
    problem = verify_output(
        TOOL,
        _input("isin", "US0378331005"),
        _iban_output(kind="isin"),
        None,
    )
    assert problem is not None
    assert "kind" in problem
    assert "isin" in problem


def test_verifier_rejects_unknown_tool_name() -> None:
    problem = verify_input("parse_log", {"kind": "iban", "value": "GB82"})
    assert problem is not None
    assert "validate_identifier" in problem


def test_verifier_rejects_unknown_task_name() -> None:
    problem = verify_task(
        "parse-log",
        [TOOL],
        _input("iban", "GB82WEST12345698765432"),
        _iban_output(),
        None,
    )
    assert problem is not None
    assert "validate-identifier" in problem


def test_verifier_accepts_single_string_tools() -> None:
    # Framework may pass ``tools`` as either a list or a bare string.
    problem = verify_task(
        TASK,
        TOOL,
        _input("iban", "GB82WEST12345698765432"),
        _iban_output(),
        None,
    )
    assert problem is None


def test_verifier_accepts_tool_enum_member() -> None:
    # Framework may pass ``Tool.VALIDATE_IDENTIFIER`` instead of the raw
    # string. Because ``Tool`` is a ``StrEnum``, the equality comparison
    # inside ``verify_input`` succeeds either way.
    from contract import Tool

    problem = verify_input(Tool.VALIDATE_IDENTIFIER, _input("iban", "GB82WEST12345698765432"))
    assert problem is None