from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
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

    role: Mapped[Optional["Role"]] = relationship(back_populates="users")


# --- 1. Core Organizational Structure -------------------------------------


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    manager_id: Mapped[Optional[str]] = mapped_column(String)
    cost_center: Mapped[Optional[str]] = mapped_column(String)

    entities: Mapped[list["Entity"]] = relationship(back_populates="department")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # Application, Facility, Vendor
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    owner_id: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="Active")  # Active, Inactive

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


class RiskFramework(Base):
    __tablename__ = "risk_frameworks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    scope_id: Mapped[Optional[int]] = mapped_column(ForeignKey("risk_scopes.id"))

    scope: Mapped[Optional["RiskScope"]] = relationship(back_populates="frameworks")
    statements: Mapped[list["RiskStatement"]] = relationship(back_populates="framework")


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

    entity: Mapped[Optional["Entity"]] = relationship(back_populates="controls")
    risk: Mapped[Optional["Risk"]] = relationship(back_populates="controls")
    issues: Mapped[list["Issue"]] = relationship(back_populates="control")


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


# --- 5. Assessment Engine Structures -----------------------------------------


class AssessmentTemplate(Base):
    __tablename__ = "assessment_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    metric_type: Mapped[str] = mapped_column(String, default="Qualitative")
    scoring_method: Mapped[str] = mapped_column(String, default="Weighted Average")

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
    selected_value: Mapped[int] = mapped_column(Integer)  # 1-5 scale
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
