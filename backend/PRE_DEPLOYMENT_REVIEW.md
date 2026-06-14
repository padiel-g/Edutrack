# EduTrack — Pre-Deployment Review (target: 2,000+ students)

Scope: Flask backend at `backend/`. Reviewed app factory, config, auth, models,
CRUD/routes, services, and deployment docs. The codebase is well-structured and
already covers many production basics (HTTPS redirect, security headers, JWT
error handlers, connection pooling, migrations, pagination on admin lists, a
load-test harness). The items below are what should be fixed or verified before
go-live, ordered by severity.

---

## CRITICAL — fix before deployment

### 1. Broken access control on the generic CRUD API (data breach risk)
`app/routes/crud.py` — `list_resource` (GET `/api/<resource>`) and
`get_resource` (GET `/api/<resource>/<id>`) are protected only by
`@jwt_required()`. Role checks exist only for `audit-logs` and `report-cards`,
plus a `Parent` special case. **Any authenticated Student or Teacher can read
every resource**, including `users`, `students`, `parents`, `payments`,
`invoices`, `student-fee-accounts`, and `messages`.

With ~2,000 student/parent logins, this exposes the full PII set of the school
(dates of birth, national IDs, addresses, phone numbers, fee balances) to any
single logged-in account. This is the most serious issue in the system.

Fix: enforce per-role allow-lists on read endpoints (e.g. only Admin/Super
Admin/Accounts Officer may list `users`, `payments`, `invoices`, etc.; teachers
limited to their own classes/students; students/parents limited to their own
records). Default-deny any resource not explicitly permitted for a role.

### 2. Mass-assignment in generic create/update
`create_resource` and `update_resource` loop over `model.__table__.columns` and
copy any matching key from the request body. A caller can set columns that were
never meant to be client-writable (e.g. `users.password_hash`, `role_id`,
`must_change_password`, `status`, `created_by_id`). It's admin-gated today, but
combined with item #1's pattern it's fragile. Define an explicit writable-field
allow-list per resource instead of "every column".

Related: creating a `user` through the generic POST never hashes a password
(`set_password` is never called), so generic-created users get an unusable or
raw-stored credential.

### 3. Shared, weak default password that violates the system's own policy
- `DEFAULT_ACCOUNTS_PASSWORD = "Edutrack"` (auth.py) and
  `student.set_parent_password("Edutrack")` (admin_students.py) hand out the
  same hard-coded password to every Accounts Officer and every parent account.
- `"Edutrack"` is 8 characters with no digit/special char — it fails the app's
  own `strong_password()` rule.
- Accounts Officers are created with `must_change_password=False`, so they are
  never forced to rotate it.

At 2,000 students this means 2,000 parent logins share one publicly-guessable
password and no forced reset. Generate a random per-account temporary password,
deliver it out-of-band, and force a change on first login.

### 4. Rate-limit storage defaults to in-process memory
`config.py` defaults `RATELIMIT_STORAGE_URI` to `memory://`, and the live `.env`
does **not** set it. Under the documented `gunicorn --workers 4`, each worker
keeps its own counters, so effective limits are 4× the intended value and reset
on every restart/redeploy — brute-force and abuse protection is largely
defeated. Redis is already a dependency and is in `.env.example`; set
`RATELIMIT_STORAGE_URI=redis://...` in the real `.env` and verify it's used.

---

## HIGH — should fix before or immediately after launch

