import csv
import io
import logging
import os
import random
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Callable, Optional, Type

from fastapi import (
    APIRouter,
    Body,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fpdf import FPDF
from pydantic import BaseModel
from sqlalchemy import inspect as sa_inspect, or_
from sqlalchemy.orm import Session

import auth
import control_testing
import models
import scoring
import schemas
from database import Base, engine, get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("ai_agent_demo")

# Ensure the schema exists even if init_db.py has not been run yet.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ServiceNow GRC Risk Management Replication API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)


@app.exception_handler(Exception)
async def log_unhandled_exceptions(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello World"}


# ---------------------------------------------------------------------------
# Auth (NR-012) — protects writes; GET endpoints stay open on purpose so the
# read-only dashboard keeps working without a login.
# ---------------------------------------------------------------------------

auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@auth_router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)) -> Any:
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not user.password_hash or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.active:
        raise HTTPException(status_code=401, detail="User is inactive")
    return schemas.Token(access_token=auth.create_token(user), user=user)


@auth_router.get("/me", response_model=schemas.UserRead)
def me(current_user: models.User = Depends(auth.require_user)) -> Any:
    return current_user


app.include_router(auth_router)


# ---------------------------------------------------------------------------
# Risk appetite (NR-005) helpers — shared by the Risk read serializer and the
# segregation-of-duties gate (NR-006), so both agree on what "breaches
# appetite" means.
# ---------------------------------------------------------------------------


def _applicable_thresholds(
    thresholds: list["models.RiskAppetiteThreshold"], category: Optional[str], department_id: Optional[int]
) -> list["models.RiskAppetiteThreshold"]:
    return [
        t
        for t in thresholds
        if (t.category is None or t.category == category)
        and (t.department_id is None or t.department_id == department_id)
    ]


def _risk_score(likelihood: Optional[int], impact: Optional[int]) -> Optional[int]:
    return likelihood * impact if likelihood is not None and impact is not None else None


def attach_breach_flags(risks: list["models.Risk"], db: Session) -> None:
    thresholds = db.query(models.RiskAppetiteThreshold).all()
    for risk in risks:
        score = _risk_score(risk.residual_likelihood, risk.residual_impact) or _risk_score(
            risk.inherent_likelihood, risk.inherent_impact
        )
        category = risk.statement.category if risk.statement else None
        department_id = risk.entity.department_id if risk.entity else None
        applicable = _applicable_thresholds(thresholds, category, department_id)
        risk.breaches_appetite = bool(
            score is not None and applicable and score > min(t.max_acceptable_score for t in applicable)
        )


def compute_risk_breach_from_data(data: dict, db: Session) -> bool:
    score = _risk_score(data.get("residual_likelihood"), data.get("residual_impact")) or _risk_score(
        data.get("inherent_likelihood"), data.get("inherent_impact")
    )
    if score is None:
        return False
    category = None
    if data.get("statement_id"):
        stmt = db.get(models.RiskStatement, data["statement_id"])
        category = stmt.category if stmt else None
    department_id = None
    if data.get("entity_id"):
        ent = db.get(models.Entity, data["entity_id"])
        department_id = ent.department_id if ent else None
    thresholds = db.query(models.RiskAppetiteThreshold).all()
    applicable = _applicable_thresholds(thresholds, category, department_id)
    return bool(applicable and score > min(t.max_acceptable_score for t in applicable))


def risk_pre_update(item: "models.Risk", data: dict, db: Session, current_user: Optional["models.User"]) -> None:
    """Segregation-of-duties gate (NR-006): a risk that breaches appetite can't
    be self-approved into Monitor by the same person it's assigned to."""
    if data.get("state") != "Monitor" or not compute_risk_breach_from_data(data, db):
        return
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required to accept a risk that breaches appetite")
    assignee = data.get("assigned_to")
    if assignee and assignee == current_user.username:
        raise HTTPException(
            status_code=403,
            detail="Segregation of duties: the risk owner cannot self-approve a Monitor transition "
            "for a risk that breaches the configured appetite threshold.",
        )


def issue_pre_update(item: "models.Issue", data: dict, db: Session, current_user: Optional["models.User"]) -> None:
    """CAPA gate (NR-004): can't close an issue with no root cause / corrective action on file."""
    if data.get("state") == "Closed" and not (data.get("root_cause") and data.get("corrective_action")):
        raise HTTPException(
            status_code=422,
            detail="Cannot close an issue without both root_cause and corrective_action recorded.",
        )


def assessment_post_create(item: "models.RiskAssessment", db: Session) -> None:
    """Instantiates a blank AssessmentResponse per template question (NR-010's
    prerequisite — the original requirements doc calls for this on every
    assessment, manual or recurring; it was never wired up before)."""
    if not item.template_id:
        return
    questions = (
        db.query(models.AssessmentQuestion)
        .filter(models.AssessmentQuestion.template_id == item.template_id)
        .all()
    )
    for question in questions:
        db.add(
            models.AssessmentResponse(
                assessment_id=item.id, question_id=question.id, selected_value=None, justification=None
            )
        )


