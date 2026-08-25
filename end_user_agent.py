"""Simulates a handful of end users logging into the live GRC API and
creating new records — a Risk, a mitigating Control, and a related Issue
each — the way a real Risk Owner would work the app day to day.

Talks to the running backend over HTTP (not the DB directly), so it
exercises real auth, RBAC, and validation exactly as a browser session
would. Requires `uvicorn main:app --port 8050` already running.
"""

import os
import random

import httpx

API = os.environ.get("GRC_API_URL", "http://127.0.0.1:8050")
DEMO_PASSWORD = "changeme123"
PERSONA_COUNT = 3

SCENARIOS = [
    {
        "risk_name": "Unpatched VPN Gateway Exposure",
        "risk_desc": "Remote-access VPN appliance is three patch cycles behind vendor security advisories.",
        "control_name": "Quarterly VPN Firmware Patch Review",
        "control_desc": "Scheduled review and application of vendor security patches for all VPN gateways.",
        "issue_title": "VPN gateway missed Q2 patch window",
        "issue_desc": "Patch review was scheduled but not completed before the quarter close.",
    },
    {
        "risk_name": "Shared Admin Credentials on Billing API",
        "risk_desc": "Multiple engineers share one admin credential for the billing API instead of individual accounts.",
        "control_name": "Individual API Credential Enforcement",
        "control_desc": "Require per-engineer API credentials with least-privilege scopes for billing systems.",
        "issue_title": "Shared credential still in use post-deadline",
        "issue_desc": "Team missed the credential-rotation deadline; shared key is still active in production.",
    },
    {
        "risk_name": "Vendor Data Retention Beyond Contract Terms",
        "risk_desc": "A SaaS vendor's data retention practice was not verified against the signed DPA terms.",
        "control_name": "Annual Vendor DPA Compliance Attestation",
        "control_desc": "Yearly attestation cycle confirming vendor data handling matches contracted terms.",
        "issue_title": "DPA attestation not on file for FY26",
        "issue_desc": "No signed attestation received from vendor for the current fiscal year.",
    },
]


def active_users(client: httpx.Client) -> list[dict]:
    users = client.get(f"{API}/api/v1/users").json()
    return [u for u in users if u["active"]]


def login(client: httpx.Client, username: str) -> str:
    resp = client.post(f"{API}/api/v1/auth/login", json={"username": username, "password": DEMO_PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]


def main() -> None:
    with httpx.Client(timeout=10.0) as client:
        users = active_users(client)
        entities = client.get(f"{API}/api/v1/entities").json()
        personas = random.sample(users, min(PERSONA_COUNT, len(users)))

        print(f"👤 End-User Agent: simulating {len(personas)} users creating records against {API}")

        for persona, scenario in zip(personas, SCENARIOS):
            username = persona["username"]
            try:
                token = login(client, username)
            except httpx.HTTPStatusError:
                print(f"  ⚠️  {username} could not log in (inactive?) — skipping")
                continue

            headers = {"Authorization": f"Bearer {token}"}
            entity = random.choice(entities)

            risk = client.post(
                f"{API}/api/v1/risks",
                headers=headers,
                json={
                    "name": scenario["risk_name"],
                    "description": scenario["risk_desc"],
                    "entity_id": entity["id"],
                    "assigned_to": username,
                    "state": "Draft",
                    "inherent_likelihood": random.randint(2, 5),
                    "inherent_impact": random.randint(2, 5),
                },
            )
            risk.raise_for_status()
            risk_id = risk.json()["id"]

            control = client.post(
                f"{API}/api/v1/controls",
                headers=headers,
                json={
                    "name": scenario["control_name"],
                    "description": scenario["control_desc"],
                    "status": "Draft",
                    "entity_id": entity["id"],
                    "risk_id": risk_id,
                },
            )
            control.raise_for_status()
            control_id = control.json()["id"]

            issue = client.post(
                f"{API}/api/v1/issues",
                headers=headers,
                json={
                    "title": scenario["issue_title"],
                    "description": scenario["issue_desc"],
                    "source": "Manual",
                    "priority": random.choice(["Medium", "High"]),
                    "state": "New",
                    "assigned_to": username,
                    "risk_id": risk_id,
                    "control_id": control_id,
                },
            )
            issue.raise_for_status()

            print(f"  ✅ {username}: created risk #{risk_id} '{scenario['risk_name']}', "
                  f"control #{control_id}, issue #{issue.json()['id']}")

        print("🎯 End-User Agent complete.")


if __name__ == "__main__":
    main()
