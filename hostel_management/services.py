"""Business-logic services.

The service layer is the single entry point used by *both* the CLI and the web
dashboard. It validates input, enforces business rules (e.g. no duplicate roll
numbers), and orchestrates repositories. Neither interface talks to the database
directly, which guarantees consistent behaviour across the two front-ends.
"""

from __future__ import annotations

from .database import Database
from .models import DEPARTMENTS, Fee, Student, ValidationError
from .repository import FeeRepository, StudentRepository

# Seed fee schedule used the first time the app runs against an empty database.
DEFAULT_FEES: dict[str, int] = {
    "COMPUTER": 45000,
    "BIO": 40000,
    "TECH": 42000,
    "PHYSICS": 38000,
    "ECO": 35000,
    "ENG": 41000,
}


class HostelService:
    """High-level operations for managing students and fees."""

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()
        self.students = StudentRepository(self.db)
        self.fees = FeeRepository(self.db)

    # -- students -------------------------------------------------------------
    def list_students(self) -> list[Student]:
        return self.students.list_all()

    def get_student(self, roll_no: int) -> Student | None:
        return self.students.get(roll_no)

    def admit_student(self, student: Student) -> Student:
        """Create a new student record (the original 'Admission Form')."""
        student.validate()
        if self.students.exists(student.roll_no):
            raise ValidationError(f"A student with roll number {student.roll_no} already exists.")
        self.students.add(student)
        return student

    def update_student(self, student: Student) -> Student:
        """Update an existing student (the original 'Modify Data')."""
        student.validate()
        if not self.students.exists(student.roll_no):
            raise ValidationError(f"No student found with roll number {student.roll_no}.")
        self.students.update(student)
        return student

    def delete_student(self, roll_no: int) -> None:
        if not self.students.exists(roll_no):
            raise ValidationError(f"No student found with roll number {roll_no}.")
        self.students.delete(roll_no)

    # -- fees -----------------------------------------------------------------
    def list_fees(self) -> list[Fee]:
        return self.fees.list_all()

    def get_fee(self, department: str) -> Fee | None:
        """Look up a department's fee (the original 'Fee Checking')."""
        return self.fees.get(department)

    def set_fee(self, department: str, amount: int) -> Fee:
        fee = Fee(department=department, amount=amount)
        fee.validate()
        if fee.department not in DEPARTMENTS:
            raise ValidationError(f"Department must be one of: {', '.join(DEPARTMENTS)}.")
        self.fees.upsert(fee)
        return fee

    # -- stats / bootstrap ----------------------------------------------------
    def stats(self) -> dict[str, int]:
        students = self.students.list_all()
        return {
            "total_students": len(students),
            "total_departments": len(DEPARTMENTS),
            "total_fees_billed": sum(s.fees for s in students),
            "outstanding_balance": sum(s.balance for s in students),
        }

    def ensure_seed_fees(self) -> None:
        """Populate the default fee schedule when the table is empty."""
        if not self.fees.list_all():
            for dept, amount in DEFAULT_FEES.items():
                self.fees.upsert(Fee(department=dept, amount=amount))

    def close(self) -> None:
        self.db.close()