# ---------------------------------------------------------------------------
# Generic CRUD router factory
#
# Every GRC table gets list/get/create/update/delete endpoints. List
# endpoints support filtering by any real column via query string, free-text
# search via `q` (NR-014), and return X-Total-Count. Writes require
# authentication (NR-012); `write_roles`/`delete_roles` narrow further.
# Optional hooks (`pre_create`, `pre_update`, `post_create`, `post_fetch`)
# let individual resources plug in validation/side effects/enrichment
# without special-casing them in the router itself.
# ---------------------------------------------------------------------------

SEARCHABLE_COLUMNS = ("name", "title", "description")


def build_crud_router(
    *,
    model: Type[Any],
    create_schema: Type[BaseModel],
    read_schema: Type[BaseModel],
    prefix: str,
    tag: str,
    write_roles: Optional[list[str]] = None,
    delete_roles: Optional[list[str]] = None,
    pre_create: Optional[Callable[[dict, Session, Optional["models.User"]], Optional[dict]]] = None,
    pre_update: Optional[Callable[[Any, dict, Session, Optional["models.User"]], None]] = None,
    post_create: Optional[Callable[[Any, Session], None]] = None,
    post_fetch: Optional[Callable[[list, Session], None]] = None,
    department_scoped: bool = False,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])
    resource = model.__name__
    mapper = sa_inspect(model)
    search_columns = [c for c in SEARCHABLE_COLUMNS if c in mapper.columns]

    write_dependency = auth.require_roles(*write_roles) if write_roles else auth.require_user
    delete_dependency = auth.require_roles(*delete_roles) if delete_roles else write_dependency

    def _apply_department_scope(query, current_user: Optional["models.User"]):
        if not department_scoped or current_user is None or current_user.department_id is None:
            return query
        role_name = current_user.role.name if current_user.role else None
        if role_name in ("Administrator", "Compliance Manager"):
            return query
        if "department_id" in mapper.columns:
            return query.filter(model.department_id == current_user.department_id)
        if "entity_id" in mapper.columns:
            dept_entity_ids = [
                row[0]
                for row in query.session.query(models.Entity.id).filter(
                    models.Entity.department_id == current_user.department_id
                )
            ]
            return query.filter(model.entity_id.in_(dept_entity_ids))
        return query

    @router.get("", response_model=list[read_schema])
    def list_items(
        request: Request,
        response: Response,
        skip: int = 0,
        limit: int = 200,
        q: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(auth.get_current_user),
    ) -> list[Any]:
        query = db.query(model)
        for key, value in request.query_params.items():
            if key in ("skip", "limit", "q") or key not in mapper.columns:
                continue
            column = mapper.columns[key]
            try:
                casted = column.type.python_type(value)
            except (TypeError, ValueError):
                continue
            query = query.filter(column == casted)
        if q and search_columns:
            like = f"%{q}%"
            query = query.filter(or_(*[getattr(model, col).ilike(like) for col in search_columns]))
        query = _apply_department_scope(query, current_user)
        response.headers["X-Total-Count"] = str(query.count())
        items = query.offset(skip).limit(limit).all()
        if post_fetch:
            post_fetch(items, db)
        return items

    @router.get("/{item_id}", response_model=read_schema)
    def get_item(item_id: int, db: Session = Depends(get_db)) -> Any:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{resource} {item_id} not found")
        if post_fetch:
            post_fetch([item], db)
        return item

    @router.post("", response_model=read_schema, status_code=201, dependencies=[Depends(write_dependency)])
    def create_item(
        payload: create_schema,  # type: ignore[valid-type]
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(auth.get_current_user),
    ) -> Any:
        data = payload.model_dump()
        if pre_create:
            data = pre_create(data, db, current_user) or data
        item = model(**data)
        db.add(item)
        db.commit()
        db.refresh(item)
        if post_create:
            post_create(item, db)
            db.commit()
            db.refresh(item)
        if post_fetch:
            post_fetch([item], db)
        return item

    @router.put("/{item_id}", response_model=read_schema, dependencies=[Depends(write_dependency)])
    def update_item(
        item_id: int,
        payload: create_schema,  # type: ignore[valid-type]
        request: Request,
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = Depends(auth.get_current_user),
    ) -> Any:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{resource} {item_id} not found")
        data = payload.model_dump()
        if pre_update:
            pre_update(item, data, db, current_user)
        changed_by = request.headers.get("X-User", "system")
        for field, value in data.items():
            old_value = getattr(item, field, None)
            if old_value != value:
                db.add(
                    models.AuditLog(
                        table_name=model.__tablename__,
                        record_id=item_id,
                        action="updated",
                        field_name=field,
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(value) if value is not None else None,
                        changed_by=changed_by,
                    )
                )
            setattr(item, field, value)
        if hasattr(item, "updated_at"):
            item.updated_at = datetime.now()
        db.commit()
        db.refresh(item)
        if post_fetch:
            post_fetch([item], db)
        return item

    @router.delete("/{item_id}", status_code=204, dependencies=[Depends(delete_dependency)])
    def delete_item(item_id: int, request: Request, db: Session = Depends(get_db)) -> None:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{resource} {item_id} not found")
        changed_by = request.headers.get("X-User", "system")
        db.add(
            models.AuditLog(
                table_name=model.__tablename__,
                record_id=item_id,
                action="deleted",
                changed_by=changed_by,
            )
        )
        db.delete(item)
        db.commit()
        return None

    return router


