INSERT INTO public.departments(name,code) VALUES ('Computer Science','CSE'),('Business Administration','MBA') ON CONFLICT DO NOTHING;
INSERT INTO public.campuses(name,address) VALUES ('Demo Main Campus','Example address, India') ON CONFLICT(name) DO NOTHING;
INSERT INTO public.academic_terms(name,starts_on,ends_on) VALUES ('Demo 2026-27 Semester 1',DATE '2026-07-01',DATE '2026-12-31') ON CONFLICT(name) DO NOTHING;
INSERT INTO public.hostels(campus_id,name,address) SELECT id,'Demo Hostel A','Demo Main Campus' FROM public.campuses WHERE name='Demo Main Campus' ON CONFLICT(campus_id,name) DO NOTHING;
INSERT INTO public.rooms(hostel_id,room_number,floor_number,room_type,capacity) SELECT id,'101',1,'standard',2 FROM public.hostels WHERE name='Demo Hostel A' ON CONFLICT(hostel_id,room_number) DO NOTHING;
INSERT INTO public.beds(room_id,bed_number) SELECT r.id,v.bed FROM public.rooms r CROSS JOIN (VALUES('A'),('B')) v(bed) WHERE r.room_number='101' ON CONFLICT(room_id,bed_number) DO NOTHING;