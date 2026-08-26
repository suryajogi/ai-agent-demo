---
layout: default
title: Backend Deep Dive
---

# Backend Deep Dive

[← Architecture Overview](02-architecture-overview.html)

Everything in this page lives in `backend/`. Read it top to bottom — each
section builds on the last, in the same order data actually flows through
the app: connection → tables → validation → API → the fine print (auth,
scoring, control testing) → seed data → reporting.

## `database.py` — the database connection

```python
DATABASE_URL = "sqlite:///./grc.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This 21-line file does three things:

1. **Points at the database file.** `DATABASE_URL` says "use SQLite, and
   the data lives in a file called `grc.db` in the current folder."
   `engine` is the object that actually knows how to open and talk to
   that file.
2. **Defines `Base`.** Every table class in `models.py` will say `class
   Risk(Base):` — inheriting from `Base` is what turns an ordinary Python
   class into "this represents a database table." This pattern (a class
   representing a table, an instance of that class representing one row)
   is called an **ORM** — Object-Relational Mapping — and the library
   doing it here is called **SQLAlchemy**. Instead of writing raw SQL
   query strings everywhere, you write Python objects and SQLAlchemy
   translates them to SQL underneath.
3. **Defines `get_db()`, a "session per request" helper.** A **session**
   is one conversation with the database — open it, do some queries,
   close it. `get_db()` is written specifically to plug into FastAPI's
   **dependency injection** system (see `main.py` below): FastAPI calls
   this function once per incoming request, hands the resulting session
   to whichever endpoint needs it, and — because of the `yield` keyword
   — automatically runs the `finally: db.close()` cleanup after that
   endpoint finishes, even if it crashed. You'll see `db: Session =
   Depends(get_db)` as a parameter on nearly every function in `main.py`;
   that's this mechanism in action.

## `models.py` — every table, as a Python class

This file defines **~25 database tables**, one Python class each. If
you've read `CLAUDE.md`'s schema blueprint, this file *is* that blueprint,
written in actual code. Every class follows the identical shape, so once
you can read one, you can read all 25:

```python
class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    entity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("entities.id"))
    state: Mapped[str] = mapped_column(String, default="Draft")
    inherent_likelihood: Mapped[Optional[int]] = mapped_column(Integer)
    ...
    entity: Mapped[Optional["Entity"]] = relationship(back_populates="risks")
    assessments: Mapped[list["RiskAssessment"]] = relationship(back_populates="risk")
