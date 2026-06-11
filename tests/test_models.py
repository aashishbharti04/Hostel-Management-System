"""Unit tests for domain models and validation."""

from __future__ import annotations

import pytest

from hostel_management.models import Fee, Student, ValidationError


def test_valid_student_normalises_fields() -> None:
    s = Student(1, "  Asha  ", "  12 Road  ", 5, "computer", 45000, 0)
    s.validate()
    assert s.name == "Asha"
    assert s.address == "12 Road"
    assert s.dept == "COMPUTER"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"roll_no": 0},
        {"name": "   "},
        {"address": ""},
        {"room_no": -1},
        {"dept": "UNKNOWN"},
        {"fees": -5},
        {"balance": -1},
    ],
)
def test_invalid_student_raises(kwargs: dict) -> None:
    base = dict(roll_no=1, name="A", address="X", room_no=1, dept="BIO", fees=1, balance=0)
    base.update(kwargs)
    with pytest.raises(ValidationError):
        Student(**base).validate()


def test_fee_validation() -> None:
    f = Fee("bio", 1000)
    f.validate()
    assert f.department == "BIO"
    with pytest.raises(ValidationError):
        Fee("BIO", -1).validate()
