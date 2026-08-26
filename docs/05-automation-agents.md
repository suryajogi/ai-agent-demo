---
layout: default
title: The Automation Agents
---

# The Automation Agents

[← Frontend Deep Dive](04-frontend-deep-dive.html)

Six Python files sit at the repo root, outside `backend/` and `frontend/`.
None of them are part of the running application — each is a standalone
program you run once, by hand, from the terminal (`python
<filename>.py`), the way you might run a one-off Background Script in
ServiceNow. They share a consistent shape: a small class taking a
`root_dir`, one clearly-named method doing the real work, status messages
prefixed with an emoji, and an `if __name__ == "__main__":` block at the
bottom (see [Your Toolbox](01-your-toolbox.html) if that line is
unfamiliar).

Two of them talk to a locally-run open-source AI model via a tool called
**Ollama** (`ollama.chat(model='llama3', ...)`) — this is a way of
running an LLM entirely on your own machine, no API key or internet
service required, as opposed to calling a hosted service like the Claude
or Gemini APIs. If you haven't installed Ollama and pulled the `llama3`
model, those two scripts simply won't run — this is noted per-script
below.

## `end_user_agent.py` and `assessor_agent.py` — simulating real users

These two are the simplest to reason about: they're plain HTTP clients,
using the **`httpx`** Python library, that log into the **already
running** backend exactly the way a browser would — over the network,
using real seeded credentials, hitting the real `/api/v1/auth/login`
endpoint — and then make real `POST` requests to create data or submit
assessments.

```python
def login(client: httpx.Client, username: str) -> str:
    resp = client.post(f"{API}/api/v1/auth/login", json={"username": username, "password": DEMO_PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]
```

Because these scripts go through the real HTTP API rather than touching
the database directly, they exercise the **real** authentication, role
checks, and validation — exactly as if a person had clicked through the
UI. `end_user_agent.py` picks a few random active users and, for each,
creates a realistic Risk → Control → Issue chain from a small set of
canned scenarios (VPN patching, shared credentials, vendor data
retention). `assessor_agent.py` instead logs in as Assessor/Administrator
users, finds their open (`Not Started`) assessments, and submits random
but plausible answers to each question, calling the same submit endpoint
`app/assessor/page.tsx` uses.

**Prerequisite**: the backend must already be running (`uvicorn main:app
--port 8050`, or `fastapi dev main.py --port 8050` — see [Running It
Yourself](06-running-locally.html)) before either of these will do
anything.

## `summary_email_agent.py` — drafting (not sending) an executive email

Pulls the live `/api/v1/reports/risk-summary` JSON and the PDF report
from the running backend, composes an email around them using Python's
built-in `email.message.EmailMessage`, and — **by default** — only saves
the result as a real `.eml` file under `reports/`, openable in any mail
client, without sending anything anywhere.

```python
parser.add_argument("--send", action="store_true", help="Actually send via SMTP (requires SMTP_* env vars)")
...
if args.send:
    host, port, user, password = (os.environ.get("SMTP_HOST"), ...)
    if not all([host, port, user, password]):
        print("❌ --send requested but SMTP_HOST/... are not all set. Not sending.")
        return
    with smtplib.SMTP(host, int(port)) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
```

Sending real mail requires **both** passing `--send` on the command line
**and** having `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASS` set as
environment variables — this double gate is deliberate: dispatching mail
on someone's behalf should always be something a human opts into
explicitly, never a side effect of just running a report.

## `product_owner_agent.py` — proposing new backlog candidates via a local LLM

Reads the original `requirements.docx` (using the `python-docx` library)
and the current table names straight out of `backend/models.py` (via a
regular expression matching `__tablename__ = "..."`, so the prompt always
reflects the *actual* current schema, not a hand-maintained description
that could drift out of date), then asks a local `llama3` model — via
Ollama — to propose up to 5 new requirements that address a **concrete
gap** in the current schema, avoiding anything already proposed.

The important design detail here is that this script is **safe by
construction**: it only ever *appends* new rows to
`PRODUCT_BACKLOG_CANDIDATES.csv`, and only after strictly validating the
model's output is well-formed JSON containing every required field. A
malformed response, or a failure to reach Ollama at all, aborts the run
and leaves the CSV completely untouched — existing rows, and any
`status` a human reviewer has already set on them, are never modified or
overwritten.

## `agentic_workflow.py` — full autonomy, and why it's flagged as risky

This is the one script in the set the project's own documentation singles
out explicitly: *"an experimental full-autonomy pipeline that regenerates
`backend/main.py` via a local model and auto-commits/pushes to `main`
with no review gate — higher risk than the scripts above; not a template
to copy for new automation."*

Reading `run_workflow_loop()` explains exactly why:

```python
prompt = f"Modify this Python FastAPI code to support these backlog requirements: ...\n\nCurrent code:\n{current_code}\n..."
response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
...
with open(main_py_path, "w") as f:
    f.write(clean_code)
...
if is_safe_to_merge:
    self.run_command("git add .", cwd=self.root_dir)
    self.run_command('git commit -m "feat(local-ai): automated build via clean local AI flow"', cwd=self.root_dir)
    self.run_command("git checkout main", cwd=self.root_dir)
    self.run_command(f"git merge {branch_name}", cwd=self.root_dir)
    self.run_command("git push origin main", cwd=self.root_dir)
```

It asks a local model to **rewrite `backend/main.py` in place**, based on
whatever's currently in `PRODUCT_BACKLOG.md`, with essentially no
structural guardrails on the model's output beyond a crude line-filter
meant to strip conversational chatter and markdown fences out of the
response. Its idea of "testing" the result (`run_qa_tests`) is just
re-running `init_db.py` and checking it didn't crash — that confirms the
database schema still loads, not that the API still behaves correctly.
If that weak check passes, it **commits and pushes straight to `main`
with no human review at any point** — the automation both writes the
change and approves it. If the check fails, its idea of recovery is
`git checkout main` — abandoning the changes on the feature branch,
rather than genuinely fixing anything.

This is a useful file to read specifically because it's an example of
what "agentic automation" looks like when the guardrails a real
production pipeline needs (real tests, a required human review step, a
protected branch, a rollback plan beyond "abandon the branch") are
missing — worth understanding critically, not worth copying as a
template for automation of your own.

## `documentation_agent.py` — this project's own `ARCHITECTURE.md` generator

The simplest of the six: walks the repo's own folder structure (skipping
`.git`, `.venv`, `node_modules`, and a few other noise folders), and
writes out `ARCHITECTURE.md` from a hardcoded Markdown template combined
with that live directory tree. `.github/workflows/doc-update.yml` reruns
this script automatically on every push to `main` and commits the
refreshed file back if it changed — a small, low-risk example of CI
automation, worth contrasting directly against `agentic_workflow.py`
above: this one only ever touches one clearly-scoped, easily-reviewed
file, and regenerating it from a template is fully deterministic (same
inputs always produce the same output), unlike an LLM rewriting arbitrary
application code.

---
[← Frontend Deep Dive](04-frontend-deep-dive.html) · [Next: Running It Yourself →](06-running-locally.html)