```

Reading this line by line, the way you'd read a Dictionary Entry list for
a table:

- `__tablename__ = "risks"` — the actual SQL table name.
- `id: Mapped[int] = mapped_column(primary_key=True)` — every table has
  this: an auto-incrementing integer ID, exactly like ServiceNow's `sys_id`
  except a plain number instead of a GUID string.
- `name: Mapped[str] = mapped_column(String, nullable=False)` — a column
  called `name`, of type string, that **can't be empty** (`nullable=False`
  is this project's version of a Dictionary Entry's "Mandatory" checkbox).
- `entity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("entities.id"))`
  — a column that stores another table's ID, linking this row to a row in
  `entities` — this *is* a reference field, exactly like a ServiceNow
  Reference field pointing at another table. `Optional[int]` means the
  value is allowed to be empty (no linked entity yet).
- `state: Mapped[str] = mapped_column(String, default="Draft")` — a plain
  text column that defaults to `"Draft"` if nothing else is set when the
  row is created — this project's version of a choice field, except the
  list of valid choices (`Draft, Assess, Respond, Review, Monitor` for
  Risk) is enforced only by convention/the frontend's dropdown, not by the
  database itself.
- `entity: Mapped[Optional["Entity"]] = relationship(back_populates="risks")`
  — this is **not** a column at all. It's SQLAlchemy's convenience layer
  on top of `entity_id`: once you have a `Risk` object in Python, writing
  `risk.entity` automatically fetches the linked `Entity` row for you (via
  the `entity_id` foreign key), instead of you writing a second query by
  hand. `back_populates="risks"` links it to the matching `relationship`
  declared over on the `Entity` class, so the connection works in both
  directions (`risk.entity` *and* `entity.risks`).

### The tables, grouped the way `CLAUDE.md` groups them

- **Identity**: `Role`, `User` — for login/auth (see `auth.py` below).
- **Org structure**: `Department`, `Entity` (an asset/app/vendor/facility
  being assessed — `Entity` also carries vendor-specific fields like
  `contract_end_date` that only mean something when `type == "Vendor"`).
- **Risk governance**: `RiskScope`, `RiskMethodology`, `RiskFramework`,
  `RiskStatement`, `Risk` — the taxonomy a Risk is classified under, and
  the Risk record itself (with `inherent_*`/`residual_*` likelihood and
  impact scores — "inherent" meaning the raw risk before any mitigation,
  "residual" meaning what's left after controls are applied).
- **Execution**: `RiskAssessment`, `RiskTask`, `Project`.
- **Compliance**: `Control` (a mitigation, optionally linked to a `Risk`),
  `Issue` (a deficiency, with root-cause/corrective-action fields for CAPA
  — Corrective and Preventive Action — tracking), `RiskMitigation`,
  `ControlFrameworkMap` (many-to-many: one control can satisfy several
  compliance frameworks), `RiskAppetiteThreshold` (the max acceptable
  score before a risk is flagged as breaching appetite).
- **Assessment engine**: `AssessmentTemplate`, `AssessmentQuestion`,
  `AssessmentOption`, `AssessmentResponse` — a configurable questionnaire
  system; a template has questions, each question can have scored answer
  options, and a response records what was actually answered.
- **Supporting tables**: `EvidenceAttachment` (uploaded files),
  `ControlTestResult` (history of automated control tests),
  `Notification` (in-app only, no email), `RiskScoreSnapshot`
  (point-in-time trend data), `AuditLog` (see below).

### `AuditLog` — how the audit trail actually gets written

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    table_name: Mapped[str] = mapped_column(String, nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)  # created, updated, deleted
    field_name: Mapped[Optional[str]] = mapped_column(String)
    old_value: Mapped[Optional[str]] = mapped_column(String)
    new_value: Mapped[Optional[str]] = mapped_column(String)
    changed_by: Mapped[Optional[str]] = mapped_column(String)
```

This table is never written to directly by hand — `main.py`'s generic
update/delete logic writes a row here automatically, one row per changed
field, every single time any record anywhere in the app is edited or
deleted. It's this project's version of ServiceNow's Audit related list,
built from scratch rather than coming for free from the platform. Read
via `GET /api/v1/audit-logs`.

## `schemas.py` — validating what goes in and out

`models.py` defines what the database looks like. `schemas.py` defines
what a valid **request** and **response** look like — using a library
called **Pydantic**. This is the layer that answers "is this JSON the
frontend just sent me actually shaped correctly?" — the closest
ServiceNow equivalent is a Data Policy or mandatory-field check that runs
*before* a record is allowed to save.

```python
class RiskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    entity_id: Optional[int] = None
    state: str = "Draft"
    inherent_likelihood: Optional[int] = None
    ...

class RiskRead(RiskCreate, ORMBase):
    id: int
    breaches_appetite: bool = False
    created_at: datetime
    updated_at: datetime
```

Notice the pattern repeated for nearly every table: a `*Create` schema and
a `*Read` schema.

- **`*Create`** describes the shape of data coming **in** — e.g. what a
  `POST /api/v1/risks` request body must look like to be accepted. `name:
  str` with no default means it's **required**; if the frontend sends a
  request missing `name`, FastAPI rejects it automatically, before any of
  your own code even runs, with a clear "field required" error. This is
  pure validation — it happens whether or not the field is nullable in
  the database.
- **`*Read`** describes the shape of data going **out** in a response. It
  extends `*Create` and adds fields that only exist *after* a record is
  saved — `id` (assigned by the database), `created_at`/`updated_at`
  (timestamps), and computed fields like `breaches_appetite` that aren't
  stored columns at all (see `main.py`'s `attach_breach_flags`, further
  down this page) — they're calculated fresh every time a Risk is read.