ADMIN_ROLES = ["Administrator", "Compliance Manager"]

CRUD_RESOURCES = [
    dict(model=models.Role, create_schema=schemas.RoleCreate, read_schema=schemas.RoleRead, prefix="/api/v1/roles", tag="roles", write_roles=["Administrator"], delete_roles=["Administrator"]),
    dict(model=models.User, create_schema=schemas.UserCreate, read_schema=schemas.UserRead, prefix="/api/v1/users", tag="users", write_roles=["Administrator"], delete_roles=["Administrator"]),
    dict(model=models.Department, create_schema=schemas.DepartmentCreate, read_schema=schemas.DepartmentRead, prefix="/api/v1/departments", tag="departments", delete_roles=ADMIN_ROLES),
    dict(model=models.Entity, create_schema=schemas.EntityCreate, read_schema=schemas.EntityRead, prefix="/api/v1/entities", tag="entities", delete_roles=ADMIN_ROLES, department_scoped=True),
    dict(model=models.RiskScope, create_schema=schemas.RiskScopeCreate, read_schema=schemas.RiskScopeRead, prefix="/api/v1/risk-scopes", tag="risk-scopes", delete_roles=ADMIN_ROLES),
    dict(model=models.RiskMethodology, create_schema=schemas.RiskMethodologyCreate, read_schema=schemas.RiskMethodologyRead, prefix="/api/v1/risk-methodologies", tag="risk-methodologies", delete_roles=ADMIN_ROLES),
    dict(model=models.RiskFramework, create_schema=schemas.RiskFrameworkCreate, read_schema=schemas.RiskFrameworkRead, prefix="/api/v1/risk-frameworks", tag="risk-frameworks", delete_roles=ADMIN_ROLES),
    dict(model=models.RiskStatement, create_schema=schemas.RiskStatementCreate, read_schema=schemas.RiskStatementRead, prefix="/api/v1/risk-statements", tag="risk-statements", delete_roles=ADMIN_ROLES),
    dict(model=models.Risk, create_schema=schemas.RiskCreate, read_schema=schemas.RiskRead, prefix="/api/v1/risks", tag="risks", delete_roles=ADMIN_ROLES, pre_update=risk_pre_update, post_fetch=attach_breach_flags, department_scoped=True),
    dict(model=models.RiskAssessment, create_schema=schemas.RiskAssessmentCreate, read_schema=schemas.RiskAssessmentRead, prefix="/api/v1/risk-assessments", tag="risk-assessments", delete_roles=ADMIN_ROLES, post_create=assessment_post_create),
    dict(model=models.RiskTask, create_schema=schemas.RiskTaskCreate, read_schema=schemas.RiskTaskRead, prefix="/api/v1/risk-tasks", tag="risk-tasks", delete_roles=ADMIN_ROLES),
    dict(model=models.Project, create_schema=schemas.ProjectCreate, read_schema=schemas.ProjectRead, prefix="/api/v1/projects", tag="projects", delete_roles=ADMIN_ROLES),
    dict(model=models.Control, create_schema=schemas.ControlCreate, read_schema=schemas.ControlRead, prefix="/api/v1/controls", tag="controls", delete_roles=ADMIN_ROLES, department_scoped=True),
    dict(model=models.Issue, create_schema=schemas.IssueCreate, read_schema=schemas.IssueRead, prefix="/api/v1/issues", tag="issues", delete_roles=ADMIN_ROLES, pre_update=issue_pre_update),
    dict(model=models.RiskMitigation, create_schema=schemas.RiskMitigationCreate, read_schema=schemas.RiskMitigationRead, prefix="/api/v1/risk-mitigations", tag="risk-mitigations", delete_roles=ADMIN_ROLES),
    dict(model=models.AssessmentTemplate, create_schema=schemas.AssessmentTemplateCreate, read_schema=schemas.AssessmentTemplateRead, prefix="/api/v1/assessment-templates", tag="assessment-templates", delete_roles=ADMIN_ROLES),
    dict(model=models.AssessmentQuestion, create_schema=schemas.AssessmentQuestionCreate, read_schema=schemas.AssessmentQuestionRead, prefix="/api/v1/assessment-questions", tag="assessment-questions", delete_roles=ADMIN_ROLES),
    dict(model=models.AssessmentOption, create_schema=schemas.AssessmentOptionCreate, read_schema=schemas.AssessmentOptionRead, prefix="/api/v1/assessment-options", tag="assessment-options", delete_roles=ADMIN_ROLES),
    dict(model=models.AssessmentResponse, create_schema=schemas.AssessmentResponseCreate, read_schema=schemas.AssessmentResponseRead, prefix="/api/v1/assessment-responses", tag="assessment-responses", delete_roles=ADMIN_ROLES),
    dict(model=models.ControlFrameworkMap, create_schema=schemas.ControlFrameworkMapCreate, read_schema=schemas.ControlFrameworkMapRead, prefix="/api/v1/control-framework-map", tag="control-framework-map", delete_roles=ADMIN_ROLES),
    dict(model=models.RiskAppetiteThreshold, create_schema=schemas.RiskAppetiteThresholdCreate, read_schema=schemas.RiskAppetiteThresholdRead, prefix="/api/v1/risk-appetite-thresholds", tag="risk-appetite-thresholds", write_roles=ADMIN_ROLES, delete_roles=ADMIN_ROLES),
]


