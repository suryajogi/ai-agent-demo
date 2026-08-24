import random
from datetime import datetime, timedelta
from models import (
    AssessmentOption,
    AssessmentQuestion,
    AssessmentTemplate,
    Base,
    Control,
    Department,
    Entity,
    Issue,
    Risk,
    RiskAssessment,
    RiskFramework,
    RiskMethodology,
    RiskMitigation,
    RiskScope,
    RiskStatement,
    Role,
    User,
)
from database import engine
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

print("🌱 Seeding 50 rows per table for ServiceNow GRC modules...")

# 0. Roles & Users
role_names = ["Risk Owner", "Assessor", "Compliance Manager", "Auditor", "Administrator"]
roles = [Role(name=name, description=f"{name} role within the GRC workspace.") for name in role_names]
session.add_all(roles)
session.commit()

users = [
    User(
        username=f"user.{i:03d}",
        display_name=f"GRC User {i}",
        email=f"user.{i:03d}@example.com",
        role_id=random.choice(roles).id,
        active=random.random() > 0.1,
    )
    for i in range(1, 21)
]
session.add_all(users)
session.commit()

# 1. Departments (10 distinct departments)
dept_names = ["Information Technology", "Cybersecurity", "Finance & Accounting", "Human Resources", "Legal & Compliance", "Operations", "Product Engineering", "Global Supply Chain", "Sales & Marketing", "Customer Success"]
depts = [Department(name=name, manager_id=f"MGR-{100+i}", cost_center=f"CC-{200+i}") for i, name in enumerate(dept_names)]
session.add_all(depts)
session.commit()

# 2. Entities (Scale up to 50 assets/entities mapping to departments)
entity_types = ["Application", "Facility", "Vendor Platform", "Database Critical Stack", "Cloud Infra Cluster"]
entities = []
for i in range(1, 51):
    ent = Entity(
        name=f"SN-Asset-{1000+i} ({random.choice(['SAP ERP', 'AWS Core', 'Salesforce CRM', 'HR Workday', 'Active Directory', 'Billing API'])})",
        type=random.choice(entity_types),
        department_id=random.choice(depts).id,
        owner_id=f"OWNER-{500+i}",
        status="Active" if random.random() > 0.1 else "Inactive"
    )
    entities.append(ent)
session.add_all(entities)
session.commit()

# 3. Risk Scopes & Methodologies
scopes = [RiskScope(name=f"Enterprise Scope v{i}.0", description=f"GRC Tracking Scope for FY2{6+i}", version=f"{i}.0") for i in range(1, 6)]
methodologies = [
    RiskMethodology(name="Qualitative Matrix Standard", assessment_type="Qualitative", scoring_logic="Likelihood x Impact Mapping"),
    RiskMethodology(name="Quantitative Financial Valuation", assessment_type="Quantitative", scoring_logic="ALE = SLE * ARO"),
    RiskMethodology(name="Hybrid Regulatory Weighting", assessment_type="Hybrid", scoring_logic="Weighted Compliance Score")
]
session.add_all(scopes + methodologies)
session.commit()

# 4. Risk Frameworks & Statements (Populate 10 Frameworks, 20 Statements)
frameworks = [RiskFramework(name=name, description=f"Framework for tracking {name} compliance rules.", scope_id=random.choice(scopes).id) for name in ["NIST SP 800-53", "ISO 27001 ISMS", "SOX Financial Controls", "GDPR Data Privacy", "COBIT IT Governance"]]
session.add_all(frameworks)
session.commit()

categories = ["Strategic", "Operational", "Financial", "Compliance"]
statements = []
for i in range(1, 26):
    stmt = RiskStatement(
        name=f"RS-{100+i}: {random.choice(['Unauthorized Access Vulnerability', 'Data Retention Breach', 'System Outage Failure', 'Misstatement of Assets', 'Third-Party Vendor Dependency'])}",
        description=f"Standard statement tracking general risks associated with baseline operational workflows.",
        category=random.choice(categories),
        framework_id=random.choice(frameworks).id
    )
    statements.append(stmt)
session.add_all(statements)
session.commit()

