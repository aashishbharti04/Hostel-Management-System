-- GHMS Supabase/PostgreSQL target schema.
-- This is a new Supabase schema baseline; it does NOT alter the existing SQLite/MySQL DB.
-- Existing legacy students/fees must be exported, mapped, and imported through a reviewed
-- migration process. Never point this migration at production without a verified backup.
begin;

create extension if not exists pgcrypto with schema extensions;
create extension if not exists btree_gist with schema extensions;

create table public.profiles (
  id uuid primary key references auth.users(id) on delete restrict,
  full_name text not null check (length(trim(full_name)) > 0),
  email text,
  account_status text not null default 'active'
    check (account_status in ('active','suspended','inactive')),
  created_at timestamptz not null default now()
);

create table public.user_roles (
  user_id uuid not null references public.profiles(id) on delete restrict,
  role text not null check (role in ('student','warden','auditor','admin')),
  primary key (user_id, role)
);

create table public.departments (
  id uuid primary key default gen_random_uuid(),
  name text not null unique check (length(trim(name)) > 0)
);

-- Retains the legacy application's natural roll number and department/fee fields.
create table public.students (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid unique references public.profiles(id) on delete restrict,
  legacy_roll_no bigint unique check (legacy_roll_no is null or legacy_roll_no > 0),
  name text not null check (length(trim(name)) > 0),
  address text not null default '',
  department_id uuid references public.departments(id) on delete restrict,
  department_code text,
  current_year smallint check (current_year is null or current_year between 1 and 12),
  status text not null default 'active'
    check (status in ('active','graduated','withdrawn','suspended')),
  created_at timestamptz not null default now()
);

create table public.fee_schedules (
  id uuid primary key default gen_random_uuid(),
  department_id uuid references public.departments(id) on delete restrict,
  legacy_department_code text,
  amount_minor bigint not null check (amount_minor >= 0),
  currency char(3) not null default 'INR',
  effective_from date not null default current_date,
  effective_until date,
  created_at timestamptz not null default now(),
  check (effective_until is null or effective_until >= effective_from)
);

