import logging
import random
from typing import Any, Optional, Type

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

import models
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
# Generic CRUD router factory
#
# Every GRC table gets list/get/create/update/delete endpoints. List endpoints
# also support filtering by any real column via query string, e.g.
# GET /api/v1/risk-assessments?assessor_id=s.washington&state=Completed
# ---------------------------------------------------------------------------


def build_crud_router(
    *,
    model: Type[Any],
    create_schema: Type[BaseModel],
    read_schema: Type[BaseModel],
    prefix: str,
    tag: str,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])
    resource = model.__name__
    mapper = sa_inspect(model)

    @router.get("", response_model=list[read_schema])
    def list_items(
        request: Request, skip: int = 0, limit: int = 200, db: Session = Depends(get_db)
    ) -> list[Any]:
        query = db.query(model)
        for key, value in request.query_params.items():
            if key in ("skip", "limit") or key not in mapper.columns:
                continue
            column = mapper.columns[key]
            try:
                casted = column.type.python_type(value)
            except (TypeError, ValueError):
                continue
            query = query.filter(column == casted)
        return query.offset(skip).limit(limit).all()

    @router.get("/{item_id}", response_model=read_schema)
    def get_item(item_id: int, db: Session = Depends(get_db)) -> Any:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{resource} {item_id} not found")
        return item

    @router.post("", response_model=read_schema, status_code=201)
    def create_item(payload: create_schema, db: Session = Depends(get_db)) -> Any:  # type: ignore[valid-type]
        item = model(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.put("/{item_id}", response_model=read_schema)
    def update_item(
        item_id: int, payload: create_schema, request: Request, db: Session = Depends(get_db)  # type: ignore[valid-type]
    ) -> Any:
        item = db.get(model, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{resource} {item_id} not found")
        changed_by = request.headers.get("X-User", "system")
        for field, value in payload.model_dump().items():
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
        db.commit()
        db.refresh(item)
        return item

    @router.delete("/{item_id}", status_code=204)
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


CRUD_RESOURCES = [
    dict(model=models.Role, create_schema=schemas.RoleCreate, read_schema=schemas.RoleRead, prefix="/api/v1/roles", tag="roles"),
    dict(model=models.User, create_schema=schemas.UserCreate, read_schema=schemas.UserRead, prefix="/api/v1/users", tag="users"),
    dict(model=models.Department, create_schema=schemas.DepartmentCreate, read_schema=schemas.DepartmentRead, prefix="/api/v1/departments", tag="departments"),
    dict(model=models.Entity, create_schema=schemas.EntityCreate, read_schema=schemas.EntityRead, prefix="/api/v1/entities", tag="entities"),
    dict(model=models.RiskScope, create_schema=schemas.RiskScopeCreate, read_schema=schemas.RiskScopeRead, prefix="/api/v1/risk-scopes", tag="risk-scopes"),
    dict(model=models.RiskMethodology, create_schema=schemas.RiskMethodologyCreate, read_schema=schemas.RiskMethodologyRead, prefix="/api/v1/risk-methodologies", tag="risk-methodologies"),
    dict(model=models.RiskFramework, create_schema=schemas.RiskFrameworkCreate, read_schema=schemas.RiskFrameworkRead, prefix="/api/v1/risk-frameworks", tag="risk-frameworks"),
    dict(model=models.RiskStatement, create_schema=schemas.RiskStatementCreate, read_schema=schemas.RiskStatementRead, prefix="/api/v1/risk-statements", tag="risk-statements"),
    dict(model=models.Risk, create_schema=schemas.RiskCreate, read_schema=schemas.RiskRead, prefix="/api/v1/risks", tag="risks"),
    dict(model=models.RiskAssessment, create_schema=schemas.RiskAssessmentCreate, read_schema=schemas.RiskAssessmentRead, prefix="/api/v1/risk-assessments", tag="risk-assessments"),
    dict(model=models.RiskTask, create_schema=schemas.RiskTaskCreate, read_schema=schemas.RiskTaskRead, prefix="/api/v1/risk-tasks", tag="risk-tasks"),
    dict(model=models.Project, create_schema=schemas.ProjectCreate, read_schema=schemas.ProjectRead, prefix="/api/v1/projects", tag="projects"),
    dict(model=models.Control, create_schema=schemas.ControlCreate, read_schema=schemas.ControlRead, prefix="/api/v1/controls", tag="controls"),
    dict(model=models.Issue, create_schema=schemas.IssueCreate, read_schema=schemas.IssueRead, prefix="/api/v1/issues", tag="issues"),
    dict(model=models.RiskMitigation, create_schema=schemas.RiskMitigationCreate, read_schema=schemas.RiskMitigationRead, prefix="/api/v1/risk-mitigations", tag="risk-mitigations"),
    dict(model=models.AssessmentTemplate, create_schema=schemas.AssessmentTemplateCreate, read_schema=schemas.AssessmentTemplateRead, prefix="/api/v1/assessment-templates", tag="assessment-templates"),
    dict(model=models.AssessmentQuestion, create_schema=schemas.AssessmentQuestionCreate, read_schema=schemas.AssessmentQuestionRead, prefix="/api/v1/assessment-questions", tag="assessment-questions"),
    dict(model=models.AssessmentOption, create_schema=schemas.AssessmentOptionCreate, read_schema=schemas.AssessmentOptionRead, prefix="/api/v1/assessment-options", tag="assessment-options"),
    dict(model=models.AssessmentResponse, create_schema=schemas.AssessmentResponseCreate, read_schema=schemas.AssessmentResponseRead, prefix="/api/v1/assessment-responses", tag="assessment-responses"),
]

for resource in CRUD_RESOURCES:
    app.include_router(build_crud_router(**resource))


# ---------------------------------------------------------------------------
# Assessor Portal: submit a filled-out questionnaire and compute the score
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/risk-assessments/{assessment_id}/submit",
    response_model=schemas.RiskAssessmentWithResponses,
    tags=["risk-assessments"],
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
# Automated Control Testing Simulator
#
# Randomly issues a Pass/Fail test result against deployed (Monitor-status)
# mitigation controls. A Fail flips the control's status to "Fail" and opens
# a linked High Priority issue for remediation.
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/simulation/trigger-test",
    response_model=schemas.SimulationResponse,
    tags=["simulation"],
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
        outcome = random.choice(["Pass", "Fail"])
        issue_id = None
        if outcome == "Fail":
            control.status = "Fail"
            issue = models.Issue(
                title=f"Control test failure: {control.name}",
                description=(
                    f"Automated control testing simulator flagged control '{control.name}' as failing."
                ),
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


# ---------------------------------------------------------------------------
# Executive reporting endpoint
# ---------------------------------------------------------------------------


@app.get(
    "/api/v1/reports/risk-summary",
    response_model=schemas.RiskSummaryReport,
    tags=["reports"],
)
def risk_summary(db: Session = Depends(get_db)) -> schemas.RiskSummaryReport:
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
    table_name: str | None = None,
    record_id: int | None = None,
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
