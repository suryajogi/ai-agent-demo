---
layout: default
title: Frontend Deep Dive
---

# Frontend Deep Dive

[← Backend Deep Dive](03-backend-deep-dive.html)

Everything on this page lives in `frontend/`. Before the code, three
concepts this entire folder is built on.

## Three ideas you need before any of this makes sense

### TypeScript is JavaScript with a type checker bolted on

**JavaScript** is the programming language every web browser runs.
**TypeScript** is JavaScript plus optional type annotations, which get
checked *before* the code ever runs (and stripped out afterward — the
browser never sees them). Every `.ts`/`.tsx` file in this project is
TypeScript.

```typescript
export interface Risk {
  id: number;
  name: string;
  description: string | null;
  breaches_appetite: boolean;
}
```

An `interface` like this describes the *shape* of an object — "a `Risk`
is guaranteed to have these exact fields, of these exact types." Compare
this directly to `backend/schemas.py`'s `RiskRead` Pydantic class — it's
the same shape, hand-mirrored in TypeScript, so the frontend knows at
write-time (not just when something breaks at runtime) whether it's
using a field that doesn't exist, or treating a number as a string. This
mirroring is manual here (there's no shared code generator linking the
two), so if the backend schema changes, someone has to update
`frontend/lib/api.ts` to match by hand.

### React: the UI is a function of state

**React** is the library this whole frontend is built with. Its core idea:
you don't write step-by-step instructions for how to update the screen
(hide this, show that, append a row) — you write a function that
describes *what the screen should look like right now*, given the current
data, and React figures out what actually changed and updates only that.
A **component** is one such function — e.g. `StatCard` below always
returns the same UI shape for whatever `label`/`value` it's given:

```tsx
function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border ...">
      <p className="text-xs ...">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
```

The mixture of TypeScript and HTML-like tags (`<div>...</div>`) inside a
function is called **JSX** — it looks like HTML but it's actually
JavaScript; `{label}` and `{value}` are "drop the value of this
variable in right here." `className` is JSX's name for HTML's `class`
attribute (renamed because `class` is already a reserved JavaScript
keyword).

**State** is data a component remembers between renders and that, when
changed, causes React to re-render — the `useState` hook you'll see
everywhere is how a component declares a piece of state:

```tsx
const [tab, setTab] = useState<Tab>("risks");
```

This declares a variable `tab` (currently `"risks"`) and a function
`setTab` used to change it. Calling `setTab("controls")` doesn't just
update the variable — it tells React "re-run this component's render
function, because something it depends on changed," and the screen
updates to match. This is the fundamental loop behind every interactive
piece of this UI: click something → call a `set...` function → React
re-renders → the screen reflects the new state. `useEffect` (also used
throughout) is a hook for running code in reaction to a component
appearing on screen or a value changing — e.g. `WorkspacePage` uses it to
fetch all the dashboard data once, right when the page first loads.

### Next.js: folders are routes, and `"use client"` matters

**Next.js** is a framework built on top of React that adds, among other
things, **file-based routing**: the folder structure under `frontend/app/`
directly determines the site's URLs (already covered in [Architecture
Overview](02-architecture-overview.html)) — no separate routing
configuration file exists to go find.

The `"use client";` line at the top of almost every file in this project
is a Next.js-specific marker meaning "this component needs to run in the
browser" (because it uses `useState`, click handlers, `localStorage`,
etc.) — Next.js can also render components entirely on the server with no
interactivity at all, but nothing in this particular app's UI does that;
everything here is a client component.

## `lib/api.ts` — the one file every screen talks to the backend through

No component in this project calls `fetch(...)` directly against the
backend — they all go through this one file, which exists for three
reasons: attach the auth token automatically, centralize error handling,
and be the single place the TypeScript types mirroring `schemas.py` live.

```typescript
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8050";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${init?.method ?? "GET"} ${path} failed (${res.status}): ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const apiGet = <T>(path: string) => request<T>(path);
export const apiPost = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });
```

