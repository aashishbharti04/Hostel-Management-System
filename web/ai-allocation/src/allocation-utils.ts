export function canFinalizeAllocationRun(status: string, solverStatus: string): boolean {
  return status === "approved" && (solverStatus === "optimal" || solverStatus === "feasible");
}
