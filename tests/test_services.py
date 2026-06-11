"""Integration tests for the service + repository + database layers."""

from __future__ import annotations

import pytest

from hostel_management.models import Student, ValidationError
from hostel_management.services import HostelService


def _student(roll: int = 1) -> Student:
    return Student(roll, "Asha", "12 Road", 5, "COMPUTER", 45000, 1000)


def test_admit_and_fetch_student(service: HostelService) -> None:
    service.admit_student(_student(1))
    fetched = service.get_student(1)
    assert fetched is not None
    assert fetched.name == "Asha"
    assert service.students.count() == 1


def test_duplicate_roll_rejected(service: HostelService) -> None:
    service.admit_student(_student(1))
    with pytest.raises(ValidationError):
        service.admit_student(_student(1))


def test_update_student(service: HostelService) -> None:
    service.admit_student(_student(1))
    s = service.get_student(1)
    assert s is not None
    s.balance = 0
    service.update_student(s)
    assert service.get_student(1).balance == 0


def test_update_missing_student_rejected(service: HostelService) -> None:
    with pytest.raises(ValidationError):
        service.update_student(_student(99))


def test_delete_student(service: HostelService) -> None:
    service.admit_student(_student(1))
    service.delete_student(1)
    assert service.get_student(1) is None


def test_seed_fees_idempotent(service: HostelService) -> None:
    service.ensure_seed_fees()
    first = len(service.list_fees())
    service.ensure_seed_fees()
    assert len(service.list_fees()) == first == 6


def test_fee_lookup(service: HostelService) -> None:
    service.set_fee("COMPUTER", 50000)
    fee = service.get_fee("computer")  # case-insensitive
    assert fee is not None and fee.amount == 50000


def test_sql_injection_is_neutralised(service: HostelService) -> None:
    """A classic injection payload must be treated as literal data, not SQL."""
    malicious = "Robert'); DROP TABLE students;--"
    service.admit_student(Student(7, malicious, "X", 1, "BIO", 1, 0))
    # Table still exists and the value was stored verbatim.
    assert service.get_student(7).name == malicious
    assert service.students.count() == 1


def test_stats(service: HostelService) -> None:
    service.admit_student(Student(1, "A", "X", 1, "BIO", 1000, 200))
    service.admit_student(Student(2, "B", "Y", 2, "ENG", 2000, 300))
    stats = service.stats()
    assert stats["total_students"] == 2
    assert stats["total_fees_billed"] == 3000
    assert stats["outstanding_balance"] == 500
