import pytest

from services.ghms_allocator import solve_allocation

pytest.importorskip("ortools")


def test_accessibility_and_unique_assignments():
    applications = [
        {
            "id": "a1",
            "student_id": "s1",
            "eligible": True,
            "priority": 10,
            "accessibility_required": True,
        },
        {"id": "a2", "student_id": "s2", "eligible": True, "priority": 20},
        {"id": "a3", "student_id": "s3", "eligible": False, "priority": 100},
    ]
    beds = [
        {"id": "b1", "hostel_id": "h1", "is_accessible": False},
        {"id": "b2", "hostel_id": "h1", "is_accessible": True},
    ]

    result = solve_allocation(applications, beds)

    assert result.status == "optimal"
    assert len(result.assignments) == 2
    assert len({assignment["bed_id"] for assignment in result.assignments}) == 2
    assert (
        next(assignment for assignment in result.assignments if assignment["student_id"] == "s1")[
            "bed_id"
        ]
        == "b2"
    )
    assert result.metrics["unassigned_eligible"] == 0


def test_coverage_precedes_preferences():
    applications = [
        {
            "id": "a1",
            "student_id": "s1",
            "eligible": True,
            "priority": 100,
            "preferred_room_types": ["premium"],
        },
        {"id": "a2", "student_id": "s2", "eligible": True, "priority": 0},
    ]
    beds = [
        {"id": "b1", "hostel_id": "h1", "room_type": "premium"},
        {"id": "b2", "hostel_id": "h1", "room_type": "standard"},
    ]

    result = solve_allocation(applications, beds)

    assert len(result.assignments) == 2
    assert {assignment["student_id"] for assignment in result.assignments} == {
        "s1",
        "s2",
    }


def test_hostel_request_is_hard_constraint():
    result = solve_allocation(
        [
            {
                "id": "a1",
                "student_id": "s1",
                "eligible": True,
                "priority": 1,
                "requested_hostel_id": "h1",
            }
        ],
        [{"id": "b1", "hostel_id": "h2"}],
    )

    assert result.assignments == ()
    assert result.metrics["unassigned_eligible"] == 1


def test_duplicate_student_is_rejected():
    applications = [
        {"id": "a1", "student_id": "s1", "eligible": True, "priority": 1},
        {"id": "a2", "student_id": "s1", "eligible": True, "priority": 1},
    ]

    with pytest.raises(ValueError, match="more than one eligible application"):
        solve_allocation(applications, [{"id": "b1", "hostel_id": "h1"}])


def test_priority_validation():
    with pytest.raises(ValueError, match="priority"):
        solve_allocation(
            [
                {
                    "id": "a1",
                    "student_id": "s1",
                    "eligible": True,
                    "priority": 101,
                }
            ],
            [{"id": "b1", "hostel_id": "h1"}],
        )