- **`ORMBase`** (defined once, reused everywhere) just tells Pydantic "it's
  fine to build this schema directly from a SQLAlchemy model object" —
  without it, Pydantic would only accept plain dictionaries.

Splitting `Create` from `Read` also means a client can never set fields
like `id` or `created_at` themselves on creation — those simply aren't
listed as accepted input on the `Create` schema, so any value sent for
them is silently ignored.

## `auth.py` — logins, passwords, and role checks

```python
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_token(user: models.User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "username": user.username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

Two ideas to unpack:

**Passwords are never stored as plain text.** `hash_password` runs a
password through **bcrypt**, a one-way scrambling algorithm — given the
scrambled output, there's no way to reverse it back into the original
password. When someone logs in, `verify_password` re-scrambles what they
typed and checks whether it matches the stored scramble — the actual
password is never compared or stored anywhere. This is standard practice
everywhere passwords are stored, ServiceNow included.

**Logging in issues a JWT ("JSON Web Token"), not a session cookie.** A
JWT is a signed, tamper-proof piece of text (created by `create_token`
above) that encodes "this is user #7, and this token expires at such-and-
such time." The frontend receives this token once at login, stores it
(`frontend/lib/api.ts`, in the browser's `localStorage`), and then sends
it back on the `Authorization: Bearer <token>` header of every subsequent
write request. `SECRET_KEY` is what makes the signature un-fakeable: only
the backend, which holds that key, can create a token that will verify
successfully.

```python
def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    payload = _decode(header[len("Bearer "):])
    ...

def require_user(user: Optional[models.User] = Depends(get_current_user)) -> models.User:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

def require_roles(*role_names: str):
    def _dependency(user: models.User = Depends(require_user)) -> models.User:
        user_role = user.role.name if user.role else None
        if user_role not in role_names:
            raise HTTPException(status_code=403, detail=...)
        return user
    return _dependency
```

These three functions are **FastAPI dependencies** — reusable
"pre-checks" that run before an endpoint's own code, declared the same
way `get_db` was: as a `Depends(...)` default value on a function
parameter. `get_current_user` reads and validates the token, returning
`None` rather than erroring if there isn't one (because `GET` endpoints
want to know *who's asking*, if anyone, without *requiring* a login).
`require_user` builds on it and actually blocks the request (HTTP 401,
"Unauthorized") if nobody's logged in. `require_roles("Administrator")`
goes one step further and blocks with 403 ("Forbidden") if the logged-in
user's role doesn't match — this is this project's version of an ACL
role check, and you'll see it attached directly to specific endpoints in
`main.py`, e.g. `dependencies=[Depends(auth.require_roles("Assessor",
"Administrator"))]` on the assessment-submission endpoint.

## `scoring.py` — turning a score into a label

```python
DEFAULT_BANDS = [
    {"min_score": 20, "max_score": 25, "label": "Critical", "color": "#dc2626"},
    {"min_score": 12, "max_score": 19, "label": "High", "color": "#f97316"},
    {"min_score": 6, "max_score": 11, "label": "Medium", "color": "#facc15"},
    {"min_score": 0, "max_score": 5, "label": "Low", "color": "#22c55e"},
]

def resolve_band(methodology, score):
    bands = (methodology.scoring_bands if methodology else None) or DEFAULT_BANDS
    for band in bands:
        if band["min_score"] <= score <= band["max_score"]:
            return band
    return None
```

A Risk's numeric score is just `likelihood × impact` (both 1–5, so the
score ranges 1–25). This tiny file's only job is mapping that number to a
human label like "Critical" — and it's configurable *per methodology*: if
a `RiskMethodology` row has its own `scoring_bands` set (stored as JSON —
see `models.py`), those are used instead of the four defaults shown
above. This is the equivalent of a configurable scoring matrix rather
than a hardcoded one.

## `control_testing.py` — pluggable, "real or simulated" control checks

```python
def run_test(control):
    connector = control.test_connector_type
    if connector == "http_health_check":
        url = config.get("url")
        response = httpx.get(url, timeout=5.0)
        if response.status_code == expect_status:
            return "Pass", f"GET {url} -> {response.status_code} ..."
        return "Fail", ...
    outcome = random.choice(["Pass", "Fail"])
    return outcome, "Simulated result (no connector configured)"
