# 🛡️ ServiceNow GRC Risk Management Replication Platform

Welcome to the autonomous, agent-built ServiceNow GRC tracking portal demonstration environment.

## 🔗 Visually Preview Our Docs
- [📑 Interactive System Architecture Manual](./ARCHITECTURE.md)
- [📦 Framework Tech Stack Blueprint](./ARCHITECTURE.md#2-tech-stack-blueprint)

## 🚀 Running Your Demo Architecture Local Instance

### 1. Launch Python FastAPI Server Backend
```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python init_db.py
fastapi dev main.py --port 8050
```

### 2. Launch Next.js UI Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```

## 🔑 Demo Login

Browsing the dashboard (`/workspace`, `/assessor`) needs no account — all
`GET` endpoints stay open. Creating, editing, or deleting a record requires
signing in at `/login`:

- **Username:** any seeded `user.NNN` (e.g. `user.001`) — `init_db.py` seeds
  20 of them, cycling through every role (Risk Owner, Assessor, Compliance
  Manager, Auditor, Administrator) so `user.005`/`010`/`015`/`020` are
  Administrators. About 1 in 10 seeded users is randomly inactive; if a
  login fails, try another `user.NNN`.
- **Password:** `changeme123` for every seeded user.

Deletes and a few sensitive actions (managing roles/users, assessment
submission) are further role-gated — see `backend/main.py`'s `ADMIN_ROLES`
and per-resource `write_roles`/`delete_roles` for the exact mapping.
