"""Executive Reporting Agent.

Connects directly to the GRC database, analyzes active risks and
under-performing controls, and prints an executive markdown report
summarizing organizational risk posture.

Run with: python reporting_agent.py
"""

from datetime import date

from database import SessionLocal
from models import Control, Issue, Risk


def print_report(text: str) -> None:
    """Local output sink for the generated report (stdout)."""
    print(text)


def inherent_score(risk: Risk) -> int:
    if risk.inherent_likelihood is None or risk.inherent_impact is None:
        return 0
    return risk.inherent_likelihood * risk.inherent_impact


def residual_score(risk: Risk) -> int:
    if risk.residual_likelihood is None or risk.residual_impact is None:
        return 0
    return risk.residual_likelihood * risk.residual_impact


def build_report() -> str:
    db = SessionLocal()
    try:
        risks = db.query(Risk).all()
        controls = db.query(Control).all()
        issues = db.query(Issue).all()

        active_risks = [r for r in risks if r.state != "Draft"]
        scored_risks = [r for r in active_risks if r.inherent_likelihood and r.inherent_impact]
        inherent_scores = [inherent_score(r) for r in scored_risks]
        residual_candidates = [r for r in scored_risks if r.residual_likelihood and r.residual_impact]
        residual_scores = [residual_score(r) for r in residual_candidates]

        avg_inherent = sum(inherent_scores) / len(inherent_scores) if inherent_scores else 0.0
        avg_residual = sum(residual_scores) / len(residual_scores) if residual_scores else 0.0
        reduction_pct = ((avg_inherent - avg_residual) / avg_inherent * 100) if avg_inherent else 0.0

        top_risks = sorted(scored_risks, key=inherent_score, reverse=True)[:5]

        failing_controls = [c for c in controls if c.status != "Monitor"]
        compliance_pct = (
            (len(controls) - len(failing_controls)) / len(controls) * 100 if controls else 0.0
        )

        open_issues = [i for i in issues if i.state != "Closed"]
        priority_order = ["Critical", "High", "Medium", "Low"]
        issues_by_priority = {p: len([i for i in open_issues if i.priority == p]) for p in priority_order}

        lines: list[str] = []
        lines.append("# Executive Risk Posture Report")
        lines.append(f"_Generated: {date.today().isoformat()}_")
        lines.append("")
        lines.append("## Summary")
        lines.append(f"- Active risks tracked: **{len(active_risks)}**")
        lines.append(f"- Average inherent risk score (likelihood x impact, 1-25): **{avg_inherent:.1f}**")
        lines.append(f"- Average residual risk score: **{avg_residual:.1f}**")
        lines.append(f"- Risk reduction achieved through mitigation: **{reduction_pct:.0f}%**")
        lines.append(f"- Control compliance rate (controls in Monitor status): **{compliance_pct:.0f}%**")
        lines.append(f"- Open issues: **{len(open_issues)}**")
        lines.append("")

        lines.append("## Top Risk Exposures")
        if top_risks:
            lines.append("| Risk | State | Inherent | Residual | Owner |")
            lines.append("|---|---|---|---|---|")
            for risk in top_risks:
                lines.append(
                    f"| {risk.name} | {risk.state} | {inherent_score(risk)} | "
                    f"{residual_score(risk) or 'n/a'} | {risk.assigned_to or 'unassigned'} |"
                )
        else:
            lines.append("No scored risks found.")
        lines.append("")

        lines.append("## Controls Requiring Attention")
        if failing_controls:
            lines.append("| Control | Status | Linked Risk |")
            lines.append("|---|---|---|")
            for control in failing_controls:
                linked_risk = control.risk.name if control.risk else "n/a"
                lines.append(f"| {control.name} | {control.status} | {linked_risk} |")
        else:
            lines.append("All controls are operating in Monitor status.")
        lines.append("")

        lines.append("## Open Issues by Priority")
        lines.append("| Priority | Count |")
        lines.append("|---|---|")
        for priority in priority_order:
            lines.append(f"| {priority} | {issues_by_priority[priority]} |")
        lines.append("")

        lines.append("## Narrative")
        narrative = []
        if reduction_pct >= 40:
            narrative.append(
                f"Mitigation efforts are meaningfully reducing exposure, cutting average risk "
                f"scores by {reduction_pct:.0f}% from inherent to residual."
            )
        else:
            narrative.append(
                f"Residual risk remains close to inherent levels (only a {reduction_pct:.0f}% "
                "reduction), suggesting mitigating controls need to mature further."
            )
        if compliance_pct < 70:
            narrative.append(
                f"Control compliance is at {compliance_pct:.0f}%, below the 70% target — "
                f"{len(failing_controls)} control(s) are not yet in a Monitor state and should "
                "be prioritized."
            )
        else:
            narrative.append(f"Control compliance is healthy at {compliance_pct:.0f}%.")
        if issues_by_priority["Critical"] or issues_by_priority["High"]:
            narrative.append(
                f"There are {issues_by_priority['Critical']} critical and "
                f"{issues_by_priority['High']} high-priority open issues requiring executive "
                "attention this cycle."
            )
        lines.append(" ".join(narrative))

        return "\n".join(lines)
    finally:
        db.close()


def main() -> None:
    print_report(build_report())


if __name__ == "__main__":
    main()
