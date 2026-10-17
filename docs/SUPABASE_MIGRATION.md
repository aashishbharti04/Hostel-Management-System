# GHMS allocation: reproducible verification and production gates

## Scope

This branch adds a **new Supabase/PostgreSQL target schema**, not an in-place
migration of the existing Flask SQLite/MySQL application. No production data is
changed by this branch. The canonical university schema and existing live
Supabase project must be reconciled before deployment.

## Run the database tests

Install Docker and the Supabase CLI. From repository root:

```sh
supabase start
supabase db reset
supabase test db
```

The tests under `supabase/tests/database` are catalog-level pgTAP checks.
They verify constraints, role grants, and RLS configuration. **They do not
establish authenticated RLS behavior or transaction concurrency safety.**

## Independent adversarial test protocol

Use a disposable PostgreSQL/Supabase instance. Create two distinct Auth
identities with `warden` role and assigned hostel scope, two eligible student
applications, one active bed, an approved immutable policy, and two independently
approved allocation runs that each select that same bed.

1. Authenticate each warden separately; retain both JWTs.
2. Start two independent database sessions and call
   `ghms_finalize_allocation_run(run_id)` concurrently.
3. Require exactly one successful commit and one rejection.
4. Verify only one active allocation exists for the bed and the losing run
   has no partial allocations or finalized event.
5. Retry the winning run; require rejection without duplicate allocations.
6. Repeat using the same student but different beds; require no overlapping
   active allocation for that student.
7. Inject a bad selected candidate after a valid candidate; verify that the
   entire RPC rolls back, including audit events.
8. Authenticate as a student, an unassigned warden, and an anonymous user.
   Require all to fail finalization.
9. Confirm users cannot directly INSERT/UPDATE `room_allocations`,
   `user_roles`, `allocation_events`, or approved policy versions.
10. Confirm a student can read only their own allocation/application and a
    warden cannot read another hostel's private records.

Record SQLSTATEs, HTTP responses, transaction outcomes, final row counts,
Git SHA, Supabase CLI version, PostgreSQL version, and CI URLs.

## Security model

The `ghms_finalize_allocation_run` SECURITY DEFINER function authenticates
the caller, checks hostel scope, locks the run row, validates selected
candidates, inserts allocations, and writes an audit event in one transaction.
PostgreSQL GiST exclusion constraints independently reject overlapping
active/pending assignments for the same bed or student. This protects the
database even if concurrent callers pass application-level prechecks.

The current RPC assigns open-ended occupancy beginning on `current_date`.
The canonical policy must specify exact start/end dates, eligibility,
accessibility and other hostel-specific restrictions before deployment.

## Release decision checklist

| Gate | Status | Required evidence |
|---|---|---|
| Migration syntax on disposable Postgres | UNVERIFIED | `supabase db reset` log |
| pgTAP schema and grants | UNVERIFIED | `supabase test db` log |
| Authenticated cross-role RLS | NOT IMPLEMENTED AS E2E | Negative/positive JWT tests |
| Two-session concurrency | NOT EXECUTED | Two-session transaction logs |
| Atomic rollback and idempotency | NOT EXECUTED | Before/after snapshots |
| Existing Flask integration | NOT IMPLEMENTED | App/API regression suite |
| Legacy data reconciliation | NOT IMPLEMENTED | Counts, balances, rollback drill |
| CP-SAT fairness and explanation | NOT IN THIS BRANCH | Solver tests and audit outputs |
| University schema/policy approval | PENDING | Signed review |
| Production release | **NO-GO** | All gates green |

No signed release candidate or claim of a passing CI run is justified until
the evidence exists. A GitHub source branch is a review artifact, not a
production approval.