```

Most Controls in the seed data have no real external system to check, so
testing them is **simulated** — a coin flip between Pass and Fail, purely
for demo purposes. But the plumbing supports a **real** check too: if a
Control's `test_connector_type` is set to `"http_health_check"` (one
seeded Control is, in `init_db.py`), this actually makes a real outbound
HTTP request to a configured URL and passes/fails based on the real
response status code. `httpx` is the Python library used to make that
outbound web request — this project's equivalent of an Outbound REST
Message.

## `main.py` — the FastAPI application, and its generic CRUD router

This is the biggest file (1,100+ lines) and the one doing the most work.
It has two very different halves: a **generic, reusable router factory**
that handles ~20 tables' worth of ordinary Create/Read/Update/Delete
endpoints without repeating code, and a set of **hand-written custom
endpoints** for everything that doesn't fit that generic shape.

### Setting up the app

```python
Base.metadata.create_all(bind=engine)
app = FastAPI(title="ServiceNow GRC Risk Management Replication API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], ...)
```

`Base.metadata.create_all(...)` tells SQLAlchemy "make sure every table
defined in `models.py` actually exists in `grc.db`" — it creates any
missing tables but never touches existing data, so it's safe to run every
time the server starts (it's a safety net in case you forget to run
`init_db.py` first).

**CORS** (Cross-Origin Resource Sharing) is a browser security rule: by
default, a web page served from one address (`localhost:3000`, the
frontend) is *not allowed* to fetch data from a different address
(`localhost:8050`, the backend) — the browser blocks it, even though
you're the one running both. `CORSMiddleware` is the backend explicitly
telling the browser "requests from `localhost:3000` are allowed" —
without this line, the frontend simply couldn't talk to the backend at
all, and you'd see CORS errors in the browser console.

### The generic CRUD router factory — the single most important pattern here

```python
def build_crud_router(*, model, create_schema, read_schema, prefix, tag,
                       write_roles=None, delete_roles=None, ...) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=list[read_schema])
    def list_items(...): ...

    @router.get("/{item_id}", response_model=read_schema)
    def get_item(...): ...

    @router.post("", response_model=read_schema, status_code=201,
                 dependencies=[Depends(write_dependency)])
    def create_item(...): ...

    @router.put("/{item_id}", ...)
    def update_item(...): ...

    @router.delete("/{item_id}", ...)
    def delete_item(...): ...

    return router
```

Instead of hand-writing five endpoints (list, get-one, create, update,
delete) separately for Risks, then again for Controls, then again for
Issues, and so on ×20 tables — which would be enormous, repetitive, and
error-prone — `build_crud_router` is a **function that builds and returns
a complete set of five endpoints**, generically, for whichever table
you pass it. Then, near the bottom of the file:

```python
CRUD_RESOURCES = [
    dict(model=models.Risk, create_schema=schemas.RiskCreate, read_schema=schemas.RiskRead,
         prefix="/api/v1/risks", tag="risks", delete_roles=ADMIN_ROLES,
         pre_update=risk_pre_update, post_fetch=attach_breach_flags, department_scoped=True),
    dict(model=models.Control, ..., prefix="/api/v1/controls", ...),
    dict(model=models.Issue, ..., prefix="/api/v1/issues", pre_update=issue_pre_update),
    ... # ~17 more, one dict per table
]
for resource in CRUD_RESOURCES:
    app.include_router(build_crud_router(**resource))