# ---------------------------------------------------------------------------
# Bulk import / export (NR-013) — registered before the generic CRUD routers
# below so the literal "/export" and "/import" sub-paths match ahead of the
# generic "/{item_id}" route on the same prefix.
# ---------------------------------------------------------------------------


def build_bulk_router(*, model: Type[Any], create_schema: Type[BaseModel], prefix: str, tag: str, columns: list[str]) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("/export")
    def export_csv(db: Session = Depends(get_db)) -> StreamingResponse:
        items = db.query(model).all()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(columns)
        for item in items:
            writer.writerow([getattr(item, col) for col in columns])
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={model.__tablename__}.csv"},
        )

    @router.post("/import", dependencies=[Depends(auth.require_user)])
    def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict[str, Any]:
        raw = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(raw))
        created = 0
        errors: list[str] = []
        for i, row in enumerate(reader, start=2):
            try:
                payload = {col: (row.get(col) or None) for col in columns if col != "id"}
                validated = create_schema(**payload)
                db.add(model(**validated.model_dump()))
                db.flush()
                created += 1
            except Exception as e:  # noqa: BLE001 — surfaced per-row, not raised
                errors.append(f"row {i}: {e}")
        db.commit()
        return {"created": created, "errors": errors}

    return router


BULK_RESOURCES = [
    dict(model=models.Risk, create_schema=schemas.RiskCreate, prefix="/api/v1/risks", tag="risks",
         columns=["name", "description", "statement_id", "entity_id", "assigned_to", "state",
                  "inherent_likelihood", "inherent_impact", "residual_likelihood", "residual_impact"]),
    dict(model=models.Control, create_schema=schemas.ControlCreate, prefix="/api/v1/controls", tag="controls",
         columns=["name", "description", "status", "entity_id", "risk_id"]),
    dict(model=models.Entity, create_schema=schemas.EntityCreate, prefix="/api/v1/entities", tag="entities",
         columns=["name", "type", "department_id", "owner_id", "status", "contract_end_date",
                  "criticality_tier", "last_due_diligence_date"]),
]

for resource in BULK_RESOURCES:
    app.include_router(build_bulk_router(**resource))

for resource in CRUD_RESOURCES:
    app.include_router(build_crud_router(**resource))


# ---------------------------------------------------------------------------
# Assessor Portal: submit a filled-out questionnaire and compute the score
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/risk-assessments/{assessment_id}/submit",
    response_model=schemas.RiskAssessmentWithResponses,
    tags=["risk-assessments"],
    dependencies=[Depends(auth.require_roles("Assessor", "Administrator"))],
)
def submit_assessment(
    assessment_id: int, payload: schemas.AssessmentSubmission, db: Session = Depends(get_db)
) -> Any:
    assessment = db.get(models.RiskAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail=f"RiskAssessment {assessment_id} not found")
    if not payload.answers:
        raise HTTPException(status_code=400, detail="At least one answer is required")
    for answer in payload.answers:
        if not 1 <= answer.selected_value <= 5:
            raise HTTPException(status_code=400, detail="selected_value must be between 1 and 5")

    # Allow resubmission by clearing any prior responses for this assessment.
    db.query(models.AssessmentResponse).filter(
        models.AssessmentResponse.assessment_id == assessment_id
    ).delete()

    question_ids = [answer.question_id for answer in payload.answers]
    questions = (
        db.query(models.AssessmentQuestion)
        .filter(models.AssessmentQuestion.id.in_(question_ids))
        .all()
    )
    weight_by_question = {question.id: question.weight for question in questions}

    weighted_sum = 0.0
    weight_total = 0.0
    for answer in payload.answers:
        weight = weight_by_question.get(answer.question_id, 1.0)
        weighted_sum += answer.selected_value * weight
        weight_total += weight
        db.add(
            models.AssessmentResponse(
                assessment_id=assessment_id,
                question_id=answer.question_id,
                selected_value=answer.selected_value,
                justification=answer.justification,
            )
        )

    assessment.score = round(weighted_sum / weight_total, 2) if weight_total else None
    assessment.state = "Completed"
    db.commit()
    db.refresh(assessment)
    return assessment


