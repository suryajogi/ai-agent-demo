---
layout: default
title: Glossary
---

# Glossary

[← Running It Yourself](06-running-locally.html)

Every technical term used across this guide, alphabetically. Each entry
notes which page it's explained in depth on, if you want the fuller
context.

**API (Application Programming Interface)** — a defined way for two
programs to talk to each other. This project's backend exposes a **REST
API** — a specific, very common style of API built on HTTP requests and
URLs. See [Architecture Overview](02-architecture-overview.html).

**async / await** — Python and TypeScript keywords marking a function
that may need to pause and wait on something slow (a network call, a disk
read) without freezing the whole program while it waits. See [Your
Toolbox](01-your-toolbox.html).

**bash / shell / terminal** — a text-only program where you type commands
instead of clicking. See [Your Toolbox](01-your-toolbox.html).

**bcrypt** — the one-way password-scrambling algorithm used to store
passwords so the original password is never recoverable from what's
stored. See [Backend Deep Dive](03-backend-deep-dive.html).

**class** — a blueprint for objects that bundle data and behavior
together; in this project's backend, every database table is defined as
one class. See [Your Toolbox](01-your-toolbox.html).

**CLI (Command-Line Interface)** — any tool operated by typing commands
in a terminal, as opposed to clicking through a graphical UI.

**component (React)** — a function that describes what a piece of the UI
should look like, given its current inputs/state. See [Frontend Deep
Dive](04-frontend-deep-dive.html).

**CORS (Cross-Origin Resource Sharing)** — the browser security rule that
blocks a web page from one address from fetching data from a different
address, unless the server explicitly allows it. See [Backend Deep
Dive](03-backend-deep-dive.html).

**CRUD** — Create, Read, Update, Delete — the four basic operations
almost every data-backed table needs, and the shape `build_crud_router`
generates generically for ~20 tables. See [Backend Deep
Dive](03-backend-deep-dive.html).

**decorator (`@something`)** — a line above a Python function that wraps
it with extra behavior, e.g. `@app.get(...)` registering a function as an
HTTP endpoint. See [Your Toolbox](01-your-toolbox.html).

**dependency (package/library)** — someone else's reusable code a project
builds on rather than writing from scratch (e.g. FastAPI, React). See
[Your Toolbox](01-your-toolbox.html).

**dependency injection (FastAPI)** — FastAPI's system for declaring "this
endpoint needs a database session / an authenticated user" as a function
parameter (`Depends(...)`), and having FastAPI supply it automatically.
See [Backend Deep Dive](03-backend-deep-dive.html).

**dictionary (Python `{...}`) / object (JSON, TypeScript)** — a set of
named key → value pairs. See [Your Toolbox](01-your-toolbox.html).

**endpoint / route** — one specific URL + HTTP method combination the
backend knows how to respond to. See [Architecture
Overview](02-architecture-overview.html).

**foreign key** — a column that stores another table's ID, linking a row
to a row in a different table — this project's equivalent of a
ServiceNow Reference field. See [Backend Deep
Dive](03-backend-deep-dive.html).

**FastAPI** — the Python web framework this project's backend is built
with; turns Python functions into HTTP API endpoints. See [Backend Deep
Dive](03-backend-deep-dive.html).

**function** — a named, reusable block of code — the closest equivalent
to a ServiceNow Script Include method. See [Your
Toolbox](01-your-toolbox.html).

**git / GitHub** — git is version-control software tracking every change
to a project's files over time; GitHub is a website that hosts git
repositories online. See [Your Toolbox](01-your-toolbox.html).

**hook (backend, `pre_create`/`pre_update`/`post_create`/`post_fetch`)** —
a plug-in Python function a specific table's CRUD router can attach, to
run extra validation or logic without special-casing that table's whole
router. See [Backend Deep Dive](03-backend-deep-dive.html).

**hook (React, `useState`/`useEffect`)** — a special kind of function
React components use to hold state or run code in reaction to something
changing. See [Frontend Deep Dive](04-frontend-deep-dive.html).

