"""Simulates a handful of Assessor-role users logging into the live GRC API,
picking up their open risk assessments, and submitting scored answers —
the same flow the Assessor Portal (frontend/app/assessor) drives, just
scripted end to end.

Talks to the running backend over HTTP, so it exercises the real
`/risk-assessments/{id}/submit` endpoint (including its Assessor/Administrator
role gate) exactly as a browser session would. Requires
`uvicorn main:app --port 8050` already running.
"""

import os
import random

import httpx

API = os.environ.get("GRC_API_URL", "http://127.0.0.1:8050")
DEMO_PASSWORD = "changeme123"
PERSONA_COUNT = 3
ASSESSMENTS_PER_PERSONA = 2

JUSTIFICATIONS = [
    "Verified via the most recent control test result on file.",
    "Confirmed with the control owner during this cycle's walkthrough.",
    "Evidence attached; no exceptions noted this period.",
    "Partial evidence only — flagged for follow-up next cycle.",
]


def login(client: httpx.Client, username: str) -> str:
    resp = client.post(f"{API}/api/v1/auth/login", json={"username": username, "password": DEMO_PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]


def assessor_users(client: httpx.Client) -> list[dict]:
    roles = {r["id"]: r["name"] for r in client.get(f"{API}/api/v1/roles").json()}
    users = client.get(f"{API}/api/v1/users").json()
    return [u for u in users if u["active"] and roles.get(u["role_id"]) in ("Assessor", "Administrator")]


def main() -> None:
    with httpx.Client(timeout=10.0) as client:
        candidates = assessor_users(client)
        personas = random.sample(candidates, min(PERSONA_COUNT, len(candidates)))
        open_assessments = client.get(f"{API}/api/v1/risk-assessments", params={"state": "Not Started"}).json()
        random.shuffle(open_assessments)

        print(f"📝 Assessor Agent: simulating {len(personas)} assessors against {API}")

        cursor = 0
        for persona in personas:
            username = persona["username"]
            try:
                token = login(client, username)
            except httpx.HTTPStatusError:
                print(f"  ⚠️  {username} could not log in (inactive?) — skipping")
                continue
            headers = {"Authorization": f"Bearer {token}"}

            batch = open_assessments[cursor : cursor + ASSESSMENTS_PER_PERSONA]
            cursor += ASSESSMENTS_PER_PERSONA
            if not batch:
                print(f"  ℹ️  {username}: no open assessments left to take")
                continue

            for assessment in batch:
                template_id = assessment.get("template_id")
                if not template_id:
                    continue
                questions = client.get(
                    f"{API}/api/v1/assessment-questions", params={"template_id": template_id}
                ).json()
                if not questions:
                    continue

                answers = [
                    {
                        "question_id": q["id"],
                        "selected_value": random.randint(1, 5),
                        "justification": random.choice(JUSTIFICATIONS),
                    }
                    for q in questions
                ]

                resp = client.post(
                    f"{API}/api/v1/risk-assessments/{assessment['id']}/submit",
                    headers=headers,
                    json={"answers": answers},
                )
                if resp.status_code >= 400:
                    print(f"  ⚠️  {username}: assessment #{assessment['id']} submit failed ({resp.status_code})")
                    continue
                result = resp.json()
                print(f"  ✅ {username}: submitted assessment #{assessment['id']} — score {result['score']}")

        print("🎯 Assessor Agent complete.")


if __name__ == "__main__":
    main()