# ---------------------------------------------------------------------------
# Recurring Assessments (NR-010)
# ---------------------------------------------------------------------------

RECURRENCE_INTERVALS = {"quarterly": timedelta(days=91), "annual": timedelta(days=365)}


@app.post("/api/v1/assessments/generate-recurring", tags=["risk-assessments"], dependencies=[Depends(auth.require_user)])
def generate_recurring_assessments(db: Session = Depends(get_db)) -> dict[str, int]:
    generated = 0
    templates = (
        db.query(models.AssessmentTemplate)
        .filter(models.AssessmentTemplate.recurrence_rule.in_(list(RECURRENCE_INTERVALS)))
        .all()
    )
    now = datetime.now()
    for template in templates:
        interval = RECURRENCE_INTERVALS[template.recurrence_rule]
        completed = (
            db.query(models.RiskAssessment)
            .filter(
                models.RiskAssessment.template_id == template.id,
                models.RiskAssessment.state == "Completed",
            )
            .all()
        )
        latest_by_risk: dict[int, models.RiskAssessment] = {}
        for a in completed:
            if a.risk_id is None:
                continue
            existing = latest_by_risk.get(a.risk_id)
            if existing is None or a.id > existing.id:
                latest_by_risk[a.risk_id] = a
        for risk_id, last in latest_by_risk.items():
            already_open = (
                db.query(models.RiskAssessment)
                .filter(models.RiskAssessment.risk_id == risk_id, models.RiskAssessment.template_id == template.id, models.RiskAssessment.state != "Completed")
                .first()
            )
            due = (template.last_generated_at or now) + interval
            if already_open or now < due:
                continue
            new_assessment = models.RiskAssessment(
                risk_id=risk_id, template_id=template.id, state="Not Started"
            )
            db.add(new_assessment)
            db.flush()
            assessment_post_create(new_assessment, db)
            generated += 1
        template.last_generated_at = now
    db.commit()
    return {"generated": generated}


# ---------------------------------------------------------------------------
# Restart Assessments — reset assessment(s) back to Not Started so they can
# be retaken, without losing the questionnaire shape (existing answers are
# blanked in place rather than deleted; any question missing a response row
# — e.g. an assessment created before assessment_post_create existed — gets
# one added). Scoped to a single risk, or every risk under an entity.
# ---------------------------------------------------------------------------


def _restart_assessment(assessment: "models.RiskAssessment", db: Session, changed_by: str) -> None:
    old_state = assessment.state
    assessment.state = "Not Started"
    assessment.score = None
    assessment.comments = None
    for response in assessment.responses:
        response.selected_value = None
        response.justification = None
    if assessment.template_id:
        existing_question_ids = {r.question_id for r in assessment.responses}
        questions = (
            db.query(models.AssessmentQuestion)
            .filter(models.AssessmentQuestion.template_id == assessment.template_id)
            .all()
        )
        for question in questions:
            if question.id not in existing_question_ids:
                db.add(
                    models.AssessmentResponse(
                        assessment_id=assessment.id, question_id=question.id,
                        selected_value=None, justification=None,
                    )
                )
    if old_state != "Not Started":
        db.add(
            models.AuditLog(
                table_name="risk_assessments", record_id=assessment.id, action="updated",
                field_name="state", old_value=old_state, new_value="Not Started", changed_by=changed_by,
            )
        )