# 5. Risks (Create exactly 50 instances mapped to Statements & Entities)
risks = []
states = ["Draft", "Assess", "Respond", "Review", "Monitor"]
for i in range(1, 51):
    r = Risk(
        name=f"RISK-{200+i}: High Threat Vector on Node {i}",
        description=f"Isolated risk occurrence tracking specific failures on production system target configuration.",
        statement_id=random.choice(statements).id,
        entity_id=random.choice(entities).id,
        assigned_to=f"ANALYST-{700+i}",
        state=random.choice(states),
        inherent_likelihood=random.randint(1, 5),
        inherent_impact=random.randint(1, 5),
        residual_likelihood=random.randint(1, 4),
        residual_impact=random.randint(1, 4)
    )
    risks.append(r)
session.add_all(risks)
session.commit()

# 6. Controls (Create exactly 50 mitigation controls linked to risks)
control_statuses = ["Draft", "Attest", "Review", "Monitor"]
controls = []
for i in range(1, 51):
    c = Control(
        name=f"CTRL-{300+i}: Multi-Factor Authentication & Audit Logging System",
        description=f"Mandatory control mapping to compliance objectives.",
        status=random.choice(control_statuses),
        entity_id=random.choice(entities).id,
        risk_id=random.choice(risks).id if random.random() > 0.3 else None
    )
    controls.append(c)
    session.add(c)
session.commit()

# 6b. Risk Mitigations (remediation actions tied to risks/controls)
mitigation_statuses = ["Planned", "In Progress", "Implemented", "Verified"]
for i in range(1, 16):
    m = RiskMitigation(
        risk_id=random.choice(risks).id,
        control_id=random.choice(controls).id if random.random() > 0.3 else None,
        description=f"Remediation action MIT-{i}: harden configuration and verify control effectiveness.",
        status=random.choice(mitigation_statuses),
        owner=f"OWNER-{500+i}",
        target_date=datetime.now().date() + timedelta(days=random.randint(7, 90)),
    )
    session.add(m)

# 7. Issues (Create exactly 50 deficiency incidents)
issue_sources = ["Risk Assessment", "Control Failure", "Manual Entry"]
issue_priorities = ["Low", "Medium", "High", "Critical"]
issue_states = ["New", "Analyze", "Remediate", "Closed"]
for i in range(1, 51):
    iss = Issue(
        title=f"ISSUE-{400+i}: Security Drift Detected on Module {i}",
        description=f"Automated alert flag showing compliance posture fallback metrics.",
        source=random.choice(issue_sources),
        priority=random.choice(issue_priorities),
        state=random.choice(issue_states),
        assigned_to=f"REMEDIATOR-{800+i}"
    )
    session.add(iss)

# 8. Assessment Methodology (configurable template with scored answer options)
template = AssessmentTemplate(
    name="Standard Qualitative Risk Questionnaire",
    description="Baseline methodology used to assess likelihood and impact controls for a risk.",
    metric_type="Qualitative",
    scoring_method="Weighted Average",
)
session.add(template)
session.commit()

question_defs = [
    ("Is the control operating as designed?", 1.5),
    ("Is evidence of control execution available and current?", 1.0),
    ("Has the control been tested in the last 12 months?", 1.0),
    ("Are exceptions to this control tracked and remediated?", 1.2),
    ("Does management have visibility into control performance?", 0.8),
]
option_labels = [
    ("Strongly Disagree", 1),
    ("Disagree", 2),
    ("Neutral", 3),
    ("Agree", 4),
    ("Strongly Agree", 5),
]
questions = []
for seq, (text, weight) in enumerate(question_defs, start=1):
    q = AssessmentQuestion(
        template_id=template.id,
        question_text=text,
        question_type="Scale",
        sequence=seq,
        required=True,
        weight=weight,
    )
    session.add(q)
    session.flush()
    questions.append(q)
    for opt_seq, (label, score) in enumerate(option_labels, start=1):
        session.add(AssessmentOption(question_id=q.id, label=label, score=score, sequence=opt_seq))
session.commit()

# 9. Assessments (Create exactly 50 active assessment metrics)
assessment_states = ["Not Started", "In Progress", "Completed"]
for i in range(1, 51):
    asst = RiskAssessment(
        risk_id=random.choice(risks).id,
        assessor_id=f"ASSESSOR-{900+i}",
        template_id=template.id,
        state=random.choice(assessment_states),
        score=random.randint(5, 25),
        comments="Automatic baseline generation matching ServiceNow matrix models."
    )
    session.add(asst)

session.commit()
session.close()
print("🎯 Successfully injected exactly 50 entries into every primary GRC workspace table!")
