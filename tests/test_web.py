"""End-to-end tests for the web dashboard and JSON API."""

from __future__ import annotations

import re


def _csrf(client, path: str) -> str:
    html = client.get(path).get_data(as_text=True)
    match = re.search(r'name="_csrf_token" value="([^"]+)"', html)
    assert match, "CSRF token not found on page"
    return match.group(1)


def test_pages_render(client) -> None:
    for path in ("/", "/students", "/fees", "/students/new"):
        assert client.get(path).status_code == 200


def test_healthz(client) -> None:
    assert client.get("/healthz").get_json() == {"status": "ok"}


def test_api_endpoints(client) -> None:
    assert client.get("/api/stats").status_code == 200
    assert len(client.get("/api/fees").get_json()) == 6
    assert client.get("/api/students").get_json() == []


def test_create_student_flow(client) -> None:
    token = _csrf(client, "/students/new")
    resp = client.post(
        "/students/new",
        data={
            "_csrf_token": token,
            "roll_no": "10",
            "name": "Test User",
            "address": "1 Road",
            "room_no": "5",
            "dept": "COMPUTER",
            "fees": "45000",
            "balance": "1000",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Test User" in resp.get_data(as_text=True)
    assert len(client.get("/api/students").get_json()) == 1


def test_create_requires_csrf(client) -> None:
    resp = client.post(
        "/students/new",
        data={
            "roll_no": "1",
            "name": "X",
            "address": "Y",
            "room_no": "1",
            "dept": "BIO",
            "fees": "1",
            "balance": "0",
        },
    )
    assert resp.status_code == 400  # missing CSRF token


def test_invalid_department_shows_error(client) -> None:
    token = _csrf(client, "/students/new")
    resp = client.post(
        "/students/new",
        data={
            "_csrf_token": token,
            "roll_no": "1",
            "name": "X",
            "address": "Y",
            "room_no": "1",
            "dept": "NOPE",
            "fees": "1",
            "balance": "0",
        },
    )
    assert "Department must be one of" in resp.get_data(as_text=True)


def test_404(client) -> None:
    assert client.get("/does-not-exist").status_code == 404
