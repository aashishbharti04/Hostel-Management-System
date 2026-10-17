import pytest
pytest.importorskip("ortools")
from services.ghms_allocator import solve_allocation

def test_accessibility_and_unique_assignments():
    apps=[{"id":"a1","student_id":"s1","eligible":True,"priority":10,"accessibility_required":True},{"id":"a2","student_id":"s2","eligible":True,"priority":20},{"id":"a3","student_id":"s3","eligible":False,"priority":100}]
    beds=[{"id":"b1","hostel_id":"h1","is_accessible":False},{"id":"b2","hostel_id":"h1","is_accessible":True}]
    r=solve_allocation(apps,beds)
    assert r.status=="optimal" and len(r.assignments)==2
    assert len({a["bed_id"] for a in r.assignments})==2
    assert next(a for a in r.assignments if a["student_id"]=="s1")["bed_id"]=="b2"
    assert r.metrics["unassigned_eligible"]==0

def test_coverage_precedes_preferences():
    apps=[{"id":"a1","student_id":"s1","eligible":True,"priority":100,"preferred_room_types":["premium"]},{"id":"a2","student_id":"s2","eligible":True,"priority":0}]
    beds=[{"id":"b1","hostel_id":"h1","room_type":"premium"},{"id":"b2","hostel_id":"h1","room_type":"standard"}]
    r=solve_allocation(apps,beds)
    assert len(r.assignments)==2 and {a["student_id"] for a in r.assignments}=={"s1","s2"}

def test_hostel_request_is_hard_constraint():
    r=solve_allocation([{"id":"a1","student_id":"s1","eligible":True,"priority":1,"requested_hostel_id":"h1"}],[{"id":"b1","hostel_id":"h2"}])
    assert r.assignments==() and r.metrics["unassigned_eligible"]==1

def test_duplicate_student_is_rejected():
    apps=[{"id":"a1","student_id":"s1","eligible":True,"priority":1},{"id":"a2","student_id":"s1","eligible":True,"priority":1}]
    with pytest.raises(ValueError,match="more than one eligible application"): solve_allocation(apps,[{"id":"b1","hostel_id":"h1"}])

def test_priority_validation():
    with pytest.raises(ValueError,match="priority"):
        solve_allocation([{"id":"a1","student_id":"s1","eligible":True,"priority":101}],[{"id":"b1","hostel_id":"h1"}])
