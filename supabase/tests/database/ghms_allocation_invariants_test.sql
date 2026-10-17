begin;
select plan(5);

select ok(not exists (
  select 1 from pg_constraint
  where conrelid = 'public.room_allocations'::regclass
    and conname not in ('room_allocations_no_bed_overlap','room_allocations_no_student_overlap')
    and contype = 'x'
), 'only expected allocation exclusion constraints are present');

select ok(exists (
  select 1 from pg_constraint
  where conrelid = 'public.room_allocations'::regclass
    and conname = 'room_allocations_no_bed_overlap' and contype = 'x'
), 'bed exclusion constraint is a PostgreSQL exclusion constraint');

select ok(exists (
  select 1 from pg_constraint
  where conrelid = 'public.room_allocations'::regclass
    and conname = 'room_allocations_no_student_overlap' and contype = 'x'
), 'student exclusion constraint is a PostgreSQL exclusion constraint');

select ok(not has_table_privilege('authenticated', 'public.user_roles', 'UPDATE'),
  'authenticated users cannot mutate roles directly');
select ok(not has_table_privilege('authenticated', 'public.room_allocations', 'INSERT'),
  'authenticated users cannot insert allocations directly');

select * from finish();
rollback;
