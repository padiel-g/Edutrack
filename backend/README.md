# EduTrack Backend

Flask REST API for the EduTrack School Management System.

**EduTrack uses PostgreSQL only. SQLite is not supported.**

## Prerequisites

- Python 3.11+
- PostgreSQL 13+

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

1. Install PostgreSQL.
2. Create database `edutrack`:

   ```sql
   CREATE DATABASE edutrack;
   ```

3. Add the PostgreSQL connection string to `.env`:

   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/edutrack
   JWT_SECRET_KEY=your-secret-key
   FLASK_ENV=development
   ```

4. Run migrations (Flask-Migrate / Alembic):

   ```bash
   flask db init
   flask db migrate -m "initial PostgreSQL schema"
   flask db upgrade
   ```

5. Start the backend with a production WSGI server:

   ```powershell
   python serve.py
   ```

   On Linux:

   ```bash
   gunicorn --workers 4 --threads 2 --timeout 120 --bind 127.0.0.1:5000 wsgi:app
   ```

## Account Administration

Accounts are stored in PostgreSQL in the `users` table. Administrators can
view them in EduTrack under **Admin > Users and Roles**, or list them from the
backend:

```bash
flask list-accounts
```

To securely reset a forgotten password:

```bash
flask reset-password --email admin@school.com
```

The command prompts for the new password without displaying it and stores only
the generated password hash. It does not bypass authentication.

To delete an account that is not linked to a student, teacher, or parent:

```bash
flask delete-account --email user@school.com
```

The command asks for confirmation. Use `--yes` only for non-interactive
administration.

If `DATABASE_URL` is missing — or points at SQLite — the backend refuses to
start and reports: `DATABASE_URL is required. EduTrack supports PostgreSQL
only.`

## API

- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- CRUD resources: `/api/users`, `/api/roles`, `/api/students`, `/api/teachers`, `/api/classes`, `/api/subjects`, `/api/attendance`, `/api/invoices`, `/api/payments`, and all other core module names.
- Analytics: `GET /api/dashboard/analytics`
- Admin students: `/api/admin/students`, `/api/admin/students/:id`, `/api/admin/students/:id/profile`, `/api/admin/student-form-options`
- Finance: `/api/finance/dashboard`, `/api/finance/fee-accounts`, `/api/finance/invoices`, `/api/finance/bulk-invoices`, `/api/finance/payments`, `/api/finance/receipts`, `/api/finance/reminders`
- PDFs: `/api/pdf/report-cards/:student_id`, `/api/pdf/invoices/:invoice_id`, `/api/pdf/receipts/:payment_id`, `/api/pdf/finance-report`, `/api/pdf/attendance-report`

See `PRODUCTION.md` for reverse proxy, PostgreSQL network restrictions,
backups, restoration tests, and load testing.
accounts@edutrack.com | Accounts | active
admin@edutrack.com    | Admin    | active
parent@edutrack.com   | Parent   | active

cd C:\Users\gpadi\Desktop\sch\backend
flask list-accounts

flask delete-account --email parent@edutrack.com --yes

waitress-serve --host=127.0.0.1 --port=5000 --threads=8 wsgi:app

postgresql://neondb_owner:npg_ZiNpd7SI6msF@ep-shy-boat-ab9lcamp-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require