BEGIN;
CREATE OR REPLACE FUNCTION private.is_admin() RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$ SELECT EXISTS(SELECT 1 FROM public.staff_assignments s WHERE s.user_id=(SELECT auth.uid()) AND s.role='admin' AND s.active) $$;
CREATE OR REPLACE FUNCTION private.is_finance() RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$ SELECT EXISTS(SELECT 1 FROM public.staff_assignments s WHERE s.user_id=(SELECT auth.uid()) AND s.role IN ('admin','finance') AND s.active) $$;
CREATE OR REPLACE FUNCTION private.is_staff_role(p_roles text[]) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$ SELECT EXISTS(SELECT 1 FROM public.staff_assignments s WHERE s.user_id=(SELECT auth.uid()) AND s.active AND s.role=ANY(p_roles)) $$;
CREATE OR REPLACE FUNCTION private.owns_student(p_student_id uuid) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$ SELECT EXISTS(SELECT 1 FROM public.student_records sr WHERE sr.id=p_student_id AND sr.user_id=(SELECT auth.uid())) $$;
CREATE OR REPLACE FUNCTION private.manages_hostel(p_hostel_id uuid) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$ SELECT EXISTS(SELECT 1 FROM public.staff_assignments s WHERE s.user_id=(SELECT auth.uid()) AND s.active AND (s.role='admin' OR (s.role IN ('warden','maintenance') AND s.hostel_id=p_hostel_id))) $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA private FROM PUBLIC,anon;
GRANT USAGE ON SCHEMA private TO authenticated;
GRANT EXECUTE ON FUNCTION private.is_admin(),private.is_finance(),private.is_staff_role(text[]),private.owns_student(uuid),private.manages_hostel(uuid) TO authenticated;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon,authenticated;
GRANT SELECT ON public.departments,public.campuses,public.academic_terms TO authenticated;
GRANT SELECT,UPDATE(full_name,phone) ON public.profiles TO authenticated;
GRANT SELECT ON public.student_records,public.staff_assignments,public.hostels,public.rooms,public.beds,public.allocations,public.fee_invoices,public.payments,public.payment_events,public.visitors,public.visitor_logs,public.announcements,public.audit_logs TO authenticated;
GRANT SELECT,INSERT ON public.room_applications,public.complaints,public.maintenance_requests,public.leave_requests TO authenticated;

DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['profiles','departments','campuses','academic_terms','student_records','staff_assignments','hostels','rooms','beds','room_applications','allocations','fee_invoices','payments','payment_events','complaints','maintenance_requests','leave_requests','visitors','visitor_logs','announcements','audit_logs']
 LOOP EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t); END LOOP;
END $$;

