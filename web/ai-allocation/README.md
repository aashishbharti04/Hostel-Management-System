# GHMS allocation dashboard

Isolated React/Vite review UI; does not replace the existing Flask/Jinja application. Configure `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`, then run `npm install && npm run dev`. Uses signed-in Supabase sessions and RLS-filtered reads. Finalization calls the guarded `ghms_finalize_allocation_run` RPC. Never put a service-role key in the browser.

The CP-SAT engine currently exposes a pure Python solver function. A trusted server adapter that loads an authorized consistent snapshot and persists solver candidates is still required before end-to-end proposals can be created. See `docs/CP_SAT_INTEGRATION.md`.