```

Every table gets its five endpoints from one call into the factory,
configured by a short dictionary of settings. This is a genuinely
important pattern to recognize, because it's *exactly* what ServiceNow's
own table API does for you automatically and invisibly — this project
just makes that machinery visible and hand-built. When you need to
understand what `GET /api/v1/controls` does, you're really reading
`build_crud_router`'s `list_items` function (defined once), not hunting
for a `controls`-specific version of it.

A few things worth knowing about what that generic machinery includes:

- **Filtering by any column** — `list_items` loops over the incoming URL's
  query parameters and, for any that match a real column name, adds a
  filter (e.g. `GET /api/v1/risks?state=Draft`).
- **Free-text search** (`?q=...`) — matches against `name`/`title`/
  `description` columns, whichever exist on that table.
- **`X-Total-Count` header** — the total row count, sent back so the
  frontend could paginate if it wanted to (`skip`/`limit` are supported
  too).
- **Auth is opt-out on reads, opt-in on writes** — `list_items`/`get_item`
  take no auth dependency at all (open reads); `create_item`/
  `update_item`/`delete_item` require `Depends(write_dependency)`, which
  defaults to "any logged-in user" (`auth.require_user`) unless the
  resource's config passed a specific `write_roles`/`delete_roles` list
  (e.g. Roles/Users can only be created by an `Administrator`).
- **Optional hooks**: `pre_create`, `pre_update`, `post_create`,
  `post_fetch` — plain Python functions a specific resource can plug in,
  to run extra logic without special-casing that resource's whole router.
  This is how a handful of business rules got layered on top of otherwise
  generic CRUD:
  - `risk_pre_update` — the **segregation-of-duties gate**: a Risk that
    breaches its configured appetite threshold can't be moved to `Monitor`
    (i.e. self-accepted) by the very same person it's assigned to. Someone
    else has to sign off.
  - `issue_pre_update` — the **CAPA gate**: an Issue can't be set to
    `Closed` unless both `root_cause` and `corrective_action` are already
    filled in.
  - `attach_breach_flags` (a `post_fetch` hook on Risks) — computes
    `breaches_appetite` fresh on every read by comparing the Risk's score
    against the applicable `RiskAppetiteThreshold` rows; this is *not* a
    stored column, so it can never go stale.
  - `assessment_post_create` (a `post_create` hook on RiskAssessments) —
    the moment a new assessment is created against a template, it
    automatically creates one blank `AssessmentResponse` row per question
    on that template, ready to be filled in.
  - `department_scoped=True` (on Entities, Risks, Controls) — restricts
    what a logged-in non-admin user can even *see* to records in their own
    department, unless their role is Administrator or Compliance Manager
    — a lightweight multi-tenancy rule.
- **Audit logging happens inside `update_item`/`delete_item` directly** —
  every changed field on an update, and every delete, writes an
  `AuditLog` row (see `models.py` above), automatically, for every table
  that goes through this router. `changed_by` comes from an `X-User`
  request header the frontend can set, defaulting to `"system"`.

### The bulk import/export router — the same factory pattern again

```python
def build_bulk_router(*, model, create_schema, prefix, tag, columns) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("/export")
    def export_csv(db): ...   # streams every row back as a CSV file

    @router.post("/import")
    def import_csv(file: UploadFile = File(...), db): ...  # reads an uploaded CSV, creates rows
    return router
