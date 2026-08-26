---
layout: default
title: Running It Yourself
---

# Running It Yourself

[← The Automation Agents](05-automation-agents.html)

This page is meant to be followed with a terminal open, copy-pasting each
command block in order. If any term here is unfamiliar, it was defined in
[Your Toolbox](01-your-toolbox.html) — this page assumes you've read that
page already.

You'll end up with **two terminal windows/tabs open at once**, each
running one long-lived process that you leave running (don't close these
windows or press Ctrl+C once they're up) while you use the app in a
browser.

## Prerequisites (one-time setup)

- **Python 3.12** — the language the backend is written in.
- **[`uv`](https://docs.astral.sh/uv/)** — the tool used to create the
  Python virtual environment and install backend packages (a faster
  modern alternative to plain `pip`).
- **Node.js** (which includes `npm`) — needed to run the frontend.

If you're not sure whether these are installed, opening a terminal and
typing `python3 --version`, `uv --version`, and `node --version` will
either print a version number (installed) or say "command not found"
(not installed — install it before continuing).

## Terminal 1 — the backend (FastAPI)

Open a terminal, then navigate into the project and the `backend` folder:

```bash
cd ~/Desktop/ai-agent-demo/backend
```

`cd` (change directory) moves your terminal's "current folder" — every
command below assumes you're standing inside `backend/`.

```bash
uv venv
```

Creates the isolated Python **virtual environment** described in [Your
Toolbox](01-your-toolbox.html) — a new `.venv` folder, specific to this
project, that will hold this project's exact package versions without
touching any other Python project on your machine. You only need to run
this once ever (or again if you delete `.venv`).

```bash
source .venv/bin/activate
```

**Activates** that virtual environment for this terminal session — from
now on, until you close this terminal window, any `python` or `pip`
command you run uses this project's isolated packages. You'll need to run
this line again every time you open a **new** terminal window to work on
the backend (it doesn't stay active across separate terminal sessions).
You'll usually see your terminal prompt change to show `(.venv)` at the
start once this has worked.

```bash
uv pip install -r requirements.txt
```

Reads `backend/requirements.txt` (the list of every Python package this
backend needs — FastAPI, SQLAlchemy, `python-jose` for JWTs, `passlib`
for password hashing, `httpx`, `fpdf2`, and so on) and downloads/installs
every one of them into `.venv`. This can take a minute the first time;
you only need to re-run it if `requirements.txt` itself changes later.

```bash
python init_db.py
```

Runs the seeding script covered in [Backend Deep Dive](03-backend-deep-dive.html)
— **this wipes and recreates `backend/grc.db` from scratch** and fills it
with demo departments, entities, risks, controls, issues, users, and
assessments. Run this once before first use; run it again any time you
want to reset the demo data back to a clean starting state (e.g. after
you've deleted/mangled records while exploring the UI).

```bash
fastapi dev main.py --port 8050
```

**Starts the backend server itself**, listening on port **8050**. `fastapi
dev` is FastAPI's own command for running a local development server —
it automatically reloads whenever you edit a `.py` file in this folder,
which matters if you're modifying the code, not just running the demo as
shipped. You should see log output ending in something like `Uvicorn
running on http://127.0.0.1:8050`. **Leave this terminal window open and
this command running** — closing it, or pressing Ctrl+C, stops the entire
backend, and the frontend (and any of the automation scripts) will have
nothing to talk to.

You can sanity-check it's alive by opening
`http://localhost:8050` directly in a browser — you should see
`{"status":"ok"}`. FastAPI also auto-generates interactive API
documentation at `http://localhost:8050/docs`, worth exploring on its
own: it lists every endpoint described in [Backend Deep
Dive](03-backend-deep-dive.html) and lets you try them directly from the
browser, similar in spirit to testing a Scripted REST API from
ServiceNow's own REST API Explorer.

## Terminal 2 — the frontend (Next.js)

Open a **second, separate** terminal window (leave the first one running
the backend), then:

```bash
cd ~/Desktop/ai-agent-demo/frontend
npm install
```

Reads `frontend/package.json` and downloads every JavaScript package the
frontend needs (React, Next.js, Tailwind CSS, TypeScript itself) into a
new `frontend/node_modules/` folder — the frontend's equivalent of the
backend's `.venv`. Only needs to be re-run if `package.json` changes.

```bash
npm run dev
```

Starts the frontend's local development server, by default on port
**3000**. Next.js will print the exact URL to open — usually
`http://localhost:3000` (if that port's already in use, it'll pick the
next free one and tell you). Like the backend, this also auto-reloads on
every file edit, and you should **leave this terminal running** the same
way as the backend's.

## Using it

Open the URL the frontend printed. You should land on the home page with
a live stats banner (proof the frontend is already successfully talking
to the backend). From there:

- **`/workspace`** browses and edits every record type read-only with no
  login required — click around freely.
- To **create, edit, or delete** anything, click "Sign in," and use any
  seeded account: username `user.001` through `user.020`, password
  `changeme123` for all of them (seeded by `init_db.py`, see [Backend
  Deep Dive](03-backend-deep-dive.html)). `user.005`/`010`/`015`/`020`
  are Administrators specifically, if you want to test admin-only actions
  like deleting Roles/Users or approving appetite-breaching risks.
- **`/assessor`** is the separate questionnaire portal (Interface B).

If the dashboard shows a red error banner instead of live numbers, it
almost always means the backend (Terminal 1) isn't running, isn't fully
started yet, or is running on a different port than the frontend expects
— double check Terminal 1's output for errors before anything else.

## Running the automation scripts (optional, after the above is up)

With **both** the backend and frontend already running (per above), open
a **third** terminal, `cd` into the repo root
(`~/Desktop/ai-agent-demo`), activate the backend's virtual environment
again (`source backend/.venv/bin/activate`, since these scripts import
the same `httpx` package the backend installed), and run any of:

```bash
python end_user_agent.py
python assessor_agent.py
python summary_email_agent.py
```

See [The Automation Agents](05-automation-agents.html) for what each one
actually does. `product_owner_agent.py` and `agentic_workflow.py`
additionally require [Ollama](https://ollama.com) installed locally with
the `llama3` model pulled (`ollama pull llama3`) — without it, they'll
print a clear error and exit rather than doing anything destructive.

---
[← The Automation Agents](05-automation-agents.html) · [Next: Glossary →](07-glossary.html)