### 5. `.env` is missing most production settings
The deployed `.env` contains only `FLASK_APP, FLASK_ENV, SECRET_KEY,
JWT_SECRET_KEY, DATABASE_URL, FRONTEND_URL`. Missing vs. `.env.example`:
`CORS_ORIGINS` (falls back to `FRONTEND_URL` — confirm that's a single correct
HTTPS origin), `RATELIMIT_STORAGE_URI` (see #4), `FORCE_HTTPS`, `TRUST_PROXY`,
DB pool tuning, `MATERIAL_UPLOAD_PATH`, `BACKUP_PATH`, and all `SMTP_*`. Without
SMTP, teacher password reset returns 503 and is unusable. Reconcile `.env` with
`.env.example` and confirm each value for the production host.

### 6. No JWT revocation / real logout
Tokens last 8 hours and `/logout` only tells the client to drop the token. The
`revoked_token_loader` is wired but there's no blocklist check, so a leaked or
shared token stays valid until expiry, and disabling/deleting an account does
not invalidate live sessions. Add a Redis-backed token blocklist (jti) and check
it in a `token_in_blocklist_loader`; revoke on logout, password change, and
account deactivation.

### 7. N+1 queries on list endpoints (scaling)
At 2,000 students these multiply quickly:
- `Student.to_dict()` lazy-loads `student_subjects` (and each subject) plus
  `school_class` per row → up to ~100 extra queries per 100-row page.
- `SchoolClass.to_dict()` runs a teacher sub-query **and** lazy-loads subjects on
  every call → N+1 when listing classes.
- `Teacher.to_dict()` runs an extra sub-query per teacher when `assigned_classes`
  is empty.

Use eager loading (`selectinload`/`joinedload`) on the list queries, or trim the
serialized payloads for list views. Load-test the admin student/teacher/class
lists and the parent/teacher dashboards at full data volume.

### 8. Synchronous email blocks a request thread
`send_password_reset_code` opens an SMTP connection inline (10s timeout). A slow
SMTP server ties up a worker thread. Low volume today, but move email to a
background task/queue before broader rollout.

### 9. Local-disk file uploads won't survive multi-host / redeploys
`MATERIAL_UPLOAD_PATH` stores learning materials on local disk. With more than
one app host (or ephemeral/container storage) uploads become inconsistent or
lost, and they aren't covered by the Postgres backup script. Use shared/object
storage (e.g. S3-compatible) or guarantee a single host + include the upload dir
in backups. Confirm `MAX_CONTENT_LENGTH` (20 MB in `.env.example`) matches the
reverse-proxy body limit.

---

## MEDIUM — hardening and operational readiness

### 10. Per-request DB work in `before_request`
`enforce_temporary_password_change` issues a `User` lookup on essentially every
authenticated API call, and `ensure_database_schema` inspects the schema until
"ready". Fine functionally; just be aware it adds a query to the hot path — you
can lean on the `mustChangePassword` claim already in the JWT instead of a DB
hit.

### 11. Login lockout / brute-force
A teacher account-security migration exists (`c4d9a81f...`), but login itself is
only IP-rate-limited (10/min). Confirm account-level lockout/backoff is actually
enforced on `/login` for all roles, not just teachers, and that limits are
keyed correctly behind the proxy (depends on #4 + `TRUST_PROXY`).

### 12. Thin automated test coverage
Only `tests/test_teacher_dashboard.py` is present. For a system holding student
PII and finance data, add tests around authorization (every role × every
resource), the payment workflow, and password/reset flows before deployment.
Wire these into CI.

### 13. Capacity / infrastructure sizing
- `serve.py` (Waitress, Windows) uses 8 threads; `gunicorn` doc uses 4 workers ×
  2 threads. Both are reasonable starting points but must be load-tested at
  2,000 users with realistic concurrency. The `loadtests/` harness exists — run
  it against staging and size workers + `DB_POOL_SIZE`/`DB_MAX_OVERFLOW`
  accordingly (current pool: 10 + 20 overflow).
- Ensure Postgres `max_connections` ≥ (workers × (pool_size + max_overflow))
  across all app hosts, or you'll exhaust connections under load.
- Add monitoring/alerting (error rate, latency, DB connections, disk) and
  centralized logging; `server.out.log`/`server.err.log` on a single box is not
  enough.

### 14. Backups
The backup scripts and a "restore is not verified until tested" note are good.
Confirm the cron/Task Scheduler job is actually installed, runs off-host
encrypted copies, and that a restore has been performed at least once.

---

## What's already solid
HTTPS redirect + HSTS and a strict security-header set; CORS restricted to
configured origins with credentials off; secrets validated for length at boot;
PostgreSQL enforced (no accidental SQLite); connection pooling with
`pool_pre_ping`; centralized JWT and error handlers; Alembic migrations incl. a
dedicated production-index migration; pagination on the admin student/teacher
lists; audit logging; teacher reset codes hashed with attempt limits and
expiry; a load-test harness and production runbook.

## Suggested order of work
1. #1 access control, #2 mass-assignment, #3 default passwords (security blockers)
2. #4 Redis rate limiting + #5 complete `.env` (config blockers)
3. #6 token revocation, #7 N+1 / load test, #11 login lockout
4. #8, #9, #10, #12, #13, #14 (hardening + ops)