create table public.hostels (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table public.warden_hostels (
  warden_id uuid not null references public.profiles(id) on delete restrict,
  hostel_id uuid not null references public.hostels(id) on delete restrict,
  primary key (warden_id, hostel_id)
);

create table public.rooms (
  id uuid primary key default gen_random_uuid(),
  hostel_id uuid not null references public.hostels(id) on delete restrict,
  room_number text not null,
  floor_number integer,
  room_type text,
  is_accessible boolean not null default false,
  status text not null default 'available'
    check (status in ('available','maintenance','inactive')),
  unique (hostel_id, room_number),
  unique (id, hostel_id)
);

create table public.beds (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references public.rooms(id) on delete restrict,
  bed_number text not null,
  status text not null default 'available'
    check (status in ('available','maintenance','inactive')),
  unique (room_id, bed_number)
);

create table public.academic_sessions (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  starts_on date not null,
  ends_on date not null,
  check (ends_on >= starts_on)
);

create table public.applications (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete restrict,
  academic_session_id uuid not null references public.academic_sessions(id) on delete restrict,
  requested_hostel_id uuid references public.hostels(id) on delete restrict,
  status text not null default 'draft'
    check (status in ('draft','submitted','eligible','ineligible','waitlisted','withdrawn')),
  submitted_at timestamptz,
  eligibility_evidence jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (student_id, academic_session_id)
);

create table public.allocation_policies (
  id uuid primary key default gen_random_uuid(),
  version_number integer not null unique check (version_number > 0),
  policy_document jsonb not null,
  policy_hash text not null unique,
  status text not null default 'draft' check (status in ('draft','approved','retired')),
  approved_by uuid references public.profiles(id) on delete restrict,
  approved_at timestamptz,
  created_at timestamptz not null default now(),
  check ((status = 'approved') = (approved_at is not null and approved_by is not null))
);

create table public.allocation_runs (
  id uuid primary key default gen_random_uuid(),
  academic_session_id uuid not null references public.academic_sessions(id) on delete restrict,
  hostel_id uuid not null references public.hostels(id) on delete restrict,
  policy_id uuid not null references public.allocation_policies(id) on delete restrict,
  algorithm_name text not null,
  algorithm_version text not null,
  input_snapshot jsonb not null,
  input_hash text not null,
  solver_config jsonb not null default '{}'::jsonb,
  solver_status text not null default 'pending'
    check (solver_status in ('pending','running','optimal','feasible','infeasible','failed')),
  status text not null default 'draft'
    check (status in ('draft','ready_for_review','approved','finalized','rejected')),
  created_by uuid not null references public.profiles(id) on delete restrict,
  approved_by uuid references public.profiles(id) on delete restrict,
  approved_at timestamptz,
  finalized_at timestamptz,
  created_at timestamptz not null default now(),
  check ((status in ('approved','finalized')) = (approved_at is not null and approved_by is not null)),
  check ((status = 'finalized') = (finalized_at is not null))
);

create table public.allocation_candidates (
  id uuid primary key default gen_random_uuid(),
  allocation_run_id uuid not null references public.allocation_runs(id) on delete restrict,
  application_id uuid not null references public.applications(id) on delete restrict,
  bed_id uuid not null references public.beds(id) on delete restrict,
  decision text not null default 'proposed'
    check (decision in ('proposed','selected','rejected')),
  explanation jsonb not null default '{}'::jsonb,
  score numeric,
  created_at timestamptz not null default now(),
  unique (allocation_run_id, application_id),
  unique (allocation_run_id, bed_id),
  unique (id, allocation_run_id)
);

create table public.room_allocations (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete restrict,
  bed_id uuid not null references public.beds(id) on delete restrict,
  application_id uuid not null references public.applications(id) on delete restrict,
  allocation_run_id uuid not null references public.allocation_runs(id) on delete restrict,
  candidate_id uuid not null unique,
  valid_from date not null,
  valid_until date,
  status text not null default 'active'
    check (status in ('pending','active','completed','cancelled')),
  approved_by uuid not null references public.profiles(id) on delete restrict,
  approved_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  check (valid_until is null or valid_until > valid_from),
  foreign key (candidate_id, allocation_run_id)
    references public.allocation_candidates(id, allocation_run_id) on delete restrict
);

alter table public.room_allocations
  add constraint room_allocations_no_bed_overlap
  exclude using gist (
    bed_id with =,
    (daterange(valid_from, valid_until, '[)')) with &&
  ) where (status in ('pending','active'));

alter table public.room_allocations
  add constraint room_allocations_no_student_overlap
  exclude using gist (
    student_id with =,
    (daterange(valid_from, valid_until, '[)')) with &&
  ) where (status in ('pending','active'));

create table public.allocation_metrics (
  id uuid primary key default gen_random_uuid(),
  allocation_run_id uuid not null references public.allocation_runs(id) on delete restrict,
  metric_name text not null,
  metric_value numeric,
  details jsonb not null default '{}'::jsonb,
  calculated_at timestamptz not null default now(),
  unique (allocation_run_id, metric_name)
);

create table public.allocation_events (
  id uuid primary key default gen_random_uuid(),
  allocation_run_id uuid not null references public.allocation_runs(id) on delete restrict,
  actor_id uuid references public.profiles(id) on delete restrict,
  event_type text not null,
  event_data jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now()
);

create index students_profile_idx on public.students(profile_id);
create index applications_student_status_idx on public.applications(student_id, status);
create index rooms_hostel_status_idx on public.rooms(hostel_id, status);
create index beds_room_status_idx on public.beds(room_id, status);
create index allocation_runs_hostel_status_idx on public.allocation_runs(hostel_id, status);
create index candidates_run_decision_idx on public.allocation_candidates(allocation_run_id, decision);
create index allocations_student_dates_idx on public.room_allocations(student_id, valid_from, valid_until);
create index allocations_bed_dates_idx on public.room_allocations(bed_id, valid_from, valid_until);
create index allocation_events_run_time_idx on public.allocation_events(allocation_run_id, occurred_at desc);

-- Role helpers are SECURITY DEFINER to avoid recursive RLS. They expose booleans only.
create or replace function public.has_role(p_role text)
returns boolean
language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.user_roles ur
    where ur.user_id = (select auth.uid()) and ur.role = p_role
  );
