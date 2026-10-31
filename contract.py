"""Typed input/output contracts for the identifier-validator plugin.

Both the tool (``src/plugin/validate_identifier.py``) and the verifier
(``verifier/__init__.py``) import these definitions. Neither imports the
other: the verifier re-implements the standards independently.

The static contract checker requires this module to import only from
``dataclasses``, ``enum``, ``slimconfig``, and ``typing``, and to declare
both a ``Tool`` and a ``Task`` Enum. No module-level annotated constants
may appear here (the checker would read them as dataclass fields with
defaults).

``Tool`` and ``Task`` derive from ``StrEnum`` so that a member compares
equal to its value string: ``Tool.VALIDATE_IDENTIFIER == "validate_identifier"``
is ``True``. That lets the verifier accept the framework's identifier
whether it passes the enum member or the raw string.
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
class ValidateInput:
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