"""Correctness, validation, and exhaustive-oracle tests."""
from __future__ import annotations
import itertools
import pytest
from pfera.baselines import first_fit, preference_greedy
from pfera.engine import solve_pfera
from pfera.metrics import metrics_for
from pfera.models import Scenario
from pfera.synthetic_data import make_scenario
from pfera.validation import validate_allocation

def scenario_one() -> Scenario:
    return Scenario(students=("s1","s2"), beds=("b1","b2"),
        eligible_beds={"s1":("b1","b2"),"s2":("b1","b2")},
        utility={("s1","b1"):100,("s1","b2"):50,("s2","b1"):90,("s2","b2"):10},
        scenario_id="hand-checkable")

def objective(scenario: Scenario, assignment: dict[str,str]) -> tuple[int,int,int,int]:
    metrics=metrics_for(scenario,assignment)
    return (int(metrics["allocated_count"]),-int(metrics["max_regret"]),
        int(metrics["total_utility"]),-int(metrics["reassignments"]))

def exhaustive_optimum(scenario: Scenario) -> tuple[int,int,int,int]:
    options=[tuple(scenario.eligible_beds[s])+(None,) for s in scenario.students]
    feasible=[]
    for choice in itertools.product(*options):
        beds=[bed for bed in choice if bed is not None]
        if len(beds)!=len(set(beds)): continue
        assignment={student:bed for student,bed in zip(scenario.students,choice) if bed is not None}
        feasible.append(objective(scenario,assignment))
    return max(feasible)

def test_cp_sat_matches_exhaustive_oracle_on_hand_case() -> None:
    scenario=scenario_one()
    result=solve_pfera(scenario,time_limit_seconds=5)
    assert result.status=="OPTIMAL"
    assert result.stage_statuses==("OPTIMAL",)*4
    assert objective(scenario,result.assignments)==exhaustive_optimum(scenario)
    assert validate_allocation(scenario,result.assignments).valid

def test_cp_sat_matches_oracle_with_unallocated_student() -> None:
    scenario=Scenario(students=("s1","s2","s3"),beds=("b1","b2"),
        eligible_beds={"s1":("b1",),"s2":("b1","b2"),"s3":("b2",)},
        utility={("s1","b1"):10,("s2","b1"):100,("s2","b2"):20,("s3","b2"):30})
    result=solve_pfera(scenario,time_limit_seconds=5)
    assert result.status=="OPTIMAL"
    assert objective(scenario,result.assignments)==exhaustive_optimum(scenario)

def test_baselines_are_valid_and_deterministic() -> None:
    scenario=scenario_one()
    for algorithm in (first_fit,preference_greedy):
        result=algorithm(scenario)
        assert result==algorithm(scenario)
        assert validate_allocation(scenario,result).valid

def test_independent_validator_rejects_duplicate_and_ineligible_bed() -> None:
    scenario=scenario_one()
    report=validate_allocation(scenario,{"s1":"b1","s2":"b1"})
    assert not report.valid
    assert any("more than one" in error for error in report.violations)
    constrained=Scenario(students=("s1",),beds=("b1","b2"),
        eligible_beds={"s1":("b1",)},utility={("s1","b1"):1})
    assert not validate_allocation(constrained,{"s1":"b2"}).valid

def test_frozen_assignment_is_checked_independently() -> None:
    scenario=Scenario(students=("s1",),beds=("b1",),eligible_beds={"s1":("b1",)},
        utility={("s1","b1"):1},previous_assignments={"s1":"b1"})
    assert validate_allocation(scenario,{"s1":"b1"},freeze_previous=True).valid
    assert not validate_allocation(scenario,{},freeze_previous=True).valid

def test_synthetic_data_is_seed_deterministic() -> None:
    args={"students":12,"beds":14,"seed":42,"eligibility_density":0.6}
    assert make_scenario(**args)==make_scenario(**args)

def test_model_rejects_missing_utility() -> None:
    scenario=Scenario(students=("s1",),beds=("b1",),eligible_beds={"s1":("b1",)},utility={})
    with pytest.raises(ValueError,match="missing integer utility"): scenario.validate()

def test_empty_instance_is_optimal() -> None:
    scenario=Scenario(students=(),beds=(),eligible_beds={},utility={})
    result=solve_pfera(scenario,time_limit_seconds=5)
    assert result.status=="OPTIMAL"
    assert result.assignments=={}
