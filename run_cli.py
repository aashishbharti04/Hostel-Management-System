"""Convenience launcher for the console application.

    python run_cli.py

Equivalent to ``python -m hostel_management.cli`` or the ``hms-cli`` script.
"""

from hostel_management.cli import main

if __name__ == "__main__":
    main()
