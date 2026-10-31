"""Verifier registry for the identifier-validator plugin."""

from __future__ import annotations

from verifier.validate_identifier import verify_validate_identifier

TOOLS = {
    "validate_identifier": verify_validate_identifier,
}

TASKS = {
    "validate-identifier": verify_validate_identifier,
}

__all__ = ["TOOLS", "TASKS"]