$$;

create or replace function public.can_manage_hostel(p_hostel_id uuid)
returns boolean
language sql stable security definer
set search_path = ''
as $$
  select public.has_role('admin') or exists (
    select 1 from public.warden_hostels wh
    where wh.warden_id = (select auth.uid()) and wh.hostel_id = p_hostel_id
  );
$$;

revoke all on function public.has_role(text) from public, anon;
revoke all on function public.can_manage_hostel(uuid) from public, anon;
grant execute on function public.has_role(text) to authenticated;
grant execute on function public.can_manage_hostel(uuid) to authenticated;

-- Prevent silent changes to an approved policy. New policy version required.
create or replace function public.prevent_approved_policy_mutation()
returns trigger language plpgsql security definer
set search_path = ''
as $$
begin
  if old.status = 'approved' then
    raise exception 'Approved policy versions are immutable; publish a new version';
  end if;
  return new;
end;
$$;
create trigger allocation_policy_immutable
before update or delete on public.allocation_policies
for each row execute function public.prevent_approved_policy_mutation();

-- Finalization is atomic. Caller must be an authenticated warden assigned to the run's hostel,
-- or an admin. Exclusion constraints are the final concurrent-writer arbiter.
create or replace function public.ghms_finalize_allocation_run(p_run_id uuid)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_actor uuid := (select auth.uid());
  v_run public.allocation_runs%rowtype;
  v_candidate record;
  v_count integer := 0;