@app.post(
    "/api/v1/risks/{risk_id}/restart-assessments",
    tags=["risk-assessments"],
    dependencies=[Depends(auth.require_roles(*ADMIN_ROLES))],
)
def restart_risk_assessments(risk_id: int, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    if db.get(models.Risk, risk_id) is None:
        raise HTTPException(status_code=404, detail=f"Risk {risk_id} not found")
    changed_by = request.headers.get("X-User", "system")
    assessments = db.query(models.RiskAssessment).filter(models.RiskAssessment.risk_id == risk_id).all()
    for assessment in assessments:
        _restart_assessment(assessment, db, changed_by)
    db.commit()
    return {"restarted_count": len(assessments), "assessment_ids": [a.id for a in assessments]}


@app.post(
    "/api/v1/entities/{entity_id}/restart-assessments",
    tags=["risk-assessments"],
    dependencies=[Depends(auth.require_roles(*ADMIN_ROLES))],
)
def restart_entity_assessments(entity_id: int, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    if db.get(models.Entity, entity_id) is None:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    changed_by = request.headers.get("X-User", "system")
    risk_ids = [r.id for r in db.query(models.Risk).filter(models.Risk.entity_id == entity_id).all()]
    assessments = (
        db.query(models.RiskAssessment).filter(models.RiskAssessment.risk_id.in_(risk_ids)).all()
        if risk_ids
        else []
    )
    for assessment in assessments:
        _restart_assessment(assessment, db, changed_by)
    db.commit()
    return {"restarted_count": len(assessments), "assessment_ids": [a.id for a in assessments]}


# ---------------------------------------------------------------------------
# Configurable Scoring Matrix (NR-011)
# ---------------------------------------------------------------------------


@app.get("/api/v1/risk-methodologies/{methodology_id}/preview-score", tags=["risk-methodologies"])
def preview_score(methodology_id: int, likelihood: int, impact: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    methodology = db.get(models.RiskMethodology, methodology_id)
    if methodology is None:
        raise HTTPException(status_code=404, detail=f"RiskMethodology {methodology_id} not found")
    score = likelihood * impact
    band = scoring.resolve_band(methodology, score)
    return {"score": score, "band": band}


# ---------------------------------------------------------------------------
# Evidence Attachments (NR-003)
# ---------------------------------------------------------------------------

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")


@app.post("/api/v1/evidence", response_model=schemas.EvidenceAttachmentRead, tags=["evidence"])
def upload_evidence(
    record_type: str = Body(...),
    record_id: int = Body(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_user),
) -> Any:
    record_dir = os.path.join(UPLOAD_ROOT, record_type, str(record_id))
    os.makedirs(record_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{file.filename}"
    disk_path = os.path.join(record_dir, stored_name)
    with open(disk_path, "wb") as f:
        f.write(file.file.read())
    attachment = models.EvidenceAttachment(
        record_type=record_type,
        record_id=record_id,
        file_name=file.filename,
        file_path=os.path.relpath(disk_path, UPLOAD_ROOT),
        content_type=file.content_type,
        uploaded_by=current_user.username,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@app.get("/api/v1/evidence", response_model=list[schemas.EvidenceAttachmentRead], tags=["evidence"])
def list_evidence(record_type: str, record_id: int, db: Session = Depends(get_db)) -> Any:
    return (
        db.query(models.EvidenceAttachment)
        .filter(models.EvidenceAttachment.record_type == record_type, models.EvidenceAttachment.record_id == record_id)
        .order_by(models.EvidenceAttachment.uploaded_at.desc())
        .all()
    )


@app.get("/api/v1/evidence/{evidence_id}/download", tags=["evidence"])
def download_evidence(evidence_id: int, db: Session = Depends(get_db)) -> FileResponse:
    attachment = db.get(models.EvidenceAttachment, evidence_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail=f"EvidenceAttachment {evidence_id} not found")
    disk_path = os.path.join(UPLOAD_ROOT, attachment.file_path)
    if not os.path.exists(disk_path):
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(disk_path, filename=attachment.file_name, media_type=attachment.content_type)


@app.delete("/api/v1/evidence/{evidence_id}", status_code=204, tags=["evidence"], dependencies=[Depends(auth.require_user)])
def delete_evidence(evidence_id: int, db: Session = Depends(get_db)) -> None:
    attachment = db.get(models.EvidenceAttachment, evidence_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail=f"EvidenceAttachment {evidence_id} not found")
    disk_path = os.path.join(UPLOAD_ROOT, attachment.file_path)
    if os.path.exists(disk_path):
        os.remove(disk_path)
    db.delete(attachment)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Vendor Lifecycle (NR-001)
# ---------------------------------------------------------------------------


@app.get("/api/v1/entities/vendors/overdue", response_model=list[schemas.EntityRead], tags=["entities"])
def overdue_vendors(db: Session = Depends(get_db)) -> Any:
    today = date.today()
    return (
        db.query(models.Entity)
        .filter(
            models.Entity.type == "Vendor",
            or_(
                models.Entity.contract_end_date <= today,
                models.Entity.last_due_diligence_date <= today - timedelta(days=365),
            ),
        )
        .all()
    )


# ---------------------------------------------------------------------------
# Overdue-Item Notifications (NR-007) — in-app only, no outbound email/Slack.
# ---------------------------------------------------------------------------


@app.post("/api/v1/notifications/run-check", response_model=schemas.NotificationCheckResult, tags=["notifications"], dependencies=[Depends(auth.require_user)])
def run_notification_check(db: Session = Depends(get_db)) -> Any:
    today = date.today()
    created, skipped = 0, 0

    overdue_tasks = db.query(models.RiskTask).filter(
        models.RiskTask.due_date < today, models.RiskTask.state != "Closed Complete"
    ).all()
    for task in overdue_tasks:
        exists = (
            db.query(models.Notification)
            .filter(models.Notification.related_type == "risk_task", models.Notification.related_id == task.id)
            .first()
        )
        if exists:
            skipped += 1
            continue
        db.add(
            models.Notification(
                recipient=task.assigned_to or "unassigned",
                subject=f"Overdue task: {task.title}",
                body=f"Task '{task.title}' was due {task.due_date} and is still {task.state}.",
                related_type="risk_task",
                related_id=task.id,
            )
        )
        created += 1

    overdue_mitigations = db.query(models.RiskMitigation).filter(
        models.RiskMitigation.target_date < today, models.RiskMitigation.status != "Verified"
    ).all()
    for mitigation in overdue_mitigations:
        exists = (
            db.query(models.Notification)
            .filter(models.Notification.related_type == "risk_mitigation", models.Notification.related_id == mitigation.id)
            .first()
        )
        if exists:
            skipped += 1
            continue
        db.add(
            models.Notification(
                recipient=mitigation.owner or "unassigned",
                subject="Overdue mitigation",
                body=f"Mitigation '{mitigation.description}' was due {mitigation.target_date} and is still {mitigation.status}.",
                related_type="risk_mitigation",
                related_id=mitigation.id,
            )
        )
        created += 1

    db.commit()
    return schemas.NotificationCheckResult(created_count=created, skipped_count=skipped)


@app.get("/api/v1/notifications/mine", response_model=list[schemas.NotificationRead], tags=["notifications"])
def my_notifications(recipient: str, db: Session = Depends(get_db)) -> Any:
    return (
        db.query(models.Notification)
        .filter(models.Notification.recipient == recipient)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


@app.post("/api/v1/notifications/{notification_id}/read", response_model=schemas.NotificationRead, tags=["notifications"], dependencies=[Depends(auth.require_user)])
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)) -> Any:
    notification = db.get(models.Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found")
    notification.read_at = datetime.now()
    db.commit()
    db.refresh(notification)
    return notification


# ---------------------------------------------------------------------------
# Automated Control Testing (NR-016) — pluggable connectors, persisted history
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/simulation/trigger-test",
    response_model=schemas.SimulationResponse,
    tags=["simulation"],
    dependencies=[Depends(auth.require_user)],
)
def trigger_control_test(
    control_id: Optional[int] = Body(default=None, embed=True),
    db: Session = Depends(get_db),
) -> schemas.SimulationResponse:
    query = db.query(models.Control)
    if control_id is not None:
        query = query.filter(models.Control.id == control_id)
        controls = query.all()
        if not controls:
            raise HTTPException(status_code=404, detail=f"Control {control_id} not found")
    else:
        controls = query.filter(models.Control.status == "Monitor").all()

    results: list[schemas.SimulationTestResult] = []
    issues_created = 0
    for control in controls:
        previous_status = control.status
        outcome, detail = control_testing.run_test(control)
        db.add(
            models.ControlTestResult(
                control_id=control.id, result=outcome, detail=detail, connector_type=control.test_connector_type
            )
        )
        issue_id = None
        if outcome == "Fail":
            control.status = "Fail"
            issue = models.Issue(
                title=f"Control test failure: {control.name}",
                description=f"Automated control testing flagged '{control.name}' as failing. {detail}",
                source="Control Failure",
                priority="High",
                state="New",
                risk_id=control.risk_id,
                control_id=control.id,
            )
            db.add(issue)
            db.flush()
            issue_id = issue.id
            issues_created += 1

        results.append(
            schemas.SimulationTestResult(
                control_id=control.id,
                control_name=control.name,
                result=outcome,
                previous_status=previous_status,
                new_status=control.status,
                issue_id=issue_id,
            )
        )

    db.commit()
    return schemas.SimulationResponse(
        tested_count=len(results),
        failed_count=issues_created,
        issues_created=issues_created,
        results=results,
    )


@app.get("/api/v1/controls/{control_id}/test-history", response_model=list[schemas.ControlTestResultRead], tags=["controls"])
def control_test_history(control_id: int, db: Session = Depends(get_db)) -> Any:
    return (
        db.query(models.ControlTestResult)
        .filter(models.ControlTestResult.control_id == control_id)
        .order_by(models.ControlTestResult.tested_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Executive reporting endpoint
# ---------------------------------------------------------------------------


def _compute_risk_summary(db: Session) -> schemas.RiskSummaryReport:
    risks = db.query(models.Risk).all()
    risks_by_state: dict[str, int] = {}
    inherent_scores: list[int] = []
    residual_scores: list[int] = []
    for risk in risks:
        risks_by_state[risk.state] = risks_by_state.get(risk.state, 0) + 1
        if risk.inherent_likelihood is not None and risk.inherent_impact is not None:
            inherent_scores.append(risk.inherent_likelihood * risk.inherent_impact)
        if risk.residual_likelihood is not None and risk.residual_impact is not None:
            residual_scores.append(risk.residual_likelihood * risk.residual_impact)

    avg_inherent = round(sum(inherent_scores) / len(inherent_scores), 2) if inherent_scores else None
    avg_residual = round(sum(residual_scores) / len(residual_scores), 2) if residual_scores else None
    risk_reduction_pct = None
    if avg_inherent is not None and avg_residual is not None and avg_inherent > 0:
        risk_reduction_pct = round((avg_inherent - avg_residual) / avg_inherent * 100, 1)

    issues = db.query(models.Issue).all()
    open_issues = [issue for issue in issues if issue.state != "Closed"]
    issues_by_priority: dict[str, int] = {}
    for issue in open_issues:
        issues_by_priority[issue.priority] = issues_by_priority.get(issue.priority, 0) + 1

    controls = db.query(models.Control).all()
    controls_by_status: dict[str, int] = {}
    for control in controls:
        controls_by_status[control.status] = controls_by_status.get(control.status, 0) + 1
    compliant_controls = controls_by_status.get("Monitor", 0)
    control_compliance_pct = (
        round(compliant_controls / len(controls) * 100, 1) if controls else None
    )

    return schemas.RiskSummaryReport(
        total_risks=len(risks),
        risks_by_state=risks_by_state,
        avg_inherent_score=avg_inherent,
        avg_residual_score=avg_residual,
        risk_reduction_pct=risk_reduction_pct,
        open_issue_count=len(open_issues),
        issues_by_priority=issues_by_priority,
        total_controls=len(controls),
        controls_by_status=controls_by_status,
        control_compliance_pct=control_compliance_pct,
    )


@app.get(
    "/api/v1/reports/risk-summary",
    response_model=schemas.RiskSummaryReport,
    tags=["reports"],
)
def risk_summary(db: Session = Depends(get_db)) -> schemas.RiskSummaryReport:
    return _compute_risk_summary(db)


@app.get("/api/v1/dashboard/stats", tags=["reports"])
def dashboard_stats(db: Session = Depends(get_db)) -> dict[str, int]:
    total_risks = db.query(models.Risk).count()
    open_issues = (
        db.query(models.Issue).filter(models.Issue.state != "Closed").count()
    )
    active_controls = (
        db.query(models.Control)
        .filter(models.Control.status.in_(["Monitor", "Review"]))
        .count()
    )
    pending_assessments = (
        db.query(models.RiskAssessment)
        .filter(models.RiskAssessment.state.in_(["In Progress", "Not Started"]))
        .count()
    )

    return {
        "totalRisks": total_risks,
        "openIssues": open_issues,
        "activeControls": active_controls,
        "pendingAssessments": pending_assessments,
    }


# --- Historical Risk Score Trending (NR-008) --------------------------------


@app.post("/api/v1/reports/snapshot", response_model=schemas.RiskScoreSnapshotRead, tags=["reports"], dependencies=[Depends(auth.require_user)])
def take_snapshot(db: Session = Depends(get_db)) -> Any:
    summary = _compute_risk_summary(db)
    snapshot = models.RiskScoreSnapshot(
        total_risks=summary.total_risks,
        avg_inherent_score=summary.avg_inherent_score,
        avg_residual_score=summary.avg_residual_score,
        open_issue_count=summary.open_issue_count,
        control_compliance_pct=summary.control_compliance_pct,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@app.get("/api/v1/reports/risk-summary/history", response_model=list[schemas.RiskScoreSnapshotRead], tags=["reports"])
def risk_summary_history(db: Session = Depends(get_db)) -> Any:
    return db.query(models.RiskScoreSnapshot).order_by(models.RiskScoreSnapshot.snapshot_at.asc()).all()


# --- Board-Ready PDF Export (NR-009) ----------------------------------------


@app.get("/api/v1/reports/risk-summary/pdf", tags=["reports"])
def risk_summary_pdf(db: Session = Depends(get_db)) -> Response:
    summary = _compute_risk_summary(db)
    top_issues = (
        db.query(models.Issue)
        .filter(models.Issue.state != "Closed")
        .order_by(models.Issue.priority.desc())
        .limit(10)
        .all()
    )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "ServiceNow GRC - Executive Risk Summary", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Totals", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Total risks: {summary.total_risks}", ln=True)
    pdf.cell(0, 6, f"Avg inherent / residual score: {summary.avg_inherent_score} / {summary.avg_residual_score}", ln=True)
    pdf.cell(0, 6, f"Risk reduction: {summary.risk_reduction_pct}%", ln=True)
    pdf.cell(0, 6, f"Open issues: {summary.open_issue_count}", ln=True)
    pdf.cell(0, 6, f"Control compliance: {summary.control_compliance_pct}%", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Risks by State", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for state, count in summary.risks_by_state.items():
        pdf.cell(0, 6, f"{state}: {count}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Top Open Issues", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for issue in top_issues:
        pdf.multi_cell(pdf.epw, 6, f"[{issue.priority}] {issue.title}")

    pdf_bytes = bytes(pdf.output())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=risk-summary.pdf"},
    )


# ---------------------------------------------------------------------------
# Audit trail (read-only — rows are written automatically by the CRUD router
# whenever a tracked resource is updated or deleted)
# ---------------------------------------------------------------------------


@app.get(
    "/api/v1/audit-logs",
    response_model=list[schemas.AuditLogRead],
    tags=["audit-logs"],
)
def list_audit_logs(
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
) -> list[Any]:
    query = db.query(models.AuditLog)
    if table_name:
        query = query.filter(models.AuditLog.table_name == table_name)
    if record_id is not None:
        query = query.filter(models.AuditLog.record_id == record_id)
    return (
        query.order_by(models.AuditLog.changed_at.desc()).offset(skip).limit(limit).all()
    )
