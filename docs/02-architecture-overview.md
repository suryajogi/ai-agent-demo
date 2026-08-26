---
layout: default
title: Architecture Overview
---

# Architecture Overview

[← Your Toolbox](01-your-toolbox.html)

## The request/response loop

Every single action in this app — loading the dashboard, clicking a tab,
saving a Risk — follows the same round trip:

```
1. You click something in the browser (frontend/, Next.js/React)
2. The frontend sends an HTTP request to the backend
   e.g. GET http://localhost:8050/api/v1/risks
3. The backend (FastAPI, backend/main.py) receives it, runs a Python
   function, queries the SQLite database through SQLAlchemy
4. The backend sends back a response — plain text data in JSON format
5. The frontend turns that JSON into what you see on screen
```

This is the exact same shape as a ServiceNow Service Portal widget's
client script calling a Scripted REST API, which then queries a table via
GlideRecord. The vocabulary differs; the shape doesn't.

### HTTP, endpoints, and JSON — the three concepts underneath everything

- **HTTP** is the protocol (agreed-upon format) that web browsers and
  servers use to talk to each other. Every request has a **method**
  (`GET` to read data, `POST` to create something, `PUT` to update, `DELETE`
  to remove — directly analogous to a Scripted REST API resource's HTTP
  method) and a **URL path** (`/api/v1/risks`).
- An **endpoint** (or **route**) is one specific URL + method combination
  that the backend knows how to respond to — e.g. "`GET /api/v1/risks`"
  is one endpoint, "`POST /api/v1/risks`" (create a new one) is a
  different endpoint, even though the URL text is identical.
- **JSON** (JavaScript Object Notation) is the plain-text format used to
  send structured data over HTTP — `{"id": 1, "name": "Unpatched VPN"}` is
  JSON. It's how the backend sends a Risk record to the frontend, and how
  the frontend sends a new Risk's field values back. It's the rough
  equivalent of the internal representation ServiceNow uses when a
  GlideRecord gets serialized for a REST response — human-readable,
  language-independent, and just key/value pairs and lists nested inside
  each other.

## The three layers of the backend, and why they're separate

The backend isn't one big file — it's deliberately split into layers, each
with one job. This mirrors, loosely, how ServiceNow separates a table's
**schema** (Dictionary Entries), its **validation rules** (Data Policies),
and its **business logic** (Business Rules) instead of mashing all three
into one place:

```
HTTP request comes in
        │
        ▼
┌─────────────────────────────┐
│ schemas.py                  │  "Is this data even shaped right?"
│ (Pydantic — validates the   │  (like a Data Policy / mandatory-field
│  shape of incoming/outgoing │   check running before anything touches
│  JSON)                      │   the database)
└─────────────┬────────────────┘
              ▼
┌─────────────────────────────┐
│ main.py                     │  "What should happen for this URL?"
│ (FastAPI — routes the       │  (like a Scripted REST API resource, or
│  request to the right       │   a Business Rule's logic)
│  Python function, applies   │
│  auth/role checks)          │
└─────────────┬────────────────┘
              ▼
┌─────────────────────────────┐
│ models.py + database.py     │  "What does the data actually look like,
│ (SQLAlchemy — the table     │   and how do I read/write it?"
│  definitions + the DB       │  (like Dictionary Entries + the table
│  connection)                │   itself)
└─────────────┬────────────────┘
              ▼
      backend/grc.db  (a single SQLite database file on disk)
```

`auth.py` and `scoring.py`/`control_testing.py` sit alongside this same
flow as shared helpers (auth is checked on the way in; scoring/control
testing are called from inside specific endpoints). The full breakdown of
every file is in [Backend Deep Dive](03-backend-deep-dive.html).

## What SQLite is, and why this project uses it

**SQLite** is a real relational database — same relational-table concept
as ServiceNow's underlying database — except it stores everything in a
**single ordinary file on disk** (`backend/grc.db`) rather than requiring
a separate database *server* process running somewhere. That makes it
perfect for a local demo project: there's nothing to install, configure,
or keep running separately — the file simply exists, and `backend/database.py`
points at it. It's not what you'd choose for a production system serving
many simultaneous users (that's what Postgres, MySQL, or ServiceNow's own
backing database are for), but for one developer running this on their
own machine, it's the simplest option that's still a real SQL database.

## Frontend architecture, zoomed out

The frontend has two main screens (**Interface A** and **Interface B** in
the project's own terminology), plus a login page and a home page:

```
frontend/app/
├── page.tsx            → "/"          the home page (live stats + two links)
├── login/page.tsx      → "/login"     sign in (only needed to write data)
└── workspace/page.tsx  → "/workspace" Interface A: the main GRC dashboard
    (+ ControlForm.tsx, RiskForm.tsx, IssueForm.tsx, EntityForm.tsx,
       DepartmentForm.tsx, AssessmentLauncherForm.tsx, RiskHeatmap.tsx,
       EvidenceList.tsx, ControlTestHistory.tsx, NotificationBell.tsx,
       ui.tsx — shared building blocks used by all of the above)
└── assessor/page.tsx   → "/assessor"  Interface B: the questionnaire portal
```

Next.js's **App Router** convention is: a folder under `app/` becomes a
URL path, and the `page.tsx` file inside it is what renders for that URL.
So `frontend/app/workspace/page.tsx` existing is *why* visiting
`/workspace` shows the dashboard — there's no separate routing
configuration file to go find, the folder structure *is* the routing
table. This is different from ServiceNow, where a page's URL and its
content are configured as separate records; here, the file's location on
disk is the configuration.

## Reads are open, writes need a login

You can browse `/workspace` and `/assessor` and see every record without
logging in — every `GET` endpoint is intentionally left open, so the
dashboard works read-only with zero setup. The moment you try to
**create, edit, or delete** anything, the backend requires a **JWT bearer
token** (see [Backend Deep Dive → auth.py](03-backend-deep-dive.html)) —
obtained by signing in at `/login` with one of the seeded demo accounts.
This is the opposite default from a typical ServiceNow instance (which
usually requires login even to read), chosen here specifically so a
recruiter/reviewer can explore the dashboard with zero friction.

## Where the AI agent scripts and the AI scaffolding fit in

Two more things live in this repo that are **not** part of the running
app:

- **The six root-level Python scripts** (`assessor_agent.py`,
  `end_user_agent.py`, etc.) are one-off automation you run by hand from
  the terminal — they talk to the *already-running* backend over the same
  HTTP API the frontend uses, simulating real users. Covered in
  [The Automation Agents](05-automation-agents.html).
- **The `ai/` folder** is explicitly **scaffolding only** — empty-ish
  agent/RAG folders sketching out a *future* AI Risk Assistant feature
  described in `PRODUCT_BACKLOG.md`. Nothing in `ai/` is wired up or
  running today; it exists so a future contributor has a starting
  skeleton. It's mentioned here only so you don't go looking for a
  feature that isn't built yet.

---
[← Your Toolbox](01-your-toolbox.html) · [Next: Backend Deep Dive →](03-backend-deep-dive.html)