begin
  if v_actor is null then
    raise exception 'Authentication required' using errcode = '42501';
  end if;
  if not (public.has_role('admin') or public.has_role('warden')) then
    raise exception 'Only an admin or warden can finalize allocations' using errcode = '42501';
  end if;

  select * into v_run
  from public.allocation_runs
  where id = p_run_id
  for update;

  if not found then raise exception 'Allocation run not found'; end if;
  if not public.can_manage_hostel(v_run.hostel_id) then
    raise exception 'No permission for this hostel' using errcode = '42501';
  end if;
  if v_run.status <> 'approved' then
    raise exception 'Run must be approved and not already finalized';
  end if;
  if v_run.solver_status not in ('optimal','feasible') then
    raise exception 'Solver result is not finalizable';
  end if;
  if not exists (
    select 1 from public.allocation_policies p
    where p.id = v_run.policy_id and p.status = 'approved'
  ) then raise exception 'Run policy is not approved'; end if;

  if not exists (
    select 1 from public.allocation_candidates c
    where c.allocation_run_id = p_run_id and c.decision = 'selected'
  ) then raise exception 'No selected candidates'; end if;

  -- Validate every selected candidate before inserting any allocations.
  for v_candidate in
    select c.id as candidate_id, c.bed_id, c.application_id,
           a.student_id, a.status as application_status, a.academic_session_id,
           b.status as bed_status, r.status as room_status, r.hostel_id,
           h.is_active as hostel_active
    from public.allocation_candidates c
    join public.applications a on a.id = c.application_id
    join public.beds b on b.id = c.bed_id
    join public.rooms r on r.id = b.room_id
    join public.hostels h on h.id = r.hostel_id
    where c.allocation_run_id = p_run_id and c.decision = 'selected'
    order by c.bed_id, a.student_id
    for update of a, b
  loop
    if v_candidate.application_status <> 'eligible'
       or v_candidate.academic_session_id <> v_run.academic_session_id then
      raise exception 'Candidate application is not eligible for this session';
    end if;
    if v_candidate.bed_status <> 'available'
       or v_candidate.room_status <> 'available'
       or not v_candidate.hostel_active
       or v_candidate.hostel_id <> v_run.hostel_id then
      raise exception 'Candidate bed/room/hostel is not available for this run';
    end if;
    if exists (
      select 1 from public.room_allocations ra
      where ra.student_id = v_candidate.student_id
        and ra.status in ('pending','active')
        and daterange(ra.valid_from, ra.valid_until, '[)') &&
            daterange(current_date, null, '[)')
    ) then raise exception 'Student already has an active allocation'; end if;
  end loop;

  for v_candidate in
    select c.id as candidate_id, c.bed_id, c.application_id, a.student_id
    from public.allocation_candidates c
    join public.applications a on a.id = c.application_id
    where c.allocation_run_id = p_run_id and c.decision = 'selected'
    order by c.bed_id, a.student_id
  loop
    insert into public.room_allocations
      (student_id, bed_id, application_id, allocation_run_id, candidate_id,
       valid_from, valid_until, status, approved_by)
    values
      (v_candidate.student_id, v_candidate.bed_id, v_candidate.application_id,
       p_run_id, v_candidate.candidate_id, current_date, null, 'active', v_actor);
    v_count := v_count + 1;
  end loop;

  update public.allocation_runs
    set status = 'finalized', finalized_at = now()
    where id = p_run_id;

  insert into public.allocation_events
    (allocation_run_id, actor_id, event_type, event_data)
  values
    (p_run_id, v_actor, 'allocation_run_finalized',
     jsonb_build_object('allocation_count', v_count, 'policy_id', v_run.policy_id));

  return v_count;
end;
$$;

revoke all on function public.ghms_finalize_allocation_run(uuid) from public, anon;
grant execute on function public.ghms_finalize_allocation_run(uuid) to authenticated;

-- RLS and least-privilege grants.
alter table public.profiles enable row level security;
alter table public.user_roles enable row level security;
alter table public.departments enable row level security;
alter table public.students enable row level security;
alter table public.fee_schedules enable row level security;
alter table public.hostels enable row level security;
alter table public.warden_hostels enable row level security;
alter table public.rooms enable row level security;
alter table public.beds enable row level security;
alter table public.academic_sessions enable row level security;
alter table public.applications enable row level security;
alter table public.allocation_policies enable row level security;
alter table public.allocation_runs enable row level security;
alter table public.allocation_candidates enable row level security;
alter table public.room_allocations enable row level security;
alter table public.allocation_metrics enable row level security;
alter table public.allocation_events enable row level security;

grant select on public.profiles, public.user_roles, public.departments,
  public.fee_schedules, public.hostels, public.rooms, public.beds,
  public.academic_sessions, public.students, public.applications,
  public.allocation_policies, public.allocation_runs, public.allocation_candidates,
  public.room_allocations, public.allocation_metrics, public.allocation_events
to authenticated;

