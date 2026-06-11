"""Data-access repositories.

Repositories translate between domain models and database rows. They contain
*no* business rules — just parameterised CRUD. This separation keeps SQL in one
place and makes the services layer trivial to unit-test against a fake repo.
"""

from __future__ import annotations

from .database import Database
from .models import Fee, Student


class StudentRepository:
    """CRUD operations for :class:`Student`."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def list_all(self) -> list[Student]:
        rows = self.db.query("SELECT * FROM students ORDER BY roll_no")
        return [Student.from_row(r) for r in rows]

    def get(self, roll_no: int) -> Student | None:
        row = self.db.query_one("SELECT * FROM students WHERE roll_no = ?", (roll_no,))
        return Student.from_row(row) if row else None

    def exists(self, roll_no: int) -> bool:
        return self.get(roll_no) is not None

    def add(self, student: Student) -> None:
        self.db.execute(
            """
            INSERT INTO students (roll_no, name, address, room_no, dept, fees, balance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student.roll_no,
                student.name,
                student.address,
                student.room_no,
                student.dept,
                student.fees,
                student.balance,
            ),
        )

    def update(self, student: Student) -> int:
        return self.db.execute(
            """
            UPDATE students
               SET name = ?, address = ?, room_no = ?, dept = ?, fees = ?, balance = ?
             WHERE roll_no = ?
            """,
            (
                student.name,
                student.address,
                student.room_no,
                student.dept,
                student.fees,
                student.balance,
                student.roll_no,
            ),
        )

    def delete(self, roll_no: int) -> int:
        return self.db.execute("DELETE FROM students WHERE roll_no = ?", (roll_no,))

    def count(self) -> int:
        row = self.db.query_one("SELECT COUNT(*) AS n FROM students")
        return int(row["n"]) if row else 0


class FeeRepository:
    """CRUD operations for department :class:`Fee` schedules."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def list_all(self) -> list[Fee]:
        rows = self.db.query("SELECT * FROM fees ORDER BY department")
        return [Fee.from_row(r) for r in rows]

    def get(self, department: str) -> Fee | None:
        row = self.db.query_one("SELECT * FROM fees WHERE department = ?", (department.upper(),))
        return Fee.from_row(row) if row else None

    def upsert(self, fee: Fee) -> None:
        """Insert or update a department fee (backend-agnostic)."""
        if self.get(fee.department):
            self.db.execute(
                "UPDATE fees SET amount = ? WHERE department = ?",
                (fee.amount, fee.department),
            )
        else:
            self.db.execute(
                "INSERT INTO fees (department, amount) VALUES (?, ?)",
                (fee.department, fee.amount),
            )

    def delete(self, department: str) -> int:
        return self.db.execute("DELETE FROM fees WHERE department = ?", (department.upper(),))
