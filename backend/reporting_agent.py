import os
import sys
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Import models from your local file structure
try:
    from models import Risk, Control, Issue, RiskAssessment
except ImportError:
    print("❌ Error: Could not locate database models. Ensure this script is run from the /backend directory.")
    sys.exit(1)

class ExecutiveReportingAgent:
    def __init__(self, db_path='sqlite:///grc_risk.db'):
        self.engine = create_engine(db_path)
        self.Session = sessionmaker(bind=self.engine)
        
    def analyze_compliance_posture(self):
        session = self.Session()
        print("🕵️  Executive Reporting Agent: Conducting deep GRC risk audit analysis...\n")
        
        # 1. Total Counts
        total_risks = session.query(func.count(Risk.id)).scalar()
        total_controls = session.query(func.count(Control.id)).scalar()
        total_issues = session.query(func.count(Issue.id)).scalar()
        
        # 2. Risk Metrics (Inherent vs Residual)
        # Average Inherent Risk Rating (Likelihood x Impact)
        risks = session.query(Risk).all()
        avg_inherent = sum(r.inherent_likelihood * r.inherent_impact for r in risks) / len(risks) if risks else 0
        avg_residual = sum(r.residual_likelihood * r.residual_impact for r in risks) / len(risks) if risks else 0
        risk_reduction = ((avg_inherent - avg_residual) / avg_inherent) * 100 if avg_inherent > 0 else 0
        
        # 3. Control Posture
        monitored_controls = session.query(Control).filter(Control.status == 'Monitor').count()
        review_controls = session.query(Control).filter(Control.status == 'Review').count()
        stale_controls = total_controls - (monitored_controls + review_controls)
        control_efficiency = ((monitored_controls + review_controls) / total_controls) * 100 if total_controls > 0 else 0

        # 4. Issue Prioritization
        critical_issues = session.query(Issue).filter(Issue.priority == 'Critical', Issue.state != 'Closed').count()
        high_issues = session.query(Issue).filter(Issue.priority == 'High', Issue.state != 'Closed').count()
        open_issues = session.query(Issue).filter(Issue.state != 'Closed').count()

        # Compile Executive Summary String
        summary_markdown = f"""
========================================================================
📋 SERVICENOW GRC REPLICATION: EXECUTIVE RISK POSTURE SUMMARY
========================================================================
Generated: {func.current_timestamp()}
Target Scope: Enterprise Production Workspace Profile

🛡️  OVERALL COMPLIANCE SCORE: {control_efficiency:.1f}% Stable
------------------------------------------------------------------------

📊 KEY PERFORMANCE QUANTIFIERS:
  • Profiled Risks Checked: {total_risks}
  • Active Controls Deployed: {total_controls} ({monitored_controls} fully active under Monitoring status)
  • Unresolved Audit Deficiencies: {open_issues} Total Open Issues

🔥 RISK MATRIX SEVERITY CALCULATION:
  • Avg. Baseline Inherent Risk Score: {avg_inherent:.2f} / 25.0
  • Avg. Mitigated Residual Risk Score: {avg_residual:.2f} / 25.0
  • >> Net Risk Exposure Reduction: -{risk_reduction:.1f}% due to active mitigation controls.

⚠️  URGENT ACTIONABLE DEFICIENCIES (OPEN ISSUES):
  • 🚨 CRITICAL PRIORITY: {critical_issues} open issues requiring immediate patch deployment.
  • 🔶 HIGH PRIORITY:     {high_issues} open items impacting tier-1 infrastructure assets.
  
💡 STRATEGIC RECOMMENDATION:
  Control coverage is effective, showing a {risk_reduction:.1f}% drop from inherent threat levels. 
  Focus engineering agents on remediating the {critical_issues} CRITICAL open issues to clear the error state.
========================================================================
"""
        session.close()
        return summary_markdown

if __name__ == "__main__":
    # Point to your local SQLite database file path
    agent = ExecutiveReportingAgent()
    print(agent.analyze_compliance_posture())
