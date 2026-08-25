from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# --- 0. Identity (users & roles) --------------------------------------------


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    display_name: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))

    role: Mapped[Optional["Role"]] = relationship(back_populates="users")
    department: Mapped[Optional["Department"]] = relationship()


# --- 1. Core Organizational Structure -------------------------------------


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    manager_id: Mapped[Optional[str]] = mapped_column(String)
    cost_center: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    entities: Mapped[list["Entity"]] = relationship(back_populates="department")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # Application, Facility, Vendor
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    owner_id: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="Active")  # Active, Inactive

    # Vendor lifecycle (NR-001) — only meaningful when type == "Vendor", but kept
    # on Entity rather than a separate table since every entity may eventually
    # need a contract/review cadence, not just vendors.
    contract_end_date: Mapped[Optional[date]] = mapped_column(Date)
    criticality_tier: Mapped[Optional[str]] = mapped_column(String)  # Low, Medium, High, Critical
    last_due_diligence_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    department: Mapped[Optional["Department"]] = relationship(back_populates="entities")
    risks: Mapped[list["Risk"]] = relationship(back_populates="entity")
    controls: Mapped[list["Control"]] = relationship(back_populates="entity")


# --- 2. Risk Registry & Governance -----------------------------------------


class RiskScope(Base):
    __tablename__ = "risk_scopes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    version: Mapped[Optional[str]] = mapped_column(String)

    frameworks: Mapped[list["RiskFramework"]] = relationship(back_populates="scope")


class RiskMethodology(Base):
    __tablename__ = "risk_methodologies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    assessment_type: Mapped[str] = mapped_column(String)  # Qualitative, Quantitative, Hybrid
    scoring_logic: Mapped[Optional[str]] = mapped_column(String)

    # Configurable scoring matrix (NR-011): list of
    # {"min_score", "max_score", "label", "color"}. None means "use the
    # application's default 4-band thresholds" (no regression for existing
    # methodologies that never configure this).
    scoring_bands: Mapped[Optional[list]] = mapped_column(JSON)


class RiskFramework(Base):
    __tablename__ = "risk_frameworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    scope_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risk_scopes.id"))

    scope: Mapped[Optional["RiskScope"]] = relationship(back_populates="frameworks")
    statements: Mapped[list["RiskStatement"]] = relationship(back_populates="framework")
    control_mappings: Mapped[list["ControlFrameworkMap"]] = relationship(back_populates="framework")


class RiskStatement(Base):
    __tablename__ = "risk_statements"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)  # Strategic, Operational, Financial, Compliance
    framework_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risk_frameworks.id"))

    framework: Mapped[Optional["RiskFramework"]] = relationship(back_populates="statements")
    risks: Mapped[list["Risk"]] = relationship(back_populates="statement")


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    statement_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risk_statements.id"))
    entity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("entities.id"))
    assigned_to: Mapped[Optional[str]] = mapped_column(String)
    state: Mapped[str] = mapped_column(String, default="Draft")  # Draft, Assess, Respond, Review, Monitor
    inherent_likelihood: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    inherent_impact: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    residual_likelihood: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    residual_impact: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    statement: Mapped[Optional["RiskStatement"]] = relationship(back_populates="risks")
    entity: Mapped[Optional["Entity"]] = relationship(back_populates="risks")
    assessments: Mapped[list["RiskAssessment"]] = relationship(back_populates="risk")
    tasks: Mapped[list["RiskTask"]] = relationship(back_populates="parent_risk")
    controls: Mapped[list["Control"]] = relationship(back_populates="risk")
    issues: Mapped[list["Issue"]] = relationship(back_populates="risk")
    mitigations: Mapped[list["RiskMitigation"]] = relationship(back_populates="risk")


