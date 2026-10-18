BEGIN;
CREATE OR REPLACE FUNCTION private.set_updated_at() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$
BEGIN NEW.updated_at=now(); RETURN NEW; END $$;
CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER applications_updated_at BEFORE UPDATE ON public.room_applications FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER invoices_updated_at BEFORE UPDATE ON public.fee_invoices FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER complaints_updated_at BEFORE UPDATE ON public.complaints FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER maintenance_updated_at BEFORE UPDATE ON public.maintenance_requests FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();

CREATE OR REPLACE FUNCTION private.audit_row_change() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE o jsonb; n jsonb; rid text;
BEGIN
 IF TG_OP IN ('UPDATE','DELETE') THEN o=to_jsonb(OLD); rid=o->>'id'; END IF;
 IF TG_OP IN ('INSERT','UPDATE') THEN n=to_jsonb(NEW); rid=n->>'id'; END IF;
 INSERT INTO public.audit_logs(actor_id,table_name,record_id,operation,old_data,new_data)
 VALUES(auth.uid(),TG_TABLE_NAME,coalesce(rid,'unknown'),TG_OP,o,n);
 IF TG_OP='DELETE' THEN RETURN OLD; END IF; RETURN NEW;
END $$;
CREATE TRIGGER allocation_audit AFTER INSERT OR UPDATE OR DELETE ON public.allocations FOR EACH ROW EXECUTE FUNCTION private.audit_row_change();
CREATE TRIGGER invoice_audit AFTER INSERT OR UPDATE OR DELETE ON public.fee_invoices FOR EACH ROW EXECUTE FUNCTION private.audit_row_change();
CREATE TRIGGER payment_audit AFTER INSERT OR UPDATE OR DELETE ON public.payments FOR EACH ROW EXECUTE FUNCTION private.audit_row_change();
REVOKE ALL ON FUNCTION private.audit_row_change() FROM PUBLIC,anon,authenticated;

-- Capacity trigger locks the parent room before counting beds. All capacity-changing
-- operations must use this trigger; concurrent bed moves should be load-tested.
CREATE OR REPLACE FUNCTION private.enforce_room_capacity() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE rid uuid; cap int; n bigint;
BEGIN
 IF TG_TABLE_NAME='rooms' THEN rid=NEW.id;
 ELSIF TG_OP='DELETE' THEN rid=OLD.room_id;
 ELSE rid=NEW.room_id; END IF;
 SELECT capacity INTO cap FROM public.rooms WHERE id=rid FOR UPDATE;
 IF FOUND THEN
   SELECT count(*) INTO n FROM public.beds WHERE room_id=rid AND status<>'inactive';
   IF n>cap THEN RAISE EXCEPTION 'Room capacity exceeded' USING ERRCODE='check_violation'; END IF;
 END IF;
 IF TG_TABLE_NAME='beds' AND TG_OP='UPDATE' AND NEW.room_id<>OLD.room_id THEN
   SELECT capacity INTO cap FROM public.rooms WHERE id=OLD.room_id FOR UPDATE;
   SELECT count(*) INTO n FROM public.beds WHERE room_id=OLD.room_id AND status<>'inactive';
   IF n>cap THEN RAISE EXCEPTION 'Old room capacity exceeded' USING ERRCODE='check_violation'; END IF;
 END IF;
 RETURN NULL;
END $$;
CREATE TRIGGER bed_capacity AFTER INSERT OR UPDATE OR DELETE ON public.beds FOR EACH ROW EXECUTE FUNCTION private.enforce_room_capacity();
CREATE TRIGGER room_capacity AFTER UPDATE OF capacity ON public.rooms FOR EACH ROW EXECUTE FUNCTION private.enforce_room_capacity();

-- Direct writes to privileged entities are prohibited; workflows below are RPC-only.
REVOKE INSERT,UPDATE,DELETE,TRUNCATE ON public.staff_assignments,public.student_records,public.allocations,public.fee_invoices,public.payments,public.payment_events,public.visitors,public.visitor_logs,public.announcements FROM anon,authenticated;
REVOKE UPDATE,DELETE,TRUNCATE ON public.room_applications,public.complaints,public.maintenance_requests,public.leave_requests FROM anon,authenticated;

