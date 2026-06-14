# Implementation Prompt — Make EduTrack Backend Production-Ready (2,000+ students)

You are working in the Flask backend at `backend/`. Address all of the issues
below from the pre-deployment review. Work in priority order, keep changes
minimal and focused, add/extend tests for each fix, and run the test suite
(`pytest`) plus `flask db upgrade` after schema changes. Do not break existing
public API response shapes unless noted. After each group, summarize what
changed and why.

## Ground rules
- Default-deny for authorization: if a role isn't explicitly allowed, reject.
- Never trust client-supplied field names blindly; use explicit allow-lists.
- No secrets or default passwords committed in code.
- Add a migration for any model/column change; never edit a model without one.
- Add a regression test for every bug you fix.

---

## CRITICAL

### 1. Fix broken access control in `app/routes/crud.py`
The generic `GET /api/<resource>` (`list_resource`) and
`GET /api/<resource>/<id>` (`get_resource`) currently require only
`@jwt_required()`. Implement per-role authorization:
- Define an explicit map of `resource -> set(roles allowed to read)`.
  Sensitive resources (`users`, `parents`, `payments`, `invoices`,
  `invoice-items`, `student-fee-accounts`, `fee-structures`, `receipts`,
  `fee-reminders`, `audit-logs`, `messages`, `notifications`) must be
  Admin/Super Admin (and Accounts Officer where finance-appropriate) only.
- Teachers: scope reads to their own classes/subjects/students, not the whole
  table.
- Students/Parents: only their own records (extend the existing Parent scoping
  to cover Student role too).
- Any resource/role combination not explicitly allowed returns 403.
- Apply the same gating to `get_resource` for single-item reads.
Add tests covering every role against each resource category (allowed vs denied).

### 2. Eliminate mass-assignment in `create_resource` / `update_resource`
Replace the `for column in model.__table__.columns: setattr(...)` pattern with
an explicit per-resource writable-field allow-list. Never allow client writes to
`id`, `password_hash`, `parent_password_hash`, `created_at`, `updated_at`,
`created_by_id`, `updated_by_id`, or `role_id` (role changes must go through a
dedicated, audited admin endpoint).
- For `users`, route password setting through `User.set_password()`; never store
  a raw or client-supplied `password_hash`. Reject `password_hash` in the body.
- Validate/whitelist on both create and update paths.
Add tests asserting protected fields are ignored/rejected.

### 3. Remove shared default passwords
- Delete the hard-coded `DEFAULT_ACCOUNTS_PASSWORD = "Edutrack"` and the
  `set_parent_password("Edutrack")` usage.
- Generate a cryptographically random temporary password per account
  (`secrets.token_urlsafe`), return it once to the creating admin (and/or email
  it), and set `must_change_password=True` so it must be rotated on first login.
- Ensure all generated temporary passwords satisfy `strong_password()`.
- Apply the same first-login forced-change flow to parent accounts.
Add tests: created accounts require a password change and the temp password is
never a fixed string.

### 4. Make rate limiting use shared storage
- Require `RATELIMIT_STORAGE_URI` to be a non-memory backend when
  `FLASK_ENV=production`; fail fast (or log a loud warning) if it's `memory://`
  in production.
- Confirm `app/extensions.py` Limiter picks up `RATELIMIT_STORAGE_URI` from
  config (set `storage_uri` via `init_app`/config).
- Document and set `RATELIMIT_STORAGE_URI=redis://...` in `.env`.

---

## HIGH

### 5. Reconcile `.env` with `.env.example`
Add/verify every production key in the deployed `.env`: `CORS_ORIGINS`,
`RATELIMIT_STORAGE_URI`, `FORCE_HTTPS`, `TRUST_PROXY`, DB pool settings,
`MATERIAL_UPLOAD_PATH`, `BACKUP_PATH`, and all `SMTP_*`. Add a startup
validation that warns when production-critical vars are missing. Document
required vars in `PRODUCTION.md`.

### 6. Implement real JWT revocation
- Add a Redis-backed token blocklist keyed by JWT `jti`.
- Implement `@jwt.token_in_blocklist_loader` to check it.
- On `/logout`, password change, and account deactivation/deletion, add the
  token's `jti` (and ideally all of a user's tokens) to the blocklist with TTL =
  remaining token lifetime.
Add tests: a logged-out / revoked token is rejected.

### 7. Remove N+1 queries on list endpoints
- Add eager loading (`selectinload`/`joinedload`) for `Student.student_subjects`
  (+ subject) and `school_class` on student list queries.
- Refactor `SchoolClass.to_dict()` and `Teacher.to_dict()` so they don't run
  per-row sub-queries; pass pre-fetched relations or add a lighter
  list-serializer variant.
- Verify with SQLAlchemy query logging that listing 100 students/classes/teachers
  issues a constant (not per-row) number of queries.

### 8. Move email sending off the request thread
Make `send_password_reset_code` asynchronous (background thread/task queue) so a
slow SMTP server can't tie up a worker. Keep the generic success response
behavior. Add a short timeout and proper error logging.

### 9. Fix file-upload storage for multi-host
Either switch learning-material uploads to shared/object storage
(S3-compatible), or document a single-host constraint and add the upload
directory to the backup routine. Confirm `MAX_CONTENT_LENGTH` matches the
reverse-proxy body-size limit.

---

## MEDIUM

### 10. Reduce per-request DB work
In `enforce_temporary_password_change`, use the `mustChangePassword` JWT claim
instead of a DB lookup on every request where possible (still verify on the
password-change path).

### 11. Account-level login lockout for all roles
Ensure `/login` enforces account lockout/backoff (not just IP rate limiting) for
every role, reusing the teacher account-security fields/migration. Verify
limiter keys work behind the proxy with `TRUST_PROXY` enabled.

### 12. Expand automated tests + CI
Add tests for: authorization matrix (role × resource), payment workflow,
password reset/change flows, and account creation. Add a CI workflow that runs
`pytest` and migration checks on every push.

### 13. Capacity & observability
- Run the existing `loadtests/` harness against staging at ~2,000 users; tune
  worker/thread counts and `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` from results.
- Verify Postgres `max_connections` >= total app pool across all hosts.
- Add health/readiness checks, request metrics, error-rate and DB-connection
  alerting, and centralized logging.

### 14. Verify backups
Confirm the backup job is scheduled, stores encrypted off-host copies, and that
a test restore has been performed successfully.

---

## Definition of done
- All CRITICAL and HIGH items implemented with passing tests.
- `pytest` green; migrations apply cleanly from a fresh DB.
- No hard-coded passwords or secrets in the codebase.
- Authorization matrix test proves non-privileged roles cannot read other users'
  or students' data.
- Load test at 2,000 users completes within acceptable latency with no
  connection-pool exhaustion.
