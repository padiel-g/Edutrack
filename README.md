# EduTrack

EduTrack is a full-stack School Management System with a Flask/PostgreSQL
backend and a Next.js/Tailwind frontend.

**EduTrack uses PostgreSQL only. SQLite is not supported.**

## Run Locally

1. Install PostgreSQL and create a database named `edutrack`:

   ```sql
   CREATE DATABASE edutrack;
   ```

2. Start the backend:

   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   # Edit .env so DATABASE_URL points at your PostgreSQL instance
   flask db init
   flask db migrate -m "initial PostgreSQL schema"
   flask db upgrade
   python serve.py
   ```

   The required environment variables are:

   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/edutrack
   SECRET_KEY=generate-a-random-value-of-at-least-32-characters
   JWT_SECRET_KEY=generate-a-different-random-value-of-at-least-32-characters
   CORS_ORIGINS=https://edutrack.example.com
   BACKUP_PATH=C:\EduTrack\backups
   FLASK_ENV=development
   ```

   If `DATABASE_URL` is missing — or points at SQLite — the backend refuses to
   start and shows `DATABASE_URL is required. EduTrack supports PostgreSQL
   only.`

3. Start the frontend:

   ```bash
   cd frontend
   npm install
   copy .env.example .env.local
   npm run dev
   ```

4. Open `http://localhost:3000`.

## Included

- PostgreSQL models with relationships, foreign keys, indexes, timestamps, and audit fields.
- Flask-Migrate / Alembic migrations as the single mechanism for managing the PostgreSQL schema.
- JWT authentication, role claims, protected API endpoints, and role-aware frontend route guards.
- Admin Student Registration module with backend-generated `EDU-YYYY-0001` registration numbers, grade/form, class/stream, and subject selection persisted in PostgreSQL.
- Accounts Officer portal at `/accounts` with fee accounts, invoices, payments, receipts, reminders, finance dashboards, and PDF export endpoints.
- CRUD REST endpoints for the requested school modules.
- Dashboard analytics endpoint backed by PostgreSQL counts and aggregates.
- PDF generation endpoints for report cards, receipts, finance reports, and attendance reports.
- Responsive dashboard shell with sidebar navigation, cards, charts, forms, tables, filters, pagination controls, loading and error states.

## Key Routes

- Admin students: `/admin/students`, `/admin/students/register`, `/admin/students/:id`
- Accounts portal: `/accounts`
- Student APIs: `/api/admin/students`, `/api/admin/students/:id`, `/api/admin/students/:id/profile`
- Finance APIs: `/api/finance/dashboard`, `/api/finance/invoices`, `/api/finance/bulk-invoices`, `/api/finance/payments`, `/api/finance/receipts`

cd C:\Users\gpadi\Desktop\sch\backend

& 'C:\Users\gpadi\AppData\Local\Programs\Python\Python311\python.exe' -c "from app import create_app; from app.extensions import db; from app.models import Role, User; app=create_app(); app.app_context().push(); role=Role.query.filter_by(name='Parent').first() or Role(name='Parent', description='Parent'); db.session.add(role); db.session.flush(); user=User(email='parent@edutrack.com', first_name='Parent', last_name='User', role=role); user.set_password('Parent@12345'); db.session.add(user); db.session.commit(); print('Parent account created')"

flask list-accounts
flask reset-password --email admin@edutrack.com
