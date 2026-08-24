# Tests

Reserved for automated tests per the recommended project structure in
`PRODUCT_BACKLOG.md`. Nothing here yet — the backend and frontend are currently
verified manually (`backend/init_db.py` + `uvicorn`, `npx tsc --noEmit`, `npx eslint`,
and live browser checks against the running app).

Suggested first tests when this is picked up:
- `backend/`: pytest against the FastAPI app (CRUD round-trips, `submit_assessment`
  scoring, the control-testing simulator, audit-log field diffs on update/delete).
- `frontend/`: component tests for the workspace forms and the risk heatmap filter.