create policy profiles_read_self_or_staff on public.profiles
for select to authenticated using (
  id = (select auth.uid()) or public.has_role('admin') or public.has_role('auditor')
  or public.has_role('warden')
);
create policy roles_read_self_or_admin on public.user_roles
for select to authenticated using (user_id = (select auth.uid()) or public.has_role('admin'));
create policy departments_read_authenticated on public.departments
for select to authenticated using (true);
create policy fee_schedules_read_authenticated on public.fee_schedules
for select to authenticated using (true);
create policy hostels_read_authenticated on public.hostels
for select to authenticated using (true);
create policy warden_hostels_read_self_or_admin on public.warden_hostels
for select to authenticated using (warden_id = (select auth.uid()) or public.has_role('admin'));
create policy rooms_read_authenticated on public.rooms
for select to authenticated using (true);
create policy beds_read_authenticated on public.beds
for select to authenticated using (true);
create policy sessions_read_authenticated on public.academic_sessions
for select to authenticated using (true);
create policy students_read_self_or_staff on public.students
for select to authenticated using (
  profile_id = (select auth.uid()) or public.has_role('admin')
  or public.has_role('auditor')
  or (public.has_role('warden') and exists (
    select 1 from public.warden_hostels wh
    join public.rooms r on r.hostel_id = wh.hostel_id
    join public.beds b on b.room_id = r.id
    join public.room_allocations ra on ra.bed_id = b.id
    where wh.warden_id = (select auth.uid()) and ra.student_id = students.id
  ))
);
create policy applications_read_owner_or_staff on public.applications
for select to authenticated using (
  exists (select 1 from public.students s where s.id = applications.student_id
    and s.profile_id = (select auth.uid()))
  or public.has_role('admin') or public.has_role('auditor')
  or (public.has_role('warden') and requested_hostel_id is not null
      and public.can_manage_hostel(requested_hostel_id))
);
create policy policies_read_authenticated on public.allocation_policies
for select to authenticated using (status = 'approved' or public.has_role('admin')
  or public.has_role('auditor') or public.has_role('warden'));
create policy runs_read_scoped on public.allocation_runs
for select to authenticated using (
  public.has_role('admin') or public.has_role('auditor')
  or (public.has_role('warden') and public.can_manage_hostel(hostel_id))
  or exists (
    select 1 from public.allocation_candidates c
    join public.applications a on a.id = c.application_id
    join public.students s on s.id = a.student_id
    where c.allocation_run_id = allocation_runs.id and s.profile_id = (select auth.uid())
  )
);
create policy candidates_read_owner_or_staff on public.allocation_candidates
for select to authenticated using (
  public.has_role('admin') or public.has_role('auditor')
  or (public.has_role('warden') and exists (
    select 1 from public.allocation_runs ar where ar.id = allocation_run_id
      and public.can_manage_hostel(ar.hostel_id)
  ))
  or exists (
    select 1 from public.applications a join public.students s on s.id = a.student_id
    where a.id = application_id and s.profile_id = (select auth.uid())
  )
);
create policy allocations_read_owner_or_staff on public.room_allocations
for select to authenticated using (
  public.has_role('admin') or public.has_role('auditor')
  or (public.has_role('warden') and exists (
    select 1 from public.rooms r join public.beds b on b.room_id = r.id
    where b.id = bed_id and public.can_manage_hostel(r.hostel_id)
  ))
  or exists (select 1 from public.students s
    where s.id = student_id and s.profile_id = (select auth.uid()))
);
create policy metrics_read_staff on public.allocation_metrics
for select to authenticated using (public.has_role('admin') or public.has_role('auditor')
  or (public.has_role('warden') and exists (
    select 1 from public.allocation_runs ar where ar.id = allocation_run_id
      and public.can_manage_hostel(ar.hostel_id)
  )));
create policy events_read_staff on public.allocation_events
for select to authenticated using (public.has_role('admin') or public.has_role('auditor')
  or (public.has_role('warden') and exists (
    select 1 from public.allocation_runs ar where ar.id = allocation_run_id
      and public.can_manage_hostel(ar.hostel_id)
  )));

-- No direct client writes to allocation decisions, role grants, policies or audit events.
revoke insert, update, delete on public.user_roles, public.warden_hostels,
  public.allocation_policies, public.allocation_runs, public.allocation_candidates,
  public.room_allocations, public.allocation_events, public.allocation_metrics
from anon, authenticated;
revoke insert, update, delete on public.students, public.applications,
  public.hostels, public.rooms, public.beds, public.fee_schedules
from anon, authenticated;

commit;
