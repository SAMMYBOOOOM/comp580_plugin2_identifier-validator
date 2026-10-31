"""Typed input/output contracts for the identifier-validator plugin.

Both the tool (``src/plugin/validate_identifier.py``) and the verifier
(``verifier/__init__.py``) import these definitions. Neither imports the
other: the verifier re-implements the standards independently.

Static-checker requirements satisfied here:

- imports only from ``dataclasses``, ``enum``, ``slimconfig``, ``typing``;
- declares a ``Tool`` Enum and a ``Task`` Enum;
- declares ``TOOLS`` mapping every ``Tool`` member to
  ``(input_class, output_class)`` and ``TASKS`` mapping every ``Task``
  member to ``(input_class, output_class)``;
- every class appearing in those tuples subclasses ``slimconfig.Output``
  — including the *input* classes.

``TOOLS`` and ``TASKS`` are unannotated on purpose: the checker treats any
annotated module-level assignment as a dataclass field with a default and
rejects it. ``Tool`` and ``Task`` derive from ``StrEnum`` so a member
compares equal to its value string, letting the verifier accept the
identifier whether the framework passes the enum member or the raw string.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from slimconfig import Output


class Tool(StrEnum):
    VALIDATE_IDENTIFIER = "validate_identifier"


class Task(StrEnum):
    VALIDATE_IDENTIFIER = "validate-identifier"


@dataclass
class ValidateInput(Output):
    kind: Annotated[
        str,
        "Identifier family to validate. Exactly 'iban' or 'isbn13'; "
        "lowercase and case-sensitive. Any other value is rejected.",
    ]
    value: Annotated[
        str,
        "Raw identifier text. ASCII space characters are ignored for both "
        "families; ASCII hyphens are additionally ignored for 'isbn13'. "
        "All other characters are significant.",
    ]


@dataclass
class ValidateOutput(Output):
    kind: Annotated[
        str,
        "Echo of the validated family: 'iban' or 'isbn13'.",
    ]
    normalized: Annotated[
        str,
        "Identifier after removing ignored separators and uppercasing. "
        "Empty string when the input had no significant characters.",
    ]
    valid: Annotated[
        bool,
        "True if and only if reason is None.",
    ]
    reason: Annotated[
        str | None,
        "None when valid; otherwise exactly one of 'empty', "
        "'invalid-characters', 'bad-format', 'bad-country', 'bad-length', "
        "'check-digit-mismatch'.",
    ]
    country_code: Annotated[
        str | None,
        "IBAN only: the two-letter ISO 3166-1 alpha-2 country code. "
        "None for ISBN-13 and for inputs rejected before the field split.",
    ]
    check_digits: Annotated[
        str | None,
        "IBAN only: the two supplied check digits (characters 3-4).",
    ]
    bban: Annotated[
        str | None,
        "IBAN only: the basic bank account number, i.e. everything after "
        "the four leading characters.",
    ]
    computed_check: Annotated[
        str | None,
        "The check characters the identifier ought to carry. IBAN: the two "
        "mod-97 check digits recomputed from the BBAN. ISBN-13: the single "
        "check digit recomputed from the first twelve digits. None when the "
        "value was rejected before those characters could be isolated.",
    ]
    isbn_prefix: Annotated[
        str | None,
        "ISBN-13 only: the three-digit EAN prefix, '978' or '979'.",
    ]
    isbn_body: Annotated[
        str | None,
        "ISBN-13 only: the nine digits between the prefix and the check digit.",
    ]
    isbn_check_digit: Annotated[
        str | None,
        "ISBN-13 only: the supplied thirteenth digit.",
    ]


TOOLS = {
    Tool.VALIDATE_IDENTIFIER: (ValidateInput, ValidateOutput),
}

TASKS = {
    Task.VALIDATE_IDENTIFIER: (ValidateInput, ValidateOutput),
}