`fetch` is the browser's built-in function for making an HTTP request —
the JavaScript-side counterpart to the HTTP concepts explained in
[Architecture Overview](02-architecture-overview.html). `request<T>` is a
**generic function** — `T` is a placeholder type, filled in by whoever
calls it (`apiGet<Risk[]>("/api/v1/risks")` means "call this, and treat
the JSON response as an array of `Risk`"). `getToken()` reads the JWT out
of the browser's `localStorage` (where `login()`, further down the file,
stored it after a successful sign-in) and attaches it as the
`Authorization: Bearer <token>` header — this is the frontend half of the
auth flow explained in [Backend Deep Dive → auth.py](03-backend-deep-dive.html).
`async`/`await` here mean exactly what they meant in the Python backend:
"this call might take a moment (it's a real network request); pause this
function here without freezing the whole page, and continue once the
response arrives."

Below `request`, the rest of the file is: thin wrapper functions
(`apiGet`/`apiPost`/`apiPut`/`apiDelete`, plus `apiUpload`/`apiDownload`
for file transfers that can't use plain JSON), the `login`/`logout`
session helpers, and a long list of TypeScript `interface`s — one per
backend schema (`Risk`, `Control`, `Issue`, `Entity`, `Department`, and
so on) — that must be kept in sync by hand with `backend/schemas.py`.

## `app/page.tsx` — the home page

The simplest page in the app: a heading, a live `<MetricBanner />`
(fetches `/api/v1/dashboard/stats` and renders the four running counts),
and two link cards to `/workspace` and `/assessor`. Worth noting only
because it demonstrates the absolute minimum shape of a page component —
everything else in this section is a more elaborate version of the same
idea.

## `app/login/page.tsx` — signing in

A standard controlled form: two `useState` fields (`username`,
`password`), a `handleSubmit` function that calls `login(username,
password)` from `lib/api.ts` on submit, and on success, redirects
(`router.push`) to wherever the user was trying to go before being
bounced to `/login` (carried in the `?next=` URL query parameter). The
`Suspense` wrapper around the actual form exists because reading a URL
query parameter (`useSearchParams`) is one of the few things Next.js
requires to be wrapped this way — a framework-specific detail, not
something specific to this app's logic.

## `app/workspace/page.tsx` — Interface A, the main dashboard

This is the largest component in the project (~770 lines), but
structurally it's simpler than it looks — it's six near-identical
sections (one per tab: Risks, Controls, Issues, Departments, Entities,
Assessments) built from the same handful of reusable pieces, defined once
in `app/workspace/ui.tsx`:

- **`Card`** — a titled box wrapping a section of content.
- **`DataTable`** — a sortable table: pass it `rows` and a list of
  `columns` (each with a `header` label, a `render` function saying how
  to display that column for a given row, and an optional `sortValue`
  function enabling click-to-sort on that column), and it handles
  rendering, sorting state, empty-state messaging, and an optional
  per-row delete button, generically, for any data shape.
- **`DetailModal`** — a popup that, given a record and a `renderView` /
  `renderEdit` pair of render functions, shows a read-only view by
  default and flips to an edit form when "Edit" is clicked.
- **`Field`, `inputClass`, `SubmitButton`** — small shared styling
  primitives so every form's inputs and buttons look identical without
  repeating the same CSS class strings everywhere.

`WorkspacePage` itself is mostly **state declarations** (one `useState`
per data type — `risks`, `controls`, `issues`, etc. — and one per
"currently viewing this record in a modal" flag), a `reload()` function
that fires all the initial `apiGet` calls in parallel via
`Promise.all([...])` when the page first loads (inside a `useEffect`),
and then, per tab, a `<Card>` containing a `*Form` component (for
creating a new record) and a `<DataTable>` (for browsing existing ones).
Clicking a row opens a `<DetailModal>` for that record; saving in the
modal updates the corresponding state array in place (e.g. `setRisks(prev
=> prev.map(r => r.id === updated.id ? updated : r))` — "replace the one
record that changed, leave everything else untouched," which is the
standard React pattern for updating one item inside a list of state).

A few features worth calling out specifically because they map onto
requirements you'll recognize from `CLAUDE.md`/`ARCHITECTURE.md`:

- The **Risk Heatmap** (`RiskHeatmap.tsx`) is a clickable
  likelihood-×-impact grid; clicking a cell filters the Risks table down
  to just that combination via the `heatmapFilter` state.
- **CSV import/export** buttons on Risks/Controls/Entities call
  `apiDownload`/`apiUpload` directly against the bulk router endpoints
  described in [Backend Deep Dive](03-backend-deep-dive.html).
- **"Restart assessments"** buttons inside the Risk/Entity detail modals
  call the corresponding `/restart-assessments` backend endpoint.
- The **appetite-breach badge** on the Risks table simply reads
  `r.breaches_appetite` — a field the backend computes fresh on every
  fetch (see `attach_breach_flags` in the backend deep dive), not
  anything the frontend calculates itself.

### `RiskForm.tsx` — the pattern every other `*Form.tsx` follows

Every form component (`RiskForm`, `ControlForm`, `IssueForm`,
`EntityForm`, `DepartmentForm`, `AssessmentLauncherForm`) follows this
exact same shape, so understanding one means understanding all six:

```tsx
export function RiskForm({ entities, record, onSaved, onCancel }: {...}) {
  const isEdit = !!record;
  const [form, setForm] = useState({
    name: record?.name ?? "",
    entity_id: record?.entity_id != null ? String(record.entity_id) : "",
    ...
  });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const payload = { name: form.name, entity_id: form.entity_id ? Number(form.entity_id) : null, ... };
    const saved = isEdit
      ? await apiPut<Risk>(`/api/v1/risks/${record!.id}`, payload)
      : await apiPost<Risk>("/api/v1/risks", payload);
    onSaved(saved);
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2">
      <Field label="Name"><input required value={form.name} onChange={...} /></Field>
      ...
      <SubmitButton disabled={submitting}>{isEdit ? "Save Changes" : "Create Risk"}</SubmitButton>
    </form>
  );
}
```

- The **same component handles both creating and editing** — `isEdit =
  !!record` (true if a `record` prop was passed in, false otherwise)
  decides whether submitting calls `apiPost` (create) or `apiPut` (edit
  this specific ID), and it's what the surrounding page passes in: with
  no `record` prop for "Create Risk," with one for the edit form inside
  `DetailModal`.
- **Form state is one `useState` object**, one key per field, initialized
  either from the existing record (edit) or blank/sensible defaults
  (create). Every input's `value` is a field on this object and its
  `onChange` calls `setForm({ ...form, fieldName: e.target.value })` —
  "keep every other field as-is, just replace this one" (`...form` is
  JavaScript's **spread syntax**, copying all existing keys before the
  explicit override).
- **HTML inputs only ever produce strings**, so numeric/optional fields
  get explicitly converted back (`Number(form.entity_id)`) and empty
  strings mapped to `null` right before sending — matching what
  `schemas.py`'s `Optional[int]` fields expect on the backend.
- `onSaved` is a callback passed down from the parent page — the form
  itself never touches the parent's state array directly; it just reports
  "here's the saved record" upward, and the parent (`WorkspacePage`)
  decides what to do with it. This one-directional flow — data down via
  props, changes reported up via callbacks — is React's standard pattern
  and shows up throughout this codebase.

## `app/assessor/page.tsx` — Interface B, the questionnaire portal

Not detailed line-by-line here since it follows patterns already covered
above, but conceptually: a self-declared-identity flow (the assessor
picks their own name from a dropdown of seeded users rather than logging
in with a password) that fetches that user's open `RiskAssessment`s,
presents each one's questions from its `AssessmentTemplate`, and submits
answers through the exact same `POST
/api/v1/risk-assessments/{id}/submit` endpoint that `assessor_agent.py`
drives from the command line (see [The Automation Agents](05-automation-agents.html))
— both are just different clients of the same backend endpoint.

---
[← Backend Deep Dive](03-backend-deep-dive.html) · [Next: The Automation Agents →](05-automation-agents.html)
