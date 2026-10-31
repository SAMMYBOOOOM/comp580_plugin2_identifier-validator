"""Shared helpers for verifier modules."""

from __future__ import annotations


def result() -> str | None:
    """Return the canonical "verified" value: no problem reported."""
    return None