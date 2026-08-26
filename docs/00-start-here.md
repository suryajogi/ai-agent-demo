---
layout: default
title: Start Here
---

# Start Here

*A developer's guide to `ai-agent-demo`, written for a ServiceNow developer
who has never written Python, used a terminal, or touched React/Next.js.*

## Who this is for

You know ServiceNow: tables, Business Rules, Scripted REST APIs, ACLs,
Client Scripts, UI Builder. You do **not** know Python, JavaScript, git, or
the command line, and that's the assumption every page in this guide
starts from. Nothing here expects you to already know what a "function" or
a "terminal command" is — every term gets defined the first time it shows
up, usually by relating it to the closest ServiceNow equivalent.

## What this project actually is

`ai-agent-demo` rebuilds a small slice of **ServiceNow's GRC (Governance,
Risk, Compliance): Risk Management module** — Risks, Controls, Issues,
Assessments, Departments, Entities — as a **standalone web application**,
completely outside the ServiceNow platform. Where ServiceNow gives you a
table, a form, and a list view for free the moment you define a table
record, here every one of those pieces has to be hand-built:

| ServiceNow gives you automatically... | ...here, this project builds it by hand, in: |
|---|---|
| A table (`sys_db_object`) | `backend/models.py` |
| Form/field validation | `backend/schemas.py` |
| A REST API for the table | `backend/main.py` |
| `gs.getUser()`, roles, ACLs | `backend/auth.py` |
| A list view / related list UI | `frontend/app/workspace/page.tsx` and friends |
| Demo data (`Load Data` / fix scripts) | `backend/init_db.py` |
| Flow Designer / scheduled jobs | the standalone Python scripts in the repo root |

Seeing it built by hand like this is actually a great way to understand
*what ServiceNow is doing for you under the hood* every time you create a
table.

## The two halves of the app

Every modern web app (this one included) is really **two separate
programs that talk to each other over the network**:

1. **The backend** — a program that owns the database and enforces the
   rules. It doesn't know or care what the screen looks like; it just
   answers requests like "give me all risks" or "create this control." This
   is the closest thing to your ServiceNow *instance* — the server side.
   Here it's written in **Python**, using a framework called **FastAPI**,
   and lives in `backend/`.
2. **The frontend** — the actual web page you click around in, running in
   the user's browser. It has no direct access to the database; it only
   ever asks the backend for data over the network, the same way a
   ServiceNow Service Portal widget calls a Scripted REST API rather than
   querying the database directly. Here it's written in **TypeScript**
   (JavaScript with extra safety checks) using a framework called
   **Next.js** (built on **React**), and lives in `frontend/`.

```
 Your browser                          Your computer's backend process
┌─────────────────────┐   HTTP request  ┌──────────────────────────────┐
│ frontend/            │ ───────────────▶│ backend/                     │
│ (Next.js/React page) │                 │ (FastAPI + a SQLite database)│
│                       │ ◀─────────────── │                              │
└─────────────────────┘   JSON response  └──────────────────────────────┘
     "the form/list UI"                     "the table + REST API"
```

They run as **two separate processes, in two separate terminal windows,
on two different network ports** (backend on port 8050, frontend on port
3000) — there is no single "run the app" button. [Running It Yourself](06-running-locally.html)
walks through starting both, command by command.

## On top of that: six small automation scripts

At the repo root there are six standalone Python scripts
(`agentic_workflow.py`, `product_owner_agent.py`, `documentation_agent.py`,
`end_user_agent.py`, `assessor_agent.py`, `summary_email_agent.py`). None
of these are part of the running app — you execute each one by hand, once,
like running a **background script** in ServiceNow. They log into the live
API, generate demo activity, or regenerate documentation. See
[The Automation Agents](05-automation-agents.html).

## How to read this guide

The pages build on each other — each one assumes you've read the ones
before it:

1. **[Your Toolbox](01-your-toolbox.html)** — what a terminal is, the exact
   bash commands this project uses, what git is, and just enough Python
   syntax to read the backend code.
2. **[Architecture Overview](02-architecture-overview.html)** — how the
   pieces fit together, zoomed out.
3. **[Backend Deep Dive](03-backend-deep-dive.html)** — every file in
   `backend/`, explained.
4. **[Frontend Deep Dive](04-frontend-deep-dive.html)** — every important
   file in `frontend/`, explained.
5. **[The Automation Agents](05-automation-agents.html)** — the root-level
   scripts.
6. **[Running It Yourself](06-running-locally.html)** — copy-pasteable,
   fully-explained setup instructions.
7. **[Glossary](07-glossary.html)** — every technical term used across
   this guide, in one place, to look back up.

If you already know what a terminal, bash, git, and Python are, skip
straight to [Architecture Overview](02-architecture-overview.html).

---
[Next: Your Toolbox →](01-your-toolbox.html)