CREATE POLICY profile_select ON public.profiles FOR SELECT TO authenticated USING(id=(SELECT auth.uid()) OR (SELECT private.is_admin()));
CREATE POLICY profile_update_self ON public.profiles FOR UPDATE TO authenticated USING(id=(SELECT auth.uid())) WITH CHECK(id=(SELECT auth.uid()));
CREATE POLICY departments_read ON public.departments FOR SELECT TO authenticated USING(true);
CREATE POLICY campuses_read ON public.campuses FOR SELECT TO authenticated USING(true);
CREATE POLICY terms_read ON public.academic_terms FOR SELECT TO authenticated USING(true);
CREATE POLICY student_read ON public.student_records FOR SELECT TO authenticated USING(user_id=(SELECT auth.uid()) OR (SELECT private.is_admin()));
CREATE POLICY staff_read ON public.staff_assignments FOR SELECT TO authenticated USING(user_id=(SELECT auth.uid()) OR (SELECT private.is_admin()));
CREATE POLICY hostels_read ON public.hostels FOR SELECT TO authenticated USING(active OR (SELECT private.manages_hostel(id)));
CREATE POLICY rooms_read ON public.rooms FOR SELECT TO authenticated USING((SELECT private.manages_hostel(hostel_id)) OR EXISTS(SELECT 1 FROM public.allocations a JOIN public.beds b ON b.id=a.bed_id JOIN public.student_records s ON s.id=a.student_id WHERE b.room_id=rooms.id AND s.user_id=(SELECT auth.uid()) AND a.status='active' AND a.start_date<=current_date AND (a.end_date IS NULL OR a.end_date>current_date)));
CREATE POLICY beds_read ON public.beds FOR SELECT TO authenticated USING(EXISTS(SELECT 1 FROM public.rooms r WHERE r.id=beds.room_id AND (SELECT private.manages_hostel(r.hostel_id))) OR EXISTS(SELECT 1 FROM public.allocations a JOIN public.student_records s ON s.id=a.student_id WHERE a.bed_id=beds.id AND s.user_id=(SELECT auth.uid()) AND a.status='active'));
CREATE POLICY applications_read ON public.room_applications FOR SELECT TO authenticated USING((SELECT private.owns_student(student_id)) OR (SELECT private.is_admin()) OR ((SELECT private.is_staff_role(ARRAY['warden'])) AND (preferred_hostel_id IS NULL OR (SELECT private.manages_hostel(preferred_hostel_id)))));
CREATE POLICY applications_insert ON public.room_applications FOR INSERT TO authenticated WITH CHECK((SELECT private.owns_student(student_id)) AND status IN ('draft','submitted') AND reviewed_by IS NULL AND reviewed_at IS NULL);
CREATE POLICY allocations_read ON public.allocations FOR SELECT TO authenticated USING((SELECT private.owns_student(student_id)) OR (SELECT private.is_admin()) OR EXISTS(SELECT 1 FROM public.beds b JOIN public.rooms r ON r.id=b.room_id WHERE b.id=allocations.bed_id AND (SELECT private.manages_hostel(r.hostel_id))));
CREATE POLICY invoices_read ON public.fee_invoices FOR SELECT TO authenticated USING((SELECT private.owns_student(student_id)) OR (SELECT private.is_finance()));
CREATE POLICY payments_read ON public.payments FOR SELECT TO authenticated USING((SELECT private.is_finance()) OR EXISTS(SELECT 1 FROM public.fee_invoices i WHERE i.id=payments.invoice_id AND (SELECT private.owns_student(i.student_id))));
CREATE POLICY payment_events_read ON public.payment_events FOR SELECT TO authenticated USING((SELECT private.is_finance()));
CREATE POLICY complaints_read ON public.complaints FOR SELECT TO authenticated USING((SELECT private.owns_student(student_id)) OR (SELECT private.is_admin()) OR assigned_to=(SELECT auth.uid()) OR EXISTS(SELECT 1 FROM public.student_records s JOIN public.allocations a ON a.student_id=s.id JOIN public.beds b ON b.id=a.bed_id JOIN public.rooms r ON r.id=b.room_id WHERE s.id=complaints.student_id AND (SELECT private.manages_hostel(r.hostel_id)) AND a.status='active'));
CREATE POLICY complaints_insert ON public.complaints FOR INSERT TO authenticated WITH CHECK((SELECT private.owns_student(student_id)) AND status='open' AND assigned_to IS NULL);
CREATE POLICY maintenance_read ON public.maintenance_requests FOR SELECT TO authenticated USING(reported_by=(SELECT auth.uid()) OR assigned_to=(SELECT auth.uid()) OR (SELECT private.is_admin()) OR EXISTS(SELECT 1 FROM public.rooms r WHERE r.id=maintenance_requests.room_id AND (SELECT private.manages_hostel(r.hostel_id))));
CREATE POLICY maintenance_insert ON public.maintenance_requests FOR INSERT TO authenticated WITH CHECK(reported_by=(SELECT auth.uid()) AND assigned_to IS NULL AND status='open');
CREATE POLICY leave_read ON public.leave_requests FOR SELECT TO authenticated USING((SELECT private.owns_student(student_id)) OR (SELECT private.is_admin()) OR (reviewed_by=(SELECT auth.uid()) AND (SELECT private.is_staff_role(ARRAY['warden']))));
CREATE POLICY leave_insert ON public.leave_requests FOR INSERT TO authenticated WITH CHECK((SELECT private.owns_student(student_id)) AND status='pending' AND reviewed_by IS NULL AND reviewed_at IS NULL);
CREATE POLICY visitors_read ON public.visitors FOR SELECT TO authenticated USING((SELECT private.is_admin()) OR EXISTS(SELECT 1 FROM public.visitor_logs v WHERE v.visitor_id=visitors.id AND ((SELECT private.owns_student(v.student_id)) OR (SELECT private.manages_hostel(v.hostel_id))));
CREATE POLICY visitor_logs_read ON public.visitor_logs FOR SELECT TO authenticated USING((SELECT private.owns_student(student_id)) OR (SELECT private.manages_hostel(hostel_id)));
CREATE POLICY announcements_read ON public.announcements FOR SELECT TO authenticated USING(published OR (SELECT private.is_admin()) OR (hostel_id IS NOT NULL AND (SELECT private.manages_hostel(hostel_id))));
CREATE POLICY audit_read_admin ON public.audit_logs FOR SELECT TO authenticated USING((SELECT private.is_admin()));
REVOKE INSERT,UPDATE,DELETE,TRUNCATE ON public.audit_logs FROM anon,authenticated;
COMMIT;
