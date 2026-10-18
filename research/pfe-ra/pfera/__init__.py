"""PFE-RA research prototype for hostel room allocation."""
from .engine import AllocationResult, solve_pfera
from .models import Scenario
from .validation import validate_allocation
__all__ = ["AllocationResult", "Scenario", "solve_pfera", "validate_allocation"]