# --- 3. Execution & Operations ----------------------------------------------


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    risk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risks.id"))
    assessor_id: Mapped[Optional[str]] = mapped_column(String)
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessment_templates.id"))
    state: Mapped[str] = mapped_column(String, default="Not Started")  # Not Started, In Progress, Completed
    score: Mapped[Optional[float]] = mapped_column(Float)
    comments: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    risk: Mapped[Optional["Risk"]] = relationship(back_populates="assessments")
    template: Mapped[Optional["AssessmentTemplate"]] = relationship(back_populates="assessments")
    responses: Mapped[list["AssessmentResponse"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class RiskTask(Base):
    __tablename__ = "risk_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    parent_risk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risks.id"))
    assigned_to: Mapped[Optional[str]] = mapped_column(String)
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String, default="Open")  # Open, Work in Progress, Closed Complete

    parent_risk: Mapped[Optional["Risk"]] = relationship(back_populates="tasks")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String)


# --- 4. Compliance & Issue Management ---------------------------------------


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="Draft")  # Draft, Attest, Review, Monitor
    entity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("entities.id"))
    risk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risks.id"))

    # Continuous control monitoring (NR-016). test_connector_type "none" (or
    # null) preserves the original random Pass/Fail demo behavior.
    test_connector_type: Mapped[Optional[str]] = mapped_column(String)  # none, http_health_check
    test_connector_config: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    entity: Mapped[Optional["Entity"]] = relationship(back_populates="controls")
    risk: Mapped[Optional["Risk"]] = relationship(back_populates="controls")
    issues: Mapped[list["Issue"]] = relationship(back_populates="control")
    framework_mappings: Mapped[list["ControlFrameworkMap"]] = relationship(back_populates="control")
    test_results: Mapped[list["ControlTestResult"]] = relationship(back_populates="control")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)  # Risk Assessment, Control Failure, Manual
    priority: Mapped[str] = mapped_column(String, default="Medium")  # Low, Medium, High, Critical
    state: Mapped[str] = mapped_column(String, default="New")  # New, Analyze, Remediate, Closed
    assigned_to: Mapped[Optional[str]] = mapped_column(String)
    risk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risks.id"))
    control_id: Mapped[Optional[int]] = mapped_column(ForeignKey("controls.id"))

    # CAPA — root cause & corrective action (NR-004).
    root_cause: Mapped[Optional[str]] = mapped_column(String)
    corrective_action: Mapped[Optional[str]] = mapped_column(String)
    effectiveness_check_date: Mapped[Optional[date]] = mapped_column(Date)
    recurrence_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    risk: Mapped[Optional["Risk"]] = relationship(back_populates="issues")
    control: Mapped[Optional["Control"]] = relationship(back_populates="issues")


class RiskMitigation(Base):
    __tablename__ = "risk_mitigations"

    id: Mapped[int] = mapped_column(primary_key=True)
    risk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risks.id"))
    control_id: Mapped[Optional[int]] = mapped_column(ForeignKey("controls.id"))
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Planned")  # Planned, In Progress, Implemented, Verified
    owner: Mapped[Optional[str]] = mapped_column(String)
    target_date: Mapped[Optional[date]] = mapped_column(Date)

    risk: Mapped[Optional["Risk"]] = relationship(back_populates="mitigations")
    control: Mapped[Optional["Control"]] = relationship()


class ControlFrameworkMap(Base):
    """One control can satisfy many frameworks and vice versa (NR-002)."""

    __tablename__ = "control_framework_map"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"), nullable=False)
    framework_id: Mapped[int] = mapped_column(ForeignKey("risk_frameworks.id"), nullable=False)
    requirement_reference: Mapped[Optional[str]] = mapped_column(String)  # e.g. "SOX 404", "ISO 27001 A.9.2"

    control: Mapped["Control"] = relationship(back_populates="framework_mappings")
    framework: Mapped["RiskFramework"] = relationship(back_populates="control_mappings")


class RiskAppetiteThreshold(Base):
    """Max acceptable inherent/residual score before a risk is flagged (NR-005)."""

    __tablename__ = "risk_appetite_thresholds"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String)  # matches risk_statements.category, or null = global
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    max_acceptable_score: Mapped[int] = mapped_column(Integer, nullable=False)

    department: Mapped[Optional["Department"]] = relationship()


