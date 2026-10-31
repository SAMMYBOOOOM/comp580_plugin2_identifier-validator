# Identifier Validator

Deterministic, offline validation of **IBAN** (ISO 13616) and **ISBN-13**
(ISO 2108) identifiers. The tool parses a raw identifier, normalises it,
applies the standard's structural and checksum rules, and returns a fully
typed record — including the checksum it *should* have had.

## Tools

### `validate_identifier`

Input (`contract.ValidateInput`):

| field   | type  | meaning                                                        |
| ------- | ----- | -------------------------------------------------------------- |
| `kind`  | `str` | exactly `"iban"` or `"isbn13"` (case-sensitive)                 |
| `value` | `str` | raw identifier; ASCII spaces are ignored, ISBN hyphens too      |

Output (`contract.ValidateOutput`):

| field              | type           | meaning                                                                 |
| ------------------ | -------------- | ----------------------------------------------------------------------- |
| `kind`             | `str`          | echo of the input family                                                |
| `normalized`       | `str`          | uppercased, separators removed                                          |
| `valid`            | `bool`         | `True` only when `reason is None`                                       |
| `reason`           | `str \| None`  | `None` when valid, else one of the closed codes below                   |
| `country_code`     | `str \| None`  | IBAN: first two letters                                                 |
| `check_digits`     | `str \| None`  | IBAN: digits 3–4 as supplied                                            |
| `bban`             | `str \| None`  | IBAN: everything after the check digits                                 |
| `computed_check`   | `str \| None`  | IBAN: the correct two check digits; ISBN-13: the correct check digit     |
| `isbn_prefix`      | `str \| None`  | ISBN-13: `"978"` or `"979"`                                             |
| `isbn_body`        | `str \| None`  | ISBN-13: the nine digits between prefix and check digit                 |
| `isbn_check_digit` | `str \| None`  | ISBN-13: the supplied thirteenth digit                                  |

Closed `reason` taxonomy: `empty`, `invalid-characters`, `bad-format`,
`bad-country`, `bad-length`, `check-digit-mismatch`.

### Tasks

- **`validate-identifier`** — runner `tool`, uses `validate_identifier`.
  Given one identifier, produce the full `ValidateOutput` record. The result
  is objectively checkable because the verifier re-derives every field from
  the raw input using its own independent implementation of the same
  standards.

## Layout

```text
identifier-validator/
├── .env
├── .gitignore
├── LICENSE
├── README.md
├── contract.py                  # shared dataclasses (tool + verifier)
├── nanoagent.yaml
├── pyproject.toml
├── uv.lock
├── product/
│   ├── icon.svg
│   └── product.yaml
├── src/plugin/
│   ├── __init__.py
│   ├── __main__.py              # MCP stdio server
│   └── validate_identifier.py   # tool implementation
├── tests/
│   ├── test_validate_identifier.py
│   └── test_verifier.py
├── ui/
│   ├── renderers.css
│   └── renderers.js
└── verifier/
    └── __init__.py              # verify_input / verify_output / verify_task