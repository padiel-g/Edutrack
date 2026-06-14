# EduTrack Frontend

Next.js App Router frontend for EduTrack.

## Setup

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

The app expects the Flask API at `NEXT_PUBLIC_API_URL=http://localhost:5000/api`.

## Portals

- Public landing page: `/`
- Login: `/login`
- Admin: `/admin`
- Teacher: `/teacher`
- Student: `/student`
- Parent: `/parent`
- Accounts Officer: `/accounts`

Protected routes are guarded by `middleware.ts` using the role cookie set after login.
