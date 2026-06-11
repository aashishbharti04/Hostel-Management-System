"""Command-line interface.

This is the modern, hardened successor to the original ``6081.program.py``
console script. Every original feature is preserved:

    1. Admission Form   -> create a student
    2. Fee Checking     -> look up a department's fee
    3. Modify Data      -> view / update a student
    4. Authorities Only -> password-gated admin actions (list / delete)
    5. Quit

Improvements over the original: a real menu loop, input validation, friendly
error handling, parameterised queries (no SQL injection), and no destructive
side effects on startup.
"""

from __future__ import annotations

from .config import get_config
from .models import DEPARTMENTS, Student, ValidationError
from .services import HostelService

BANNER = r"""
==========================================================
            WELCOME TO THE HOSTEL MANAGEMENT SYSTEM
==========================================================
"""

MENU = """
  1. Admission Form
  2. Fee Checking
  3. Modify / View Data
  4. Authorities Only
  5. Quit
"""


def _prompt_int(label: str) -> int:
    while True:
        raw = input(label).strip()
        try:
            return int(raw)
        except ValueError:
            print("  ! Please enter a whole number.")


def _prompt_nonempty(label: str) -> str:
    while True:
        raw = input(label).strip()
        if raw:
            return raw
        print("  ! This field is required.")


def _prompt_department(label: str) -> str:
    print("  Departments:", ", ".join(DEPARTMENTS))
    while True:
        raw = input(label).strip().upper()
        if raw in DEPARTMENTS:
            return raw
        print(f"  ! Choose one of: {', '.join(DEPARTMENTS)}")


def admission_form(service: HostelService) -> None:
    print("\n--- ADMISSION FORM ---")
    student = Student(
        roll_no=_prompt_int("  Roll number: "),
        name=_prompt_nonempty("  Name: "),
        address=_prompt_nonempty("  Address: "),
        room_no=_prompt_int("  Room number: "),
        dept=_prompt_department("  Department: "),
        fees=_prompt_int("  Fees: "),
        balance=_prompt_int("  Balance: "),
    )
    try:
        service.admit_student(student)
        print(f"  > Admitted {student.name} (roll {student.roll_no}).")
    except ValidationError as exc:
        print(f"  ! {exc}")


def fee_checking(service: HostelService) -> None:
    print("\n--- FEE CHECKING ---")
    dept = _prompt_department("  Department: ")
    fee = service.get_fee(dept)
    if fee:
        print(f"  > Fee for {dept}: {fee.amount}")
    else:
        print(f"  ! No fee configured for {dept}.")


def modify_data(service: HostelService) -> None:
    print("\n--- MODIFY / VIEW DATA ---")
    roll_no = _prompt_int("  Roll number: ")
    student = service.get_student(roll_no)
    if not student:
        print(f"  ! No student found with roll number {roll_no}.")
        return

    print("  Current record:")
    for key, value in student.to_dict().items():
        print(f"    {key}: {value}")

    if input("  Update this record? (y/N): ").strip().lower() != "y":
        return

    student.name = input(f"  Name [{student.name}]: ").strip() or student.name
    student.address = input(f"  Address [{student.address}]: ").strip() or student.address
    student.fees = _prompt_int(f"  Fees [{student.fees}]: ")
    student.balance = _prompt_int(f"  Balance [{student.balance}]: ")
    try:
        service.update_student(student)
        print("  > Record updated.")
    except ValidationError as exc:
        print(f"  ! {exc}")


def authorities_only(service: HostelService) -> None:
    print("\n--- AUTHORITIES ONLY ---")
    password = input("  Admin password: ").strip()
    if password != get_config().admin_password:
        print("  ! Access denied. You are not authorised to use this section.")
        return

    students = service.list_students()
    if not students:
        print("  (no students on record)")
        return

    print(f"  {len(students)} student(s) on record:")
    for s in students:
        print(f"    {s.roll_no:>4}  {s.name:<20}  {s.dept:<8}  bal={s.balance}")

    raw = input("  Delete a roll number (blank to skip): ").strip()
    if raw:
        try:
            service.delete_student(int(raw))
            print(f"  > Deleted roll {raw}.")
        except (ValidationError, ValueError) as exc:
            print(f"  ! {exc}")


def main() -> None:
    service = HostelService()
    service.ensure_seed_fees()
    print(BANNER)
    actions = {
        1: admission_form,
        2: fee_checking,
        3: modify_data,
        4: authorities_only,
    }
    try:
        while True:
            print(MENU)
            choice = _prompt_int("  Enter your choice: ")
            if choice == 5:
                print("\n  Goodbye!")
                break
            action = actions.get(choice)
            if action:
                action(service)
            else:
                print("  ! Invalid choice. Pick 1-5.")
    except (KeyboardInterrupt, EOFError):
        print("\n  Goodbye!")
    finally:
        service.close()


if __name__ == "__main__":
    main()
