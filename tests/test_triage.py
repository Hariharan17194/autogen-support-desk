"""Tests for triage parsing and department matching — no API calls."""

import json

import pytest

from agents import DEPARTMENTS, _match_department, parse_triage

FALLBACK = "Account & General"


def test_five_departments_configured():
    assert len(DEPARTMENTS) == 5
    assert FALLBACK in DEPARTMENTS


@pytest.mark.parametrize("name", list(DEPARTMENTS))
def test_exact_department_name_matches(name):
    assert _match_department(name) == name
    assert _match_department(name.upper()) == name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("billing team", "Billing"),
        ("technical", "Technical Support"),
        ("shipping", "Shipping & Returns"),
    ],
)
def test_partial_department_name_matches(raw, expected):
    assert _match_department(raw) == expected


@pytest.mark.parametrize("raw", ["", None, "legal", "🤷"])
def test_unknown_department_falls_back(raw):
    assert _match_department(raw) == FALLBACK


def test_parse_valid_json_wrapped_in_prose():
    payload = {
        "research": "Customer reports a duplicate charge.",
        "department": "Billing",
        "confidence": 0.92,
        "reason": "Mentions being charged twice.",
    }
    text = f"Here is my routing decision:\n```json\n{json.dumps(payload)}\n```"
    result = parse_triage(text)
    assert result.department == "Billing"
    assert result.confidence == pytest.approx(0.92)
    assert result.research.startswith("Customer reports")


def test_parse_garbage_falls_back_safely():
    result = parse_triage("I think this is about something.")
    assert result.department == FALLBACK
    assert result.confidence == 0.0
    assert "defaulted" in result.reason.lower()


def test_parse_broken_json_uses_keywords_in_raw_text():
    # Invalid JSON → the parser falls back to keyword-matching the raw reply.
    result = parse_triage('{"department": "Billing", "confidence": }')
    assert result.department == "Billing"
    assert result.confidence == 0.0
