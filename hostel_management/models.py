"""Domain models and validation.

Plain dataclasses keep the data shape explicit and fully typed. Validation lives
here so that both the CLI and the web layer enforce identical rules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# The departments offered by the hostel. Kept as the single source of truth so
# the CLI menu and the web dropdowns never drift apart.
DEPARTMENTS: tuple[str, ...] = (
    "COMPUTER",
    "BIO",
    "TECH",
    "PHYSICS",
    "ECO",
    "ENG",
)


class ValidationError(ValueError):
    """Raised when user-supplied data fails a business rule."""


@dataclass
class Student:
    """A hostel resident."""

    roll_no: int
    name: str
    address: str
    room_no: int
    dept: str
    fees: int
    balance: int = 0

    def validate(self) -> None:
        if self.roll_no <= 0:
            raise ValidationError("Roll number must be a positive integer.")
        if not self.name.strip():
            raise ValidationError("Name is required.")
        if not self.address.strip():
            raise ValidationError("Address is required.")
        if self.room_no <= 0:
            raise ValidationError("Room number must be a positive integer.")
        if self.dept.upper() not in DEPARTMENTS:
            raise ValidationError(f"Department must be one of: {', '.join(DEPARTMENTS)}.")
        if self.fees < 0:
            raise ValidationError("Fees cannot be negative.")
        if self.balance < 0:
            raise ValidationError("Balance cannot be negative.")
        self.dept = self.dept.upper()
        self.name = self.name.strip()
        self.address = self.address.strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Student:
        return cls(
            roll_no=int(row["roll_no"]),
            name=row["name"],
            address=row["address"],
            room_no=int(row["room_no"]),
            dept=row["dept"],
            fees=int(row["fees"]),
            balance=int(row["balance"]),
        )


@dataclass
class Fee:
    """A department fee schedule entry."""

    department: str
    amount: int

    def validate(self) -> None:
        if not self.department.strip():
            raise ValidationError("Department is required.")
        if self.amount < 0:
            raise ValidationError("Fee amount cannot be negative.")
        self.department = self.department.strip().upper()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Fee:
        return cls(department=row["department"], amount=int(row["amount"]))
