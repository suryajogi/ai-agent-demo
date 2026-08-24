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


class UserRead(UserCreate, ORMBase):
    id: int


# --- Departments / Entities --------------------------------------------------


class DepartmentCreate(BaseModel):
    name: str
    manager_id: Optional[str] = None
    cost_center: Optional[str] = None


class DepartmentRead(DepartmentCreate, ORMBase):
    id: int


class EntityCreate(BaseModel):
    name: str
    type: str
    department_id: Optional[int] = None
    owner_id: Optional[str] = None
    status: str = "Active"


class EntityRead(EntityCreate, ORMBase):
    id: int


# --- Risk registry & governance ----------------------------------------------


class RiskScopeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: Optional[str] = None


class RiskScopeRead(RiskScopeCreate, ORMBase):
    id: int


class RiskMethodologyCreate(BaseModel):
    name: str
    assessment_type: str
    scoring_logic: Optional[str] = None


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


class ControlRead(ControlCreate, ORMBase):
    id: int


class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    source: str
    priority: str = "Medium"
    state: str = "New"
    assigned_to: Optional[str] = None
    risk_id: Optional[int] = None
    control_id: Optional[int] = None


class IssueRead(IssueCreate, ORMBase):
    id: int


class RiskMitigationCreate(BaseModel):
    risk_id: Optional[int] = None
    control_id: Optional[int] = None
    description: str
    status: str = "Planned"
    owner: Optional[str] = None
    target_date: Optional[date] = None


class RiskMitigationRead(RiskMitigationCreate, ORMBase):
    id: int


# --- Assessment engine structures ----------------------------------------------


class AssessmentTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    metric_type: str = "Qualitative"
    scoring_method: str = "Weighted Average"


class AssessmentTemplateRead(AssessmentTemplateCreate, ORMBase):
    id: int


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
    selected_value: int
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
