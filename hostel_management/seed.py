"""Seed the database with sample data.

Run with ``python -m hostel_management.seed``. Safe to run repeatedly: existing
records are left untouched.
"""

from __future__ import annotations

from .models import Student
from .services import HostelService

SAMPLE_STUDENTS: list[Student] = [
    Student(1, "Aarav Sharma", "12 MG Road, Delhi", 101, "COMPUTER", 45000, 5000),
    Student(2, "Diya Patel", "8 Lake View, Pune", 102, "BIO", 40000, 0),
    Student(3, "Vivaan Rao", "44 Park Street, Kolkata", 103, "TECH", 42000, 2000),
    Student(4, "Ananya Iyer", "5 Marine Drive, Mumbai", 104, "PHYSICS", 38000, 0),
    Student(5, "Kabir Singh", "19 Sector 17, Chandigarh", 105, "ENG", 41000, 1500),
]


def run() -> None:
    service = HostelService()
    service.ensure_seed_fees()
    created = 0
    for student in SAMPLE_STUDENTS:
        if not service.students.exists(student.roll_no):
            service.admit_student(student)
            created += 1
    print(f"Seed complete. Fees ensured; {created} sample student(s) added.")
    service.close()


if __name__ == "__main__":
    run()
