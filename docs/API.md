# API Reference

The web dashboard exposes a small **read-only JSON API** for programmatic access and
client-side enhancement. All endpoints return `application/json`.

Base URL (development): `http://127.0.0.1:5000`

## Endpoints

### `GET /api/stats`
Dashboard summary statistics.

```json
{
  "total_students": 5,
  "total_departments": 6,
  "total_fees_billed": 206000,
  "outstanding_balance": 8500
}
```

### `GET /api/students`
List all students.

```json
[
  {
    "roll_no": 1,
    "name": "Aarav Sharma",
    "address": "12 MG Road, Delhi",
    "room_no": 101,
    "dept": "COMPUTER",
    "fees": 45000,
    "balance": 5000
  }
]
```

### `GET /api/students/<roll_no>`
A single student by roll number.

- **200** — the student object (same shape as above)
- **404** — `{ "error": "not found" }`

```bash
curl http://127.0.0.1:5000/api/students/1
```

### `GET /api/fees`
The department fee schedule.

```json
[
  { "department": "BIO", "amount": 40000 },
  { "department": "COMPUTER", "amount": 45000 }
]
```

### `GET /healthz`
Health check for load balancers / uptime monitors.

```json
{ "status": "ok" }
```

## Mutations

State-changing operations (create/update/delete students, set fees) are performed through
the **HTML forms** in the dashboard. They are POST-only and protected by a per-session CSRF
token, so they are intended for the UI rather than direct API calls.

## Status Codes

| Code | Meaning |
| --- | --- |
| 200 | Success |
| 400 | Bad request (e.g. missing/invalid CSRF token on a form POST) |
| 404 | Resource not found |
| 500 | Server error |

## Notes

- Currency values are integers (whole rupees).
- Department codes are uppercase: `COMPUTER`, `BIO`, `TECH`, `PHYSICS`, `ECO`, `ENG`.
