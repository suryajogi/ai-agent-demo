from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Identity (users & roles) -------------------------------------------------


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RoleRead(RoleCreate, ORMBase):
    id: int


class UserCreate(BaseModel):
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[int] = None
    active: bool = True
    department_id: Optional[int] = None


class UserRead(UserCreate, ORMBase):
    id: int


# --- Auth (NR-012) -------------------------------------------------------------


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# --- Departments / Entities --------------------------------------------------


class DepartmentCreate(BaseModel):
    name: str
    manager_id: Optional[str] = None
    cost_center: Optional[str] = None


class DepartmentRead(DepartmentCreate, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime


class EntityCreate(BaseModel):
    name: str
    type: str
    department_id: Optional[int] = None
    owner_id: Optional[str] = None
    status: str = "Active"
    contract_end_date: Optional[date] = None
    criticality_tier: Optional[str] = None
    last_due_diligence_date: Optional[date] = None


class EntityRead(EntityCreate, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime


# --- Risk registry & governance ----------------------------------------------


class RiskScopeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: Optional[str] = None


class RiskScopeRead(RiskScopeCreate, ORMBase):
    id: int


class ScoringBand(BaseModel):
    min_score: int
    max_score: int
    label: str
    color: str


class RiskMethodologyCreate(BaseModel):
    name: str
    assessment_type: str
    scoring_logic: Optional[str] = None
    scoring_bands: Optional[list[ScoringBand]] = None


class RiskMethodologyRead(RiskMethodologyCreate, ORMBase):
    id: int


class RiskFrameworkCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scope_id: Optional[int] = None


class RiskFrameworkRead(RiskFrameworkCreate, ORMBase):
    id: int


class RiskStatementCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    framework_id: Optional[int] = None


class RiskStatementRead(RiskStatementCreate, ORMBase):
    id: int


class RiskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    statement_id: Optional[int] = None
    entity_id: Optional[int] = None
    assigned_to: Optional[str] = None
    state: str = "Draft"
    inherent_likelihood: Optional[int] = None
    inherent_impact: Optional[int] = None
    residual_likelihood: Optional[int] = None
    residual_impact: Optional[int] = None


class RiskRead(RiskCreate, ORMBase):
    id: int
    breaches_appetite: bool = False
    created_at: datetime
    updated_at: datetime


# --- Execution & operations ---------------------------------------------------


class RiskAssessmentCreate(BaseModel):
    risk_id: Optional[int] = None
    assessor_id: Optional[str] = None
    template_id: Optional[int] = None
    state: str = "Not Started"
    score: Optional[float] = None
    comments: Optional[str] = None


class RiskAssessmentRead(RiskAssessmentCreate, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime


class RiskTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    parent_risk_id: Optional[int] = None
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    state: str = "Open"


class RiskTaskRead(RiskTaskCreate, ORMBase):
    id: int


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class ProjectRead(ProjectCreate, ORMBase):
    id: int


# --- Compliance & issue management --------------------------------------------


class ControlCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "Draft"
    entity_id: Optional[int] = None
    risk_id: Optional[int] = None
    test_connector_type: Optional[str] = None
    test_connector_config: Optional[dict] = None


class ControlRead(ControlCreate, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime


class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    source: str
    priority: str = "Medium"
    state: str = "New"
    assigned_to: Optional[str] = None
    risk_id: Optional[int] = None
    control_id: Optional[int] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    effectiveness_check_date: Optional[date] = None
    recurrence_count: int = 0


class IssueRead(IssueCreate, ORMBase):
    id: int
    created_at: datetime
    updated_at: datetime


class RiskMitigationCreate(BaseModel):
    risk_id: Optional[int] = None
    control_id: Optional[int] = None
    description: str
    status: str = "Planned"
    owner: Optional[str] = None
    target_date: Optional[date] = None


class RiskMitigationRead(RiskMitigationCreate, ORMBase):
    id: int


class ControlFrameworkMapCreate(BaseModel):
    control_id: int
    framework_id: int
    requirement_reference: Optional[str] = None


class ControlFrameworkMapRead(ControlFrameworkMapCreate, ORMBase):
    id: int


class RiskAppetiteThresholdCreate(BaseModel):
    name: str
    category: Optional[str] = None
    department_id: Optional[int] = None
    max_acceptable_score: int


class RiskAppetiteThresholdRead(RiskAppetiteThresholdCreate, ORMBase):
    id: int


class EvidenceAttachmentRead(ORMBase):
    id: int
    record_type: str
    record_id: int
    file_name: str
    content_type: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: datetime


class ControlTestResultRead(ORMBase):
    id: int
    control_id: int
    tested_at: datetime
    result: str
    detail: Optional[str] = None
    connector_type: Optional[str] = None


class NotificationRead(ORMBase):
    id: int
    recipient: str
    subject: str
    body: Optional[str] = None
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    created_at: datetime
    read_at: Optional[datetime] = None


class NotificationCheckResult(BaseModel):
    created_count: int
    skipped_count: int


class RiskScoreSnapshotRead(ORMBase):
    id: int
    snapshot_at: datetime
    total_risks: int
    avg_inherent_score: Optional[float] = None
    avg_residual_score: Optional[float] = None
    open_issue_count: int
    control_compliance_pct: Optional[float] = None


# --- Assessment engine structures ----------------------------------------------


class AssessmentTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    metric_type: str = "Qualitative"
    scoring_method: str = "Weighted Average"
    recurrence_rule: Optional[str] = None


class AssessmentTemplateRead(AssessmentTemplateCreate, ORMBase):
    id: int
    last_generated_at: Optional[datetime] = None


class AssessmentQuestionCreate(BaseModel):
    template_id: Optional[int] = None
    question_text: str
    question_type: str = "Scale"
    sequence: int = 1
    required: bool = True
    weight: float = 1.0


class AssessmentQuestionRead(AssessmentQuestionCreate, ORMBase):
    id: int


class AssessmentOptionCreate(BaseModel):
    question_id: Optional[int] = None
    label: str
    score: int
    sequence: int = 1


class AssessmentOptionRead(AssessmentOptionCreate, ORMBase):
    id: int


class AssessmentTemplateWithQuestions(AssessmentTemplateRead):
    questions: list[AssessmentQuestionRead] = []


class AssessmentResponseCreate(BaseModel):
    assessment_id: Optional[int] = None
    question_id: Optional[int] = None
    selected_value: Optional[int] = None
    justification: Optional[str] = None


class AssessmentResponseRead(AssessmentResponseCreate, ORMBase):
    id: int


# --- Assessor Portal submission ------------------------------------------------


class AssessmentAnswer(BaseModel):
    question_id: int
    selected_value: int
    justification: Optional[str] = None


class AssessmentSubmission(BaseModel):
    answers: list[AssessmentAnswer]


class RiskAssessmentWithResponses(RiskAssessmentRead):
    responses: list[AssessmentResponseRead] = []


# --- Control testing simulator ------------------------------------------------


class SimulationTestResult(BaseModel):
    control_id: int
    control_name: str
    result: str  # Pass, Fail
    previous_status: str
    new_status: str
    issue_id: Optional[int] = None


class SimulationResponse(BaseModel):
    tested_count: int
    failed_count: int
    issues_created: int
    results: list[SimulationTestResult]


# --- Audit trail -------------------------------------------------------------


class AuditLogRead(BaseModel):
    id: int
    table_name: str
    record_id: int
    action: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: Optional[str] = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Reporting -------------------------------------------------------------


class RiskSummaryReport(BaseModel):
    total_risks: int
    risks_by_state: dict[str, int]
    avg_inherent_score: Optional[float]
    avg_residual_score: Optional[float]
    risk_reduction_pct: Optional[float]
    open_issue_count: int
    issues_by_priority: dict[str, int]
    total_controls: int
    controls_by_status: dict[str, int]
    control_compliance_pct: Optional[float]