```

Same idea as the CRUD factory, applied to CSV import/export, registered
only for Risks, Controls, and Entities. It's registered **before** the
generic CRUD routers on purpose — otherwise a request to
`/api/v1/risks/export` could get mistakenly matched by the generic
`/api/v1/risks/{item_id}` route (treating the word `export` as if it were
an ID) instead of the intended export endpoint. Route-ordering like this
is a common gotcha in every web framework, not specific to FastAPI.

### The hand-written custom endpoints

Everything below the CRUD/bulk router setup is a one-off endpoint that
doesn't fit the generic shape — each is a plain function with a
`@app.get(...)` / `@app.post(...)` decorator, the same decorator pattern
explained in [Your Toolbox](01-your-toolbox.html). Grouped by what they
do:

- **Auth** — `POST /api/v1/auth/login` (checks the password, returns a
  JWT) and `GET /api/v1/auth/me` (returns whoever the current token
  belongs to).
- **Assessment submission** — `POST
  /api/v1/risk-assessments/{id}/submit` — takes a list of question
  answers, computes a **weighted average** score (`Σ(answer × question
  weight) / Σ(weights)`), saves each answer as an `AssessmentResponse`,
  and marks the assessment `Completed`. This is what both the `/assessor`
  frontend page and the `assessor_agent.py` script actually call.
- **Recurring assessments** — `POST
  /api/v1/assessments/generate-recurring` — for any template with a
  `recurrence_rule` (`quarterly`/`annual`), finds risks whose last
  completed assessment is now overdue and creates a fresh
  `Not Started` assessment for each.
- **Restart assessments** — `POST /api/v1/risks/{id}/restart-assessments`
  and the `/entities/{id}/...` equivalent — resets assessment(s) back to
  `Not Started` in place (blanking answers rather than deleting rows), so
  they can be retaken.
- **Scoring preview** — `GET
  /api/v1/risk-methodologies/{id}/preview-score` — given a likelihood and
  impact, returns the score and which band it falls in for that specific
  methodology, without needing an actual Risk to exist yet.
- **Evidence attachments** — upload/list/download/delete files, stored on
  disk under `backend/uploads/<record_type>/<record_id>/`, tracked as
  `EvidenceAttachment` rows. `uuid.uuid4().hex` is used to prefix the
  stored filename so two different uploads can never collide on disk even
  if the original filenames match.
- **Vendor lifecycle** — `GET /api/v1/entities/vendors/overdue` — vendors
  whose contract has ended or whose last due-diligence review is over a
  year old.
- **Notifications** — `POST /api/v1/notifications/run-check` scans for
  overdue Tasks/Mitigations and creates an in-app `Notification` for each
  (skipping ones already created, so re-running the check is safe);
  `GET /notifications/mine` and `POST /{id}/read` round it out. There's no
  outbound email/Slack — this is in-app only.
- **Control testing** — `POST /api/v1/simulation/trigger-test` — runs
  `control_testing.run_test()` (see above) against one Control or every
  `Monitor`-status Control, records a `ControlTestResult`, and
  auto-creates a High-priority `Issue` for any that fail.
- **Reporting** — `GET /api/v1/reports/risk-summary` (the JSON numbers
  behind the dashboard's stat cards), `.../pdf` (the same data rendered as
  a downloadable PDF via the `fpdf2` library), `.../history` (trend
  snapshots saved by `POST /reports/snapshot`), and `GET
  /api/v1/dashboard/stats` (the four numbers on the home page's live
  banner).
- **Audit trail** — `GET /api/v1/audit-logs`, read-only, filterable by
  table/record — the only way `AuditLog` rows are ever read back out.

## `init_db.py` — seeding demo data

```python
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
...
users = [User(username=f"user.{i:03d}", ..., role_id=roles[(i - 1) % len(roles)].id, ...) for i in range(1, 21)]
```

Running this file **wipes and rebuilds `grc.db` from scratch**
(`drop_all` then `create_all`), then inserts realistic-looking demo data:
20 users cycling deterministically through every role (so `user.005`,
`010`, `015`, `020` are guaranteed to be Administrators — the `% 5`
arithmetic is what guarantees the cycle), 10 departments, 50 entities, 50
risks, 50 controls, ~50 issues, a full assessment template with 5
weighted questions and a 1–5 Likert scale of answer options, and 50
assessment records. Every seeded user's password is `changeme123` — set
once via `auth.hash_password(...)` and reused for all of them. This is
this project's version of an `Load Data`/fix-script combo you might run
once against a fresh instance.

The `for i in range(1, 51): ...` construct here is Python's **`for`
loop** — "run the code below once for each number from 1 up to (not
including) 51," i.e. 50 times. `[expr for x in range(...)]` — a **list
comprehension** — is a compact way of writing "build a list by running
this expression once per item"; you'll see it throughout this file and
the rest of the codebase as a shorthand for a `for` loop that builds up a
list.

## `reporting_agent.py` — a standalone summary printout

This one small script (run manually, from inside `backend/`, with
`python reporting_agent.py`) connects to the database directly (not
through the HTTP API) and prints a formatted executive summary to the
terminal — total risks/controls/issues, average inherent vs. residual
score, and open critical/high issue counts. It's a simpler, offline
cousin of the `/api/v1/reports/risk-summary` endpoint, useful for a quick
terminal-only sanity check without needing the server running.

---
[← Architecture Overview](02-architecture-overview.html) · [Next: Frontend Deep Dive →](04-frontend-deep-dive.html)
