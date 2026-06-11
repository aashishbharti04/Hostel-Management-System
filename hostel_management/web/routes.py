"""HTTP routes for the dashboard and the JSON API.

Server-rendered pages handle the human-facing UI; the ``/api`` endpoints expose
the same data as JSON for programmatic use and for the small amount of
progressive enhancement on the client (live search, skeleton loaders).

Security notes:
* All database access goes through the service layer, which uses parameterised
  queries — there is no string-built SQL anywhere.
* Jinja2 autoescaping is on by default, mitigating stored/reflected XSS.
* Mutating routes are POST-only and protected by a per-session CSRF token.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..models import DEPARTMENTS, Student, ValidationError
from ..services import HostelService


def _service() -> HostelService:
    """Create a request-scoped service (and ensure seed fees exist)."""
    service = HostelService()
    service.ensure_seed_fees()
    return service


def _csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def _require_csrf() -> None:
    sent = request.form.get("_csrf_token", "")
    if not sent or not secrets.compare_digest(sent, session.get("_csrf_token", "")):
        abort(400, description="Invalid or missing CSRF token.")


def csrf_protect(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if request.method == "POST":
            _require_csrf()
        return view(*args, **kwargs)

    return wrapper


def register_routes(app: Flask) -> None:
    # Expose helpers to every template.
    app.jinja_env.globals["csrf_token"] = _csrf_token
    app.jinja_env.globals["DEPARTMENTS"] = DEPARTMENTS

    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        from datetime import datetime

        return {"year": datetime.now().year}

    # -- pages ---------------------------------------------------------------
    @app.get("/")
    def dashboard():  # type: ignore[no-untyped-def]
        service = _service()
        try:
            return render_template(
                "dashboard.html",
                stats=service.stats(),
                students=service.list_students()[:5],
                fees=service.list_fees(),
            )
        finally:
            service.close()

    @app.get("/students")
    def students():  # type: ignore[no-untyped-def]
        service = _service()
        try:
            query = request.args.get("q", "").strip().lower()
            items = service.list_students()
            if query:
                items = [
                    s
                    for s in items
                    if query in s.name.lower() or query in s.dept.lower() or query in str(s.roll_no)
                ]
            return render_template("students/list.html", students=items, query=query)
        finally:
            service.close()

    @app.route("/students/new", methods=["GET", "POST"])
    @csrf_protect
    def student_new():  # type: ignore[no-untyped-def]
        service = _service()
        try:
            if request.method == "POST":
                try:
                    student = _student_from_form(request.form)
                    service.admit_student(student)
                    flash(f"Admitted {student.name} (roll {student.roll_no}).", "success")
                    return redirect(url_for("students"))
                except (ValidationError, ValueError) as exc:
                    flash(str(exc), "error")
                    return render_template("students/form.html", student=request.form, mode="new")
            return render_template("students/form.html", student=None, mode="new")
        finally:
            service.close()

    @app.route("/students/<int:roll_no>/edit", methods=["GET", "POST"])
    @csrf_protect
    def student_edit(roll_no: int):  # type: ignore[no-untyped-def]
        service = _service()
        try:
            existing = service.get_student(roll_no)
            if not existing:
                abort(404)
            if request.method == "POST":
                try:
                    student = _student_from_form(request.form, roll_no=roll_no)
                    service.update_student(student)
                    flash("Record updated.", "success")
                    return redirect(url_for("students"))
                except (ValidationError, ValueError) as exc:
                    flash(str(exc), "error")
                    return render_template("students/form.html", student=request.form, mode="edit")
            return render_template("students/form.html", student=existing.to_dict(), mode="edit")
        finally:
            service.close()

    @app.post("/students/<int:roll_no>/delete")
    @csrf_protect
    def student_delete(roll_no: int):  # type: ignore[no-untyped-def]
        service = _service()
        try:
            try:
                service.delete_student(roll_no)
                flash(f"Deleted roll {roll_no}.", "success")
            except ValidationError as exc:
                flash(str(exc), "error")
            return redirect(url_for("students"))
        finally:
            service.close()

    @app.route("/fees", methods=["GET", "POST"])
    @csrf_protect
    def fees():  # type: ignore[no-untyped-def]
        service = _service()
        try:
            if request.method == "POST":
                try:
                    service.set_fee(
                        request.form.get("department", ""),
                        int(request.form.get("amount", "0")),
                    )
                    flash("Fee schedule updated.", "success")
                except (ValidationError, ValueError) as exc:
                    flash(str(exc), "error")
                return redirect(url_for("fees"))
            return render_template("fees.html", fees=service.list_fees())
        finally:
            service.close()

    # -- JSON API ------------------------------------------------------------
    @app.get("/api/stats")
    def api_stats():  # type: ignore[no-untyped-def]
        service = _service()
        try:
            return jsonify(service.stats())
        finally:
            service.close()

    @app.get("/api/students")
    def api_students():  # type: ignore[no-untyped-def]
        service = _service()
        try:
            return jsonify([s.to_dict() for s in service.list_students()])
        finally:
            service.close()

    @app.get("/api/students/<int:roll_no>")
    def api_student(roll_no: int):  # type: ignore[no-untyped-def]
        service = _service()
        try:
            student = service.get_student(roll_no)
            if not student:
                return jsonify({"error": "not found"}), 404
            return jsonify(student.to_dict())
        finally:
            service.close()

    @app.get("/api/fees")
    def api_fees():  # type: ignore[no-untyped-def]
        service = _service()
        try:
            return jsonify([f.to_dict() for f in service.list_fees()])
        finally:
            service.close()

    @app.get("/healthz")
    def healthz():  # type: ignore[no-untyped-def]
        return jsonify({"status": "ok"})


def _student_from_form(form: Any, roll_no: int | None = None) -> Student:
    """Build a validated Student from submitted form data."""
    return Student(
        roll_no=roll_no if roll_no is not None else int(form.get("roll_no", "0")),
        name=form.get("name", ""),
        address=form.get("address", ""),
        room_no=int(form.get("room_no", "0")),
        dept=form.get("dept", ""),
        fees=int(form.get("fees", "0")),
        balance=int(form.get("balance", "0")),
    )
