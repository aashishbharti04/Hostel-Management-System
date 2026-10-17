import { describe, expect, it } from "vitest";
import { canFinalizeAllocationRun } from "./allocation-utils";

describe("canFinalizeAllocationRun", () => {
  it("allows only approved optimal or feasible runs", () => {
    expect(canFinalizeAllocationRun("approved", "optimal")).toBe(true);
    expect(canFinalizeAllocationRun("approved", "feasible")).toBe(true);
  });

  it("rejects unapproved and non-solution runs", () => {
    expect(canFinalizeAllocationRun("pending", "optimal")).toBe(false);
    expect(canFinalizeAllocationRun("approved", "infeasible")).toBe(false);
    expect(canFinalizeAllocationRun("approved", "unknown")).toBe(false);
  });
});
