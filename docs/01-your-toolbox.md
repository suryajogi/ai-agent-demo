---
layout: default
title: Your Toolbox
---

# Your Toolbox: Terminal, Git, and Python Basics

[← Back to Start Here](00-start-here.html)

In ServiceNow, almost everything happens inside the browser: you log into
an instance, and every tool (Studio, Script Editor, Update Sets) is a UI on
top of it. Outside of ServiceNow, a huge amount of software development
happens instead in a **terminal** — a text-only window where you type
commands instead of clicking buttons. This page explains that terminal,
the specific commands this project uses, what **git** is, and enough
**Python** to read `backend/*.py`.

## 1. What a terminal actually is

The **terminal** (also called a **shell**, or on Mac specifically
**Terminal.app**, running a program called **bash** or **zsh**) is a
program where you type a line of text, press Enter, and a command runs
immediately — no menus, no mouse. Where you'd click through *System
Definition > Scripts* in ServiceNow, here you type a line and hit Enter.

Every terminal has a **current directory** — the folder it's "standing in"
right now, shown in the prompt. Commands that mention files (like "run this
Python file") act on files *relative to that current directory*, the same
way a relative reference in a ServiceNow script needs the right table
context. This is why almost every instruction in this project starts with
`cd backend` or `cd frontend` — you're telling the terminal "stand inside
this folder" before running the next command.

### Commands you'll actually see in this project

| Command | What it does | ServiceNow-ish analogy |
|---|---|---|
| `cd <folder>` | **C**hange **D**irectory — move into a folder | Navigating into an application scope |
| `ls` | **L**i**s**t the files in the current folder | Browsing a table's list view |
| `pwd` | Print the current folder's full path | — |
| `python init_db.py` | Run the Python program in the file `init_db.py` | Running a Background Script |
| `source .venv/bin/activate` | Turn on a Python "virtual environment" (see below) | — |
| `uv pip install -r requirements.txt` | Download and install the Python libraries this project depends on | Installing a plugin from the Store |
| `npm install` | Download and install the JavaScript libraries the frontend depends on | Installing a plugin from the Store |
| `npm run dev` | Start the frontend's local development server | — |
| `git status` / `git log` / `git commit` | See/save changes to the code, tracked by git (see below) | Creating/committing an Update Set |

A command is often followed by **flags** — extra words starting with `-`
or `--` that change its behavior, like `-r requirements.txt` above meaning
"read the list of things to install from this file." You don't need to
memorize these; every command you actually need to run is spelled out
verbatim in [Running It Yourself](06-running-locally.html) — you can
copy-paste it.

### `if __name__ == "__main__":` — why some files run and others don't

You'll see this exact line near the bottom of most Python files in this
repo:

```python
if __name__ == "__main__":
    main()
```

Python files can either be **run directly** (`python assessor_agent.py`)
or **imported by another file** (the way `main.py` imports `models.py` to
use its table definitions, without wanting to re-run `models.py` as a
program). This line means: "only run the code below if this specific file
is the one that was launched directly from the terminal — if some other
file merely imported this one for its definitions, skip this part." It's
Python's version of "only run this script when I explicitly execute it,
not just when something references it."

## 2. Virtual environments and package managers (`pip`, `uv`, `npm`)

ServiceNow plugins are versioned and installed per-instance from the
Store. Python and JavaScript projects have an equivalent idea, but it's
manual:

- A **package** (a.k.a. **library** or **dependency**) is someone else's
  reusable code that this project builds on instead of writing from
  scratch — e.g. FastAPI (the web framework) or SQLAlchemy (the database
  layer) are packages, not code written for this project.
- `backend/requirements.txt` and `frontend/package.json` are literally just
  lists of which packages, and which versions, this project needs.
- **`pip`** (and the faster, modern **`uv`**, which this project uses) is
  the tool that reads `requirements.txt` and actually downloads/installs
  those Python packages onto your machine. **`npm`** does the same job for
  JavaScript packages, reading `package.json`.
- A **virtual environment** (the `.venv` folder, created by `uv venv`) is
  an isolated, project-specific install location for Python packages —
  so this project's exact package versions don't clash with some other
  Python project's different versions on the same machine. `source
  .venv/bin/activate` is the command that tells your terminal "for this
  session, use *this* project's isolated set of packages." You'll always
  run it before running any `python` command in `backend/`.

There's no `.venv` equivalent for the frontend — `npm install` puts
everything into a `frontend/node_modules/` folder instead, which serves
the same isolating purpose.

## 3. Git and GitHub, briefly

**Git** is a version-control system: it records a history of every change
ever made to the project's files, who made it, and why — conceptually
similar to a ServiceNow **Update Set**, except every single save is
recorded (not just what you explicitly capture), and the full history
travels with the code forever.

**GitHub** is a website that hosts git repositories online (so other
people, or your future self on another machine, can download/see them) —
think of it as the shared instance everyone clones from, plus a web UI for
browsing history and code, plus (relevant to this guide) the ability to
publish a **GitHub Pages** website straight from files in the repo.

A few terms you'll encounter:

- **Repository ("repo")** — one project's entire tracked folder + its full
  history. `ai-agent-demo` is one repo.
- **Commit** — one saved snapshot of changes, with a message describing
  what changed and why.
- **Clone** — downloading a full copy of a repo (history included) onto
  your machine: `git clone <url>`.
- **Branch** — a parallel line of commits, for working on something
  without touching the main line (`main`) until it's ready.
- **Push** / **pull** — uploading your new commits to GitHub / downloading
  commits made elsewhere.

You won't need to run git commands yourself just to *use* this project —
only `git clone` once, to get a copy. It's mentioned here because you'll
see it referenced in code comments (e.g. `agentic_workflow.py` runs `git
commit` and `git push` on its own — more on why that's risky in
[The Automation Agents](05-automation-agents.html)).

## 4. Just enough Python to read `backend/*.py`

You don't need to become a Python programmer to follow this guide — you
need to recognize a handful of shapes when you see them, the way you can
follow an unfamiliar Business Rule if you already know what `current`,
`if`, and `gs.info()` mean.

### Variables and types

```python
DATABASE_URL = "sqlite:///./grc.db"
TOKEN_EXPIRE_MINUTES = 60 * 12
```

A **variable** is just a named value — same idea as a script include's
property. Python doesn't require declaring a type up front (unlike
Java/Apex); it figures out from the value whether something is text (a
**string**, in quotes), a whole number (an **int**), a decimal (a
**float**), true/false (a **bool**), or `None` (Python's version of
`null`/no value).

### Functions

```python
def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

A **function** is a named, reusable block of code — the direct equivalent
of a Script Include method. `def` starts the definition; the text after
each argument name (`password: str`) and after `->` are **type hints** —
documentation-only notes saying "this argument should be a string" and
"this function returns a string." Python doesn't actually enforce these at
runtime the way Apex enforces types, but tools (and readers) use them to
catch mistakes early.

### Classes

```python
class Risk(Base):
    __tablename__ = "risks"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
```

A **class** is a blueprint for creating objects that bundle data and
behavior together — think of it like a table's schema plus its business
rules bundled into one definition. In `backend/models.py`, every database
table is one Python class; each line inside is one column, and you'll see
this exact shape ~25 times, once per table (see
[Backend Deep Dive](03-backend-deep-dive.html)).

### Imports

```python
from database import Base, engine, get_db
import models
```

**`import`** pulls in code defined in another file, the way one Script
Include can call another. `import models` makes everything in
`models.py` available as `models.Risk`, `models.Control`, etc.; `from
database import get_db` pulls in just that one specific thing directly by
name, so it's used as `get_db` rather than `database.get_db`.

### Decorators (`@something`)

```python
@app.get("/api/v1/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)) -> dict[str, int]:
    ...
```

A line starting with `@` right above a function is a **decorator** — it
wraps the function with extra behavior without changing the function's own
code. `@app.get("/api/v1/dashboard/stats")` is FastAPI's way of saying
"whenever an HTTP GET request comes in for this exact URL, run the
function directly below." This is the single most important pattern to
recognize in `backend/main.py` — it's the closest thing to defining a
Scripted REST API resource in ServiceNow: the decorator is the URL/method
mapping, the function body is the resource script.

### `async def` and `await`

```python
async def log_unhandled_exceptions(request: Request, exc: Exception) -> JSONResponse:
```

`async` marks a function as one that might need to **wait** on something
slow (like a network call or disk read) without freezing the whole
program while it waits — other requests can be handled in the meantime.
`await` (used elsewhere in the codebase) is where that waiting actually
happens. You can read `async def` as "an ordinary function, except it's
allowed to pause and let other work happen while it's waiting on
something." You don't need to reason about this deeply to follow the code
— just recognize it as a function definition.

### Dictionaries and lists

```python
{"status": "ok"}                       # a dictionary: named key → value pairs
["Draft", "Assess", "Respond"]         # a list: an ordered sequence of values
```

A **dictionary** (`{...}`) is a set of key/value pairs — structurally the
same idea as a JSON object, and in fact these get converted directly to
JSON when sent to the frontend (see
[Architecture Overview](02-architecture-overview.html) for what JSON is).
A **list** (`[...]`) is an ordered collection, like a JS array or a simple
in-memory table.

That's the complete vocabulary you need. Every remaining Python
construct you'll meet in this codebase (`for` loops, `if`/`else`,
f-strings like `f"Risk {risk_id} not found"`) reads almost exactly like
its plain-English description, so it's called out inline in
[Backend Deep Dive](03-backend-deep-dive.html) rather than here.

---
[← Start Here](00-start-here.html) · [Next: Architecture Overview →](02-architecture-overview.html)
