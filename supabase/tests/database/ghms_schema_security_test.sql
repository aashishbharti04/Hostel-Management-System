begin;
select plan(12);

select has_table('public', 'students', 'students table exists');
select has_table('public', 'fee_schedules', 'fee schedules table exists');
select has_table('public', 'allocation_runs', 'allocation runs table exists');
select has_table('public', 'allocation_candidates', 'allocation candidates table exists');
select has_table('public', 'room_allocations', 'room allocations table exists');
select has_table('public', 'allocation_events', 'allocation event audit table exists');
select has_column('public', 'students', 'legacy_roll_no', 'legacy roll number retained for migration');
select has_column('public', 'allocation_runs', 'input_hash', 'run input is fingerprinted');
select has_index('public', 'room_allocations', 'room_allocations_no_bed_overlap',
  'bed overlap exclusion constraint exists');
select has_index('public', 'room_allocations', 'room_allocations_no_student_overlap',
  'student overlap exclusion constraint exists');
select ok((select relrowsecurity from pg_class where oid = 'public.room_allocations'::regclass),
  'room allocations has RLS enabled');
select ok(has_function_privilege('authenticated',
  'public.ghms_finalize_allocation_run(uuid)', 'EXECUTE'),
  'authenticated role can invoke guarded finalization RPC');

select * from finish();
rollback;