**HTTP** — the protocol web browsers and servers use to communicate;
every request has a method (GET/POST/PUT/DELETE) and a URL. See
[Architecture Overview](02-architecture-overview.html).

**import** — pulling code defined in one file into another file so it can
be used there. See [Your Toolbox](01-your-toolbox.html).

**JSON (JavaScript Object Notation)** — the plain-text format used to
send structured data over HTTP. See [Architecture
Overview](02-architecture-overview.html).

**JSX** — the HTML-like syntax used inside React component functions;
looks like HTML but is actually JavaScript/TypeScript. See [Frontend Deep
Dive](04-frontend-deep-dive.html).

**JWT (JSON Web Token)** — a signed, tamper-proof piece of text issued at
login, proving who a user is on every subsequent request, without the
server needing to remember a session. See [Backend Deep
Dive](03-backend-deep-dive.html).

**list (Python `[...]`) / array (TypeScript `[...]`)** — an ordered
collection of values. See [Your Toolbox](01-your-toolbox.html).

**list comprehension** — Python shorthand for building a list from a loop
in one line, e.g. `[User(...) for i in range(1, 21)]`. See [Backend Deep
Dive](03-backend-deep-dive.html).

**Next.js** — the React-based framework the frontend is built with;
adds, among other things, file-based routing (a folder's location under
`app/` determines its URL). See [Frontend Deep
Dive](04-frontend-deep-dive.html).

**npm** — the package manager for JavaScript/TypeScript projects; reads
`package.json` and installs the frontend's dependencies. See [Your
Toolbox](01-your-toolbox.html).

**ORM (Object-Relational Mapping)** — a library (SQLAlchemy, here) that
lets you interact with database tables as Python classes/objects instead
of writing raw SQL strings. See [Backend Deep
Dive](03-backend-deep-dive.html).

**package manager** — a tool that installs a project's third-party
dependencies from a list (`pip`/`uv` for Python, `npm` for JavaScript).
See [Your Toolbox](01-your-toolbox.html).

**Pydantic** — the Python library used to define and validate the shape
of data going in/out of the API (`backend/schemas.py`). See [Backend Deep
Dive](03-backend-deep-dive.html).

**React** — the JavaScript/TypeScript library the frontend's UI is built
with; the core idea is describing what the UI should look like given
current data, rather than issuing step-by-step update instructions. See
[Frontend Deep Dive](04-frontend-deep-dive.html).

**relational database / SQL / SQLite** — a database that stores data in
tables with defined columns and relationships between them, queried with
SQL (Structured Query Language). SQLite is a specific, lightweight
relational database that stores everything in a single file on disk. See
[Architecture Overview](02-architecture-overview.html).

**repository ("repo")** — one project's entire tracked folder plus its
full git history. See [Your Toolbox](01-your-toolbox.html).

**session (database)** — one open conversation with the database, used
to run queries and then closed. See [Backend Deep
Dive](03-backend-deep-dive.html).

**state (React)** — data a component remembers between renders that,
when changed, causes the screen to update. See [Frontend Deep
Dive](04-frontend-deep-dive.html).

**terminal** — see **bash**.

**TypeScript** — JavaScript plus optional type annotations, checked
before the code runs and removed before it reaches the browser. See
[Frontend Deep Dive](04-frontend-deep-dive.html).

**type hint (Python)** — an optional annotation noting what type a
variable/argument/return value is expected to be, for documentation and
tooling, not strictly enforced at runtime. See [Your
Toolbox](01-your-toolbox.html).

**variable** — a named value. See [Your Toolbox](01-your-toolbox.html).

**virtual environment (`.venv`)** — an isolated, project-specific
installation location for Python packages, so different projects'
package versions never conflict on the same machine. See [Your
Toolbox](01-your-toolbox.html).

---
[← Running It Yourself](06-running-locally.html) · [Back to Start Here](00-start-here.html)
