"""Pulls the live executive risk summary + board PDF from the running GRC API
and composes an email around them.

By default this only DRAFTS the email — it writes a real .eml file to
reports/ (attachment included) that opens in any mail client, and does not
send anything. No SMTP server or credentials are configured in this
environment, and dispatching mail on a user's behalf always needs their
explicit go-ahead, so sending is an opt-in a human takes deliberately: set
SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS/MAIL_FROM/MAIL_TO and pass --send.
"""

import argparse
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

import httpx

API = os.environ.get("GRC_API_URL", "http://127.0.0.1:8050")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

DEFAULT_FROM = "grc-reporting@example-company.local"
DEFAULT_TO = "leadership@example-company.local"


def fetch_summary_and_pdf(client: httpx.Client) -> tuple[dict, bytes]:
    summary = client.get(f"{API}/api/v1/reports/risk-summary").json()
    pdf_bytes = client.get(f"{API}/api/v1/reports/risk-summary/pdf").content
    return summary, pdf_bytes


def compose_body(summary: dict) -> str:
    states = ", ".join(f"{k}: {v}" for k, v in summary["risks_by_state"].items())
    priorities = ", ".join(f"{k}: {v}" for k, v in summary["issues_by_priority"].items())
    return f"""Hi team,

Here is the automated GRC risk summary for {datetime.now().strftime('%Y-%m-%d')}. Full detail is in the attached PDF.

Headline numbers:
  - Total risks tracked: {summary['total_risks']}
  - Average inherent / residual score: {summary['avg_inherent_score']} / {summary['avg_residual_score']}
  - Risk reduction from controls: {summary['risk_reduction_pct']}%
  - Open issues: {summary['open_issue_count']} ({priorities})
  - Control compliance: {summary['control_compliance_pct']}%

Risks by state: {states}

This summary was generated automatically from the live risk register — please
treat the attached PDF as the source of truth for this reporting cycle.

— GRC Reporting Agent
"""


def build_message(summary: dict, pdf_bytes: bytes, mail_from: str, mail_to: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"GRC Executive Risk Summary — {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.set_content(compose_body(summary))
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="risk-summary.pdf")
    return msg


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Actually send via SMTP (requires SMTP_* env vars)")
    parser.add_argument("--to", default=os.environ.get("MAIL_TO", DEFAULT_TO))
    parser.add_argument("--from-addr", default=os.environ.get("MAIL_FROM", DEFAULT_FROM))
    args = parser.parse_args()

    os.makedirs(REPORTS_DIR, exist_ok=True)

    print(f"📊 Summary Email Agent: pulling risk-summary + PDF from {API}")
    with httpx.Client(timeout=15.0) as client:
        summary, pdf_bytes = fetch_summary_and_pdf(client)

    msg = build_message(summary, pdf_bytes, args.from_addr, args.to)

    eml_path = os.path.join(REPORTS_DIR, f"risk-summary-{datetime.now().strftime('%Y%m%d-%H%M%S')}.eml")
    with open(eml_path, "wb") as f:
        f.write(bytes(msg))
    print(f"✉️  Drafted email saved to {eml_path} (open in Mail/Outlook to review)")

    if args.send:
        host, port, user, password = (
            os.environ.get("SMTP_HOST"),
            os.environ.get("SMTP_PORT"),
            os.environ.get("SMTP_USER"),
            os.environ.get("SMTP_PASS"),
        )
        if not all([host, port, user, password]):
            print("❌ --send requested but SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS are not all set. Not sending.")
            return
        with smtplib.SMTP(host, int(port)) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        print(f"📤 Sent to {args.to} via {host}:{port}")
    else:
        print("ℹ️  Not sent — no SMTP configured and --send not passed. This is a draft only.")


if __name__ == "__main__":
    main()