CREATE OR REPLACE FUNCTION public.withdraw_room_application(p_application_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE owner_id uuid;
BEGIN
 SELECT s.user_id INTO owner_id FROM public.room_applications a JOIN public.student_records s ON s.id=a.student_id
 WHERE a.id=p_application_id FOR UPDATE OF a;
 IF NOT FOUND OR owner_id IS DISTINCT FROM auth.uid() THEN RAISE EXCEPTION 'Application not found or not owned' USING ERRCODE='42501'; END IF;
 UPDATE public.room_applications SET status='withdrawn',updated_at=now()
 WHERE id=p_application_id AND status IN ('draft','submitted');
 IF NOT FOUND THEN RAISE EXCEPTION 'Application cannot be withdrawn'; END IF;
END $$;

CREATE OR REPLACE FUNCTION public.review_room_application(p_application_id uuid,p_decision text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE h uuid;
BEGIN
 IF p_decision NOT IN ('under_review','approved','rejected') THEN RAISE EXCEPTION 'Invalid decision'; END IF;
 SELECT preferred_hostel_id INTO h FROM public.room_applications WHERE id=p_application_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Application not found'; END IF;
 IF NOT (private.is_admin() OR (private.is_staff_role(ARRAY['warden']) AND h IS NOT NULL AND private.manages_hostel(h))) THEN
  RAISE EXCEPTION 'Not authorized' USING ERRCODE='42501';
 END IF;
 UPDATE public.room_applications SET status=p_decision,reviewed_by=auth.uid(),reviewed_at=now(),updated_at=now()
 WHERE id=p_application_id AND status IN ('submitted','under_review');
 IF NOT FOUND THEN RAISE EXCEPTION 'Application is not reviewable'; END IF;
END $$;

CREATE OR REPLACE FUNCTION public.allocate_bed(p_student_id uuid,p_bed_id uuid,p_start_date date,p_end_date date DEFAULT NULL,p_application_id uuid DEFAULT NULL)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE h uuid; rid uuid; sid_status text; aid uuid;
BEGIN
 IF p_end_date IS NOT NULL AND p_end_date<=p_start_date THEN RAISE EXCEPTION 'Invalid date range'; END IF;
 SELECT r.hostel_id,r.id INTO h,rid FROM public.beds b JOIN public.rooms r ON r.id=b.room_id
 JOIN public.hostels ho ON ho.id=r.hostel_id
 WHERE b.id=p_bed_id AND b.status='available' AND r.status='available' AND ho.active
 FOR UPDATE OF b,r;
 IF NOT FOUND THEN RAISE EXCEPTION 'Bed or room unavailable'; END IF;
 IF NOT (private.is_admin() OR private.manages_hostel(h)) THEN RAISE EXCEPTION 'Not authorized for hostel' USING ERRCODE='42501'; END IF;
 SELECT status INTO sid_status FROM public.student_records WHERE id=p_student_id FOR SHARE;
 IF NOT FOUND OR sid_status<>'active' THEN RAISE EXCEPTION 'Student not eligible'; END IF;
 IF p_application_id IS NOT NULL AND NOT EXISTS(
  SELECT 1 FROM public.room_applications a WHERE a.id=p_application_id AND a.student_id=p_student_id AND a.status='approved'
 ) THEN RAISE EXCEPTION 'Approved application for this student required'; END IF;
 INSERT INTO public.allocations(student_id,bed_id,application_id,start_date,end_date,allocated_by)
 VALUES(p_student_id,p_bed_id,p_application_id,p_start_date,p_end_date,auth.uid()) RETURNING id INTO aid;
 RETURN aid;
END $$;

-- Server-only RPC. A trusted webhook must validate provider signature, invoice mapping,
-- currency, amount, and event freshness before invoking this function.
CREATE OR REPLACE FUNCTION public.record_verified_payment(p_invoice_id uuid,p_amount numeric,p_provider text,p_provider_reference text,p_idempotency_key text,p_provider_event_id text)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE inv public.fee_invoices%ROWTYPE; pid uuid; paid numeric(12,2);
BEGIN
 IF coalesce(auth.role(),'')<>'service_role' THEN RAISE EXCEPTION 'Trusted payment service required' USING ERRCODE='42501'; END IF;
 IF p_amount<=0 OR p_provider IS NULL OR p_provider_reference IS NULL OR p_idempotency_key IS NULL OR p_provider_event_id IS NULL THEN RAISE EXCEPTION 'Invalid payment input'; END IF;
 SELECT * INTO inv FROM public.fee_invoices WHERE id=p_invoice_id FOR UPDATE;
 IF NOT FOUND OR inv.status='cancelled' THEN RAISE EXCEPTION 'Invoice unavailable'; END IF;
 SELECT id INTO pid FROM public.payments WHERE idempotency_key=p_idempotency_key;
 IF FOUND THEN RETURN pid; END IF;
 IF EXISTS(SELECT 1 FROM public.payment_events WHERE provider_event_id=p_provider_event_id) THEN RAISE EXCEPTION 'Provider event already processed'; END IF;
 SELECT coalesce(sum(amount),0) INTO paid FROM public.payments WHERE invoice_id=p_invoice_id AND status='successful';
 IF paid+p_amount>inv.amount THEN RAISE EXCEPTION 'Payment exceeds invoice balance'; END IF;
 INSERT INTO public.payments(invoice_id,amount,provider,provider_reference,idempotency_key,status,paid_at)
 VALUES(p_invoice_id,p_amount,p_provider,p_provider_reference,p_idempotency_key,'successful',now()) RETURNING id INTO pid;
 INSERT INTO public.payment_events(payment_id,provider_event_id,event_type) VALUES(pid,p_provider_event_id,'payment.succeeded');
 SELECT coalesce(sum(amount),0) INTO paid FROM public.payments WHERE invoice_id=p_invoice_id AND status='successful';
 UPDATE public.fee_invoices SET status=CASE WHEN paid>=amount THEN 'paid' ELSE 'partial' END,updated_at=now() WHERE id=p_invoice_id;
 RETURN pid;
END $$;

REVOKE ALL ON FUNCTION public.withdraw_room_application(uuid) FROM PUBLIC,anon;
REVOKE ALL ON FUNCTION public.review_room_application(uuid,text) FROM PUBLIC,anon;
REVOKE ALL ON FUNCTION public.allocate_bed(uuid,uuid,date,date,uuid) FROM PUBLIC,anon;
REVOKE ALL ON FUNCTION public.record_verified_payment(uuid,numeric,text,text,text,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.withdraw_room_application(uuid),public.review_room_application(uuid,text),public.allocate_bed(uuid,uuid,date,date,uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.record_verified_payment(uuid,numeric,text,text,text,text) TO service_role;
COMMIT;