class EvidenceAttachment(Base):
    """Files attached to a risk/control/issue/assessment (NR-003)."""

    __tablename__ = "evidence_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_type: Mapped[str] = mapped_column(String, nullable=False)  # risk, control, issue, assessment
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)  # relative path under backend/uploads/
    content_type: Mapped[Optional[str]] = mapped_column(String)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ControlTestResult(Base):
    """Persisted history for control tests, real or simulated (NR-016)."""

    __tablename__ = "control_test_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"), nullable=False)
    tested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    result: Mapped[str] = mapped_column(String, nullable=False)  # Pass, Fail
    detail: Mapped[Optional[str]] = mapped_column(String)
    connector_type: Mapped[Optional[str]] = mapped_column(String)

    control: Mapped["Control"] = relationship(back_populates="test_results")


class Notification(Base):
    """In-app notifications (NR-007) — no outbound email/webhook delivery."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient: Mapped[str] = mapped_column(String, nullable=False)  # free-text identity, matches assigned_to/owner
    subject: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[Optional[str]] = mapped_column(String)
    related_type: Mapped[Optional[str]] = mapped_column(String)  # risk_task, risk_mitigation
    related_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class RiskScoreSnapshot(Base):
    """Point-in-time snapshot of the risk-summary report, for trending (NR-008)."""

    __tablename__ = "risk_score_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    total_risks: Mapped[int] = mapped_column(Integer, default=0)
    avg_inherent_score: Mapped[Optional[float]] = mapped_column(Float)
    avg_residual_score: Mapped[Optional[float]] = mapped_column(Float)
    open_issue_count: Mapped[int] = mapped_column(Integer, default=0)
    control_compliance_pct: Mapped[Optional[float]] = mapped_column(Float)


# --- 5. Assessment Engine Structures -----------------------------------------


class AssessmentTemplate(Base):
    __tablename__ = "assessment_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    metric_type: Mapped[str] = mapped_column(String, default="Qualitative")
    scoring_method: Mapped[str] = mapped_column(String, default="Weighted Average")

    # Recurring assessments (NR-010).
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String)  # none, quarterly, annual
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    questions: Mapped[list["AssessmentQuestion"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["RiskAssessment"]] = relationship(back_populates="template")


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessment_templates.id"))
    question_text: Mapped[str] = mapped_column(String, nullable=False)
    question_type: Mapped[str] = mapped_column(String, default="Scale")  # Scale, MultipleChoice, YesNo
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    template: Mapped[Optional["AssessmentTemplate"]] = relationship(back_populates="questions")
    responses: Mapped[list["AssessmentResponse"]] = relationship(back_populates="question")
    options: Mapped[list["AssessmentOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class AssessmentOption(Base):
    __tablename__ = "assessment_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessment_questions.id"))
    label: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[int] = mapped_column(Integer)  # points this choice contributes to the response scale
    sequence: Mapped[int] = mapped_column(Integer, default=1)

    question: Mapped[Optional["AssessmentQuestion"]] = relationship(back_populates="options")


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risk_assessments.id"))
    question_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessment_questions.id"))
    selected_value: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 scale; null until answered
    justification: Mapped[Optional[str]] = mapped_column(String)

    assessment: Mapped[Optional["RiskAssessment"]] = relationship(back_populates="responses")
    question: Mapped[Optional["AssessmentQuestion"]] = relationship(back_populates="responses")


# --- 6. Audit Trail -----------------------------------------------------------


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str] = mapped_column(String, nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)  # created, updated, deleted
    field_name: Mapped[Optional[str]] = mapped_column(String)
    old_value: Mapped[Optional[str]] = mapped_column(String)
    new_value: Mapped[Optional[str]] = mapped_column(String)
    changed_by: Mapped[Optional[str]] = mapped_column(String)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
