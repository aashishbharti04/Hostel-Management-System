from hostel_management.fairness_audit import DecisionRecord, counterfactual_check, exhaustive_optimum, group_fairness_report

def test_group_metrics_use_eligible_denominator():
    records = [DecisionRecord("a1","A",True,True,"approved"), DecisionRecord("a2","A",True,False,"waitlisted"), DecisionRecord("a3","A",False,False,"ineligible"), DecisionRecord("b1","B",True,True,"approved"), DecisionRecord("b2","B",True,False,"waitlisted")]
    report = group_fairness_report(records, "A")
    assert report["groups"]["A"]["eligible_count"] == 2
    assert report["groups"]["A"]["selection_rate"] == 0.5
    assert report["groups"]["B"]["rate_difference"] == 0.0

def test_disparity_is_reported_as_diagnostic():
    records = [DecisionRecord("a1","A",True,True,"approved"), DecisionRecord("a2","A",True,True,"approved"), DecisionRecord("b1","B",True,False,"waitlisted"), DecisionRecord("b2","B",True,True,"approved")]
    report = group_fairness_report(records, "A")
    assert report["groups"]["B"]["selection_rate_ratio"] == 0.5
    assert "Descriptive disparity only" in report["interpretation"]

def test_missing_eligible_reference_fails_closed():
    records = [DecisionRecord("b1","B",False,False,"ineligible")]
    try:
        group_fairness_report(records, "B")
    except ValueError as exc:
        assert "no eligible" in str(exc)
    else:
        raise AssertionError("expected ValueError")

def test_counterfactual_invariance_and_detection():
    case = {"eligible": True, "priority": 2, "color": "blue"}
    result = counterfactual_check(lambda x: (x["eligible"], x["priority"]), case, "color", "green")
    assert result["passed"]
    leaked = counterfactual_check(lambda x: x["color"] == "blue", case, "color", "green")
    assert not leaked["passed"]

def test_exhaustive_oracle_finds_best_feasible_subset():
    candidates = [{"id":"a","eligible":True,"score":4},{"id":"b","eligible":True,"score":9},{"id":"c","eligible":False,"score":100},{"id":"d","eligible":True,"score":5}]
    result = exhaustive_optimum(candidates, 2, lambda chosen: sum(c["score"] for c in chosen))
    assert result["status"] == "OPTIMAL_EXHAUSTIVE"
    assert result["objective_value"] == 14
    assert result["selected_ids"] == ["b", "d"]
    assert result["subsets_examined"] == 7

def test_exhaustive_oracle_rejects_duplicate_ids():
    try:
        exhaustive_optimum([{"id":"x","eligible":True},{"id":"x","eligible":True}], 1, lambda chosen: len(chosen))
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("expected ValueError")
