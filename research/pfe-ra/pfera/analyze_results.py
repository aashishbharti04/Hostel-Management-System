"""Paired benchmark analysis; outputs descriptive statistics and bootstrap CIs."""
from __future__ import annotations
import argparse, csv, json, random, statistics
from pathlib import Path
try:
    from scipy.stats import wilcoxon
except ImportError:
    wilcoxon = None

METRICS = ("allocated_count", "allocation_rate", "max_regret", "mean_regret", "total_utility", "reassignments")
BASELINES = ("first_fit", "preference_greedy")

def ci(values, reps=5000, seed=20261018):
    if not values: return [None, None]
    rng = random.Random(seed)
    means = sorted(statistics.mean(values[rng.randrange(len(values))] for _ in values) for _ in range(reps))
    return [means[int(.025*(reps-1))], means[int(.975*(reps-1))]]

def holm(rows):
    ix=sorted((r["p_value"],i) for i,r in enumerate(rows) if r["p_value"] is not None)
    m=len(ix); adjusted=[None]*len(rows); running=0.0
    for rank,(p,i) in enumerate(ix):
        running=max(running,min(1.0,(m-rank)*p))
        adjusted[i]=running
    for i,r in enumerate(rows): r["holm_adjusted_p_value"]=adjusted[i]
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="results/benchmark_results.json")
    ap.add_argument("--output",default="results")
    ap.add_argument("--bootstrap-replicates",type=int,default=5000)
    args=ap.parse_args()
    out=Path(args.output); data=json.loads(Path(args.input).read_text()); raw=data["results"]
    keyed={(r["scenario"],r["algorithm"]):r for r in raw}
    comparisons=[]
    scenarios=sorted({r["scenario"] for r in raw})
    for baseline in BASELINES:
        for metric in METRICS:
            pairs=[]
            for scenario in scenarios:
                a=keyed.get((scenario,"pfe_ra")); b=keyed.get((scenario,baseline))
                if a is None or b is None: continue
                if metric not in a or metric not in b: continue
                pairs.append((float(a[metric]),float(b[metric])))
            diffs=[a-b for a,b in pairs]
            if not diffs: continue
            if wilcoxon is None: p=None
            elif all(d==0 for d in diffs): p=1.0
            else:
                try: p=float(wilcoxon(diffs,alternative="two-sided",method="auto").pvalue)
                except ValueError: p=1.0
            comparisons.append({
                "comparison":f"pfe_ra - {baseline}","metric":metric,"n_pairs":len(diffs),
                "mean_difference":statistics.mean(diffs),"median_difference":statistics.median(diffs),
                "bootstrap_95_ci":ci(diffs,args.bootstrap_replicates,seed=20261018+len(diffs)+len(metric)),
                "p_value":p,
                "interpretation":"positive favors PFE-RA" if metric in ("allocated_count","allocation_rate","total_utility") else "negative favors PFE-RA"
            })
    holm(comparisons)
    (out/"paired_statistics.json").write_text(json.dumps(comparisons,indent=2))
    fields=list(comparisons[0]) if comparisons else ["comparison","metric","n_pairs"]
    with (out/"paired_statistics.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(comparisons)
    pfe=[r for r in raw if r["algorithm"]=="pfe_ra"]
    fairness={
      "status":"LIMITED_PROXY_METRICS_ONLY",
      "note":"The current Scenario model has no protected/group membership field, so group allocation-rate parity cannot be measured. Regret and reassignment are not substitutes for group fairness.",
      "pfe_ra_runs":len(pfe),
      "all_pfe_ra_optimal":bool(pfe) and all(r.get("status")=="OPTIMAL" for r in pfe),
      "all_pfe_ra_valid":bool(pfe) and all(not r.get("validation_errors") for r in pfe),
      "mean_allocation_rate":statistics.mean(float(r["allocation_rate"]) for r in pfe) if pfe else None,
      "mean_max_regret":statistics.mean(float(r["max_regret"]) for r in pfe) if pfe else None,
      "mean_utility":statistics.mean(float(r["total_utility"]) for r in pfe) if pfe else None,
      "mean_reassignments":statistics.mean(float(r["reassignments"]) for r in pfe) if pfe else None,
      "group_parity":"NOT_MEASURED: group attribute is absent from the current scenario schema"
    }
    (out/"fairness_analysis.json").write_text(json.dumps(fairness,indent=2))
    md=["# Paired PFE-RA benchmark analysis","",
      "Results are paired by synthetic scenario ID. Confidence intervals use a deterministic percentile bootstrap; Wilcoxon tests are two-sided and p-values are Holm-adjusted across the reported comparison family.","",
      "| Comparison | Metric | Pairs | Mean difference | Median difference | Bootstrap 95% CI | p | Holm p |",
      "|---|---|---:|---:|---:|---|---:|---:|"]
    for r in comparisons:
        ci_text="NA" if r["bootstrap_95_ci"][0] is None else f'[{r["bootstrap_95_ci"][0]:.3f}, {r["bootstrap_95_ci"][1]:.3f}]'
        pv="NA" if r["p_value"] is None else f'{r["p_value"]:.4g}'
        hp="NA" if r["holm_adjusted_p_value"] is None else f'{r["holm_adjusted_p_value"]:.4g}'
        md.append(f'| {r["comparison"]} | {r["metric"]} | {r["n_pairs"]} | {r["mean_difference"]:.3f} | {r["median_difference"]:.3f} | {ci_text} | {pv} | {hp} |')
    md += ["","## Fairness scope","",
      fairness["note"],"","The current repository schema cannot support group parity claims. Do not describe regret or reassignment metrics as group fairness."]
    (out/"paired_statistics.md").write_text("\n".join(md)+"\n")
    print(json.dumps({"comparisons":len(comparisons),"pfe_ra_runs":len(pfe),"all_optimal":fairness["all_pfe_ra_optimal"],"fairness_scope":fairness["status"]},indent=2))
if __name__=="__main__": main()
